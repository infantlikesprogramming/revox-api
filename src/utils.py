from pytube import YouTube
from datetime import datetime
from isodate import parse_duration
from googleapiclient.discovery import build
import re
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

from src.translation.schemas import YoutubeInfo
import boto3
import logging
from botocore.exceptions import ClientError
import os
from src.speechinfo.schemas import YoutubeInfoResponse
from pydub import AudioSegment

load_dotenv()

youtube_key = os.environ.get("YOUTUBE_API_KEY")


def merge_mp3_files(file_paths, output_path):
    # Initialize an empty AudioSegment
    combined = AudioSegment.empty()
    # Append each MP3 file
    for path in file_paths:
        audio = AudioSegment.from_file(path, format="mp3")

        combined += audio

    # Export as MP3

    combined.export(output_path, format="mp3")
    return None


def file_to_s3(filepath):
    s3 = boto3.client("s3")

    bucket_name = "demo-audio-streaming-service"

    try:
        response = s3.upload_file(filepath, bucket_name, os.path.basename(filepath))
    except ClientError as e:
        logging.error(e)
        return False
    return True


async def get_speech_info_from_url(url):
    try:

        youtube = build("youtube", "v3", developerKey=youtube_key)

        video_id = extract_video_id(url)

        request = youtube.videos().list(part="snippet, contentDetails", id=video_id)

        response = request.execute()

        if not response.get("items"):
            print("Error: No video data found")
            return None
        total_seconds = 0
        snippet = response["items"][0]["snippet"]
        content_details = response["items"][0]["contentDetails"]
        uploader = snippet.get("channelTitle", "Unknown")
        publish_date = datetime.strptime(snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        language = snippet.get("defaultAudioLanguage", "Not specified")
        title = snippet.get("title", "Unknown")
        duration = content_details.get(
            "duration", "Unknown"
        )  # ISO 8601 duration (e.g., PT5M30S)

        if duration != "Unknown":
            # Parse ISO 8601 duration to a timedelta object
            duration_timedelta = parse_duration(duration)

            # Extract hours, minutes, seconds
            total_seconds = int(duration_timedelta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            # Format as hours:minutes:seconds
            duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_formatted = "Unknown"

        # transcript = get_transcript(video_id)
        print(f"Title: {title}")
        print(f"Uploader: {uploader}")
        print(
            "Published Date: ",
            publish_date.strftime("%Y-%m-%d %H:%M:%S").split(" ")[0],
        )
        print(f"Language: {language}")
        # transcript_list = []
        # for parts in transcript[1]:
        #     text = parts["text"]
        #     transcript_list.append(text)
        # transcript_text = " ".join(transcript_list)
        return YoutubeInfo(
            title=title,
            uploader=uploader,
            publish_date=publish_date.strftime("%Y-%m-%d %H:%M:%S").split(" ")[0],
            language=language,
            # transcript=transcript_text,
            duration=duration_formatted,
            duration_in_seconds=total_seconds,
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


async def get_video_info_from_url(url):
    try:

        youtube = build("youtube", "v3", developerKey=youtube_key)

        video_id = extract_video_id(url)

        request = youtube.videos().list(part="snippet, contentDetails", id=video_id)

        response = request.execute()

        if not response.get("items"):
            print("Error: No video data found")
            return None

        snippet = response["items"][0]["snippet"]
        content_details = response["items"][0]["contentDetails"]
        uploader = snippet.get("channelTitle", "Unknown")
        publish_date = datetime.strptime(snippet["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        language = snippet.get("defaultAudioLanguage", "Not specified")
        title = snippet.get("title", "Unknown")
        duration = content_details.get(
            "duration", "Unknown"
        )  # ISO 8601 duration (e.g., PT5M30S)

        if duration != "Unknown":
            # Parse ISO 8601 duration to a timedelta object
            duration_timedelta = parse_duration(duration)

            # Extract hours, minutes, seconds
            total_seconds = int(duration_timedelta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            # Format as hours:minutes:seconds
            duration_formatted = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration_formatted = "Unknown"

        # transcript = get_transcript(video_id)
        print(f"Title: {title}")
        print(f"Uploader: {uploader}")
        print(
            "Published Date: ",
            publish_date.strftime("%Y-%m-%d %H:%M:%S").split(" ")[0],
        )
        print(f"Language: {language}")
        # transcript_list = []
        # for parts in transcript[1]:
        #     text = parts["text"]
        #     transcript_list.append(text)
        # transcript_text = " ".join(transcript_list)
        return YoutubeInfoResponse(
            title=title,
            uploader=uploader,
            publish_date=publish_date.strftime("%Y-%m-%d %H:%M:%S").split(" ")[0],
            language=language,
            duration=duration_formatted,
        )

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    print(match.group(1))
    return match.group(1) if match else None


def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        language = next(iter(transcript_list))
        return [
            language.language.split(" ")[0],
            YouTubeTranscriptApi.get_transcript(video_id, [language.language_code]),
        ]

    except Exception as e:
        print(f"Transcript Error: {str(e)}")
        return None
