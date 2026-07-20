# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

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

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
