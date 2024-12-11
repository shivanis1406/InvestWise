from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

#Add code to search for videos using serp api
videos = [
"https://www.youtube.com/watch?v=TtTQyvvirwg",
"https://www.youtube.com/watch?v=tgSiAW31cGY",
"https://www.youtube.com/watch?v=zXPhj8Bug4k",
"https://www.youtube.com/watch?v=JlFcrHJQwM8",
"https://www.youtube.com/watch?v=l9KZlq6c5E8",
"https://www.youtube.com/watch?v=v3g59EqHpjk",
"https://www.youtube.com/watch?v=JL1iuVOyN0U"
]

def download_transcript(video_id):
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
    srt_transcript = formatter.format_transcript(final_transcript)
    
    # Save to a file
    with open(f"{video_id}_transcript.srt", "w", encoding="utf-8") as file:
        file.write(srt_transcript)
    
    print(f"Transcript saved as {video_id}_transcript.srt")

# Example usage
video_id = videos[1].split("=")[-1]
download_transcript(video_id)
