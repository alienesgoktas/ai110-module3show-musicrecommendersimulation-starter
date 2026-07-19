# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Phase 1–2: Concept Research and Data Design

> Not a stretch feature — logged here for transparency about how AI was used
> during the design phases. Full research output lives in [`research.md`](research.md).

### Prompt 1 — How real recommenders work

> *"Act as a senior machine learning engineer specializing in recommendation
> systems. Provide a deep-dive breakdown comparing Collaborative Filtering and
> Content-Based Filtering, covering high-level architecture, technical mechanisms
> and data vectors, cold-start behavior, and the real-world hybrid approach used
> by platforms like Spotify and YouTube."*

**What it produced:** A structured comparison saved to `research.md` — the
implicit-feedback matrix factorization objective, spectrogram CNNs predicting CF
latent vectors, a cold-start matrix, and the two-stage
candidate-generation → ranking → re-ranking pipeline.

**What I took from it:** The realization that my project has *no interaction
data at all*, so collaborative filtering isn't a design option I'm rejecting —
the data to build it does not exist. That reframed the whole project as
content-based by necessity, which is now the opening argument in my README.

**What I verified:** Checked the four cited papers are real and correctly
attributed. Noted in `research.md` that published architectures describe these
systems as of publication date; current production internals are proprietary.

### Prompt 2 — Data types in recommender systems

> *"Identify the main data types involved in these systems, such as likes, skips,
> playlists, tempo, or mood."*

**What it produced:** A split between *signal categories* (explicit feedback,
implicit feedback, sequence/relational, item content, context, user attributes,
derived) and *representation types* (continuous normalized vs. unbounded,
categorical low- vs. high-cardinality, boolean, ordinal, sequential, text).

**What I took from it:** The warning that unbounded numeric features must be
normalized before entering a weighted sum — directly relevant to `tempo_bpm`
(60–168) sitting alongside 0–1 features.

### Prompt 3 — Feature selection and the scoring rule

> *"Analyze the available data in songs.csv and suggest which features would be
> most effective for a simple content-based recommender. Then explain how to
> score a numerical feature like energy so that songs closer to the user's
> preference are rewarded, rather than just higher values. Should a matching
> genre be worth more than a matching mood? And why do we need both a Scoring
> Rule and a Ranking Rule?"*

**What it produced:** The AI ran an actual correlation analysis on the CSV rather
than guessing, and found that in the 10-song starter catalog `tempo_bpm`
(r = +0.96), `danceability` (+0.86) and `acousticness` (−0.99) were nearly
perfectly correlated with `energy`.

**What I took from it:** This changed my feature list. Scoring all four numerics
would have been counting one signal four times at an effective weight of ~4.0,
drowning out genre and mood. I dropped `tempo_bpm` and `danceability` from the
scoring rule for this reason, and kept `valence` because it was the only numeric
that was *not* correlated with energy (r = +0.19).

Also adopted: `closeness = 1 − |song.energy − user.target_energy|` so the score
peaks at a match and decays in both directions, and the scoring/ranking split
(per-song pure function vs. list-level policy that owns `k`, tie-breaks and
diversity).

**What I pushed back on / verified manually:** I re-ran the correlation numbers
myself against the CSV rather than trusting the claim. I also had to decide
whether `target_valence` was worth adding to `UserProfile`, since the starter
class did not have that field.

### Prompt 4 — Expanding the dataset

> *"Generate 5–10 additional songs in valid CSV format matching the existing
> headers. Cover a diverse range of genres and moods not already present in the
> starter file."*

**What it produced:** 10 songs (ids 11–20) adding 9 genres (hip hop, folk, metal,
classical, house, bluegrass, r&b, afrobeats, country) and 5 moods (confident,
melancholy, euphoric, romantic, nostalgic).

**What I took from it:** Beyond variety, several rows were designed to break the
`energy`/`acousticness` correlation found in Prompt 3 — a loud acoustic bluegrass
track (#16, energy 0.87 / acousticness 0.90) and a quiet electronic one (#17,
energy 0.32 / acousticness 0.07). Two `ambient` songs now sit at opposite ends of
acousticness, so genre can no longer predict production style.

**Measured effect after expansion:**

| correlation with energy | before | after |
|---|---|---|
| acousticness | −0.99 | −0.72 |
| danceability | +0.86 | +0.69 |
| valence | +0.19 | +0.38 |
| tempo_bpm | +0.96 | +0.91 |

**Limitations I noted rather than hid:** `tempo_bpm` is still redundant
(+0.91), and genre is now sparse at 16 genres across 20 songs, so exact genre
matches will rarely fire. Both are documented as known trade-offs instead of
being engineered away.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

The assignment asked me to learn more about how streaming platforms like spotify youtube etc. predicts what the user will like next. So I provided a prompt for it to make a plan.

**Prompts used:**

Act as a senior machine learning engineer specializing in recommendation systems. I want to understand exactly how major music and video streaming platforms like Spotify and YouTube predict what a user will love next. 

Please provide a deep-dive breakdown that compares and contrasts the two core pillars of recommendation engines: **Collaborative Filtering** and **Content-Based Filtering**.

To keep this highly structured and actionable, please organize your response into the following sections:

1. **High-Level Architectural Breakdown:** Define Collaborative Filtering (leveraging collective user behavior) vs. Content-Based Filtering (analyzing intrinsic item attributes) in simple, architectural terms. How do they fundamentally differ in the data inputs they require?
2. **Technical Mechanisms & Data Vectors:** 
   * For Collaborative Filtering, explain how user-item interaction matrices, matrix factorization, or embeddings map similarities between users (e.g., "Users who liked X also liked Y").
   * For Content-Based Filtering, explain how platforms analyze raw assets—such as audio features (tempo, valence, timbre via spectrograms) or video data (tags, transcripts, visual framing)—to create an item profile.
3. **The "Cold Start" and Lifecycle Matrix:** Create a text-based matrix or comparison table illustrating how each approach handles:
   * A brand-new user with zero history.
   * A brand-new song/video with zero plays.
   * Niche or hyper-specific tastes.
4. **Real-World Synergy (The Hybrid Approach):** Explain how platforms like Spotify (e.g., Discover Weekly) or YouTube blend these two approaches to overcome individual limitations. What does the final "re-ranking" or hybrid pipeline look like in practice?

Keep your tone analytical, technical yet accessible, and use concrete examples from modern streaming platforms where applicable.

**What did the agent generate or change?**

<!-- List the files edited, code generated, or commands run -->

**What did you verify or fix manually?**

<!-- Describe anything the agent got wrong or that required human review -->

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

<!-- e.g., Strategy, Factory, Observer, etc. -->

**How did AI help you brainstorm or implement it?**

<!-- Describe the conversation or suggestions that led to your decision -->

**How does the pattern appear in your final code?**

<!-- Point to the relevant class or method -->
