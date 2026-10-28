/* ============================================================
   Dr. Flora - Akıllı Zirai Karar Destek Asistanı (PlantDoctorAI)
   ============================================================ */

(function () {
    // 1. Dr. Flora için gerekli CSS Stilleri
    const style = document.createElement("style");
    style.innerHTML = `
        /* Yüzen Başlatıcı Buton */
        .flora-launcher {
            position: fixed;
            bottom: 28px;
            right: 28px;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            background: linear-gradient(135deg, #10b981, #059669);
            box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 9999;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 2px solid rgba(255, 255, 255, 0.25);
            font-size: 26px;
        }
        .flora-launcher:hover {
            transform: scale(1.08) translateY(-2px);
            box-shadow: 0 12px 30px rgba(16, 185, 129, 0.6);
        }

        /* Sohbet Kartı Penceresi */
        .flora-chat-card {
            position: fixed;
            bottom: 96px;
            right: 28px;
            width: 380px;
            height: 530px;
            background: #0f1420;
            border: 1px solid #2c3b55;
            border-radius: 18px;
            display: none;
            flex-direction: column;
            z-index: 9999;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75);
            overflow: hidden;
            font-family: 'Plus Jakarta Sans', sans-serif;
            animation: floraPop 0.25s ease-out forwards;
        }

        @keyframes floraPop {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .flora-header {
            padding: 16px 20px;
            background: #090c13;
            border-bottom: 1px solid #1e293b;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .flora-header-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .flora-status-dot {
            width: 9px;
            height: 9px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
        }
        .flora-close-btn {
            background: none;
            border: none;
            color: #94a3b8;
            font-size: 18px;
            cursor: pointer;
        }
        .flora-close-btn:hover { color: #f1f5f9; }

        .flora-body {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 13px;
        }

        .flora-msg {
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 12px;
            line-height: 1.5;
            word-break: break-word;
        }
        .flora-msg.bot {
            background: #141b2b;
            color: #f1f5f9;
            border: 1px solid #1e293b;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .flora-msg.user {
            background: #10b981;
            color: #042417;
            font-weight: 600;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }

        .flora-footer {
            padding: 12px 16px;
            background: #090c13;
            border-top: 1px solid #1e293b;
            display: flex;
            gap: 8px;
        }
        .flora-input {
            flex: 1;
            background: #141b2b;
            border: 1px solid #1e293b;
            color: #ffffff;
            font-family: inherit;
            font-size: 13px;
            padding: 9px 12px;
            border-radius: 8px;
            outline: none;
        }
        .flora-input:focus { border-color: #10b981; }
        .flora-send-btn {
            background: #10b981;
            border: none;
            color: #042417;
            font-weight: 700;
            padding: 9px 14px;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.15s;
        }
        .flora-send-btn:hover { background: #059669; }
    `;
    document.head.appendChild(style);

    // 2. Chatbot HTML Bileşenlerini Ekle
    const chatContainer = document.createElement("div");
    chatContainer.innerHTML = `
        <div class="flora-launcher" id="floraLauncher" title="Dr. Flora ile Sohbet Et">
            🌿
        </div>

        <div class="flora-chat-card" id="floraChatCard">
            <div class="flora-header">
                <div class="flora-header-info">
                    <span class="flora-status-dot"></span>
                    <div>
                        <div style="font-size: 14px; font-weight: 800; color: #ffffff;">Dr. Flora</div>
                        <div style="font-size: 11px; color: #10b981; font-weight: 600;">Zirai Karar Destek Asistanı</div>
                    </div>
                </div>
                <button class="flora-close-btn" id="floraCloseBtn">✕</button>
            </div>

            <div class="flora-body" id="floraMessages">
                <div class="flora-msg bot">
                    Merhaba! Ben <strong>Dr. Flora</strong>. Bitki sağlığı, yaptığınız son teşhisin reçetesi veya doğru ilaçlama saatleri hakkında bana dilediğinizi sorabilirsiniz! 🌱
                </div>
            </div>

            <div class="flora-footer">
                <input type="text" class="flora-input" id="floraInput" placeholder="Dr. Flora'ya bir soru sorun..." />
                <button class="flora-send-btn" id="floraSendBtn">Gönder</button>
            </div>
        </div>
    `;
    document.body.appendChild(chatContainer);

    // 3. Etkileşim ve API Mantığı
    const launcher = document.getElementById("floraLauncher");
    const chatCard = document.getElementById("floraChatCard");
    const closeBtn = document.getElementById("floraCloseBtn");
    const sendBtn = document.getElementById("floraSendBtn");
    const input = document.getElementById("floraInput");
    const messages = document.getElementById("floraMessages");

    launcher.addEventListener("click", () => {
        chatCard.style.display = (chatCard.style.display === "flex") ? "none" : "flex";
        if (chatCard.style.display === "flex") input.focus();
    });

    closeBtn.addEventListener("click", () => {
        chatCard.style.display = "none";
    });

    async function sendUserMessage() {
        const text = input.value.trim();
        if (!text) return;

        // Kullanıcı mesajını ekle
        appendMessage(text, "user");
        input.value = "";

        // En son yapılan teşhis bilgisini bağlam olarak al
        const contextData = (typeof lastDiagnosisResponse !== "undefined" && lastDiagnosisResponse) 
            ? lastDiagnosisResponse.teshis 
            : null;
        const treatmentData = (typeof lastDiagnosisResponse !== "undefined" && lastDiagnosisResponse) 
            ? lastDiagnosisResponse.tedavi_onerileri 
            : null;

        try {
            const res = await fetch("http://127.0.0.1:5000/api/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mesaj: text,
                    baglam: {
                        turkce_ad: contextData ? contextData.turkce_ad : null,
                        tedavi_onerileri: treatmentData
                    }
                })
            });

            const data = await res.json();
            appendMessage(data.yanit, "bot");
        } catch (e) {
            appendMessage("Şu anda sunucuyla iletişim kurulamıyor. Flask API'nin açık olduğundan emin olun.", "bot");
        }
    }

    function appendMessage(htmlContent, sender) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `flora-msg ${sender}`;
        msgDiv.innerHTML = htmlContent;
        messages.appendChild(msgDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    sendBtn.addEventListener("click", sendUserMessage);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendUserMessage();
    });
})();