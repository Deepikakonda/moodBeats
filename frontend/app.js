const API_BASE = window.__API_BASE__ || "http://127.0.0.1:5000";

const form = document.getElementById("mood-form");
const textArea = document.getElementById("mood-text");
const playlistEl = document.getElementById("playlist");
const playlistHint = document.getElementById("playlist-hint");
const refreshBtn = document.getElementById("refresh-btn");
const moodCard = document.getElementById("mood-card");
const moodLabel = document.querySelector("[data-mood-label]");
const moodPolarity = document.querySelector("[data-mood-polarity]");
const moodSubjectivity = document.querySelector("[data-mood-subjectivity]");

let lastSubmission = "";

function setLoading(isLoading) {
  const submitBtn = form.querySelector("button[type='submit']");
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "Generating..." : "Generate playlist";
  refreshBtn.disabled = isLoading;
}

function renderTracks(tracks) {
  playlistEl.innerHTML = "";
  const template = document.getElementById("track-template");

  tracks.forEach((track) => {
    const node = template.content.firstElementChild.cloneNode(true);
    const cover = node.querySelector(".track-card__art");
    const title = node.querySelector(".track-card__title");
    const artists = node.querySelector(".track-card__artists");
    const album = node.querySelector(".track-card__album");
    const actions = node.querySelector(".track-card__actions");

    cover.src = track.image_url || "https://placehold.co/200x200/111428/ffffff?text=Mood";
    cover.alt = `${track.name} album art`;
    title.textContent = track.name;
    artists.textContent = track.artists.join(", ");
    album.textContent = track.album || "Unknown album";

    actions.innerHTML = "";
    if (track.preview_url) {
      const audio = document.createElement("audio");
      audio.controls = true;
      audio.src = track.preview_url;
      actions.appendChild(audio);
    } else {
      const placeholder = document.createElement("span");
      placeholder.className = "track-card__placeholder";
      placeholder.textContent = "Preview not available";
      actions.appendChild(placeholder);
    }

    if (track.external_url) {
      const link = document.createElement("a");
      link.href = track.external_url;
      link.target = "_blank";
      link.rel = "noreferrer noopener";
      link.textContent = "Open in Spotify";
      link.className = "track-card__link";
      actions.appendChild(link);
    }

    playlistEl.appendChild(node);
  });
}

function updateMoodCard(mood) {
  moodLabel.textContent = mood.label;
  moodPolarity.textContent = mood.polarity;
  moodSubjectivity.textContent = mood.subjectivity;
  moodCard.hidden = false;
}

async function fetchPlaylist(text) {
  const response = await fetch(`${API_BASE}/api/playlist`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = payload.error || "Unable to generate playlist. Please try again.";
    throw new Error(message);
  }

  return response.json();
}

async function handleSubmit(event, overrideText) {
  if (event) {
    event.preventDefault();
  }

  const entry = overrideText ?? textArea.value.trim();

  if (!entry) {
    playlistHint.textContent = "Add at least a few words before we can curate music.";
    return;
  }

  setLoading(true);
  playlistHint.textContent = "Analyzing your mood and crafting a playlist...";

  try {
    const data = await fetchPlaylist(entry);
    lastSubmission = entry;
    renderTracks(data.tracks);
    updateMoodCard(data.mood);
    playlistHint.textContent = data.warning || "Enjoy your personalized Spotify mix.";
    refreshBtn.hidden = false;
  } catch (error) {
    playlistHint.textContent = error.message;
  } finally {
    setLoading(false);
  }
}

form.addEventListener("submit", (event) => handleSubmit(event));

refreshBtn.addEventListener("click", () => {
  if (!lastSubmission) return;
  handleSubmit(undefined, lastSubmission);
});
