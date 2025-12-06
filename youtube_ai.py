import os
import sys
import json
import argparse
import hashlib
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from apify_client import ApifyClient
from openai import OpenAI
import tiktoken

#enviroments
load_dotenv()

GENIUS_SEARCH_URL = "https://genius.com/api/search/song"

#apis
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

try:
    if not APIFY_TOKEN or not OPENROUTER_KEY:
        raise ValueError(".env dosyasında API anahtarları eksik!")
        
    apify_client = ApifyClient(APIFY_TOKEN)
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_KEY,
        default_headers={
            "HTTP-Referer": "https://github.com/cemdilmegani/youtube-ai",
            "X-Title": "YouTubeAI",
        }
    )
except Exception as e:
    print(f"Kurulum Hatası: {e}")
    sys.exit(1)


#functions
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
        #apify youtube scraper
        run = apify_client.actor("streamers/youtube-scraper").call(run_input=run_input)
        
        if not run:
            raise ValueError("Actor başlatılamadı.")

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

#prompt engineering
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
    """ 
    Adım 3: Requests ve BeautifulSoup kullanarak Genius.com'dan veri çeker.
    """
    print(f"[*] {len(song_list)} şarkı için Genius üzerinden sözler kazınıyor...")
    
    songs_with_lyrics_data = []
    found_count = 0
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }

    for song in song_list:
        try:
            params = {"q": f"{artist_name} {song}", "page": 1}
            
            resp = requests.get(GENIUS_SEARCH_URL, params=params, headers=headers, timeout=15)
            
            lyrics_text = ""
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get("response", {}).get("sections", []) and data["response"]["sections"][0]["hits"]:
                    hit = data["response"]["sections"][0]["hits"][0]
                    song_url = hit["result"]["url"]
                    
                    page_resp = requests.get(song_url, headers=headers, timeout=15)
                    soup = BeautifulSoup(page_resp.text, "html.parser")
                    
                    lyrics_containers = soup.find_all("div", {"data-lyrics-container": "true"})
                    
                    if lyrics_containers:
                        for container in lyrics_containers:
                            for br in container.find_all("br"):
                                br.replace_with("\n")
                            lyrics_text += container.get_text(separator="\n")
            else:
                print(f"    ! API Hatası: {resp.status_code}")

            if lyrics_text:
                found_count += 1
                lyrics_text = lyrics_text.strip()
                print(f"    + {song}: Bulundu ({len(lyrics_text)} karakter)")
            else:
                print(f"    - {song}: Bulunamadı")
            
            songs_with_lyrics_data.append({
                "name": song,
                "lyrics": lyrics_text
            })
            
            #rate limit
            time.sleep(0.5)

        except Exception as e:
            print(f"    - {song}: Hata ({str(e)})")
            songs_with_lyrics_data.append({"name": song, "lyrics": ""})

    print(f"    -> Toplam {len(song_list)} şarkıdan {found_count} tanesinin sözleri çekildi.")
    return songs_with_lyrics_data

def analyze_lyrics_and_format(songs_data, artist_name, album_name):
    """ Adım 4 & 5: Tiktoken analizi ve JSON oluşturma. """
    print("[*] Token analizi yapılıyor...")
    
    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except:
        enc = tiktoken.get_encoding("gpt2")
    
    analyzed_songs = []
    total_tokens_all = 0
    
    for item in songs_data:
        lyrics = item["lyrics"]
        song_name = item["name"]
        
        char_count = 0
        word_count = 0
        token_count = 0
        t_per_w = 0.0
        lyrics_hash = "N/A"
        
        if lyrics:
            char_count = len(lyrics)
            words = lyrics.split()
            word_count = len(words)
            try:
                tokens = enc.encode(lyrics)
                token_count = len(tokens)
            except:
                token_count = 0
                
            t_per_w = round(token_count / word_count, 2) if word_count > 0 else 0
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
    
    token_counts = [str(s["lyrics_length_tokens"]) for s in songs_json["songs"]]
    
    if not token_counts or all(x == "0" for x in token_counts):
        print("!! UYARI: Hiçbir şarkı sözü bulunamadığı için embedding sonucu hatalı olabilir.")

    concatenated_tokens = ",".join(token_counts)
    
    try:
        response = client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=concatenated_tokens
        )
        
        if not response.data:
            raise ValueError("API'den boş yanıt döndü.")

        embedding_vector = response.data[0].embedding
        
        formatted_vector = ",".join([f"{x:.10f}" for x in embedding_vector])
        
        final_hash = hashlib.md5(formatted_vector.encode("utf-8")).hexdigest()
        return final_hash
        
    except Exception as e:
        print(f"!! Embedding Hatası: {str(e)}")
        return "ERROR"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube URL")
    parser.add_argument("mode", choices=["json", "hash"], help="Mode: json | hash")
    args = parser.parse_args()
    
    try:
        #step 1
        artist = get_artist_from_youtube(args.url)
        
        #step 2
        album_data = get_first_album_songs(artist)
        if not album_data["songs"]:
            raise ValueError("Şarkı listesi alınamadı.")
            
        #step 3
        songs_with_lyrics = get_lyrics(album_data["songs"], artist)
        
        #step 4
        final_json = analyze_lyrics_and_format(songs_with_lyrics, artist, album_data["album"])
        
        #output mode
        if args.mode == "json":
            print(json.dumps(final_json, indent=2, ensure_ascii=False))
        elif args.mode == "hash":
            result_hash = generate_hash_from_embeddings(final_json)
            print(result_hash)
            
    except Exception as e:
        print(f"Genel Hata: {e}")

if __name__ == "__main__":
    main()