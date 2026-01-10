import wts.youtube.videos as videos
import wts.youtube.transcripts as transcripts

def main():
    channel_url = "https://www.youtube.com/@ryanthreethousand"
    vid_list = videos.get_video_ids(channel_url)
    transcripts.get_transcript(vid_list)

if __name__ == "__main__":
    main()