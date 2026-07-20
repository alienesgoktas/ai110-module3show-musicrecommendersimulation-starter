# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**Vibe Check 1.0**

It checks whether a song matches the vibe you asked for. That is all it does.

---

## 2. Intended Use

**Goal:** You describe the kind of music you want. It picks songs from a small
catalog that match that description, ranks them best-first, and tells you why it
picked each one.

**What it assumes about you:**

- You can name one genre you want.
- You can name one mood you want.
- You know roughly how energetic you want the music, on a 0 to 1 scale.
- You have a yes/no preference about acoustic sound.

**Who it is for:** This is a classroom project. It is for learning how
recommenders work, not for real listeners. It has 20 songs in it. A real music
app has tens of millions.

**What it should NOT be used for:**

- Real product recommendations. The catalog is far too small.
- Deciding which artists get promoted or paid. It has no fairness safeguards.
- Any claim about what people "really" like. It only knows what you typed in.
- Users with rare taste. See section 6 — it fails them quietly, which is worse
  than failing loudly.

---

## 3. How the Model Works

Imagine handing a shop assistant a short list of what you want. They walk down
the shelf and give every album a point score.

Each song can earn points five ways:

1. **Genre.** 2 points if it is exactly the genre you asked for. 1 point if it is
   close — "indie pop" earns half credit for someone who asked for "pop".
2. **Mood.** 1.5 points if the mood matches.
3. **Energy.** Up to 1.5 points, based on how *close* the song's energy is to
   your target. This is the important bit: closer is better, in *both*
   directions. If you ask for calm music, a very loud song loses points — it does
   not win for being "more" energetic.
4. **Valence.** Up to 0.5 points, same closeness idea. Valence means how upbeat
   or happy the song sounds. It separates "loud and angry" from "loud and
   cheerful", which energy alone cannot do.
5. **Sound.** Up to 1 point. If you like acoustic music, acoustic songs earn
   points. If you don't, produced songs earn them instead. Same number, read
   backwards.

Add it all up. The best possible score is 6.5. Then sort every song by its score,
highest first, and show the top few.

**What I changed from the starter:** The starter just returned the first few
songs in the file, ignoring the user completely. I wrote all the scoring, added
the closeness rule for numbers, added a partial-credit rule for similar genres,
and made every song carry a list of reasons so the output explains itself. I also
added a valence preference to the user profile, which the starter did not have.

---

## 4. Data

**Size:** 20 songs in `data/songs.csv`.

**Started with:** 10 songs, provided with the assignment.

**I added 10 more.** I added 9 new genres (hip hop, folk, metal, classical,
house, bluegrass, r&b, afrobeats, country) and 5 new moods (confident,
melancholy, euphoric, romantic, nostalgic).

I did not add them randomly. In the original 10 songs, energy and acousticness
moved together almost perfectly — quiet songs were always acoustic and loud songs
never were. That meant acousticness told you nothing new. So I deliberately added
a loud acoustic song (bluegrass) and a quiet electronic one (ambient) to break
that pattern. It worked: the correlation went from −0.99 to −0.72.

**Each song has:** genre, mood, energy, tempo, valence, danceability,
acousticness, plus title and artist.

**What I use for scoring:** genre, mood, energy, valence, acousticness.

**What I deliberately ignore:** tempo and danceability. In this catalog they are
almost the same information as energy, so scoring them would count one thing
three times.

**What is missing from the data:**

- Lyrics and language.
- Any sense of whether a song is popular, old, or new.
- Any record of what anyone has actually listened to.
- Non-Western musical traditions are barely represented.
- Only one song per genre for 13 of the 16 genres. This turned out to matter a
  lot — see section 6.

---

## 5. Strengths

**It works well for users whose taste is common in the catalog.** The pop
listener and the lofi listener both get sensible lists all the way down, because
those genres have several songs each.

**The closeness rule works.** I tested a listener wanting calm music and a
listener wanting loud music. Neither was ever shown the other's songs. A simpler
system that rewarded "more energy" would have handed the loudest song to
everybody.

**Every recommendation explains itself.** The output shows exactly where each
point came from. Real recommenders mostly cannot do this — their reasoning is
buried in a model nobody can read. Mine can be checked by hand with a
calculator, which is how I caught the mood problem in section 6.

**A brand-new song works immediately.** Add a row to the CSV and it can be
recommended right away. Real systems struggle badly with this — a song nobody has
played has no data, so it never gets shown, so nobody plays it.

