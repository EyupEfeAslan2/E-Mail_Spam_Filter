import imaplib
import email
import requests
import time
import os

# --- YAPILANDIRMA ---
IMAP_SERVER = "imap.gmail.com"  # Örn: Outlook için imap-mail.outlook.com
EMAIL_ACCOUNT = "sizin_epostaniz@gmail.com"
APP_PASSWORD = "sizin_uygulama_sifreniz"  # Güvenlik için normal şifre yerine uygulama şifresi kullanın
API_URL = "http://127.0.0.1:8000/predict"
CHECK_INTERVAL = 60 # Saniye cinsinden bekleme süresi

def get_email_body(msg):
    """E-posta içeriğini (body) ayıklar."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode()
    else:
        return msg.get_payload(decode=True).decode()
    return ""

def check_inbox():
    """Gelen kutusuna bağlanır, okunmamış e-postaları alır ve Spam filtresine gönderir."""
    try:
        # IMAP Sunucusuna Bağlan
        print(f"[{time.strftime('%X')}] {IMAP_SERVER} sunucusuna bağlanılıyor...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
        mail.select("inbox")

        # Okunmamış mesajları ara
        status, messages = mail.search(None, 'UNSEEN')
        if status != "OK":
            print("Gelen kutusu okunamadı.")
            return

        email_ids = messages[0].split()
        if not email_ids:
            print(f"[{time.strftime('%X')}] Yeni e-posta yok.")
        
        for e_id in email_ids:
            # E-postayı getir
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = email.header.decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                    
                    print(f"\n[YENİ E-POSTA] Konu: {subject}")
                    
                    body = get_email_body(msg)
                    if body:
                        # E-postayı API'ye gönder (Spam Analizi)
                        print("  -> Spam filtresine gönderiliyor...")
                        try:
                            response = requests.post(API_URL, json={"text": body})
                            if response.status_code == 200:
                                result = response.json()
                                conf = int(result['confidence'] * 100)
                                print(f"  -> SONUÇ: {result['prediction']} (%{conf} Güven - {result['layer']})")
                            else:
                                print(f"  -> API Hatası: {response.status_code}")
                        except Exception as api_err:
                            print(f"  -> API'ye ulaşılamadı: {api_err}")

        mail.logout()
    except Exception as e:
        print(f"Bağlantı veya okuma hatası: {e}")

if __name__ == "__main__":
    print("===================================================")
    print(" IMAP Email Watcher & Spam Filter Integrator")
    print("===================================================")
    print("Uyarı: Bu script, Data Structures proje gereksinimleri")
    print("için IMAP entegrasyonu göstermek amacıyla yazılmıştır.")
    print("Çalıştırmadan önce EMAIL_ACCOUNT ve APP_PASSWORD güncelleyin.\n")
    
    # Sürekli dinleme döngüsü (Demonstration)
    try:
        while True:
            check_inbox()
            print(f"{CHECK_INTERVAL} saniye bekleniyor...\n")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nİzleme durduruldu.")
