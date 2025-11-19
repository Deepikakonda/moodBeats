# MoodBeats

MoodBeats is a lightweight full-stack prototype that turns a short journal entry into a personalized Spotify playlist. It uses TextBlob for sentiment analysis, maps the detected mood to curated Spotify genres, and streams track previews inside a single-page experience.

## Stack

- **Backend**: Python, Flask, Flask-Cors, TextBlob, Spotify Web API, python-dotenv
- **Frontend**: Static HTML/CSS/JS (vanilla) with a responsive layout

## Getting Started

### 1. Backend (Flask)

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate   # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a template:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_MARKET=US
PLAYLIST_LIMIT=12
```

Run the API:

```bash
flask --app app run --debug
# or
python app.py
```

### 2. Frontend

For quick local use you can open `frontend/index.html` directly in the browser. For CORS-friendly development, serve it with any static server:

```bash
cd frontend
npx serve .
# or use python -m http.server
```

Visit http://localhost:3000 (or whichever port your static server prints) and ensure the backend is reachable at http://127.0.0.1:5000.

## API Overview

`POST /api/playlist`

```json
{
  "text": "Feeling optimistic after landing the big presentation!"
}
```

Response:

```json
{
  "mood": { "label": "happy", "polarity": 0.58, "subjectivity": 0.63 },
  "tracks": [
    {
      "id": "xyz",
      "name": "Song Title",
      "artists": ["Artist"],
      "album": "Album name",
      "preview_url": "https://p.scdn.co/mp3-preview/...",
      "external_url": "https://open.spotify.com/track/...",
      "image_url": "https://i.scdn.co/image/..."
    }
  ],
  "warning": null,
  "timestamp": 1683563456
}
```

If Spotify credentials are missing or the API call fails, the route falls back to a curated static playlist and sets a descriptive warning message.

<img width="1862" height="900" alt="image" src="https://github.com/user-attachments/assets/9b5fb808-c739-4ab1-b7d2-cb2ea1f2c474" />


## Notes

- TextBlob is downloaded at install time; no extra corpora downloads are necessary.
- Store your Spotify credentials securely (never commit `.env`).
- The frontend exposes a refresh button so you can regenerate playlists with the same journal entry, useful when experimenting with Spotify parameters.
