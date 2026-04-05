# Section: Negative Controls — What the Fingerprint Is NOT
## (To be integrated into Paper IV: Division Architecture, after Gate Seven)

**Experiments 21–23 | April 2026**
**Intellectual property: Emad Suleiman Alwan — up2b.ai**

---

## Motivation

A reviewer confronting the {3, 6, 9} fingerprint will naturally ask:
*"Can the pattern be explained by a known linguistic property — semantic clustering,
syntactic structure, or positional regularity?"*

We deploy three experiments using self-attention mechanisms from transformer models
(AraBERT v2, 135M parameters) to test — and reject — each of these hypotheses.

---

## Experiment 21 — Semantic Clustering Test

**Question:** Do words whose Abjad digit root falls in {3, 6, 9} cluster together
in a modern language model's semantic space?

**Method:**
- 14,868 unique Quranic words embedded via AraBERT (768 dimensions)
- Dimensionality reduction: PCA(50) → UMAP(2D)
- Cluster separation: Silhouette Score, Davies-Bouldin Index
- Permutation test: 500 label shuffles on centroid distance

**Results:**

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Silhouette Score | 0.001 | No clustering (0 = random) |
| Davies-Bouldin Index | 140.8 | Very poor separation |
| Centroid Distance | 0.068 | Negligible |
| **p-value** | **0.874** | **Not significant** |

**Verdict:** D369 words are uniformly distributed across semantic space.
The fingerprint is **not semantic** — it cannot be reduced to a set of
thematically related words.

---

## Experiment 22 — Attention Flow Analysis

**Question:** Do AraBERT's 144 attention heads (12 layers x 12 heads)
preferentially connect D369 words to each other?

**Method:**
- 2,000 Quranic ayahs processed through AraBERT with attention extraction
- For each ayah: D369->D369 attention flow ratio computed per head
- Same analysis on Bukhari control (1,000 pseudo-ayahs of ~12 words)
- Effect size comparison: Cohen's d between Quran and Bukhari

**Results:**

| Metric | Quran | Bukhari |
|--------|-------|---------|
| D369 fraction | 38.9% | 33.3% |
| Expected D369->D369 flow | 39.2% | 33.3% |
| Observed D369->D369 flow | 22.1% | 19.6% |
| **Deviation from expected** | **-43.2%** | **-41.2%** |
| Significant heads (Bonferroni) | 141/144 | 144/144 |

| Effect Size | Value | Magnitude |
|-------------|-------|-----------|
| **Cohen's d** | **0.33** | **Small** |

**Verdict:** D369 words preferentially attend to non-D369 words in **both**
the Quran and Bukhari — this is a **general Arabic language property**, not
a Quran-specific phenomenon. The Quran shows a slightly stronger deviation
(d = 0.33), but this difference is too small to support a uniqueness claim
on this dimension.

**Honest assessment:** The attention-flow asymmetry reveals that high-frequency
function words (which tend to carry D369 digit roots: "من" = 9, "في" = 9,
"الله" = 3, "إن" = 6) serve as syntactic bridges in Arabic text generally.
This is interesting linguistically but does not explain the fingerprint's
uniqueness.

---

## Experiment 23 — Positional Pattern Test

**Question:** Can a self-attention classifier learn to predict whether a surah's
total digit root falls in {3, 6, 9} from the sequence of word-level digit roots?

**Method:**
- Each of 114 surahs represented as a sequence of digit roots (integers 1-9)
- Lightweight PyTorch model: Embedding(16d) -> Sinusoidal PE -> Self-Attention(2 heads) -> Classifier
- 10-fold cross-validation
- Attention template comparison: D369 surahs vs. non-D369 surahs

**Results:**

| Encoding | CV Accuracy | Baseline (majority) | Above baseline? |
|----------|-------------|---------------------|-----------------|
| Special-6 (K6) | 53.5% | 55.3% | **No** |
| Abjad | 67.5% | 69.3% | **No** |

| Attention Pattern | D369 Surahs | Non-D369 Surahs |
|-------------------|-------------|-----------------|
| Self-attention (diagonal) | 0.0107 | 0.0092 |

**Verdict:** The model fails to learn D369 membership from digit root sequences
alone. The fingerprint is **not positionally learnable** — it cannot be reduced
to a pattern in which positions within a surah carry D369 values.

---

## Synthesis — Three Negatives, One Positive

| Hypothesis | Experiment | Result | p / d |
|------------|-----------|--------|-------|
| Fingerprint is semantic | Exp. 21 | **Rejected** | p = 0.874 |
| Fingerprint is syntactic | Exp. 22 | **Rejected** | d = 0.33 (not unique) |
| Fingerprint is positional | Exp. 23 | **Rejected** | Below baseline |
| Fingerprint is numerical/holistic | Exps. 1-7 | **Confirmed** | p = 0.007 (K6) |

These three negative results, combined with the positive results from
Experiments 1-7, support the following conclusion:

> **The {3, 6, 9} fingerprint is a numerical phenomenon that emerges from the
> holistic composition of the Quranic text. It cannot be reduced to semantic
> content, syntactic structure, or positional regularity. It requires the
> specific words in their specific order within the specific 114-surah
> architecture — a property that no control text exhibits.**

---

## Technical Notes

- **Model:** AraBERT v2 (aubmindlab/bert-base-arabertv2), 135M parameters, CPU inference
- **Tokenization:** WordPiece with subword-to-word aggregation for attention analysis
- **Statistical tests:** Permutation test (Exp. 21), bootstrap z-test with Bonferroni correction (Exp. 22), cross-validation (Exp. 23)
- **Reproducibility:** All code in `experiments/21_embedding_geometry/`, `experiments/22_attention_fingerprint/`, `experiments/23_custom_attention_d369/`
- **Database:** Same d369_research.db (78,248 words) used in all previous experiments
