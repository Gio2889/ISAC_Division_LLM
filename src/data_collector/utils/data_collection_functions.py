# youtube_scraper.py
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import Search
import pandas as pd
import wikipedia
from bs4 import BeautifulSoup
import requests
from time import sleep
import os

def get_video_transcripts(topic, max_videos=50,max_tries=50):
    ytt_api = YouTubeTranscriptApi()
    search = Search(topic)
    results = search.results[:max_videos]
    tries = 0
    transcripts = []
    for video in results:
        if os.path.exists(f"data/transcripts/{video.video_id}_transcript.txt"):
            with open(f"data/transcripts/{video.video_id}_transcript.txt","w") as f:
                f.read(full_text)
            transcripts.append({
            "source": f"YouTube: {video.title}",
            "content": full_text
            })
            continue
        fetched_transcript = None
        print(f"-- {video.title} --")
        while tries < max_tries:
            try:
                #fetched_transcript = ytt_api.fetch(video.video_id)
                transcript_list = ytt_api.list(video.video_id)
                transcript = transcript_list.find_generated_transcript(['en'])
                fetched_transcript = transcript.fetch()
            except:
                sleep(0.01)

            if fetched_transcript:
                try:
                    fetched_transcript = ytt_api.fetch(video.video_id)
                except:
                    sleep(0.01)

            if fetched_transcript:
                print(f"got transcript for {video.title}")
                break
            tries += 1
        if not fetched_transcript:
            print(f"failed to get trascript for {video.title}")
        else:
            full_text = ""
            for snippet in fetched_transcript.snippets:
                full_text = full_text+" "+snippet.text
            with open(f"data/transcripts/{video.video_id}_transcript.txt","w") as f:
                f.write(full_text)
            transcripts.append({
            "source": f"YouTube: {video.title}",
            "content": full_text
            })
    return transcripts


def get_wikipedia_data(topic):
    search = wikipedia.search(topic)
    try:
        page = wikipedia.page(search[0])
        return [{
            "source": f"Wikipedia: {page.title}",
            "content": page.content
        }]
    except:
        return []

# csv_loader.py
def load_csv_data(file_path):
    df = pd.read_csv(file_path)
    # Convert to text format
    return [{
        "source": f"CSV: {file_path}",
        "content": row.to_string()
    } for _, row in df.iterrows()]

def get_webpage_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.text, 'html.parser')
        return [{
            "source": f"Webpage: {url}",
            "content": soup.get_text()  # Extracts text from the webpage
        }]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []