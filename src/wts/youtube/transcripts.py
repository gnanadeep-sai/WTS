from youtube_transcript_api import YouTubeTranscriptApi

ytt_api = YouTubeTranscriptApi()

def get_transcript(video_ids:list[str]):
    for id in video_ids:
        fetched_transcript = ytt_api.fetch(video_id=id, languages=["en"])
    print("Done")

def main():
    video_id = "5COUxxTRcL0"
    get_transcript(video_id)

if __name__ == "__main__":
    main()