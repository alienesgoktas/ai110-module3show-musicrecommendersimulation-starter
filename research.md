# Research Notes: How Streaming Platforms Recommend

Background research for the Music Recommender Simulation. Focus: the two core
pillars of production recommendation engines — **Collaborative Filtering** and
**Content-Based Filtering** — and how platforms like Spotify and YouTube combine
them.

**Research prompt used:** *"Act as a senior ML engineer specializing in
recommendation systems. Provide a deep-dive breakdown comparing Collaborative
Filtering and Content-Based Filtering, covering architecture, technical
mechanisms, cold-start behavior, and the real-world hybrid approach."*

---

## 1. High-Level Architectural Breakdown

The cleanest way to separate them is by **what dies if you delete the data**.

**Collaborative Filtering (CF)** knows nothing about the item itself. To a CF
model, a song is an opaque integer ID. All signal comes from the *co-occurrence
structure of behavior*: who listened to what, in what order, alongside what else.
Delete the audio files and CF is unaffected. Delete the interaction logs and CF
is dead.

**Content-Based Filtering (CBF)** knows nothing about other users. It builds an
item profile from *intrinsic attributes* — spectral features, tags, transcripts,
metadata — and matches it against a user profile built from that same feature
space. Delete every other user's history and CBF still works for you. Delete the
item features and it's dead.

### Data inputs compared

| | Collaborative Filtering | Content-Based Filtering |
|---|---|---|
| **Primary input** | User × item interaction events | Item attribute vectors |
| **Item representation** | Learned from behavior (opaque ID → embedding) | Derived from the asset (engineered or learned from raw media) |
| **User representation** | Learned from behavior | Aggregate of features of items the user engaged with |
| **Scales with** | Number of interactions | Richness of the feature extractor |
| **Failure mode** | Sparse/absent history | Feature space too coarse to capture taste |

### The key asymmetry

**CF learns a similarity metric it was never told; CBF applies a similarity
metric you designed.**

CF discovers that a Bad Bunny track and a Rosalía track belong together because
listeners treat them as belonging together — no one encoded "reggaeton
adjacency." CBF only discovers what its features can express. If the feature
vector is `{genre, tempo, energy}`, two songs sharing those values are identical
to the model, no matter how differently humans hear them.

