import base64
import logging
import os
import time
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from textblob import TextBlob

load_dotenv()

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=os.getenv("MOODBEATS_LOG_LEVEL", "INFO"))
LOGGER = logging.getLogger("moodbeats")

MOOD_KEYWORDS = {
    "happy": ["happy", "joy", "joyful", "excited", "great", "awesome", "grateful"],
    "sad": ["sad", "down", "blue", "depressed", "lonely", "upset", "cry"],
    "angry": ["angry", "mad", "furious", "frustrated", "annoyed", "irritated"],
    "chill": ["calm", "relaxed", "peaceful", "serene", "chill"],
    "energetic": ["pumped", "motivated", "energetic", "hype", "unstoppable", "focus"],
    "romantic": ["love", "romantic", "crush", "date", "affection", "heart"],
}

MOOD_GENRE_MAP = {
    "happy": {"seeds": ["pop", "indie-pop", "dance"], "target_energy": 0.8, "target_valence": 0.9},
    "sad": {"seeds": ["acoustic", "soft-rock", "piano"], "target_energy": 0.35, "target_valence": 0.2},
    "chill": {"seeds": ["chill", "lo-fi", "ambient"], "target_energy": 0.45, "target_valence": 0.55},
    "angry": {"seeds": ["metal", "hard-rock", "punk"], "target_energy": 0.9, "target_valence": 0.25},
    "energetic": {"seeds": ["edm", "work-out", "house"], "target_energy": 0.95, "target_valence": 0.7},
    "romantic": {"seeds": ["r-n-b", "soul", "romance"], "target_energy": 0.55, "target_valence": 0.75},
    "focus": {"seeds": ["classical", "instrumental", "sleep"], "target_energy": 0.25, "target_valence": 0.4},
}

FALLBACK_TRACKS = [
    {
        "id": "0VjIjW4GlUZAMYd2vXMi3b",
        "name": "Blinding Lights",
        "artists": ["The Weeknd"],
        "album": "After Hours",
        "preview_url": None,
        "external_url": "https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b",
        "image_url": "https://i.scdn.co/image/ab67616d0000b27375f5bce01fa8de6d9f62002a",
    },
    {
        "id": "4RVwu0g32PAqgUiJoXsdF8",
        "name": "good 4 u",
        "artists": ["Olivia Rodrigo"],
        "album": "SOUR",
        "preview_url": "https://p.scdn.co/mp3-preview/ba8242713c0bcbce833b0dff78eaefdd8f2fa2f3",
        "external_url": "https://open.spotify.com/track/4RVwu0g32PAqgUiJoXsdF8",
        "image_url": "https://i.scdn.co/image/ab67616d0000b273f1fdbea5b7d1db9fee96060f",
    },
    {
        "id": "0rFke7rXGrC0TMFARmPzqk",
        "name": "Lost in Yesterday",
        "artists": ["Tame Impala"],
        "album": "The Slow Rush",
        "preview_url": "https://p.scdn.co/mp3-preview/92e21bf0b92bb3a849247fc9bae8792e95af1f52",
        "external_url": "https://open.spotify.com/track/0rFke7rXGrC0TMFARmPzqk",
        "image_url": "https://i.scdn.co/image/ab67616d0000b273b96a26b10a4112e63f7b7ac5",
    },
    {
        "id": "4iV5W9uYEdYUVa79Axb7Rh",
        "name": "The Less I Know The Better",
        "artists": ["Tame Impala"],
        "album": "Currents",
        "preview_url": "https://p.scdn.co/mp3-preview/cc089216c35987b7d342ecffa73a02ebc1fad6f5",
        "external_url": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh",
        "image_url": "https://i.scdn.co/image/ab67616d0000b2736abcf049d88bcebac1483fcf",
    },
    {
        "id": "2YpeDb67231RjR0MgVLzsG",
        "name": "Still Feel.",
        "artists": ["half-alive"],
        "album": "Now, Not Yet",
        "preview_url": "https://p.scdn.co/mp3-preview/4b2ff1c6ed27a0d47820a84b526f5c872826ffba",
        "external_url": "https://open.spotify.com/track/2YpeDb67231RjR0MgVLzsG",
        "image_url": "https://i.scdn.co/image/ab67616d0000b27365379b3f9d3a4fe26c7c0b65",
    },
    {
        "id": "5ChkMS8OtdzJeqyybCc9R5",
        "name": "Midnight City",
        "artists": ["M83"],
        "album": "Hurry up, We're Dreaming",
        "preview_url": "https://p.scdn.co/mp3-preview/b0bbc8b9a29f7bf8c809f5d457f41726b2dfca7b",
        "external_url": "https://open.spotify.com/track/5ChkMS8OtdzJeqyybCc9R5",
        "image_url": "https://i.scdn.co/image/ab67616d0000b273f1f30f7b843fc7dc3b3f70c0",
    },
]