**It cannot chase popularity.** There are no play counts, so it cannot pile
everyone onto the same few hit songs. Real recommenders are widely criticised for
doing exactly that.

---

## 6. Limitations and Bias

**The main weakness I found: the system rewards people whose taste is common in
the catalog and quietly fails people whose taste is rare.** My catalog has 20
songs spread across 16 genres, so 13 genres contain only a single song. When I
tested a "sad folk" listener, the one folk song scored 6.41 and the next result
dropped to 2.71 — a cliff of 3.74 points. By contrast, the pop listener's scores
declined gently from 6.22 to 4.72, because pop and indie pop actually have
neighbours in the catalog. Both users are shown a confident, nicely formatted
list of five songs, but only one of those lists is meaningful: past the single
exact match, the folk listener is really just being shown "any quiet song."
Nothing in the output warns them of this, which I think is the more serious
problem — the system is equally confident whether it has a real answer or not.

**Mood turned out to be nearly decorative.** I removed the mood check entirely
and only 1 of 15 top-3 slots changed across five profiles. For the pop listener,
removing mood made *Sunrise City* and *Gym Hero* tie exactly at 4.72, with the
order decided by song ID. So a feature I advertised as one of my two headline
categorical signals is, in practice, mostly a tiebreaker. This is a bias in the
sense that the system claims to care about how a user wants to *feel* and then
largely ignores it.

**The system also can't be told what someone dislikes.** The profile only holds
positive preferences, so a listener who loves quiet music but hates country has
no way to express that, and the country song will keep appearing whenever its
energy happens to be close.

**Other features it ignores entirely:** lyrics and language, artist familiarity,
release date, popularity, and any notion of listening history. Two songs with
identical numbers are perfectly interchangeable to this system even if a human
would never confuse them.

**One bias it does *not* have, worth noting:** with no play counts in the data,
it cannot favour already-popular songs — a failure mode that real recommenders
are widely criticised for. That is a genuine, if accidental, advantage of the
content-based approach here.

---

## 7. Evaluation

### Profiles tested

| Profile | Genre / Mood | Target energy | Acoustic? |
|---|---|---|---|
| Pop Fan | pop / happy | 0.80 | no |
| Lofi Student | lofi / chill | 0.35 | yes |
| Metalhead | metal / intense | 0.95 | no |
| Sad Folk | folk / melancholy | 0.30 | yes |
| Jazz Chill | jazz / relaxed | 0.35 | yes |

### What I looked for

Three things: whether each profile's top result was something I would actually
pick by hand, whether different profiles got genuinely *different* lists, and
whether one song kept winning regardless of who was asking.

### Results, and comparisons between profiles

Every profile's #1 was its exact genre-and-mood match, and no two profiles shared
a top result — so the system does discriminate between users at the top of the
list. The interesting differences are further down.

**Pop Fan vs. Metalhead.** These are near-opposites and their lists reflect it:
the pop listener gets *Sunrise City* (bright, 0.82 energy) while the metalhead
gets *Ironclad* (0.97 energy, valence 0.21). But **both** end up with *Gym Hero*
in their top 3, for completely different reasons — for the pop fan it matches on
genre, for the metalhead it matches on mood and energy. That makes sense: it is a
pop song with metal's intensity, so it sits between them.

**Lofi Student vs. Metalhead.** The clearest split. Nothing overlaps at all, and
the energy targets (0.35 vs 0.95) push them to opposite ends of the catalog. The
lofi list is calm and acoustic-leaning; the metal list is loud and produced. This
is the comparison that convinced me the energy-closeness rule works — the
metalhead is never shown a quiet song and the student is never shown a loud one.

**Lofi Student vs. Jazz Chill.** Both want calm, acoustic, low-energy music, and
they *do* overlap (*Library Rain* appears for both) — correctly, since it fits
both descriptions. But their #1s differ, so genre still does the work of telling
two similar users apart. This is the pair I would point to as evidence the
weighting is balanced: similar users get similar-but-not-identical lists.

**Sad Folk vs. everyone.** The odd one out. Its #1 scores as high as anyone's
(6.41) but its #2 scores 2.71, the steepest fall of any profile. Its results
after the first are chosen almost entirely by energy, so it drifts into ambient
and classical — not wrong, but not really *folk* either.

### What surprised me

