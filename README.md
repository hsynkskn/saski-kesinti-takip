# SASKİ ÇAY MAH. Su Kesintisi Takip Botu

ÇARŞAMBA ilçesi ÇAY MAH. için SASKİ su kesintisi ve güncellemelerini otomatik takip eden Python botu.

Bot, **GitHub Actions** ile bilgisayarınız kapalıyken bile 3 saatte bir kontrol yapar ve **sadece yeni kesinti/güncelleme** olduğunda size mail gönderir.

---

## Özellikler

- Sadece ÇARŞAMBA - ÇAY MAH. ile ilgili duyuruları takip eder
- **Sadece yeni** kesinti veya güncelleme olduğunda mail atar
- Toplam kesinti ve güncelleme sayısını raporlar
- GitHub Actions ile 7/24 çalışır (bilgisayar kapalıyken de)
- State kaydederek tekrar tekrar aynı duyuruyu mail atmaz

---

## Kullanılan Teknolojiler

- Python 3.11
- BeautifulSoup4 (Web scraping)
- smtplib (Email gönderme)
- GitHub Actions (Cron Job)
- Dependabot (Bağımlılık güncelleme)

---

## Kurulum

### 1. Repoyu Klonla
```bash
git clone https://github.com/kullanicin/saski-kesinti-takip.git
cd saski-kesinti-takip

### 2. Gereksinimleri Yükle
pip install -r requirements.txt
### 3. Mail Ayarları
GitHub reposunda Settings → Secrets and variables → Actions kısmına şu 3 secret’i ekleyin:

EMAIL_FROM → Gönderen Gmail adresi
EMAIL_TO → Mailin gideceği adres
EMAIL_PASSWORD → Gmail 16 haneli App Password

## Dosya Yapısı:

.
├── saski_kesinti_takip.py          # Ana bot dosyası
├── requirements.txt                # Python paketleri
├── son_durum.json                  # Son durum (otomatik oluşur)
├── .github/
│   ├── workflows/
│   │   ├── kesinti-takip.yml       # Ana workflow (3 saatte bir)
│   │   └── security-scan.yml       # Güvenlik taraması
│   └── dependabot.yml              # Bağımlılık güncelleme
└── README.md

## Kontrol Saatleri (UTC)

Bot şu saatlerde kontrol yapar:
03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 (UTC)
Türkiye saatiyle: 06:00, 09:00, 12:00, 15:00, 18:00, 21:00, 00:00