SPOTIFY_TOKEN_CACHE = {"value": None, "expires_at": 0.0}


def _keyword_override(text: str) -> Optional[str]:
    lowered = text.lower()
    for mood, keywords in MOOD_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return mood
    return None


def classify_mood(text: str) -> Dict[str, float]:
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 3)
    subjectivity = round(blob.sentiment.subjectivity, 3)

    mood = _keyword_override(text)
    if mood:
        return {"label": mood, "polarity": polarity, "subjectivity": subjectivity}

    if polarity >= 0.45:
        mood = "happy"
    elif polarity >= 0.15:
        mood = "chill"
    elif polarity <= -0.5:
        mood = "angry"
    elif polarity <= -0.15:
        mood = "sad"
    elif subjectivity <= 0.35:
        mood = "focus"
    else:
        mood = "chill"

    return {"label": mood, "polarity": polarity, "subjectivity": subjectivity}


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def _build_basic_auth_header(client_id: str, client_secret: str) -> str:
    token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8"))
    return f"Basic {token.decode('ascii')}"


def _request_spotify_token() -> Optional[str]:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        LOGGER.error("Spotify credentials missing. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
        return None

    headers = {
        "Authorization": _build_basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "client_credentials"}

    try:
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers=headers,
            data=data,
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        LOGGER.exception("Failed to fetch Spotify token: %s", exc)
        return None

    token = payload.get("access_token")
    expires_in = payload.get("expires_in", 3600)
    if token:
        SPOTIFY_TOKEN_CACHE["value"] = token
        SPOTIFY_TOKEN_CACHE["expires_at"] = time.time() + (expires_in - 30)
        LOGGER.info("Fetched Spotify token successfully. Expires in %s seconds.", expires_in)
    else:
        LOGGER.error("Spotify token response missing 'access_token': %s", payload)
    return token


def _get_spotify_token() -> Optional[str]:
    now = time.time()
    if SPOTIFY_TOKEN_CACHE["value"] and now < SPOTIFY_TOKEN_CACHE["expires_at"]:
        return SPOTIFY_TOKEN_CACHE["value"]
    return _request_spotify_token()


def _build_track(track: Dict) -> Dict:
    album = track.get("album", {})
    images = album.get("images", [])
    image_url = images[0]["url"] if images else None
    artists = [artist["name"] for artist in track.get("artists", [])]

    return {
        "id": track.get("id"),
        "name": track.get("name"),
        "artists": artists,
        "album": album.get("name"),
        "preview_url": track.get("preview_url"),
        "external_url": track.get("external_urls", {}).get("spotify"),
        "image_url": image_url,
    }


def fetch_spotify_recommendations(mood_label: str, limit: int = 12) -> Tuple[List[Dict], Optional[str]]:
    mood_config = MOOD_GENRE_MAP.get(mood_label, MOOD_GENRE_MAP["chill"])
    token = _get_spotify_token()
    if not token:
        return FALLBACK_TRACKS, "Falling back to static sample playlist. Provide Spotify credentials for live data."

    params = {
        "seed_genres": ",".join(mood_config["seeds"]),
        "limit": limit,
        "market": os.getenv("SPOTIFY_MARKET", "US"),
        "target_energy": mood_config["target_energy"],
        "target_valence": mood_config["target_valence"],
    }

    try:
        response = requests.get(
            "https://api.spotify.com/v1/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        tracks = [_build_track(track) for track in data.get("tracks", [])]
        return tracks or FALLBACK_TRACKS, None
    except requests.RequestException as exc:
        LOGGER.exception("Spotify recommendations request failed: %s", exc)
        return FALLBACK_TRACKS, "Unable to reach Spotify. Showing sample playlist instead."


@app.route("/api/health", methods=["GET"])
def health() -> Tuple[str, int]:
    return jsonify({"status": "ok"}), 200


@app.route("/api/playlist", methods=["POST"])
def playlist() -> Tuple[str, int]:
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text", "").strip()
    limit = payload.get("limit") or _get_env_int("PLAYLIST_LIMIT", 12)

    if not text:
        return jsonify({"error": "Please share how you're feeling to build a playlist."}), 400

    mood = classify_mood(text)
    tracks, warning = fetch_spotify_recommendations(mood["label"], limit=limit)

    return (
        jsonify(
            {
                "mood": mood,
                "tracks": tracks,
                "warning": warning,
                "timestamp": int(time.time()),
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True)
