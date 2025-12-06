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
    Apify 'streamers/youtube-scraper' actor'ü kullanılır.
    """
    print(f"[*] YouTube videosu analiz ediliyor: {video_url}")
    
    # Apify Actor Girdisi (Sadece meta veriyi istiyoruz, yorumları vs değil)
    run_input = {
        "startUrls": [{"url": video_url}],
        "maxResults": 1,
        "downloadSubtitles": False,
        "downloadComments": False,
    }

    try:
        # Actor: 'streamers/youtube-scraper' (Hızlı ve ucuzdur)
        # Not: Eğer bu actor hata verirse 'apify/youtube-scraper' kullanabiliriz.
        run = apify_client.actor("streamers/youtube-scraper").call(run_input=run_input)
        
        # Dataset'ten veriyi çek
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        if not dataset_items:
            raise ValueError("Apify videoyu bulamadı veya veri boş döndü.")

        video_data = dataset_items[0]
        title = video_data.get("title", "")
        channel_name = video_data.get("channelName", "")

        print(f"    -> Bulunan Başlık: {title}")
        
        # STRATEJİ: Sanatçıyı bulmak için başlığı analiz et
        # Genelde format: "Artist - Song Name" şeklindedir.
        if "-" in title:
            # Tireden önceki kısmı al ve boşlukları temizle
            artist = title.split("-")[0].strip()
        else:
            # Tire yoksa, kanal adını sanatçı varsay (Örn: RihannaVEVO -> Rihanna olabilir, ama şimdilik direkt alalım)
            artist = channel_name.strip()
            
        print(f"    -> Tespit Edilen Sanatçı: {artist}")
        return artist

    except Exception as e:
        print(f"!! Apify Hatası: {str(e)}")
        sys.exit(1) # Kritik hata, programı durdur.

def get_first_album_songs(artist_name):
    """
    Adım 2: OpenRouter (LLM) kullanarak sanatçının İLK albüm şarkılarını bulur.
    """
    print(f"[*] {artist_name} için ilk albüm bilgisi OpenRouter'dan isteniyor...")

    # Prompt Engineering: LLM'e ne yapması gerektiğini net bir şekilde söylüyoruz.
    prompt = f"""
    You are a music expert helper.
    1. Identify the first studio album of the artist "{artist_name}".
    2. List all the songs in that album in their original release order.
    3. Output ONLY a valid JSON object with this exact format:
    {{
      "album_name": "Album Name Here",
      "songs": ["Song 1", "Song 2", "Song 3"]
    }}
    4. Do not write any introduction or explanation, just the JSON string.
    """

    try:
        # OpenRouter Çağrısı
        # Model olarak 'openai/gpt-3.5-turbo' veya ücretsiz 'google/gemini-pro' gibi modeller seçilebilir.
        # OpenRouter'da popüler ve ucuz bir model kullanalım:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini", # Veya "google/gemini-2.0-flash-exp:free" (ücretsizse)
            messages=[
                {"role": "system", "content": "You are a helpful music database assistant. Output JSON only."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        
        # Bazen LLM'ler JSON'ı ```json ... ``` blokları içine alır, onları temizleyelim.
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        
        # String'i Python sözlüğüne (Dictionary) çevir
        data = json.loads(content)
        
        album_name = data.get("album_name", "Unknown Album")
        songs = data.get("songs", [])
        
        print(f"    -> Bulunan Albüm: {album_name}")
        print(f"    -> Şarkı Sayısı: {len(songs)}")
        
        return {"album": album_name, "songs": songs}

    except Exception as e:
        print(f"!! LLM Hatası: {str(e)}")
        # Hata durumunda boş liste dön ki program çökmesin
        return {"album": "Error", "songs": []}

def get_lyrics(song_list, artist_name):
    """
    Adım 3: Apify Genius Scraper kullanarak şarkı sözlerini çeker.
    GÜNCELLEME: 'canadesk/genius-lyrics-scraper' kullanıldı.
    """
    print(f"[*] {len(song_list)} şarkı için sözler aranıyor (Bu işlem biraz sürebilir)...")
    
    # Şarkıları arama sorgularına dönüştür
    search_queries = [f"{artist_name} {song} lyrics" for song in song_list]
    
    run_input = {
        "searchQueries": search_queries,
        "maxItems": 1, # Her sorgu için 1 sonuç
        # canadesk actor'ü bazen farklı parametreler isteyebilir ama basic kullanımı budur
    }

    songs_with_lyrics_data = []
    
    try:
        # ACTOR GÜNCELLENDİ: canadesk/genius-lyrics-scraper
        run = apify_client.actor("canadesk/genius-lyrics-scraper").call(run_input=run_input)
        
        # Sonuçları al
        if run:
            dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        else:
            dataset_items = []

        # Map oluştur: { "Sorgu": "Lyrics" }
        lyrics_map = {}
        for item in dataset_items:
            # canadesk genellikle 'searchQuery' veya 'title' döner. 
            # Eşleşme için item içindeki verileri kontrol edelim.
            # Not: Bu scraper bazen metaveriyi 'searchQuery' field'ında döner.
            query_used = item.get("searchQuery", "").lower() 
            lyrics = item.get("lyrics", "")
            
            # Eğer lyrics varsa haritaya ekle
            if lyrics:
                # Basit bir eşleştirme için title'ı da kullanabiliriz
                title = item.get("title", "").lower()
                lyrics_map[title] = lyrics
                # Query ile de yedekleyelim
                if query_used:
                    lyrics_map[query_used] = lyrics

        # Orijinal listeyi dön ve eşleştir
        found_count = 0
        for song in song_list:
            song_lower = song.lower()
            found_lyrics = ""
            
            # Haritada şarkı adı geçiyor mu diye bak
            for k, v in lyrics_map.items():
                if song_lower in k: 
                    found_lyrics = v
                    break
            
            if found_lyrics:
                found_count += 1
            
            songs_with_lyrics_data.append({
                "name": song,
                "lyrics": found_lyrics
            })
            
        print(f"    -> {len(song_list)} şarkıdan {found_count} tanesinin sözleri bulundu.")
        return songs_with_lyrics_data

    except Exception as e:
        print(f"!! Genius Scraper Hatası: {str(e)}")
        return [{"name": s, "lyrics": ""} for s in song_list]

def analyze_lyrics_and_format(songs_data, artist_name, album_name):
    """
    Adım 4 & 5: Token hesabı yapar ve JSON formatını oluşturur.
    Parametreleri (songs_data, artist_name, album_name) olarak güncelledik.
    """
    print("[*] Token analizi ve metrik hesaplamaları yapılıyor...")
    
    # Tiktoken encoding yükle (cl100k_base)
    enc = tiktoken.get_encoding("cl100k_base")
    
    analyzed_songs = []
    total_tokens_all = 0
    
    for item in songs_data:
        lyrics = item["lyrics"]
        song_name = item["name"]
        
        if not lyrics:
            # Sözler bulunamadıysa değerleri 0 geç
            analyzed_songs.append({
                "name": song_name,
                "lyrics_length_chars": 0,
                "lyrics_length_words": 0,
                "lyrics_length_tokens": 0,
                "tokens_per_word": 0,
                "lyrics_hash": "N/A"
            })
            continue

        # 1. Temizlik (Gerekirse)
        # lyrics = lyrics.strip() 

        # 2. Metrikler
        char_count = len(lyrics)
        
        # Kelime sayısı (basit split)
        words = lyrics.split()
        word_count = len(words)
        
        # Token sayısı (tiktoken)
        tokens = enc.encode(lyrics)
        token_count = len(tokens)
        
        # Token / Kelime oranı
        t_per_w = round(token_count / word_count, 2) if word_count > 0 else 0
        
        # 3. MD5 Hash (Raw lyrics üzerinden)
        # UTF-8 encode edip hashliyoruz
        lyrics_hash = hashlib.md5(lyrics.encode("utf-8")).hexdigest()
        
        total_tokens_all += token_count
        
        # Şarkı objesini oluştur
        song_obj = {
            "name": song_name,
            "lyrics_length_chars": char_count,
            "lyrics_length_words": word_count,
            "lyrics_length_tokens": token_count,
            "tokens_per_word": t_per_w,
            "lyrics_hash": lyrics_hash
        }
        analyzed_songs.append(song_obj)
        
    # Ortalamayı hesapla
    avg_tokens = round(total_tokens_all / len(analyzed_songs), 2) if analyzed_songs else 0
    
    # Final JSON Yapısı
    final_output = {
        "artist": artist_name,
        "album_name": album_name,
        "songs": analyzed_songs,
        "total_tokens_all_songs": total_tokens_all,
        "avg_tokens_per_song": avg_tokens
    }
    
    return final_output

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
        album_data = get_first_album_songs(artist)
        album_name = album_data["album"]
        songs_list = album_data["songs"]
        
        if not songs_list:
            raise ValueError("Albüm şarkıları bulunamadı!")
            
        # 3. Sözleri çek (Parametreleri güncelledik)
        songs_with_lyrics = get_lyrics(songs_list, artist)
        
        # 4. Analiz yap (Buraya albüm adını da gönderelim ki final JSON'da olsun)
        final_json = analyze_lyrics_and_format(songs_with_lyrics, artist, album_name)
        
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