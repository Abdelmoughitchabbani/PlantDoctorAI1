import os
import io
import base64
import cv2
import numpy as np
import sqlite3
import requests
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# 1. Model ve Donanım Hazırlığı
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

with open("classes.txt", "r", encoding="utf-8") as f:
    class_names = [line.strip() for line in f.readlines()]

num_classes = len(class_names)

model = models.resnet50(weights=None)
num_features = model.fc.in_features
model.fc = nn.Linear(num_features, num_classes)
model.load_state_dict(torch.load("plant_disease_resnet50.pth", map_location=device))
model = model.to(device)
model.eval()

# ----------------- GRAD-CAM (EXPLAINABLE AI) ----------------- #
class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_full_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate_heatmap(self, input_tensor, class_idx):
        self.model.zero_grad()
        output = self.model(input_tensor)
        
        target = output[0, class_idx]
        target.backward()

        gradients = self.gradients[0].cpu().data.numpy()
        activations = self.activations[0].cpu().data.numpy()

        weights = np.mean(gradients, axis=(1, 2))
        cam = np.zeros(activations.shape[1:], dtype=np.float32)

        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = np.maximum(cam, 0)
        cam = cv2.resize(cam, (224, 224))
        cam = cam - np.min(cam)
        cam_max = np.max(cam)
        if cam_max > 0:
            cam = cam / cam_max
        return cam

# ResNet-50'nin son konvolüsyon katmanı
grad_cam = GradCAM(model, model.layer4)

def overlay_cam_on_image(original_image_bytes, cam_mask):
    img = Image.open(io.BytesIO(original_image_bytes)).convert("RGB")
    img = img.resize((224, 224))
    img_np = np.array(img)

    heatmap = cv2.applyColorMap(np.uint8(255 * cam_mask), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

    superimposed = np.uint8(0.6 * img_np + 0.4 * heatmap)
    
    buffered = io.BytesIO()
    Image.fromarray(superimposed).save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

PLANTNET_API_KEY = "2b10vhHLKGRGrCf0En1VSnpHe"
PLANTNET_ENDPOINT = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANTNET_API_KEY}"

def plantnet_tanimla(resim_bytes):
    try:
        files = [('images', ('leaf.jpg', resim_bytes, 'image/jpeg'))]
        data = {'organs': ['leaf']}
        res = requests.post(PLANTNET_ENDPOINT, files=files, data=data, timeout=8)
        if res.status_code == 200:
            ilk_eslesme = res.json()['results'][0]
            return {
                "bilimsel_ad": ilk_eslesme['species']['scientificNameWithoutAuthor'],
                "skor": round(ilk_eslesme['score'] * 100, 2)
            }
    except Exception as e:
        print(f"Pl@ntNet API Hatası: {e}")
    return None

