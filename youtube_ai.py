import os
import sys
import json
import argparse
import hashlib
from dotenv import load_dotenv
from apify_client import ApifyClient
from openai import OpenAI
import tiktoken

# 1. Çevresel Değişkenleri Yükle
load_dotenv()

# 2. API Kurulumları
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

# İstemcileri Başlatma
try:
    if not APIFY_TOKEN or not OPENROUTER_KEY:
        raise ValueError(".env dosyasında API anahtarları eksik!")
        
    apify_client = ApifyClient(APIFY_TOKEN)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_KEY,
        default_headers={
            "HTTP-Referer": os.getenv("OR_SITE_URL", "https://github.com/cemdilmegani"),
            "X-Title": os.getenv("OR_APP_NAME", "YouTubeAI"),
        }
    )
except Exception as e:
    print(f"Kurulum Hatası: {e}")
    sys.exit(1)

# --- FONKSİYONLAR ---

def get_artist_from_youtube(video_url):
    """ Adım 1: YouTube URL'sinden sanatçı ismini bulur. """
    print(f"[*] YouTube videosu analiz ediliyor: {video_url}")
    
    run_input = {
        "startUrls": [{"url": video_url}],
        "maxResults": 1,
        "downloadSubtitles": False,
        "downloadComments": False,
    }

    try:
        # Apify: Youtube Scraper
        run = apify_client.actor("streamers/youtube-scraper").call(run_input=run_input)
        dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        if not dataset_items:
            raise ValueError("Apify videoyu bulamadı.")

        video_data = dataset_items[0]
        title = video_data.get("title", "")
        channel_name = video_data.get("channelName", "")

        print(f"    -> Bulunan Başlık: {title}")
        
        if "-" in title:
            artist = title.split("-")[0].strip()
        else:
            artist = channel_name.strip()
            
        print(f"    -> Tespit Edilen Sanatçı: {artist}")
        return artist

    except Exception as e:
        print(f"!! Apify YouTube Hatası: {str(e)}")
        sys.exit(1)

