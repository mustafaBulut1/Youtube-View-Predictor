import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import os
import time

# List of API keys
API_KEYS = [
    """
    API keys 
    """
]

# Name of the output file
FILENAME = "youtube_dataset.csv"

# Search filter types (to get different kinds of videos)
SEARCH_TYPES = ["viewCount", "relevance", "rating", "date"]

# List of words to search on YouTube
SEARCH_QUERIES = [
    # Group 1: Random or low quality names
    "IMG 0001", "IMG 1234", "DSC 0001", "MVI 0001", "MOV 0001", "video", 
    "untitled", "test video", "my first video", "VID 2024", "GOPR 0001",
    
    # Group 2: Popular and Viral
    "new", "live", "2025", "best", "top 10", "shorts", "viral", "trending",
    "asmr", "funny", "prank", "challenge", "tiktok", "meme", "comedy", "satisfying",
    
    # Group 3: Games
    "minecraft", "roblox", "gta 5", "fortnite", "valorant", "gameplay", "stream", 
    "ps5", "league of legends", "call of duty", "pokemon", "sims 4", "fifa 24", 
    "horror game", "speedrun", "elden ring",
    
    # Group 4: Music
    "music", "song", "lofi", "remix", "karaoke", "lyrics", "cover", "relaxing music", 
    "bass boosted", "rap", "hip hop", "meditation sounds", "rain sounds",
    
    # Group 5: Education and Tutorial
    "vlog", "tutorial", "how to", "diy", "life hacks", "makeup", "workout", 
    "study", "cooking", "coding", "python", "excel tutorial", "photoshop",
    
    # Group 6: Tech and News
    "review", "unboxing", "tech news", "iphone 15", "samsung galaxy", "macbook", 
    "news", "interview", "podcast", "football", "nba", "movie trailer", "messi", "ronaldo"
]

# Columns for the CSV file
COLUMNS_ORDER = [
    "query_used", "search_type", "video_title", "duration_sec", "is_shorts",
    "views", "like_count", "comment_count", "upload_date", 
    "video_url", "thumbnail_url", "desc", "tags", "category", 
    "follower_count", "default_language", "video_id", "has_manuel_subtitle"
]

# Global variables for API keys
current_key_index = 0
youtube_service = None

def get_service():
    """ Get the YouTube tool. If the key is old, use the new one. """
    global youtube_service, current_key_index
    
    if youtube_service:
        return youtube_service
        
    # Check if we used all keys
    if current_key_index >= len(API_KEYS):
        print("ERROR: All API keys are finished! Stopping.")
        return None
    
    api_key = API_KEYS[current_key_index]
    # Show last 4 letters of the key
    print(f"Using New Key: ...{api_key[-4:] if len(api_key)>4 else 'KEY'}")
    youtube_service = build('youtube', 'v3', developerKey=api_key)
    return youtube_service

def switch_key():
    """ Change to the next key if there is an error. """
    global current_key_index, youtube_service
    print(f"Key (...{API_KEYS[current_key_index][-4:]}) failed. Switching...")
    
    current_key_index += 1
    youtube_service = None # Reset service
    return get_service()

def safe_api_call(func_lambda):
    """
    Try to call the API. If error, switch key and try again.
    """
    global youtube_service
    
    while True:
        service = get_service()
        if not service: return None # No keys left
        
        try:
            return func_lambda(service).execute()
            
        except HttpError as e:
            # Error 403 or 429 means limit reached
            if e.resp.status in [403, 429]: 
                print(f"API Limit Error: {e.reason}")
                if not switch_key(): return None
                # Loop will restart with new key
            else:
                print(f"   ! Unknown Error: {e}")
                return None 
        except Exception as e:
            print(f"   ! Critical Error: {e}")
            return None

def parse_duration(duration_str):
    """ Convert YouTube time (PT1H2M10S) to seconds. """
    if not isinstance(duration_str, str): return 0
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match: return 0
    h = int(match.group(1)) if match.group(1) else 0
    m = int(match.group(2)) if match.group(2) else 0
    s = int(match.group(3)) if match.group(3) else 0
    return h * 3600 + m * 60 + s

