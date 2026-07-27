import requests
from bs4 import BeautifulSoup
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ===================== AYARLAR =====================
URL = "https://www.saski.gov.tr/sukesintileri/"
ILCE = "ÇARŞAMBA"
MAHALLE = "ÇAY MAH"

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

STATE_FILE = "son_durum.json"
# ==================================================

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"kesintiler": [], "toplam_kesinti": 0, "guncellemeler": 0}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_page_content():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Sayfa çekilemedi: {e}")
        return None

def parse_kesintiler(html):
    soup = BeautifulSoup(html, 'html.parser')
    kesintiler = []

    # Tabloyu bul
    table = soup.find('table')
    if not table:
        return kesintiler

    rows = table.find_all('tr')
    
    for row in rows[1:]:  # başlık satırını atla
        cols = row.find_all('td')
        if len(cols) < 4:
            continue

        baslangic = cols[0].get_text(strip=True)
        bitis = cols[1].get_text(strip=True)
        nedeni = cols[2].get_text(strip=True)
        etkilenen = cols[3].get_text(strip=True)

        # Sadece ÇARŞAMBA + ÇAY MAH içeren satırları al
        if ILCE in etkilenen and MAHALLE in etkilenen:
            kayit = {
                "baslangic": baslangic,
                "bitis": bitis,
                "nedeni": nedeni,
                "etkilenen": etkilenen,
                "unique_id": f"{baslangic}|{bitis}|{nedeni}|{etkilenen}"
            }
            kesintiler.append(kayit)

    return kesintiler

def send_email(yeni_kesintiler, toplam_kesinti, toplam_guncelleme):
    subject = f"🚨 SASKİ ÇAY MAH. - {len(yeni_kesintiler)} Yeni Duyuru"
    
    body = f"""Merhaba,

ÇARŞAMBA ilçesi ÇAY MAH. için yeni su kesintisi / güncelleme tespit edildi!

📊 Toplam İstatistik:
• Toplam Kesinti    : {toplam_kesinti}
• Toplam Güncelleme : {toplam_guncelleme}

🕒 Kontrol Zamanı (UTC): {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')}

Detaylar:
"""
    for i, k in enumerate(yeni_kesintiler, 1):
        body += f"""
{i}. 
   • Başlangıç      : {k['baslangic']}
   • Bitiş          : {k['bitis']}
   • Nedeni         : {k['nedeni']}
   • Etkilenen Yerler: {k['etkilenen']}
"""
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Mail başarıyla gönderildi!")
    except Exception as e:
        print(f"❌ Mail gönderilemedi: {e}")

def check_kesinti():
    print(f"\n🔍 [UTC {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')}] Site kontrol ediliyor...")
    
    if not os.path.exists(STATE_FILE):
        save_state({"kesintiler": [], "toplam_kesinti": 0, "guncellemeler": 0})
    
    html = get_page_content()
    if not html:
        print("   Kontrol tamamlandı (hata oluştu).\n")
        return
    
    current_kesintiler = parse_kesintiler(html)
    state = load_state()
    
    # Daha önce kaydedilmiş unique_id'leri al
    eski_idler = set(state.get("kesintiler", []))
    
    yeni_kesintiler = []
    for k in current_kesintiler:
        if k["unique_id"] not in eski_idler:
            yeni_kesintiler.append(k)
    
    if yeni_kesintiler:
        # Yeni id'leri kaydet
        for k in yeni_kesintiler:
            state["kesintiler"].append(k["unique_id"])
        
        state["toplam_kesinti"] = len(state["kesintiler"])
        state["guncellemeler"] += len(yeni_kesintiler)
        save_state(state)
        
        print(f"🚨 {len(yeni_kesintiler)} YENİ duyuru bulundu! Mail gönderiliyor...")
        send_email(yeni_kesintiler, state["toplam_kesinti"], state["guncellemeler"])
    else:
        print(f"✅ Yeni duyuru yok. ({len(current_kesintiler)} ilgili kayıt tarandı)\n")

# ===================== ANA KISIM =====================
if __name__ == "__main__":
    print("=== SASKİ ÇAY MAH. Su Kesintisi Takip Botu (GitHub Actions) ===\n")
    check_kesinti()