This is why CF tends to win on raw accuracy wherever data is dense — it captures
latent taste dimensions ("music for coding," "songs that sound good in a car at
night") that nobody would think to hand-engineer.

---

## 2. Technical Mechanisms & Data Vectors

### 2.1 Collaborative Filtering

#### The interaction matrix

Start with a matrix `R` of shape `[num_users × num_items]`. At streaming scale
that is roughly 10⁸ × 10⁸, and it is catastrophically sparse — the average user
has touched a vanishing fraction of the catalog. The matrix is never
materialized; observed entries are stored as a sparse list.

Streaming platforms work with **implicit feedback**, not ratings. Nobody rates
songs 1–5. The signals are plays, completion rate, skips (a skip at 3 seconds is
a strong negative), saves, playlist adds, repeat listens.

This changes the math: an unobserved entry isn't "disliked," it's "unknown." The
standard treatment (Hu, Koren & Volinsky, 2008) fits *all* entries but weights
them by a confidence term derived from interaction count:

```
minimize  Σ  c_ui · (p_ui − xᵤᵀ yᵢ)²  +  λ(‖xᵤ‖² + ‖yᵢ‖²)
          u,i
  where   p_ui = 1 if any interaction, else 0
          c_ui = 1 + α · (play count, or listening time)
```

#### Matrix factorization

Approximate `R ≈ X · Yᵀ`, where `X` is `[users × d]` and `Y` is `[items × d]`,
with `d` typically 50–500. Each user and item becomes a `d`-dimensional vector in
a shared latent space; predicted affinity is the dot product `xᵤᵀ yᵢ`.

The latent dimensions are **emergent, not designed**. Inspecting them reveals
axes loosely corresponding to acoustic-vs-electronic, mainstream-vs-obscure,
regional clusters, era — but no dimension is guaranteed to be interpretable, and
most aren't. That's the trade: a representation richer than anything hand-built,
at the cost of explainability.

Alternating Least Squares (ALS) is the classic solver — fix `Y`, solve for `X` in
closed form, fix `X`, solve for `Y`, repeat. It parallelizes cleanly across
users, which is why it was the workhorse at Spotify scale for years.

**"Users who liked X also liked Y"** falls out of this geometry directly.
Item-item similarity is cosine distance in `Y`-space. Two songs end up near each
other when the same latent user-taste vectors score high on both — i.e. when the
same *kinds of people* play both. The audio was never compared.

#### Modern variants

- **Item2vec / playlist embeddings** — treat a playlist or session as a
  "sentence" and songs as "words," then run word2vec. Songs appearing in similar
  playlist contexts get similar vectors. Enormously effective for music
  specifically, because human-curated playlists are a dense, high-quality
  co-occurrence signal that doesn't exist in most domains.
- **Two-tower neural retrieval** — a user encoder and an item encoder trained
  jointly, scored by dot product. Same geometry as MF, but each tower can ingest
  arbitrary features — this is the seam where content signal gets injected.
- **Sequential models** — transformers over the ordered listen history, capturing
  *intent drift* within a session. The last five tracks predict the sixth far
  better than an all-time aggregate does.

#### The retrieval trick

Once everything is a vector, "find the best candidates" becomes approximate
nearest-neighbor search (HNSW, ScaNN, FAISS) over 10⁸ items in single-digit
milliseconds. This is why the dot-product formulation survives even in deep
architectures — it is the only scoring function supporting sublinear retrieval at
catalog scale.

### 2.2 Content-Based Filtering

CBF's job: turn a raw asset into a vector without consulting any user.

**Tier 1 — engineered audio descriptors.** DSP over the waveform yields tempo
(beat tracking via onset-strength autocorrelation), key, loudness, plus
higher-level composites. Spotify's public track-features set — `energy`,
`valence`, `danceability`, `acousticness`, `instrumentalness`, `speechiness` —
descends from The Echo Nest, acquired in 2014. Interpretable and cheap.

> This is exactly the feature vocabulary in this lab's `data/songs.csv`. That
> dataset is a miniature of a real production feature store.

**Tier 2 — learned representations from spectrograms.** Skip hand-engineering
entirely: convert audio to a mel-spectrogram (a 2D time × frequency image), then
run a CNN or audio transformer over it. The model learns timbre, texture, and
production-style features that have no names.

The pivotal result is van den Oord, Dieleman & Schrauwen (2013), in collaboration
with Spotify: **train a CNN on spectrograms to predict the CF latent vectors**
produced by matrix factorization. That's the key architectural move — rather than
building a separate content-based similarity space, learn a function
`audio → CF-embedding-space`. A brand-new track with zero plays gets a
*predicted* collaborative embedding straight from its waveform and drops into the
same ANN index as everything else. **Cold start becomes a regression problem
instead of a modeling gap.**

**Tier 3 — text and cultural context.** Audio alone misses much of what makes
music similar to humans. Platforms use playlist titles, artist bios, music blogs,
and reviews, embedded via TF-IDF or transformers. This is how a model learns
"shoegaze" or "sad girl autumn" — concepts that are cultural, not acoustic.

**Video (YouTube).** The analogous stack: title/description/tag embeddings, ASR
transcripts (dominant for talking-head and educational content), thumbnail CNN
features, OCR of on-screen text, visual scene embeddings, plus channel-level and
topic-cluster features. Text is generally the strongest content signal; heavy
visual models are expensive and contribute less per unit of compute for most
content.

---

## 3. The Cold Start and Lifecycle Matrix

| Scenario | Collaborative Filtering | Content-Based Filtering | Practical resolution |
|---|---|---|---|
| **New user, zero history** | ❌ **Fails hard.** No row in `R` → no embedding. Fallback is global popularity: generic, and it hurts first-session retention. | ⚠️ **Fails too, but recoverably.** Needs a user profile, but that profile can be *declared* rather than inferred. | Onboarding flow — Spotify's artist-picker directly bootstraps a content/artist profile. Plus demographic/geo priors and aggressive exploration in session 1. One explicit signal beats zero implicit ones. |
| **New item, zero plays** | ❌ **Fails completely.** No interactions → no column → never retrieved. And if it's never retrieved, it never gets interactions: **self-reinforcing invisibility.** | ✅ **Handles natively.** Features exist the moment the file is uploaded. CBF's single strongest argument. | Predict the CF embedding from content (the 2013 CNN approach), then force exploration traffic. YouTube explicitly feeds video-age to the ranker so it can learn recency preference rather than inherit a stale training-set bias. |
| **Niche / hyper-specific taste** | ⚠️ **Mixed.** Excellent *if* the niche has critical mass — often better than CBF here, since it captures scene coherence audio features miss. Fails for genuinely sparse long-tail items; popularity bias pulls toward the head. | ⚠️ **Mixed the other way.** Fine at "more things that sound like this," bad at cultural boundaries. Will happily recommend an acoustically-similar track from a scene the listener would reject. | Hybrid: CBF to reach the tail, CF to enforce scene coherence, diversity constraints at re-rank to prevent head-collapse. |
| **Mature user, mature catalog** | ✅ **Dominant.** Dense signal, and CF's latent dimensions outperform any hand-designed feature space. | ⚠️ **Weaker.** Tends toward a **filter bubble** — structurally cannot suggest something dissimilar-but-loved. | CF-led candidate generation, CBF as a secondary source for novelty and tail coverage. |

### Two cross-cutting biases

These are the ones that surface in fairness audits:

- **Popularity bias** — CF trains on interactions; popular items have more
  interactions, so they get recommended, generating more interactions.
  Uncorrected, this monotonically concentrates listening onto the head of the
  catalog. Mitigations: popularity-aware negative sampling, inverse-propensity
  weighting, explicit tail quotas at re-rank.
- **Position / presentation bias** — feedback is only observed on what was shown.
  The model learns from its own past choices, so its blind spots
  self-perpetuate. YouTube's 2019 ranking work (Zhao et al.) models position bias
  explicitly via a "shallow tower" that is removed at serving time.

---

## 4. Real-World Synergy: The Hybrid Pipeline

No production system is purely one or the other. The industry-standard shape is
**two-stage retrieve-and-rank**, canonically described in Covington, Adams &
Sargin (2016) for YouTube:

```
CATALOG (10⁸ items)
   │
   ├─ STAGE 1: CANDIDATE GENERATION  — many sources, run in parallel
   │    • CF: ANN lookup on user embedding            (personalized, dense-data)
   │    • Sequence model: next-item from session      (short-term intent)
   │    • Content: audio/text similarity to recent likes (cold items, tail)
   │    • Graph: playlist / channel co-occurrence
   │    • Heuristics: trending, followed artists, geo-popular, fresh releases
   │   →  each returns ~hundreds; union ≈ 500–1000 candidates
   │   →  optimized for RECALL. Cheap per item. Content sources are the only
   │      ones that can surface a zero-play item — cold start is solved HERE.
   │
   ├─ FILTERING — already-seen, disliked/blocked artists, regional licensing,
   │              policy and safety, explicit-content settings
   │
   ├─ STAGE 2: RANKING  — one expensive model over ~1000 items
   │    Features: CF embeddings + content embeddings + user context
   │      (time of day, device, headphones vs. speaker)
   │      + item age + past impressions of this item + interaction history
   │    Multi-task heads predicting several objectives at once:
   │      completion, skip probability, save, share, long-term retention
   │      (YouTube's MMoE handles correlated/conflicting objectives; the
   │       target is expected watch time, not CTR — a deliberate
   │       anti-clickbait fix)
   │
   └─ STAGE 3: RE-RANKING  — business and experience logic on the top ~50
        • Diversity: cap per-artist and per-genre density
        • Sequencing: audio-feature-aware ordering so energy/tempo flow
          sensibly — pure content-based, applied after all the ML
        • Freshness and exploration: reserve slots for uncertain items
        • Editorial and contractual placement
        →  final 20–30 delivered
```

### Case study: Discover Weekly

The clearest illustration of the blend. Its core signal is **playlist
co-occurrence CF** — the enormous corpus of user-made playlists treated as a
co-occurrence graph, so tracks that keep company with tracks you play become
candidates. Layered on top:

- an **audio model** letting never-played tracks enter the pool at all,
- **NLP** over playlist titles and web text for cultural context,
- a hard **filter** removing anything already heard.

That last constraint is what makes the product *feel* different from the rest of
the app — a deliberate optimization for discovery over accuracy, which a pure
engagement-maximizing ranker would never choose on its own.

### The synergy in one line

**CF supplies the taste geometry, CBF supplies coverage of the catalog, and the
ranker learns how much to trust each per-user, per-context.** When history is
thin or the item is new, the model leans on content features; when history is
rich, CF embeddings dominate. The blend isn't a fixed weight — it's learned, and
it varies per request.

---

## 5. Implications for This Project

The `score_song` function in this project is a **pure content-based recommender
with hand-set weights**. The `songs.csv` columns (`energy`, `valence`,
`tempo_bpm`, `acousticness`, `danceability`) are a direct miniature of a real
content feature store.

This means the system inherits CBF's genuine properties, not toy ones:

| Property | Consequence here |
|---|---|
| ✅ No item cold start | A brand-new song added to the CSV is recommendable instantly — no plays required. |
| ✅ Fully explainable | Every point in the score traces to a named feature, so `explain_recommendation` can be honest rather than post-hoc. Production CF cannot do this. |
| ❌ No collective intelligence | It cannot learn that two songs go together for reasons outside its columns. |
| ❌ Filter bubble by construction | It can only recommend what is near what was asked for. It will never surface a delightful surprise. |
| ⚠️ Weights encode a theory of taste | Whichever weight is highest (genre vs. energy vs. mood) *is* the model's implicit claim about what taste is — and it applies identically to every user. |

Each of these is empirically demonstrable once the scoring function exists, which
makes for a far stronger model card than simply asserting them.

---

## References

- Hu, Koren & Volinsky (2008). *Collaborative Filtering for Implicit Feedback
  Datasets.* — confidence-weighted MF; the basis of ALS on play counts.
- van den Oord, Dieleman & Schrauwen (2013). *Deep Content-Based Music
  Recommendation.* — CNN on spectrograms predicting CF latent factors; the
  canonical cold-start bridge.
- Covington, Adams & Sargin (2016). *Deep Neural Networks for YouTube
  Recommendations.* — the two-stage candidate-generation / ranking architecture.
- Zhao et al. (2019). *Recommending What Video to Watch Next: A Multitask Ranking
  System.* — MMoE multi-objective ranking and the position-bias shallow tower.

*Note: published papers describe these systems as of their publication dates.
Current production internals at Spotify and YouTube are proprietary and have
evolved since.*
