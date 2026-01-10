"""
Module for retrieving video ID's from a YouTube channel.

This module fetches the list of videos for a given channel URL and
returns video ID's required for transcript extraction.
"""

from dotenv import load_dotenv
import os
import src.wts.exceptions as exceptions
import requests
import subprocess

load_dotenv()

api_key = os.getenv("API_KEY")

CHANNEL_ID_FETCH_TIMEOUT = 15

def get_channel_id(url: str) -> str:
    """
    Retrieve the channel ID from a YouTube channel URL.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--print", "filename",
                "-o", "%(channel_id)s",
                "--skip-download",
                "--playlist-items", "1",
                "--no-warnings",
                url
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=CHANNEL_ID_FETCH_TIMEOUT
        )
        return result.stdout.strip()
    
    except subprocess.CalledProcessError as e:
        err = e.stderr if e.stderr else "unknown error"
        msg = (
            f"Failed to fetch channel ID for the URL: {url}.\n"
            f"Check below for the error.\n{err}"
        )
        raise exceptions.ChannelFetchError(msg) from e
    
    except subprocess.TimeoutExpired as e:
        raise exceptions.ChannelFetchError(
            f"Timed out while fetching channel ID for the URL: {url}") from e

def get_upload_playlist_id(channel_id: str) -> str:
    """
    Retrieve the upload playlist ID for a given channel ID.
    """
    params = {
        "part": "contentDetails",
        "maxResults": 50,
        "id": channel_id,
        "key": api_key
    }
    response = requests.get(url="https://youtube.googleapis.com/youtube/v3/channels", params=params)
    data = response.json()
    playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    return playlist_id

def get_video_ids(channel_url: str) -> list[str]:
    """
    Retrieve video ID's from a YouTube channel URL and return them as a list.
    """
    id = get_channel_id(channel_url)
    playlist_id = get_upload_playlist_id(id)
    video_ids = []
    next_page_token = None
    # YouTube paginates the results with a max of only 50 items per page. The result also consists of a token
    # to access previous or/and next pages (if any) which can be used to send requests to get subsequent pages.
    # If there is no previous page or next page, the respective fields will not be present in the JSON.
    while True:
        params = {
            "part": "contentDetails",
            "maxResults": 50,
            "playlistId": playlist_id,
            "key": api_key
        }
        if next_page_token:
            params["pageToken"] = next_page_token
        next_page_token = None
        response = requests.get("https://youtube.googleapis.com/youtube/v3/playlistItems", params=params)
        data = response.json()
        for playlist_item in data["items"]:
            video_ids.append(playlist_item["contentDetails"]["videoId"])
        if "nextPageToken" in data:
            next_page_token = data["nextPageToken"]
        if next_page_token is None:
            break
    return video_ids

def main():
    channel_url = "https://www.youtube.com/@LinusTechTips"
    get_video_ids(channel_url)

if __name__ == "__main__":
    main()