"""Content-based music recommender: scores songs against a user taste profile."""

import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass

# --- Algorithm Recipe weights (see README.md) ------------------------------
W_GENRE = 2.0           # exact genre match
W_GENRE_PARTIAL = 1.0   # shared word, e.g. "indie pop" for a "pop" fan
W_MOOD = 1.5            # exact mood match
W_ENERGY = 1.5          # scaled by closeness to the user's target
W_VALENCE = 0.5         # scaled by closeness to the user's target
W_ACOUSTIC = 1.0        # scaled by acousticness, or its inverse

NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.5   # defaulted so existing callers keep working

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Scores one song for one user, returning (score, reasons)."""
        return score_song(vars(user), vars(song))

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Returns the k best-scoring songs for the user, highest score first."""
        return sorted(self.songs, key=lambda s: (-self.score(user, s)[0], s.id))[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explains in one sentence why a song was recommended to a user."""
        score, reasons = self.score(user, song)
        return f"Scored {score:.2f} - " + "; ".join(reasons or ["no strong matches"])


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            song = dict(row)
            song["id"] = int(song["id"])
            for field in NUMERIC_FIELDS:
                song[field] = float(song[field])
            songs.append(song)
    return songs


def _closeness(a: float, b: float) -> float:
    """Returns 1.0 when two 0-1 values match, falling to 0.0 as they diverge."""
    return 1.0 - abs(a - b)


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    score = 0.0
    reasons: List[str] = []

    # 1. Genre - the heaviest term. Exact match beats a shared-word match
    #    ("indie pop" for someone who asked for "pop").
    want_genre = str(user_prefs.get("favorite_genre", "")).lower()
    song_genre = str(song.get("genre", "")).lower()
    if want_genre and want_genre == song_genre:
        score += W_GENRE
        reasons.append(f"genre match: {song_genre} (+{W_GENRE:.1f})")
    elif want_genre and set(want_genre.split()) & set(song_genre.split()):
        score += W_GENRE_PARTIAL
        reasons.append(f"partial genre match: {song_genre} (+{W_GENRE_PARTIAL:.1f})")

    # 2. Mood.
    want_mood = str(user_prefs.get("favorite_mood", "")).lower()
    if want_mood and want_mood == str(song.get("mood", "")).lower():
        score += W_MOOD
        reasons.append(f"mood match: {want_mood} (+{W_MOOD:.1f})")

    # 3. Energy - scored by closeness to the target, not by magnitude, so a
    #    user wanting calm music is not handed the most intense track.
    if user_prefs.get("target_energy") is not None:
        points = W_ENERGY * _closeness(song["energy"], float(user_prefs["target_energy"]))
        score += points
        reasons.append(f"energy {song['energy']:.2f} vs target "
                       f"{float(user_prefs['target_energy']):.2f} (+{points:.2f})")

    # 4. Valence - same idea, smaller weight. The only numeric not strongly
    #    correlated with energy, so it separates dark from bright.
    if user_prefs.get("target_valence") is not None:
        points = W_VALENCE * _closeness(song["valence"], float(user_prefs["target_valence"]))
        score += points
        reasons.append(f"valence {song['valence']:.2f} vs target "
                       f"{float(user_prefs['target_valence']):.2f} (+{points:.2f})")

    # 5. Acoustic preference - read the same column in opposite directions.
    if "likes_acoustic" in user_prefs:
        acousticness = float(song["acousticness"])
        if user_prefs["likes_acoustic"]:
            points = W_ACOUSTIC * acousticness
            label = "acoustic"
        else:
            points = W_ACOUSTIC * (1.0 - acousticness)
            label = "produced"
        score += points
        reasons.append(f"{label} sound (+{points:.2f})")

    return round(score, 2), reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, "; ".join(reasons or ["no strong matches"])))

    # sorted() returns a new list and leaves `songs` untouched; .sort() would
    # reorder the caller's catalog in place. Ties break on id so runs repeat.
    scored.sort(key=lambda item: (-item[1], item[0]["id"]))
    return scored[:k]
