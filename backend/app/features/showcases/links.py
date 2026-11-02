"""Strict provider links and generated previews; never fetch arbitrary pasted URLs."""
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import parse_qs, urlsplit
from uuid import UUID


@dataclass(frozen=True)
class VideoLink:
    url: str
    platform: Literal["youtube", "instagram"]
    thumbnail_url: str | None


def parse_video_link(value: str) -> VideoLink:
    value = value.strip()
    if "://" not in value:
        value = f"https://{value}"
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise ValueError("Enter a valid YouTube Shorts or Instagram Reel link.") from exc
    if (
        parts.scheme != "https" or parts.username or parts.password or port is not None
        or re.search(r"[\s\\\x00-\x1f\x7f]", value)
    ):
        raise ValueError("Use a plain HTTPS YouTube Shorts or Instagram Reel link.")
    host = (parts.hostname or "").lower()
    path = parts.path.rstrip("/")
    video_id = None
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        match = re.fullmatch(r"/shorts/([A-Za-z0-9_-]{11})", path)
        if match:
            video_id = match[1]
        elif path == "/watch":
            values = parse_qs(parts.query).get("v", [])
            if len(values) == 1 and re.fullmatch(r"[A-Za-z0-9_-]{11}", values[0]):
                video_id = values[0]
    elif host == "youtu.be":
        match = re.fullmatch(r"/([A-Za-z0-9_-]{11})", path)
        if match:
            video_id = match[1]
    if video_id:
        return VideoLink(
            url=f"https://www.youtube.com/shorts/{video_id}",
            platform="youtube",
            thumbnail_url=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        )
    if host in {"instagram.com", "www.instagram.com"}:
        match = re.fullmatch(r"/reel/([A-Za-z0-9_-]{5,64})", path)
        if match:
            return VideoLink(f"https://www.instagram.com/reel/{match[1]}/", "instagram", None)
    raise ValueError("Paste a YouTube Shorts/video link or an Instagram /reel/ link, not a profile or channel.")


def validate_cover_url(
    cover_url: str | None, video: VideoLink, supabase_url: str, auth_user_id: UUID,
) -> str:
    if not cover_url or cover_url == video.thumbnail_url:
        if video.thumbnail_url:
            return video.thumbnail_url
        raise ValueError("Upload a thumbnail or poster before publishing this Instagram Reel.")
    base = supabase_url.rstrip("/")
    prefix = f"{base}/storage/v1/object/public/profile-images/{auth_user_id}/showcase-"
    if not base or not cover_url.startswith(prefix):
        raise ValueError("Upload your thumbnail using the showcase image picker.")
    image_id = cover_url[len(prefix):]
    if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.webp", image_id):
        raise ValueError("Invalid showcase thumbnail URL.")
    return cover_url
