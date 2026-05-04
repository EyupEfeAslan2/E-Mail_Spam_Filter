import imaplib
import email
import requests
import time
import os
from email.header import decode_header

# --- YAPILANDIRMA ---
IMAP_SERVER = os.getenv("SPAM_IMAP_SERVER", "imap.gmail.com")
IMAP_FOLDER = os.getenv("SPAM_IMAP_FOLDER", "inbox")
SPAM_FOLDER = os.getenv("SPAM_IMAP_SPAM_FOLDER", "")
EMAIL_ACCOUNT = os.getenv("SPAM_EMAIL_ACCOUNT", "")
APP_PASSWORD = os.getenv("SPAM_EMAIL_APP_PASSWORD", "")
API_URL = os.getenv("SPAM_API_URL", "http://127.0.0.1:8000/predict")
CHECK_INTERVAL = int(os.getenv("SPAM_CHECK_INTERVAL", "60"))
REQUEST_TIMEOUT = int(os.getenv("SPAM_API_TIMEOUT", "10"))

def get_email_body(msg):
    """E-posta içeriğini (body) ayıklar."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True) or b""
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def decode_subject(msg):
    decoded = decode_header(msg.get("Subject", ""))[0][0]
    if isinstance(decoded, bytes):
        return decoded.decode(errors="replace")
    return decoded


def move_to_spam(mail, email_id):
    """Spam klasörü ayarlıysa IMAP üzerinde mesajı taşır."""
    if not SPAM_FOLDER:
        return
    mail.copy(email_id, SPAM_FOLDER)
    mail.store(email_id, "+FLAGS", "\\Deleted")

def check_inbox():
    """Gelen kutusuna bağlanır, okunmamış e-postaları alır ve Spam filtresine gönderir."""
    if not EMAIL_ACCOUNT or not APP_PASSWORD:
        raise RuntimeError("SPAM_EMAIL_ACCOUNT ve SPAM_EMAIL_APP_PASSWORD ortam değişkenleri gerekli.")
    try:
        # IMAP Sunucusuna Bağlan
        print(f"[{time.strftime('%X')}] {IMAP_SERVER} sunucusuna bağlanılıyor...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
        mail.select(IMAP_FOLDER)

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
                    subject = decode_subject(msg)
                    
                    print(f"\n[YENİ E-POSTA] Konu: {subject}")
                    
                    body = get_email_body(msg)
                    if body:
                        # E-postayı API'ye gönder (Spam Analizi)
                        print("  -> Spam filtresine gönderiliyor...")
                        try:
                            response = requests.post(API_URL, json={"text": body}, timeout=REQUEST_TIMEOUT)
                            if response.status_code == 200:
                                result = response.json()
                                conf = int(result['confidence'] * 100)
                                print(f"  -> SONUÇ: {result['prediction']} (%{conf} Güven - {result['layer']})")
                                if result["prediction"].lower() == "spam":
                                    move_to_spam(mail, e_id)
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
    print("Kimlik bilgileri ortam değişkenlerinden okunur; kaynak koda parola yazılmaz.\n")
    
    # Sürekli dinleme döngüsü (Demonstration)
    try:
        while True:
            check_inbox()
            print(f"{CHECK_INTERVAL} saniye bekleniyor...\n")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\nİzleme durduruldu.")