**1. My weights barely matter.** I ran the suggested experiment — halving genre
(2.0 → 1.0) while doubling energy (1.5 → 3.0) — expecting the lists to be
reshuffled. Only **2 of 15** top-3 slots changed. Three of five profiles were
completely unaffected. The reason is that the top result is almost always the one
song matching both genre and mood, and it wins by such a margin that reweighting
cannot dislodge it. I had assumed my weight choices were the most important
decision in the project; the experiment showed the *dataset* matters far more.

**2. Removing mood entirely changed almost nothing** — 1 of 15 slots. Described
in Limitations above. This was the most useful result, because it contradicted
what I wrote in my plan.

**3. The one change that did help.** In experiment A, the pop fan's third slot
changed from *Gym Hero* (pop but intense) to *Ocean Bus Route* (happy afrobeats).
I think that is genuinely **more accurate**, not merely different — someone
asking for happy pop probably wants the upbeat song over the gym track. So
lowering the genre weight improved one specific result while leaving everything
else alone. That is a small effect, but it is a real one, and it points the same
direction as my predicted "genre over-prioritization" bias.

### Explaining "Gym Hero" without the code

Imagine describing your taste to a shop assistant with three requests: *pop*,
*happy*, and *upbeat but not exhausting*. The assistant gives each song a point
score — 2 points for being pop, 1.5 for being happy, and up to 1.5 more for
having about the right energy level.

*Gym Hero* is pop, and it is energetic, so it collects points for two of your
three requests. It just isn't happy — it's intense. Meanwhile a genuinely happy
afrobeats song collects points for mood and energy but scores zero on genre.
Because being pop is worth more than being happy, the gym track edges ahead.

The system is not confused. It is doing exactly what I told it to do — I told it
genre matters more than mood, and this is what that instruction looks like in
practice. Seeing it play out is what made me realise the choice was more
debatable than I thought when I made it.

### Tests written

10 automated tests in `tests/test_recommender.py`, including checks that a
low-energy listener is *not* handed the highest-energy song, that an exact genre
match outranks a partial one which outranks none, and that asking for
recommendations does not reorder the caller's catalog.

---

## 8. Future Work

**1. Warn the user when there is no good answer.** This is the fix I would do
first. The system currently returns five songs with total confidence even when
only one is a real match. I would set a minimum score, and say "only 1 good match
found" instead of padding the list with near-random filler. The information is
already there — the score cliff shows it clearly — the system just throws it
away.

**2. Let people say what they dislike, and like more than one thing.** Right now
you get exactly one genre and one mood. Real taste is a mix: mostly indie, some
jazz, definitely no metal. I would let the profile hold a few weighted genres and
a list of things to avoid. This would also fix the problem where someone gets
recommended a genre they hate just because its energy happened to match.

**3. Stop one artist or genre filling the whole list.** I would add a rule at the
ranking stage capping how many songs from the same artist or genre can appear in
the top 5. Real recommenders do this, and it is a list-level rule, not a scoring
rule — which is exactly why I kept scoring and ranking as separate steps.

**Also worth doing:** make mood earn its place or remove it. Right now it barely
affects anything, so I would either weight it properly or drop it and be honest
that the system is really matching on genre and energy.

---

## 9. Personal Reflection

The thing that stuck with me is that **the data mattered more than the algorithm
did.** I spent most of my planning time arguing with myself about weights —
should genre be worth 2 points or 1.5, is mood worth more than energy. Then I
tested it, halved the genre weight, doubled the energy weight, and almost nothing
moved. Two results out of fifteen. Later I deleted the mood check entirely and
one result changed. All that careful reasoning was aimed at the part of the
system that turned out to matter least.

What actually controlled the output was the shape of the catalog. Because most of
my genres only have one song in them, the top result was decided before the
weights ever got involved. I think that is the real lesson: a recommender is
mostly a reflection of the data it was given, and tuning it can only rearrange
what is already there.

The other thing I did not expect was how uneven the failure is. The system does
not break for everyone at once. It works fine for the pop listener and falls
apart for the folk listener, and it looks *identical* in both cases — same clean
formatting, same five results, same confident tone. Nothing in the output says
"I'm guessing now." That changed how I think about music apps. When a playlist
feels slightly off, I now assume the system is padding, because it would rather
show me something than admit it has run out of good answers.

I also came away thinking explainability is underrated. My whole system can be
checked with a calculator, and that is how I found out mood was doing nothing.
Real recommenders cannot be audited that way, which means a flaw like mine could
sit in one for years without anyone noticing.

<!-- TODO: rewrite this section in your own voice before submitting -->
