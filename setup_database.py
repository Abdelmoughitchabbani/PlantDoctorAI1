import sqlite3

def veritabani_olustur():
    conn = sqlite3.connect("plant_doctor.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Table dial l-Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tam_ad TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        sifre_hash TEXT NOT NULL,
        kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Table dial l-Amrad w l-Wasfat
    cursor.execute("DROP TABLE IF EXISTS hastaliklar")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hastaliklar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sinif_adi TEXT UNIQUE NOT NULL,
        turkce_ad TEXT NOT NULL,
        bitki_turu TEXT NOT NULL,
        hastalik_tipi TEXT NOT NULL,
        belirtiler TEXT NOT NULL,
        biyolojik_tedavi TEXT NOT NULL,
        kimyasal_tedavi TEXT NOT NULL,
        onleyici_tedbirler TEXT NOT NULL,
        optimum_nem REAL,
        optimum_sicaklik REAL
    )
    """)

    # 3. Table dial l-Histori m-rebota b User ID
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teshis_kayitlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        teshis_edilen_sinif TEXT NOT NULL,
        turkce_ad TEXT,
        guven_skoru REAL NOT NULL,
        enlem REAL,
        boylam REAL,
        sicaklik REAL,
        nem REAL,
        risk_durumu TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)

    # 38 Classes kamlin b les détails dialhom
    veriler = [
        # Elma (Apple)
        ("Apple___Apple_scab", "Elma Karalekesi", "Elma", "Mantari",
         "Yapraklarda zeytin yeşili lekeler, zamanla nekrotik kahverengileşme ve deformasyon.",
         "Etkilenen yaprakları toplayıp yakın veya gömün; taç içine hava girmesi için budama yapın.",
         "Bakır sülfat, Kaptan veya Difenokonazol etken maddeli fungisitler.",
         "Sabah erken sulama yaparak yaprak ıslaklık süresini minimumda tutun.", 80.0, 18.0),

        ("Apple___Black_rot", "Elma Siyah Çürüklüğü", "Elma", "Mantari",
         "Yapraklarda kurbağa gözü benzeri konsantrik halkalı lekeler, meyvede siyah çürüklük.",
         "Kanserli dalları en az 15 cm geriden budayın; mumyalaşmış meyveleri bahçeden uzaklaştırın.",
         "Tiyofanat-metil veya Bakır bazlı fungisit uygulaması.",
         "Ağaç kabuğundaki yaralanmaları aşı macunu ile kapatın.", 75.0, 24.0),

        ("Apple___Cedar_apple_rust", "Elma Pas Hastalığı", "Elma", "Mantari",
         "Yaprak üst yüzeyinde parlak sarı-turuncu lekeler, alt yüzeyde tüpsü spor çıkıntıları.",
         "Bahçe çevresindeki yabani ardıç (Juniperus) ağaçlarını temizleyin.",
         "Mankozeb veya Miklobutanil içeren sistemik mantar ilaçları.",
         "Dirençli elma çeşitleri tercih edilmeli ve ara konukçular kesilmelidir.", 85.0, 15.0),

        ("Apple___healthy", "Sağlıklı Elma Yaprağı", "Elma", "Sağlıklı",
         "Yaprak dokusu homojen, lekesiz, fotosentez kapasitesi optimal.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Düzenli damla sulama, dengeli taban ve yaprak gübrelemesi.", None, None),

        # Yaban Mersini (Blueberry)
        ("Blueberry___healthy", "Sağlıklı Yaban Mersini", "Yaban Mersini", "Sağlıklı",
         "Düzgün klorofil dağılımı, sağlam kutikula tabakası, hastalık lezyonu yok.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Toprak pH derecesini 4.5-5.2 aralığında tutun; asidik malçlama yapın.", None, None),

        # Kiraz / Vişne (Cherry)
        ("Cherry_(including_sour)___Powdery_mildew", "Kiraz Külleme Hastalığı", "Kiraz", "Mantari",
         "Genç yaprak ve sürgünlerde beyaz unsu toz tabakası, kıvrılma ve kuruma.",
         "Sürgün uçlarındaki enfekte kısımları budayın; kükürt tozlaması yapın.",
         "Kükürt (WP) veya Tebukonazol içerikli sistemik fungisitler.",
         "Aşırı azotlu gübrelemeden kaçının; hava akımını kesen sık dikimi engelleyin.", 60.0, 22.0),

        ("Cherry_(including_sour)___healthy", "Sağlıklı Kiraz Yaprağı", "Kiraz", "Sağlıklı",
         "Pürüzsüz yaprak yüzeyi, klorofil yoğunluğu normal, canlı doku.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Dengeli sulama, kış budaması ve bordo bulamacı ile standart koruma.", None, None),

        # Mısır (Corn / Maize)
        ("Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Mısır Gri Yaprak Lekesi", "Mısır", "Mantari",
         "Yaprak damarları arasında dikdörtgen şeklinde uzun gri-kahverengi nekrotik lezyonlar.",
         "Hasat sonrası anız artıklarını derin sürümle toprağa gömün.",
         "Azoksistrobin veya Piraklostrobin kombinasyonlu fungisitler.",
         "En az 2 yıllık münavebe (ekim nöbeti) uygulayın; dayanıklı hibrit tohum seçin.", 90.0, 27.0),

        ("Corn_(maize)___Common_rust_", "Mısır Pas Hastalığı", "Mısır", "Mantari",
         "Yaprağın her iki yüzeyinde tarçın kahverengisi tozlu püstüller (spor yığınları).",
         "Dayanıklı genotipler kullanın; yabancı ot mücadelesi yapın.",
         "Hastalık erken evrede fark edilirse Tebuconazole uygulaması.",
         "Erken ekim yaparak bitkinin kritik dönemi spor uçuşundan önce geçmesini sağlayın.", 80.0, 18.0),

        ("Corn_(maize)___Northern_Leaf_Blight", "Mısır Kuzey Yaprak Yanıklığı", "Mısır", "Mantari",
         "Yapraklarda puro biçiminde büyük, eliptik gri-yeşil veya soluk kahverengi yanık lekeleri.",
         "Bulaşık bitki artıklarını tarladan uzaklaştırın veya derine gömün.",
         "Propikonazol veya Difenokonazol etken maddeli ilaçlama.",
         "Dayanıklı tohum varyeteleri ekin; aşırı yağmurlama sulamadan kaçının.", 85.0, 20.0),

        ("Corn_(maize)___healthy", "Sağlıklı Mısır Yaprağı", "Mısır", "Sağlıklı",
         "Geniş yaprak ayası canlı yeşil renkte, lezyon ve nekroz bulunmamaktadır.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Döneme uygun çinko ve azot takviyesi, düzenli sulama.", None, None),

        # Üzüm (Grape)
        ("Grape___Black_rot", "Bağ Siyah Çürüklüğü", "Üzüm", "Mantari",
         "Yapraklarda kırmızımsı kahverengi dairesel lekeler, salkımlarda kuruma ve mumyalaşma.",
         "Enfekte salkım ve yaprakları toplayıp imha edin; asma altını temiz tutun.",
         "Mankozeb veya Miklobutanil içeren fungisitlerle erken ilkbahar ilaçlaması.",
         "Asmaları yerden yüksekte telli terbiye sistemine alın.", 80.0, 24.0),

        ("Grape___Esca_(Black_Measles)", "Bağ Kav (Esca) Hastalığı", "Üzüm", "Mantari",
         "Yaprak damarları arasında kaplan postu deseni oluşturan sarı-kırmızı nekrozlar.",
         "Hastalıklı omcaları işaretleyip kışın ayrı aletle budayın ve aletleri dezenfekte edin.",
         "Doğrudan etkili kimyasal çözümü yoktur; yaralara aşı macunu sürülmelidir.",
         "Budama yaralarını açık bırakmayın; don veya budama sonrası koruyucu ilaç atın.", 70.0, 25.0),

        ("Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Bağ Yaprak Yanıklığı", "Üzüm", "Mantari",
         "Yaprak üzerinde düzensiz koyu kahverengi lekeler, yaprak kenarlarında kuruma.",
         "Hava akımını engelleyen obur sürgünleri seyreltin.",
         "Bakırlı preparatlar veya Kaptan ile ilaçlama.",
         "Bağ içi yabancı ot kontrolü sağlayarak taban nemini düşürün.", 75.0, 22.0),

        ("Grape___healthy", "Sağlıklı Üzüm Yaprağı", "Üzüm", "Sağlıklı",
         "Canlı yeşil, karakteristik dilimli yaprak yapısı, hastalık emaresi yok.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Yıllık kış budaması, dengeli potasyum gübrelemesi.", None, None),

        # Portakal / Narenciye (Orange)
        ("Orange___Haunglongbing_(Citrus_greening)", "Narenciye Yeşillenme (Huanglongbing)", "Narenciye", "Bakteriyel",
         "Yapraklarda asimetrik sarı beneklenme (mottling), damarlarda kalınlaşma ve mantarlaşma.",
         "Bakteriyi taşıyan Psillid vektör böcekleriyle biyolojik mücadele (ör. Tamarixia radiata).",
         "Doğrudan kimyasal tedavisi yoktur; vektör böceklere karşı İnsektisit uygulanır.",
         "Karantina kurallarına kesinlikle uyun; hastalıklı ağaçları kökleyip yakın.", 70.0, 28.0),

        # Şeftali (Peach)
        ("Peach___Bacterial_spot", "Şeftali Bakteriyel Leke", "Şeftali", "Bakteriyel",
         "Yapraklarda su emmiş gibi küçük lekeler, zamanla delinme ('saçma deliği' görünümü).",
         "Bakteriostatik bakırlı bileşikler; hastalıklı sürgünlerin budanması.",
         "Sonbaharda yaprak dökümünde %2'lik, ilkbaharda gözler uyanırken %1'lik Bordo Bulamacı.",
         "Hassas çeşitlerden kaçının; rüzgar kıranlar oluşturarak yaprak sürtünmesini önleyin.", 85.0, 22.0),

        ("Peach___healthy", "Sağlıklı Şeftali Yaprağı", "Şeftali", "Sağlıklı",
         "Mızraksı yaprak formu düzgün, parlak yeşil ve lezyonsuz.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Düzenli sulama ve kış mücadelesi programı.", None, None),

        # Biber (Pepper Bell)
        ("Pepper,_bell___Bacterial_spot", "Biber Bakteriyel Leke", "Biber", "Bakteriyel",
         "Yapraklarda sarı haleli küçük dairesel kahverengi lekeler, yaprak dökülmesi.",
         "Tohumları sıcak su dezenfeksiyonundan geçirin; hastalıklı fideleri tarlaya dikmeyin.",
         "Bakır hidroksit ve mankozeb karışımlı koruyucu bakterisit uygulaması.",
         "Damla sulama kullanın; yaprakları ıslatacak üstten sulamadan kesinlikle kaçının.", 85.0, 26.0),

        ("Pepper,_bell___healthy", "Sağlıklı Biber Yaprağı", "Biber", "Sağlıklı",
         "Pürüzsüz, koyu yeşil ve dik yaprak formu; patojen yok.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Dengeli kalsiyum ve magnezyum beslemesi; düzenli havalandırma.", None, None),

        # Patates (Potato)
        ("Potato___Early_blight", "Patates Erken Yanıklık", "Patates", "Mantari",
         "Yaşlı alt yapraklarda hedef tahtasına benzeyen iç içe halkalı koyu kahverengi lekeler.",
         "Bitki artıklarını tarladan uzaklaştırın; dengeli azot-fosfor gübrelemesi yapın.",
         "Mankozeb, Klorotalonil veya Difenokonazol fungisitleri.",
         "3-4 yıllık ekim nöbeti uygulayın; patates ardına domates ekmeyin.", 80.0, 24.0),

        ("Potato___Late_blight", "Patates Geç Yanıklık (Mildiyö)", "Patates", "Mantari",
         "Yaprak uçlarında hızla büyüyen su damlası şeklinde koyu lezyonlar, yaprak altında beyaz küf.",
         "Hastalık görülen ocakları hemen sökün; aşırı sulamayı durdurun.",
         "Metalaksil, Simoksanil veya Bakır bazlı sistemik fungisitler.",
         "Sertifikalı temiz tohumluk yumru kullanın; sıraları hakim rüzgara paralel dikin.", 90.0, 18.0),

        ("Potato___healthy", "Sağlıklı Patates Yaprağı", "Patates", "Sağlıklı",
         "Bileşik yapraklar homojen renk ve yapıda, turgor basıncı dengeli.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Boğaz doldurma işlemini zamanında yapın; taban nemini kontrol edin.", None, None),

        # Ahududu (Raspberry)
        ("Raspberry___healthy", "Sağlıklı Ahududu Yaprağı", "Ahududu", "Sağlıklı",
         "Tırtıklı yaprak kenarları temiz, leke ve deformasyon yok.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Düzenli organik madde takviyesi ve budama.", None, None),

        # Soya Fasulyesi (Soybean)
        ("Soybean___healthy", "Sağlıklı Soya Fasulyesi", "Soya", "Sağlıklı",
         "Üçlü yaprakçıklar sağlıklı klorofil düzeyinde, lekesiz.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Rizobiyum bakteri aşılaması ve uygun sıra arası çapalama.", None, None),

        # Kabak (Squash)
        ("Squash___Powdery_mildew", "Kabak Külleme Hastalığı", "Kabak", "Mantari",
         "Geniş yaprak ayasında un serpilmiş gibi beyaz pudramsı lekeler, yaprakta kuruma.",
         "Kabakgil yabancı otlarını temizleyin; hastalıklı yaşlı yaprakları budayın.",
         "Kükürt, Azoksistrobin veya Miklobutanil içeren fungisitler.",
         "Bitkileri sık dikmeyin; gölgeli alanlar yerine tam güneş alan yerleri seçin.", 70.0, 26.0),

        # Çilek (Strawberry)
        ("Strawberry___Leaf_scorch", "Çilek Yaprak Yanıklığı", "Çilek", "Mantari",
         "Yapraklarda mor-kırmızı haleli düzensiz koyu lekeler; yaprak kenarlarında yanıklık.",
         "Hasat sonrasında yaşlı yaprakları biçip tarladan uzaklaştırın.",
         "Bakır oksiklorür veya Kaptan ile koruyucu ilaçlama.",
         "Plastik malç kullanarak yaprakların toprakla temasını engelleyin.", 85.0, 20.0),

        ("Strawberry___healthy", "Sağlıklı Çilek Yaprağı", "Çilek", "Sağlıklı",
         "Üç parçalı yaprak ayası canlı yeşil ve sağlam dokuda.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Damla sulama borularını kontrol edin, malçlamayı koruyun.", None, None),

        # Domates (Tomato)
        ("Tomato___Bacterial_spot", "Domates Bakteriyel Leke", "Domates", "Bakteriyel",
         "Yapraklarda yağ lekesi şeklinde başlayan, zamanla kahverengileşen sarı haleli küçük benekler.",
         "Bakır ve Bacillus subtilis biyopreparatları; seralarda hava sirkülasyonu.",
         "Bakır hidroksit veya Bakır oksiklorür uygulaması.",
         "Tohumları 50°C sıcak suda 25 dakika tutarak termoterapi uygulayın.", 85.0, 27.0),

        ("Tomato___Early_blight", "Domates Erken Yanıklık", "Domates", "Mantari",
         "Yapraklarda konsantrik halkalı hedef tahtası lezyonları, sararma ve yaprak dökümü.",
         "Toprağı siyah malç ile örtün; alt yaprakları zamanında budayın.",
         "Mankozeb, Klorotalonil veya Difenokonazol fungisitleri.",
         "Seraları düzenli havalandırarak oransal nemi %70'in altında tutun.", 80.0, 24.0),

        ("Tomato___Late_blight", "Domates Geç Yanıklık (Mildiyö)", "Domates", "Mantari",
         "Yapraklarda geniş, yağ lekesi benzeri hızla kararan alanlar, nemli havada beyaz küf tabakası.",
         "Hastalıklı fideleri derhal imha edin; damla sulamaya geçin.",
         "Metalaksil, Dimetomorf veya Fosetil-Al sistemik fungisitleri.",
         "Serin ve aşırı nemli hava dalgalarında önleyici temas etkili ilaçlama yapın.", 90.0, 19.0),

        ("Tomato___Leaf_Mold", "Domates Yaprak Küfü", "Domates", "Mantari",
         "Yaprak üstünde soluk sarı lekeler, alt yüzeyinde ise zeytin yeşili-kahverengi kadifemsi küf.",
         "Sera oransal nemini düşürün; bitkileri havalandıracak aralıklarla dikin.",
         "Bakırlı fungisitler veya Boskalid etken maddesi.",
         "Gece ve gündüz sera sıcaklık farkını azaltarak yoğuşmayı önleyin.", 85.0, 22.0),

        ("Tomato___Septoria_leaf_spot", "Domates Septoria Yaprak Lekesi", "Domates", "Mantari",
         "Yapraklarda kenarları koyu, merkezi açık gri çok sayıda küçük dairesel leke.",
         "Enfekte alt yaprakları erkenden koparın; tarladaki solanaceae artıklarını yakın.",
         "Klorotalonil veya Mankozeb etken maddeli koruyucu ilaçlama.",
         "Yağmurlama sulamadan kaçının; bitki tabanına su sıçramasını önleyin.", 85.0, 23.0),

        ("Tomato___Spider_mites Two-spotted_spider_mite", "İki Noktalı Kırmızı Örümcek Zararı", "Domates", "Zararlı / Akar",
         "Yaprak üstünde minik sarı-beyaz noktacıklar, yaprak altında ince ipeksi ağlar ve bronzlaşma.",
         "Yırtıcı akar salımı (Phytoseiulus persimilis) ile biyolojik kontrol.",
         "Abamektin, Spiromesifen veya Heksitiyazoks içerikli akarisitler.",
         "Tarlanın tozlu olmasını engelleyin; tarla kenarındaki yabani otları biçin.", 40.0, 30.0),

        ("Tomato___Target_Spot", "Domates Hedef Leke Hastalığı", "Domates", "Mantari",
         "Yapraklarda belirgin hedef tahtası şeklinde halkalı koyu kahverengi nekrozlar.",
         "Sıra aralarını geniş tutarak hava akımı sağlayın; hastalıklı dokuları uzaklaştırın.",
         "Azoksistrobin veya Klorotalonil içerikli fungisitler.",
         "Aşırı nemli periyotlarda koruyucu kimyasal kalkan oluşturun.", 80.0, 25.0),

        ("Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Domates Sarı Yaprak Kıvırcıklık Virüsü (TYLCV)", "Domates", "Viral",
         "Yapraklarda yukarı doğru fincan şeklinde kıvrılma, sararma, boğum aralarında kısalma ve bodurluk.",
         "Sarı yapışkan tuzaklar kurun; tül geçirerek Beyazsinek girişini engelleyin.",
         "Virüsün ilacı yoktur; vektör Beyazsinek (Bemisia tabaci) ile İnsektisitle mücadele edilir.",
         "Dirençli çeşit tohumları ekin; bulaşık fideleri derhal söküp torbaya koyarak atın.", 60.0, 28.0),

        ("Tomato___Tomato_mosaic_virus", "Domates Mozaik Virüsü (ToMV)", "Domates", "Viral",
         "Yapraklarda koyu ve açık yeşil alacalı mozaik deseni, eğrelti otu benzeri yaprak deformasyonu.",
         "Budama aletlerini %10'luk çamaşır suyu veya yağsız süt ile dezenfekte edin.",
         "Kimyasal ilacı yoktur; mekanik taşınmayı engellemek esastır.",
         "Tütün kullanan işçilerin ellerini yıkamadan bitkilere dokunmasını engelleyin.", None, None),

        ("Tomato___healthy", "Sağlıklı Domates Yaprağı", "Domates", "Sağlıklı",
         "Bileşik yapraklar homojen koyu yeşil, yaprak ayası diri ve lekesiz.",
         "Müdahale gerekmez.", "Kimyasal uygulama önerilmez.",
         "Dengeli N-P-K gübreleme, damla sulama ve düzenli havalandırma takvimi.", None, None)
    ]

    cursor.execute("DELETE FROM hastaliklar")
    cursor.executemany("""
    INSERT INTO hastaliklar 
    (sinif_adi, turkce_ad, bitki_turu, hastalik_tipi, belirtiler, biyolojik_tedavi, kimyasal_tedavi, onleyici_tedbirler, optimum_nem, optimum_sicaklik)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, veriler)

    conn.commit()
    conn.close()
    print("Database b les tables dial users, hastaliklar w teshis_kayitlari t-sawat b naja7!")

if __name__ == "__main__":
    veritabani_olustur()