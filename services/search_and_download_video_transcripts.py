from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter, SRTFormatter
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os, json
from language_tool_python import LanguageTool

load_dotenv()

def advanced_spell_check(text):
    tool = LanguageTool('en-US')
    corrected = tool.correct(text)
    return corrected

def search_videos(company_name):
    params = {
    "engine": "google_videos",
    "q": company_name,
    "google_domain": "google.com",
    "hl": "en",
    "gl": "in",
    "safe": "active",
    "num": "20",
    "tbs": "qdr:d",
    "api_key": os.getenv("SERP_API_KEY")
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results["video_results"]

def download_yt_transcript(video_id):
    try:
        # Attempt to get the English transcript
        final_transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        print("English Transcript:")
    except Exception as e:
        print("English transcript not available:", e)
        # If English is not available, get transcripts in other languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            if transcript.is_translatable:
                print(f"Transcripts available in {transcript.language} ({transcript.language_code})")
                # Translate to English
                try:
                    translated_transcript = transcript.translate('en').fetch()
                    print("Translated Transcript:")
                    break
                except:
                    continue
        final_transcript = translated_transcript
    
    # Format and save the transcript with timestamps
    #print(final_transcript)
    formatter = JSONFormatter()
    srt_transcript = ""
    for segment in json.loads(formatter.format_transcript(final_transcript)):
        print(f"segment : {segment}")
        # Spell check the text

        corrected_text = advanced_spell_check(segment["text"])  # Corrected text

        srt_transcript += str(segment["start"]) + " sec : " + corrected_text + "\n"
    
    # Save to a file
    with open(f"{video_id}_transcript.srt", "w", encoding="utf-8") as file:
        file.write(srt_transcript)
    
    print(f"Transcript saved as {video_id}_transcript.srt")

# Example usage
#Add code to search for videos using serp api
company_name = "zomato"
videos = search_videos(company_name)

for i in range(len(videos)):

    print(f"Title : {videos[i]['title']}")
    print(f"Link : {videos[i]['link']}")

    if "www.youtube.com" in videos[i]["link"]:
        video_id = videos[i]["link"].split("=")[-1]
        print(f"Video_id is {video_id}")
        download_yt_transcript(video_id)