def main():
    print(f"--- YOUTUBE SCRAPER STARTED ({len(API_KEYS)} Keys) ---")
    
    if not get_service(): return

    # Check if file exists to continue
    existing_ids = set()
    processed_queries = set()
    
    if os.path.isfile(FILENAME):
        try:
            # Read old data
            df_old = pd.read_csv(FILENAME, sep=";", usecols=['video_id', 'query_used'])
            existing_ids = set(df_old['video_id'].unique())
            processed_queries = set(df_old['query_used'].unique())
            print(f"Found existing file: {len(existing_ids)} videos loaded.")
            print(f"{len(processed_queries)} words already done. Skipping them.")
        except: pass

    # Loop through all search words
    for q_idx, query in enumerate(SEARCH_QUERIES):
        
        # If we already did this word, skip it
        if query in processed_queries:
            continue

        print(f"\n[{q_idx+1}/{len(SEARCH_QUERIES)}] Processing: '{query}'")
        
        query_video_ids = []
        id_to_search_type = {} 

        # --- STEP 1: SEARCH FOR VIDEOS ---
        for sort_method in SEARCH_TYPES:
            # Call API safely
            response = safe_api_call(
                lambda yt: yt.search().list(
                    part="id",
                    q=query,
                    type="video",
                    maxResults=50,
                    order=sort_method
                )
            )
            
            if response:
                for item in response.get('items', []):
                    # Check if it has a video ID
                    if 'id' not in item or 'videoId' not in item['id']:
                        continue
                    
                    vid = item['id']['videoId']
                    # Don't add if we already have it
                    if vid not in existing_ids and vid not in query_video_ids:
                        query_video_ids.append(vid)
                        id_to_search_type[vid] = sort_method

        if not query_video_ids: continue
        print(f"   > Found {len(query_video_ids)} new videos. Getting details...")

        # --- STEP 2: GET VIDEO DETAILS ---
        video_data = []
        channel_ids = set()

        # Process 50 videos at a time
        for i in range(0, len(query_video_ids), 50):
            batch_ids = query_video_ids[i:i+50]
            
            res = safe_api_call(
                lambda yt: yt.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(batch_ids)
                )
            )
            
            if not res: continue

            for item in res.get('items', []):
                stats = item['statistics']
                snippet = item['snippet']
                content = item['contentDetails']
                
                # Skip auto-generated Mix playlists
                title = snippet.get('title', '')
                if title.startswith("Mix -") or title.startswith("Mix:"):
                    continue

                # Get duration in seconds
                dur_sec = parse_duration(content.get('duration'))
                # Check if it is a Short video (<= 60 seconds)
                is_short = 1 if dur_sec <= 60 else 0 

                row = {
                    "query_used": query,
                    "search_type": id_to_search_type.get(item['id'], "mixed"),
                    "video_title": title,
                    "duration_sec": dur_sec,
                    "is_shorts": is_short,
                    "views": stats.get('viewCount', 0),
                    "like_count": stats.get('likeCount', 0),
                    "comment_count": stats.get('commentCount', 0),
                    "upload_date": snippet.get('publishedAt'),
                    "video_url": f"https://www.youtube.com/watch?v={item['id']}",
                    "thumbnail_url": snippet['thumbnails']['high']['url'] if 'high' in snippet['thumbnails'] else "",
                    "desc": snippet.get('description', "").replace("\n", " "), # Clean new lines
                    "tags": ", ".join(snippet.get('tags', [])),
                    "category": snippet.get('categoryId'),
                    "default_language": snippet.get('defaultAudioLanguage', 'unknown'),
                    "has_manuel_subtitle": content.get('caption', 'false'),
                    "video_id": item['id'],
                    "channel_id": snippet.get('channelId')
                }
                video_data.append(row)
                if row['channel_id']: channel_ids.add(row['channel_id'])

        # --- STEP 3: GET SUBSCRIBER COUNTS ---
        subs_map = {}
        # Check channels 50 at a time
        channel_list = list(channel_ids)
        for i in range(0, len(channel_list), 50):
            batch = channel_list[i:i+50]
            res = safe_api_call(
                lambda yt: yt.channels().list(
                    part="statistics",
                    id=','.join(batch)
                )
            )
            if res:
                for item in res.get('items', []):
                    subs_map[item['id']] = item['statistics'].get('subscriberCount', 0)

        # --- STEP 4: SAVE DATA ---
        final_rows = []
        for row in video_data:
            ch_id = row.pop('channel_id')
            row['follower_count'] = subs_map.get(ch_id, 0)
            final_rows.append(row)
            existing_ids.add(row['video_id'])

        if final_rows:
            df_new = pd.DataFrame(final_rows)
            # Make sure all columns exist
            for col in COLUMNS_ORDER:
                if col not in df_new.columns: df_new[col] = None
            df_new = df_new[COLUMNS_ORDER]
            
            # Create file or append to file
            if not os.path.isfile(FILENAME):
                df_new.to_csv(FILENAME, index=False, encoding='utf-8-sig', sep=';')
            else:
                df_new.to_csv(FILENAME, mode='a', header=False, index=False, encoding='utf-8-sig', sep=';')
            
            print(f"SAVED: {len(df_new)} rows.")

if __name__ == "__main__":
    main()
