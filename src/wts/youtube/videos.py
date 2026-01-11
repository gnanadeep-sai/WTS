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
YOUTUBE_API_TIMEOUT = 5
MAX_RESULTS_PER_PAGE = 50  # The API only supports a maximum of 50


def get_channel_id(url: str) -> str:
    """
    Retrieve the channel ID from a YouTube channel URL.
    """
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--print",
                "filename",
                "-o",
                "%(channel_id)s",
                "--skip-download",
                "--playlist-items",
                "1",
                "--no-warnings",
                url,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=CHANNEL_ID_FETCH_TIMEOUT,
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
            f"Timed out while fetching channel ID for the URL: {url}"
        ) from e


def yt_api_req(type: str, params: dict) -> dict:
    try:
        response = requests.get(
            url=f"https://youtube.googleapis.com/youtube/v3/{type}",
            params=params,
            timeout=YOUTUBE_API_TIMEOUT,
        )
        response.raise_for_status()
        try:
            data = response.json()
            return data
        except ValueError as e:
            msg = f"Invalid data received:\n {response.text}"
            raise exceptions.YouTubeAPIError(msg) from e

    except requests.ConnectionError as e:
        msg = f"Failed to connect to the API. Check details below:\n{str(e)}"
        raise exceptions.YouTubeAPIError(msg) from e
    except requests.HTTPError as e:
        status_code = e.response.status_code
        msg = f"received bad response code from YouTubeAPI:{status_code}"
        raise exceptions.YouTubeAPIError(msg) from e
    except requests.Timeout as e:
        msg = "YouTubeAPI took too long to respond"
        raise exceptions.YouTubeAPIError(msg) from e


def get_upload_playlist_id(channel_id: str) -> str:
    """
    Retrieve the upload playlist ID for a given channel ID.
    """
    try:
        params = {
            "part": "contentDetails",
            "maxResults": MAX_RESULTS_PER_PAGE,
            "id": channel_id,
            "key": api_key,
        }

        data = yt_api_req("playlists", params)
        playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except (KeyError, TypeError) as e:
        msg = f"Invalid data received:\n {data}"
        raise exceptions.YouTubeAPIError(msg) from e

    return playlist_id


def get_video_ids(channel_url: str) -> list[str]:
    """
    Retrieve video ID's from a YouTube channel URL and return them as a list.
    """
    id = get_channel_id(channel_url)
    playlist_id = get_upload_playlist_id(id)
    video_ids = []
    next_page_token = None
    # YouTube paginates the results with a max of only 50 items per page.
    # The result also consists of a token to access previous or/and next pages (if any)
    # which can be used to send requests to get subsequent pages.
    # If there is no previous page or next page, the respective fields will not be present in the JSON.
    while True:
        params = {
            "part": "contentDetails",
            "maxResults": MAX_RESULTS_PER_PAGE,
            "playlistId": playlist_id,
            "key": api_key,
        }

        if next_page_token:
            params["pageToken"] = next_page_token
        next_page_token = None
        try:
            data = yt_api_req("playlistItems", params)
            for playlist_item in data["items"]:
                video_ids.append(playlist_item["contentDetails"]["videoId"])
            if "nextPageToken" in data:
                next_page_token = data["nextPageToken"]
        except (KeyError, TypeError) as e:
            msg = f"Invalid data received:\n {data}"
            raise exceptions.YouTubeAPIError(msg) from e

        if next_page_token is None:
            break
    return video_ids
