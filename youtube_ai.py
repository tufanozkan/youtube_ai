import os
import sys
import json
import argparse
import hashlib
from dotenv import load_dotenv
from apify_client import ApifyClient
from openai import OpenAI
import tiktoken

# 1. Çevresel Değişkenleri Yükle (.env dosyasını okur)
load_dotenv()

# 2. API Kurulumları
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

# İstemcileri (Clients) Başlatma
# Apify bağlantısı
apify_client = ApifyClient(APIFY_TOKEN)

# OpenRouter (OpenAI SDK uyumlu) bağlantısı
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
)

# --- FONKSİYONLAR ---

def get_artist_from_youtube(video_url):
    """
    Adım 1: YouTube URL'sinden sanatçı ismini bulur.
    Apify YouTube Scraper kullanılacak.
    """
    print(f"[*] YouTube videosu analiz ediliyor: {video_url}")
    # TODO: Burayı kodlayacağız
    return "Sanatçı Adı (Placeholder)"

def get_first_album_songs(artist_name):
    """
    Adım 2: LLM kullanarak sanatçının ilk albüm şarkılarını bulur.
    """
    print(f"[*] {artist_name} için ilk albüm aranıyor...")
    # TODO: Burayı kodlayacağız
    return ["Song 1", "Song 2"]

def get_lyrics(song_list, artist_name):
    """
    Adım 3: Genius üzerinden şarkı sözlerini çeker.
    """
    print(f"[*] Şarkı sözleri indiriliyor...")
    # TODO: Burayı kodlayacağız
    return [{"name": "Song 1", "lyrics": "la la la"}]

def analyze_lyrics_and_format(songs_data):
    """
    Adım 4 & 5: Token hesabı yapar ve JSON formatını oluşturur.
    """
    # TODO: Burayı kodlayacağız
    return {} # JSON objesi dönecek

def generate_hash_from_embeddings(songs_json):
    """
    Adım 6, 7 & 8: Embedding oluşturur ve MD5 hash üretir.
    """
    # TODO: Burayı kodlayacağız
    return "md5_hash_placeholder"

# --- ANA AKIŞ (MAIN) ---

def main():
    # CLI Argümanlarını Ayarla (Terminalden veri girişi için)
    parser = argparse.ArgumentParser(description="YouTube AI Scraping Agent")
    parser.add_argument("url", help="YouTube Video URL")
    parser.add_argument("mode", choices=["json", "hash"], help="Çıktı modu: 'json' veya 'hash'")
    
    args = parser.parse_args()
    
    try:
        # İŞ AKIŞI
        # 1. Sanatçıyı bul
        artist = get_artist_from_youtube(args.url)
        
        # 2. Albümü bul
        songs_list = get_first_album_songs(artist)
        
        # 3. Sözleri çek
        songs_with_lyrics = get_lyrics(songs_list, artist)
        
        # 4. Analiz yap (Tokenlar vs.)
        final_json = analyze_lyrics_and_format(songs_with_lyrics)
        
        if args.mode == "json":
            # JSON çıktısını ekrana bas
            print(json.dumps(final_json, indent=2))
            
        elif args.mode == "hash":
            # Hash hesapla ve bas
            result_hash = generate_hash_from_embeddings(final_json)
            print(result_hash)

    except Exception as e:
        print(f"Hata oluştu: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    main()