def veritabani_protokol_getir(sinif_adi):
    conn = sqlite3.connect("plant_doctor.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT turkce_ad, bitki_turu, hastalik_tipi, belirtiler, biyolojik_tedavi, 
               kimyasal_tedavi, onleyici_tedbirler, optimum_nem, optimum_sicaklik 
        FROM hastaliklar WHERE sinif_adi = ?
    """, (sinif_adi,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "turkce_ad": row[0],
            "bitki_turu": row[1],
            "hastalik_tipi": row[2],
            "belirtiler": row[3],
            "biyolojik_tedavi": row[4],
            "kimyasal_tedavi": row[5],
            "onleyici_tedbirler": row[6],
            "optimum_nem": row[7],
            "optimum_sicaklik": row[8]
        }
    return None

def varsayilan_kullanici_id():
    conn = sqlite3.connect("plant_doctor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def teshis_kaydet(user_id, sinif, turkce_ad, skor, lat, lon, temp, hum, risk):
    try:
        if not user_id:
            user_id = varsayilan_kullanici_id()

        conn = sqlite3.connect("plant_doctor.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO teshis_kayitlari 
            (user_id, teshis_edilen_sinif, turkce_ad, guven_skoru, enlem, boylam, sicaklik, nem, risk_durumu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, str(sinif), str(turkce_ad), float(skor), float(lat), float(lon), float(temp), float(hum), str(risk)))
        conn.commit()
        conn.close()
        print(f"[DB BAŞARILI] {turkce_ad} kaydı user_id={user_id} için eklendi.")
        return True
    except Exception as e:
        print(f"[DB HATA] teshis_kayitlari tablosuna eklenemedi: {e}")
        return False

# ----------------- CANLI HAVA DURUMU (OPEN-METEO REST API) ----------------- #
@app.route("/api/hava-durumu", methods=["GET"])
def get_live_weather():
    lat = request.args.get("lat", default=40.8438, type=float)
    lon = request.args.get("lon", default=31.1565, type=float)
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            curr = data.get("current", {})
            return jsonify({
                "durum": "basarili",
                "sicaklik": curr.get("temperature_2m", 24.0),
                "nem": curr.get("relative_humidity_2m", 80.0)
            }), 200
    except Exception as e:
        print(f"Hava durumu servisi hatası: {e}")
        
    return jsonify({"durum": "varsayilan", "sicaklik": 24.0, "nem": 80.0}), 200

# ----------------- KULLANICI İŞLEMLERİ (AUTH) ----------------- #
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    tam_ad = data.get("tam_ad", "").strip()
    email = data.get("email", "").strip()
    sifre = data.get("sifre", "").strip()

    if not tam_ad or not email or not sifre:
        return jsonify({"durum": "hata", "mesaj": "Tüm alanlar zorunludur!"}), 400

    sifre_hash = generate_password_hash(sifre)

    try:
        conn = sqlite3.connect("plant_doctor.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (tam_ad, email, sifre_hash) VALUES (?, ?, ?)", 
                       (tam_ad, email, sifre_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return jsonify({
            "durum": "basarili",
            "mesaj": "Kayıt başarılı",
            "user_id": user_id,
            "tam_ad": tam_ad,
            "email": email
        }), 201
    except sqlite3.IntegrityError:
        return jsonify({"durum": "hata", "mesaj": "Bu e-posta adresi zaten kayıtlı!"}), 409
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    sifre = data.get("sifre", "").strip()

    if not email or not sifre:
        return jsonify({"durum": "hata", "mesaj": "E-posta ve şifre zorunludur!"}), 400

    conn = sqlite3.connect("plant_doctor.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, tam_ad, email, sifre_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[3], sifre):
        return jsonify({
            "durum": "basarili",
            "mesaj": "Giriş başarılı",
            "user_id": user[0],
            "tam_ad": user[1],
            "email": user[2]
        }), 200
    else:
        return jsonify({"durum": "hata", "mesaj": "E-posta veya şifre hatalı!"}), 401

@app.route("/api/gecmis", defaults={"user_id": None}, methods=["GET"])
@app.route("/api/gecmis/<int:user_id>", methods=["GET"])
@app.route("/api/history/<int:user_id>", methods=["GET"])
def get_user_history(user_id):
    try:
        conn = sqlite3.connect("plant_doctor.db")
        cursor = conn.cursor()
        
        # Harita ve geçmiş için enlem ve boylam da çekilir
        if user_id:
            cursor.execute("""
                SELECT id, tarih, teshis_edilen_sinif, turkce_ad, guven_skoru, sicaklik, nem, risk_durumu, enlem, boylam
                FROM teshis_kayitlari WHERE user_id = ? ORDER BY id DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT id, tarih, teshis_edilen_sinif, turkce_ad, guven_skoru, sicaklik, nem, risk_durumu, enlem, boylam
                FROM teshis_kayitlari ORDER BY id DESC LIMIT 50
            """)

        rows = cursor.fetchall()
        conn.close()

        kayitlar = []
        for r in rows:
            kayitlar.append({
                "id": r[0],
                "tarih": str(r[1])[:16],
                "sinif": r[2],
                "turkce_ad": r[3] if r[3] else r[2],
                "guven_skoru": r[4],
                "sicaklik": r[5] if r[5] is not None else 24.0,
                "nem": r[6] if r[6] is not None else 82.0,
                "risk_durumu": r[7] if r[7] else "Normal Saha Şartları",
                "enlem": r[8] if r[8] is not None else 40.8438,
                "boylam": r[9] if r[9] is not None else 31.1565
            })
        return jsonify({"durum": "basarili", "kayitlar": kayitlar}), 200
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

# ----------------- TEŞHİS VE KARAR DESTEK ENDPOINT ----------------- #
@app.route("/api/teshis", methods=["POST"])
def teshis_et():
    if "image" not in request.files:
        return jsonify({"hata": "Görsel yüklenmedi"}), 400

    file = request.files["image"]
    img_bytes = file.read()

    raw_user_id = request.form.get("user_id", default=None)
    user_id = None
    if raw_user_id not in (None, "", "null", "undefined", "None"):
        try:
            user_id = int(raw_user_id)
        except ValueError:
            user_id = None

    print(f"--> Gelen Analiz İsteği - user_id: {user_id} (Ham Değer: {raw_user_id})")

    # Model Tahmini
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    tensor_img = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        ciktilar = model(tensor_img)
        olasiliklar = torch.nn.functional.softmax(ciktilar[0], dim=0)
        en_yuksek_olasilik, index = torch.max(olasiliklar, 0)

    tahmin_sinifi = class_names[index.item()]
    guven_skoru = round(en_yuksek_olasilik.item() * 100, 2)
    
    # Grad-CAM Isı Haritası
    cam_mask = grad_cam.generate_heatmap(tensor_img, index.item())
    heatmap_base64 = overlay_cam_on_image(img_bytes, cam_mask)

    plantnet_sonuc = plantnet_tanimla(img_bytes)
    tedavi = veritabani_protokol_getir(tahmin_sinifi)

    lat = float(request.form.get("lat", 40.8438))
    lon = float(request.form.get("lon", 31.1565))
    temp = float(request.form.get("temp", 24.0))
    hum = float(request.form.get("humidity", 82.0))

    risk_durumu = "Normal Saha Şartları"
    if tedavi and tedavi["hastalik_tipi"] != "Sağlıklı":
        opt_nem = tedavi["optimum_nem"]
        opt_sicaklik = tedavi["optimum_sicaklik"]

        if opt_nem and opt_sicaklik:
            if hum >= (opt_nem - 10) and abs(temp - opt_sicaklik) <= 5:
                risk_durumu = f"⚠️ Yüksek Risk: Mevcut mikroklima ({temp}°C, %{hum} Nem), bu {tedavi['hastalik_tipi'].lower()} patojenin çoğalması için ideal!"
            else:
                risk_durumu = "Orta Risk: Çevresel koşullar patojen patlaması için sınırda."

    turkce_ad = tedavi["turkce_ad"] if tedavi else tahmin_sinifi

    kaydedildi = teshis_kaydet(user_id, tahmin_sinifi, turkce_ad, guven_skoru, lat, lon, temp, hum, risk_durumu)

    yanit = {
        "teshis": {
            "model_sinif": tahmin_sinifi,
            "turkce_ad": turkce_ad,
            "hastalik_tipi": tedavi["hastalik_tipi"] if tedavi else "Bilinmiyor",
            "guven_skoru": f"%{guven_skoru}"
        },
        "botanik_dogrulama": plantnet_sonuc,
        "cevre_ve_konum": {
            "koordinatlar": {"enlem": lat, "boylam": lon},
            "olculen_nem": f"%{hum}",
            "olculen_sicaklik": f"{temp}°C",
            "karar_destek_uyarisi": risk_durumu
        },
        "tedavi_onerileri": tedavi,
        "isi_haritasi": f"data:image/jpeg;base64,{heatmap_base64}",
        "db_kayit": kaydedildi
    }

    return jsonify(yanit), 200
# ----------------- DR. FLORA - AKILLI ZİRAİ ASİSTAN (CHATBOT) ----------------- #
@app.route("/api/chatbot", methods=["POST"])
def flora_chat():
    data = request.get_json() or {}
    user_msg = data.get("mesaj", "").strip().lower()
    last_context = data.get("baglam", {})

    if not user_msg:
        return jsonify({"yanit": "Merhaba! Ben Dr. Flora. Bitki sağlığı, zirai hastalıklar veya ilaçlama ile ilgili bana soru sorabilirsiniz."})

    # 1. Selamlaşma / Tanışma
    if any(w in user_msg for w in ["merhaba", "selam", "kimsin", "dr flora", "flora"]):
        return jsonify({
            "yanit": "Merhaba! Ben <strong>Dr. Flora</strong>, PlantDoctorAI platformunun akıllı ziraat asistanıyım. En son gerçekleştirdiğiniz teşhis sonuçları, ilaçlama dozu, sulama veya kültürel mücadele ile ilgili sorularınızı yanıtlayabilirim. 🌱"
        })

    # 2. Mevcut Teşhis Üzerinden Sorulan Sorular
    current_disease = last_context.get("turkce_ad")
    treatment = last_context.get("tedavi_onerileri")

    if current_disease and any(w in user_msg for w in ["bu hastalık", "tedavi", "ne yapmalıyım", "ilaç", "nasıl geçer", "çözüm"]):
        if treatment:
            return jsonify({
                "yanit": f"Şu an analiz edilen <strong>{current_disease}</strong> için tavsiyelerim:<br><br>"
                         f"🌿 <strong>Biyolojik & Kültürel:</strong> {treatment.get('biyolojik_tedavi', 'Belirtilmedi')}<br><br>"
                         f"🧪 <strong>Kimyasal İlaçlama:</strong> {treatment.get('kimyasal_tedavi', 'Belirtilmedi')}<br><br>"
                         f"⚠️ <em>Not: İlaçlamayı güneşin dik olmadığı sabah erken veya akşamüstü saatlerinde yapınız.</em>"
            })

    # 3. Sulama / Su Yönetimi
    if any(w in user_msg for w in ["sulama", "su", "ne zaman sulanır"]):
        return jsonify({
            "yanit": "Sulama yaparken mantari ve bakteriyel hastalıkların yayılmaması için yaprakları ıslatan yağmurlama yerine mutlaka <strong>damla sulama</strong> tercih edilmelidir. Sulamayı yaprakların hızla kuruyabileceği sabah erken saatlerde yapmanız önerilir."
        })

    # 4. İlaçlama Saati ve Koşulları
    if any(w in user_msg for w in ["saat", "rüzgar", "hava", "ne zaman ilaç"]):
        return jsonify({
            "yanit": "Zirai ilaçlama için en ideal zaman <strong>rüzgarsız hava</strong> ve <strong>25°C altı sıcaklıktır</strong> (genellikle sabah 06:00-09:00 veya akşam 17:00-19:00 arası). Yağmur beklentisi varsa ilaçlama ertelenmelidir; aksi halde ilaç yıkanır."
        })

    # 5. Gübreleme / Besleme
    if any(w in user_msg for w in ["gübre", "azot", "potasyum", "kalsiyum"]):
        return jsonify({
            "yanit": "Hastalık döneminde aşırı <strong>azotlu gübrelemeden</strong> kaçınınız; fazla azot dokuları yumuşatarak mantar ve böcek girişini kolaylaştırır. Bitki bağışıklığını artırmak için dengeli <strong>potasyum ve kalsiyum</strong> takviyesi önerilir."
        })

    # 6. Veritabanından Genel Hastalık Sorgusu
    try:
        conn = sqlite3.connect("plant_doctor.db")
        cursor = conn.cursor()
        cursor.execute("SELECT turkce_ad, biyolojik_tedavi, kimyasal_tedavi FROM hastaliklar")
        all_diseases = cursor.fetchall()
        conn.close()

        for d_name, bio, chem in all_diseases:
            if d_name.lower() in user_msg:
                return jsonify({
                    "yanit": f"<strong>{d_name}</strong> hakkında protokolüm:<br><br>"
                             f"🌿 <strong>Biyolojik Mücadele:</strong> {bio}<br><br>"
                             f"🧪 <strong>Kimyasal Tedavi:</strong> {chem}"
                })
    except Exception as e:
        print(f"Chatbot DB sorgu hatası: {e}")

    # Varsayılan Zirai Danışman Yanıtı
    return jsonify({
        "yanit": "Bu konuda bitkinizin taze yaprak fotoğrafını <strong>Teşhis & Tarama</strong> sekmesinden yükleyerek analiz başlatabilirsiniz. Analiz sonrası patojenin türüne göre en doğru tedavi protokolünü anında sunabilirim. 🌿"
    })
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)