def get_first_album_songs(artist_name):
    """ Adım 2: LLM kullanarak sanatçının İLK albüm şarkılarını bulur. """
    print(f"[*] {artist_name} için ilk albüm bilgisi OpenRouter'dan isteniyor...")

    prompt = f"""
    You are a music expert.
    1. Identify the first studio album of the artist "{artist_name}".
    2. List all the songs in that album in their original release order.
    3. Output ONLY a valid JSON object with this exact format:
    {{
      "album_name": "Album Name",
      "songs": ["Song 1", "Song 2"]
    }}
    4. No markdown formatting, just raw JSON.
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful music database assistant. Output JSON only."},
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "")
        
        data = json.loads(content)
        album_name = data.get("album_name", "Unknown Album")
        songs = data.get("songs", [])
        
        print(f"    -> Bulunan Albüm: {album_name}")
        print(f"    -> Şarkı Sayısı: {len(songs)}")
        
        return {"album": album_name, "songs": songs}

    except Exception as e:
        print(f"!! LLM Hatası: {str(e)}")
        return {"album": "Error", "songs": []}

def get_lyrics(song_list, artist_name):
    """ Adım 3: Apify Genius Scraper (canadesk) kullanarak şarkı sözlerini çeker. """
    print(f"[*] {len(song_list)} şarkı için sözler aranıyor (Bu işlem 30-60sn sürebilir)...")
    
    search_queries = [f"{artist_name} {song} lyrics" for song in song_list]
    
    # canadesk/genius-lyrics-scraper parametreleri
    run_input = {
        "searchQueries": search_queries,
        "maxItems": 1
    }

    songs_with_lyrics_data = []
    
    try:
        # GÜNCEL ACTOR: canadesk/genius-lyrics-scraper
        print("    -> Apify 'canadesk/genius-lyrics-scraper' çağrılıyor...")
        run = apify_client.actor("canadesk/genius-lyrics-scraper").call(run_input=run_input)
        
        dataset_items = []
        if run:
            dataset_items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        # Eşleştirme Haritası
        lyrics_map = {}
        for item in dataset_items:
            # canadesk çıktısında lyrics genelde 'lyrics' alanındadır
            lyrics = item.get("lyrics", "")
            
            # Eşleştirme için title veya searchQuery kullan
            title = item.get("title", "").lower()
            query_used = item.get("searchQuery", "").lower()
            
            if lyrics:
                if title: lyrics_map[title] = lyrics
                if query_used: lyrics_map[query_used] = lyrics

        found_count = 0
        for song in song_list:
            song_lower = song.lower()
            found_lyrics = ""
            
            # Basit eşleştirme
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
        # Hata durumunda boş dön
        return [{"name": s, "lyrics": ""} for s in song_list]

def analyze_lyrics_and_format(songs_data, artist_name, album_name):
    """ Adım 4 & 5: Tiktoken analizi ve JSON oluşturma. """
    print("[*] Token analizi yapılıyor...")
    enc = tiktoken.get_encoding("cl100k_base")
    
    analyzed_songs = []
    total_tokens_all = 0
    
    for item in songs_data:
        lyrics = item["lyrics"]
        song_name = item["name"]
        
        # Varsayılan değerler
        char_count = 0
        word_count = 0
        token_count = 0
        t_per_w = 0.0
        lyrics_hash = "N/A"
        
        if lyrics:
            char_count = len(lyrics)
            words = lyrics.split()
            word_count = len(words)
            tokens = enc.encode(lyrics)
            token_count = len(tokens)
            t_per_w = round(token_count / word_count, 2) if word_count > 0 else 0
            # UTF-8 hash
            lyrics_hash = hashlib.md5(lyrics.encode("utf-8")).hexdigest()
            
            total_tokens_all += token_count
        
        analyzed_songs.append({
            "name": song_name,
            "lyrics_length_chars": char_count,
            "lyrics_length_words": word_count,
            "lyrics_length_tokens": token_count,
            "tokens_per_word": t_per_w,
            "lyrics_hash": lyrics_hash
        })
        
    avg_tokens = round(total_tokens_all / len(analyzed_songs), 2) if analyzed_songs else 0
    
    return {
        "artist": artist_name,
        "album_name": album_name,
        "songs": analyzed_songs,
        "total_tokens_all_songs": total_tokens_all,
        "avg_tokens_per_song": avg_tokens
    }

def generate_hash_from_embeddings(songs_json):
    """ Adım 6, 7 & 8: Embedding ve Final Hash. """
    print("[*] Embedding ve Hash hesaplanıyor...")
    
    # Token listesi string'i
    token_counts = [str(s["lyrics_length_tokens"]) for s in songs_json["songs"]]
    concatenated_tokens = ",".join(token_counts)
    
    # Embedding Çağrısı
    try:
        response = client.embeddings.create(
            model="nomic-ai/nomic-embed-text-v1.5",
            input=concatenated_tokens
        )
        embedding_vector = response.data[0].embedding
        
        # Formatlama: {:.10f}
        formatted_vector = ",".join([f"{x:.10f}" for x in embedding_vector])
        
        # MD5 Hash
        final_hash = hashlib.md5(formatted_vector.encode("utf-8")).hexdigest()
        return final_hash
        
    except Exception as e:
        print(f"!! Embedding Hatası: {str(e)}")
        return "ERROR"

# --- MAIN ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("mode", choices=["json", "hash"], help="Mode: json | hash")
    args = parser.parse_args()
    
    try:
        # Adım 1
        artist = get_artist_from_youtube(args.url)
        
        # Adım 2
        album_data = get_first_album_songs(artist)
        if not album_data["songs"]:
            raise ValueError("Şarkı listesi alınamadı.")
            
        # Adım 3
        songs_with_lyrics = get_lyrics(album_data["songs"], artist)
        
        # Adım 4
        final_json = analyze_lyrics_and_format(songs_with_lyrics, artist, album_data["album"])
        
        # Çıktı Modu
        if args.mode == "json":
            print(json.dumps(final_json, indent=2, ensure_ascii=False))
        elif args.mode == "hash":
            result_hash = generate_hash_from_embeddings(final_json)
            print(result_hash)
            
    except Exception as e:
        print(f"Genel Hata: {e}")

if __name__ == "__main__":
    main()