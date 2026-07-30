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
    return {
        "kesintiler": {},          # key: stable_id → detaylar
        "toplam_kesinti": 0,
        "guncellemeler": 0
    }

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
            # Bitiş saati değişse bile aynı kesintiyi tanımak için stable key
            stable_id = f"{baslangic}|{nedeni}|{etkilenen}"
            
            kayit = {
                "baslangic": baslangic,
                "bitis": bitis,
                "nedeni": nedeni,
                "etkilenen": etkilenen,
                "stable_id": stable_id
            }
            kesintiler.append(kayit)

    return kesintiler

def send_email(yeni_veya_guncel, toplam_kesinti, toplam_guncelleme, is_update=False):
    if is_update:
        subject = f"🔄 SASKİ ÇAY MAH. - Bitiş Saati Güncellendi ({len(yeni_veya_guncel)} adet)"
    else:
        subject = f"🚨 SASKİ ÇAY MAH. - Yeni Kesinti ({len(yeni_veya_guncel)} adet)"
    
    body = f"""Merhaba,

ÇARŞAMBA ilçesi ÇAY MAH. için {'bitiş saati güncellendi' if is_update else 'yeni su kesintisi'} tespit edildi!

📊 Toplam İstatistik:
• Toplam Kesinti    : {toplam_kesinti}
• Toplam Güncelleme : {toplam_guncelleme}

🕒 Kontrol Zamanı (UTC): {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')}

Detaylar:
"""
    for i, k in enumerate(yeni_veya_guncel, 1):
        body += f"""
{i}. 
   • Başlangıç       : {k['baslangic']}
   • Bitiş           : {k['bitis']}
   • Nedeni          : {k['nedeni']}
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
        save_state({
            "kesintiler": {},
            "toplam_kesinti": 0,
            "guncellemeler": 0
        })
    
    html = get_page_content()
    if not html:
        print("   Kontrol tamamlandı (hata oluştu).\n")
        return
    
    current_kesintiler = parse_kesintiler(html)
    state = load_state()
    
    yeni_kesintiler = []
    guncellenen_kesintiler = []
    
    for k in current_kesintiler:
        sid = k["stable_id"]
        
        if sid not in state["kesintiler"]:
            # Tamamen yeni kesinti
            yeni_kesintiler.append(k)
            state["kesintiler"][sid] = {
                "baslangic": k["baslangic"],
                "bitis": k["bitis"],
                "nedeni": k["nedeni"],
                "etkilenen": k["etkilenen"]
            }
        else:
            # Daha önce kaydedilmiş
            eski_bitis = state["kesintiler"][sid]["bitis"]
            
            if eski_bitis != k["bitis"]:
                # Bitiş saati değişmiş → güncelleme maili at
                guncellenen_kesintiler.append(k)
                state["kesintiler"][sid]["bitis"] = k["bitis"]
            # else: bitiş aynı → hiçbir şey yapma (tekrar mail atma)
    
    # Yeni kesintiler varsa mail at
    if yeni_kesintiler:
        state["toplam_kesinti"] = len(state["kesintiler"])
        state["guncellemeler"] += len(yeni_kesintiler)
        save_state(state)
        print(f"🚨 {len(yeni_kesintiler)} YENİ kesinti bulundu!")
        send_email(yeni_kesintiler, state["toplam_kesinti"], state["guncellemeler"], is_update=False)
    
    # Bitiş saati değişenler varsa mail at
    if guncellenen_kesintiler:
        state["guncellemeler"] += len(guncellenen_kesintiler)
        save_state(state)
        print(f"🔄 {len(guncellenen_kesintiler)} kesintinin bitiş saati güncellendi!")
        send_email(guncellenen_kesintiler, state["toplam_kesinti"], state["guncellemeler"], is_update=True)
    
    if not yeni_kesintiler and not guncellenen_kesintiler:
        print(f"✅ Yeni veya güncellenen duyuru yok. ({len(current_kesintiler)} ilgili kayıt tarandı)\n")

# ===================== ANA KISIM =====================
if __name__ == "__main__":
    print("=== SASKİ ÇAY MAH. Su Kesintisi Takip Botu ===\n")
    check_kesinti()
