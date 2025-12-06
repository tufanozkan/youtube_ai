# YouTube AI - Şarkı Bilgisi Analiz Aracı

YouTube videolarından sanatçı bilgilerini otomatik olarak çıkaran ve Genius API'sini kullanarak şarkı detaylarını getiren AI destekli bir Python uygulaması.

## 🎯 Özellikler

- **YouTube Video Analizi**: YouTube videolarından başlık ve açıklama analizi
- **Sanatçı Bilgisi Çıkarma**: OpenAI/OpenRouter API kullanarak sanatçı ismini otomatik olarak tespit etme
- **Şarkı Detayları**: Genius.com API'sini kullanarak şarkı lyrics ve metadatasını alma
- **Akıllı Token Yönetimi**: OpenRouter API kullanımı için token hesaplama ve yönetimi
- **Hata Kontrolü**: Kapsamlı hata yönetimi ve validation

## 📋 Gereksinimler

- Python 3.8+
- Apify API Token
- OpenRouter API Key
- İnternet Bağlantısı

## 🚀 Kurulum

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/tufanozkan/youtube_ai.git
cd youtube_ai
```

### 2. Virtual Environment Oluşturun

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# veya
venv\Scripts\activate  # Windows
```

### 3. Gerekli Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 4. .env Dosyasını Oluşturun

Proje kök dizininde `.env` dosyası oluşturun ve aşağıdaki API anahtarlarınızı ekleyin:

```env
APIFY_API_TOKEN=your_apify_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
```

**API Anahtarları Nasıl Alınır:**

- **Apify Token**: [Apify Dashboard](https://console.apify.com) üzerinden
- **OpenRouter API Key**: [OpenRouter Platform](https://openrouter.ai) üzerinden

## 💻 Kullanım

### Komut Satırından Çalıştırma

```bash
python Cem_Dilmegani_YouTube_AI.py --url "YouTube Video URL'si"
```

### Örnek Kullanım

```bash
python Cem_Dilmegani_YouTube_AI.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

## 📦 Bağımlılıklar

| Paket          | Versiyon | Açıklama                        |
| -------------- | -------- | ------------------------------- |
| apify-client   | Latest   | Apify API istemcisi             |
| openai         | Latest   | OpenAI/OpenRouter API istemcisi |
| tiktoken       | Latest   | OpenAI token sayacı             |
| python-dotenv  | Latest   | .env dosyası yönetimi           |
| requests       | Latest   | HTTP istekleri                  |
| beautifulsoup4 | Latest   | HTML/XML parsing                |

## 🔄 İş Akışı

1. **YouTube Analizi**: YouTube videosundan başlık ve açıklama bilgilerini Apify kullanarak çıkarır
2. **AI İşleme**: OpenRouter API'sini kullanarak sanatçı ismini tanımlar
3. **Şarkı Araması**: Genius API'sini kullanarak şarkı bilgilerini bulur
4. **Sonuç**: Sanatçı ve şarkı bilgilerini döndürür

## ⚙️ Konfigürasyon

### Ortam Değişkenleri

- `APIFY_API_TOKEN`: Apify API erişimi için gerekli
- `OPENROUTER_API_KEY`: OpenRouter API erişimi için gerekli

## 🐛 Hata Giderme

### "API anahtarları eksik" Hatası

`.env` dosyasının proje kök dizininde olduğundan ve tüm gerekli API anahtarlarını içerdiğinden emin olun.

### Rate Limiting

Genius API'sı rate limiting uyguluyor. Çok sayıda istek yaparken aralıklar verin.

## 📝 Lisans

Bu proje açık kaynak kodludur. Detaylar için LICENSE dosyasına bakın.

## 👨‍💻 Geliştirici

- **Tufan Özkan** - [GitHub](https://github.com/tufanozkan)

## 🙏 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Lütfen şunları yapın:

1. Repository'yi fork edin
2. Feature branch'i oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'i push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📞 İletişim & Destek

Sorularınız veya önerileriniz için [GitHub Issues](https://github.com/tufanozkan/youtube_ai/issues) açabilirsiniz.

---

**Son Güncelleme**: 6 Aralık 2025
