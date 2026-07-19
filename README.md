# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

**My version** is a content-based music recommender built on a 10-song catalog.
The user describes the kind of music they want — a genre, a mood, a target energy
level, and whether they prefer acoustic or produced sound — and the system scores
every song in the catalog against that description, then returns the best
matches ranked highest first. Every recommendation comes with a plain-language
explanation of *why* it was chosen, because the score is assembled from named
features rather than a black-box model.

The design choice I care most about is that numeric features are scored by
**closeness rather than magnitude**: a user asking for low-energy music gets
genuinely calm songs, instead of being handed the most intense track in the
catalog. I also deliberately excluded `tempo_bpm` and `danceability` after
finding they are almost perfectly correlated with `energy` in this dataset —
including them would have quietly counted the same signal four times.

---

## How The System Works

### How real recommenders work, and what mine does instead

Real platforms like Spotify and YouTube lean mostly on **collaborative
filtering**: they ignore what a song sounds like and instead learn from the
behavior of millions of listeners — plays, skips, saves, and especially which
songs people put in the same playlists. If lots of people who play song X also
play song Y, the system links X and Y without ever analyzing the audio. That
works extremely well at scale, but it needs an enormous amount of interaction
data, and it can't recommend a song nobody has played yet.

My simulator has no listening history at all — just a catalog of 10 songs and
their attributes — so it uses the other pillar, **content-based filtering**. It
compares the *properties of each song* against a user's stated preferences and
scores the match. This means it can recommend a brand-new song the moment it is
added to the CSV, and it can explain every recommendation in plain language,
since every point in the score comes from a named feature. The trade-off is that
it can only ever suggest things similar to what the user already asked for — it
has no way to discover that two songs belong together for cultural reasons its
columns don't capture.

**What my version prioritizes:** matching the *situation* over matching
popularity. I weight genre and mood most heavily, then how closely a song's
energy matches the user's target, and I treat "close to your target energy" as
better than "high energy" — so a user looking for calm music gets calm music
rather than the most intense track in the catalog.

### Features used

I checked the correlations between the numeric columns before choosing, and found
that `tempo_bpm` (+0.96), `danceability` (+0.86) and `acousticness` (−0.99) are
almost perfectly correlated with `energy` in this catalog. Scoring all of them
would just be counting energy four times and drowning out genre and mood, so I
deliberately use only a subset.

**`Song` uses:**

| Feature | Type | Role in scoring |
|---|---|---|
| `genre` | categorical | Exact match scores highest; partial match (`indie pop` for `pop`) scores partial credit |
| `mood` | categorical | Exact match bonus |
| `energy` | float 0–1 | Compared by *closeness* to the user's target |
| `valence` | float 0–1 | Compared by closeness; the only numeric not correlated with energy, so it separates "intense and happy" from "intense and dark" |
| `acousticness` | float 0–1 | Read through the user's acoustic preference rather than scored directly |
| `id` | int | Not a feature — used only as a stable tie-breaker |
| `title`, `artist` | text | Display only |

Deliberately excluded: `tempo_bpm` and `danceability` (redundant with energy).

**`UserProfile` stores:**

| Field | Type | Meaning |
|---|---|---|
| `favorite_genre` | str | Preferred genre |
| `favorite_mood` | str | Preferred mood |
| `target_energy` | float 0–1 | The energy level being aimed for — not a minimum |
| `likes_acoustic` | bool | Whether acoustic production is a plus or a minus |
| `target_valence` | float 0–1 | How positive/upbeat the user wants the music. Added to the starter profile; defaults to 0.5 so existing code keeps working |

### Scoring Rule (one song)

Each song accumulates points from independent terms:

```
score = genre_points          # 2.0 exact match, 1.0 partial match, else 0
      + mood_points           # 1.5 if the mood matches, else 0
      + 1.5 * (1 - |song.energy  - user.target_energy|)
      + 0.5 * (1 - |song.valence - user.target_valence|)
      + acoustic_points       # 1.0 * acousticness, or 1.0 * (1 - acousticness)
```

The energy term is the important one. Using the *difference* rather than the raw
value means the score peaks when the song matches the user's target and falls off
in **both** directions — a 0.30 and a 0.50 song score identically against a 0.40
target. Scoring raw energy instead would recommend the single most intense track
in the catalog to everyone.

Genre is weighted above mood because a genre mismatch is the more serious error:
a listener who asks for lofi and is handed intense rock rejects it outright,
while a listener who wants "chill" and gets a "relaxed" jazz track is usually
satisfied. The weights are kept close together on purpose — a very large genre
weight would turn the recommender into a genre filter with no variety.

### Ranking Rule (the list)

Scoring answers "how well does this one song fit?" — but a score of 4.2 means
nothing on its own. The **ranking rule** turns scores into an actual
recommendation:

1. Score every song in the catalog.
2. Sort by score, highest first.
3. Break ties by `id`, so results are stable and reproducible.
4. Return the top `k`.

Keeping these separate matters because ranking involves decisions a single-song
function structurally cannot make — how many results to return, what breaks a
tie, and whether the same artist should be allowed to fill the whole list. Those
are all list-level concerns. Real recommenders make the same split: scoring is
their ranking model, and this step is their re-ranking stage, where diversity and
freshness rules are applied.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



