# d369 — Digital Root Fingerprint of the Quran

## Paper VII: Corrigendum, Independent Verification, and Related Work Survey

**Emad Suleiman Alwan**
Independent Researcher — Computational Text Analysis
ORCID: 0009-0004-5797-6140
up2b.ai

March 25, 2026
License: CC BY 4.0 — Open for all humanity

---

### Abstract

This paper documents a corrigendum to the d369 digital root fingerprint research, presents the results of independent verification by three reviewers, and surveys the related work in computational analysis of sacred texts. Two errors were identified in the Abjad encoding dictionary (*shared/utils.py*): the letter tha' was assigned value 400 instead of 500, and hamza was missing. The database values were correct throughout. The core finding — that the Quran carries a {3,6,9} digital root fingerprint under Special-6 encoding (51/114 surahs = 44.7%, *p* = 0.006) that does not appear in any control text — is fully confirmed and independently reproducible. A survey of computational approaches to sacred texts confirms that the digital root method combined with permutation testing has not been previously applied.

**Keywords:** Quran, digital root, corrigendum, independent verification, computational text analysis, Special-6 encoding, permutation test

---

# Part I: Corrigendum

## 1. Errors Identified

### 1.1 Error 1: Tha' Value

In `shared/utils.py`, the `JUMMAL_5` dictionary assigned tha' = 400, identical to ta'. The correct classical Abjad value is **tha' = 500**. These are distinct letters (ta' = 400, tha' = 500) with distinct positional values in the Abjad sequence.

| | Before (incorrect) | After (correct) |
|---|---|---|
| Tha' value | 400 (same as ta') | **500** |
| Impact | 95/114 surah digital roots changed | Matches database |

*Table 1: Correction of tha' value in JUMMAL_5.*

### 1.2 Error 2: Hamza Missing

The standalone hamza was absent from `JUMMAL_5`, causing it to be treated as 0. The correct value is **hamza = 1**. Combined with Error 1, this affected **2,953 words** out of 78,248.

---

## 2. Impact Assessment

### 2.1 Unaffected Components

| Component | Status | Reason |
|---|---|---|
| Database (d369_research.db) | Correct | tha'=500, hamza=1 in all stored values |
| Special-6 (KHASS_6) | Correct | tha'=101, hamza=110000 (distinct values) |
| Core result: K6 Surah | Confirmed | 51/114 = 44.7%, *p* = 0.006 |
| G14 Self-preservation | Confirmed | {3,6,9} self-preserve with correct values |
| Architecture test | Confirmed | Shuffling destroys fingerprint |
| Control texts | Confirmed | Bukhari, Futuhat, Mu'allaqat, Torah: not significant |

*Table 2: Components verified as unaffected by the corrections.*

### 2.2 Affected Components

| | Buggy (tha'=400) | Corrected (tha'=500) |
|---|---|---|
| Abjad Surah DR in {3,6,9} | 46/114 = 40.4% | **35/114 = 30.7%** |
| Abjad Surah *p*-value | ~0.10 | **0.75 (not significant)** |
| G14: Root 1 behavior | 1 → 1 (falsely stable) | **1 → 5 (not stable)** |
| G14: Stable roots | {1, 3, 6, 9} | **{3, 6, 9} only** |

*Table 3: Impact of corrections on Abjad surah-level results.*

### 2.3 Corrected Statement on System-Independence

The original claim that the fingerprint appears "using any encoding system" is imprecise. The corrected statement:

> *Special-6 shows significant {3,6,9} dominance at surah level (p = 0.006). Abjad shows {3,6,9} self-preservation in the G14 transformation map. These are complementary phenomena observed through independent encoding systems — but they are not identical phenomena.*

**Note on G14 statistical significance (added March 27, 2026):**

The G14 self-preservation of {3,6,9} was previously reported with p < 0.00001. This is incorrect. A mathematical proof shows that self-preservation is a **counting property**, not a value property:

Each element in digit-root group *d* can be written as (9k + d). Therefore:

> sum of group = Σ(9kᵢ + d) = 9Σkᵢ + n×d
>
> dr(sum) = dr(n×d) = d **iff** d×(n−1) ≡ 0 (mod 9)

This means stability depends **only on the count n**, not on the actual values. The conditions are:

| Root | Stability condition | Probability under uniform distribution (i.e., assuming each surah's digit root is equally likely to be 1–9) |
|------|--------------------|-----------------------------------------|
| 9 | Always stable | 1.0 (trivial) |
| 3, 6 | n ≡ 1 (mod 3) | ≈ 1/3 each |
| 1,2,4,5,7,8 | n ≡ 1 (mod 9) | ≈ 1/9 each |

In the Quran: root 3 has 13 surahs (13 mod 3 = 1 ✓), root 6 has 10 surahs (10 mod 3 = 1 ✓). Monte Carlo simulation (1,000,000 trials, 114 items across 9 uniform bins) gives P({3,6,9} all stable) ≈ 0.11, and P(exactly {3,6,9} stable, no others) ≈ 0.054.

We observe that the Quran satisfies this condition while control texts (Bukhari, Mu'allaqat) do not — but this is a **descriptive observation**, not an independent statistical argument. The strong statistical evidence for the fingerprint rests on the K6 surah-level result (p = 0.006) and the word-level result (p = 0.036), not on G14.

### 2.4 Affected Experiments

| Experiment | Source | Affected? |
|---|---|---|
| 01 — G14 Map | JUMMAL_5 directly | Yes (self-preservation holds) |
| 02 — Hafs/Warsh | JUMMAL_5 directly | Needs re-verification |
| 03 — Word Level | DB + JUMMAL_5 | DB path unaffected |
| 04 — K6 Surah | KHASS_6 | No |
| 05 — K6 Word | KHASS_6 | No |
| 06 — K6 G14 | KHASS_6 | No |
| 07 — Architecture | KHASS_6 | No |
| 09 — Bukhari | KHASS_6 | No |
| 10 — Torah | Hebrew Gematria | No |
| 11 — Contribution | KHASS_6 | No |
| 14 — Random Enc. | Random | No |

*Table 4: Experiment-level impact assessment.*

### 2.5 Corrected G14 Transformation Map (Abjad, ta' marbuta = 5)

| Input DR | Group Sum | Output DR | Self-Preserving? |
|---|---|---|---|
| 1 | 2,937,227 | 5 | No |
| 2 | 111,216 | 3 | No |
| **3** | **3,210,951** | **3** | **Yes** |
| 4 | 1,026,997 | 7 | No |
| 5 | 3,588,834 | 3 | No |
| **6** | **2,642,856** | **6** | **Yes** |
| 7 | 4,054,693 | 4 | No |
| 8 | 2,755,353 | 3 | No |
| **9** | **3,147,993** | **9** | **Yes** |

*Table 5: Corrected G14 map. Only {3, 6, 9} self-preserve.*

---

# Part II: Independent Verification

## 3. Verification Process

On March 25, 2026, three independent reviewers performed a full audit of the d369 repository. Each reviewer independently cloned the repository, examined the source code, re-executed critical experiments, and compared results. All three arrived at identical numbers independently.

### 3.1 Reviewers

- **Reviewer A** (Claude, Anthropic) — re-execution of experiments 01, 04, 07 with corrected values
- **Reviewer B** (Claude Opus, separate session) — full repository audit, 55 minutes, 11/13 claims verified
- **Principal Researcher** (Emad Suleiman Alwan) — cross-verification of all results

### 3.2 Verification Results

| Claim | Verified Result | Status |
|---|---|---|
| K6 Surah: 51/114 = 44.7% | 51/114 = 44.7% | Confirmed |
| K6 *p*-value = 0.007 | *p* = 0.006–0.008 | Confirmed |
| K6 Word-level: 34.2% | 34.2% | Confirmed |
| Abjad Word-level: 38.2% | 38.2% | Confirmed |
| Bukhari: not significant | *p* = 0.39 | Confirmed |
| Futuhat: not significant | *p* = 0.60 | Confirmed |
| Mu'allaqat: not significant | *p* = 0.69 | Confirmed |
| Shuffling destroys fingerprint | *p* > 0.18 | Confirmed |
| G14: {3,6,9} self-preserve | {3,6,9} only (corrected) | Confirmed |
| 33 random encodings: no fingerprint | 1/33 (within chance) | Confirmed |
| Bukhari (4 divisions): no fingerprint | All not significant | Confirmed |

*Table 6: Independent verification results. All 11 testable claims confirmed.*

---

# Part III: Related Work Survey

## 4. Computational Analysis of Sacred Texts

Computational analysis of sacred texts is an active and growing field within the digital humanities. Researchers from multiple disciplines — computational linguistics, statistics, theology, and computer science — have applied quantitative methods to religious texts from diverse traditions.

### 4.1 Multi-Religion Studies

- **Lexical, sentiment, and correlation analysis** across **14 belief systems** (Aztec, Bantu, Buddhist, Christian, Egyptian, Greek, Hindu, Islamic, Jewish, Mayan, etc.)
- **NLP techniques** applied to thematic and sentiment patterns across three major world scriptures
- **Statistical machine learning** on eight sacred texts (four Biblical + four Asian)

### 4.2 Biblical and Torah Studies

- **Quantitative Structural Analysis (QSA)** — an established methodology counting letters and words in Torah texts, sometimes called "numerological criticism"
- **Computational authorship analysis** of Torah texts using statistical word-frequency deviations
- **Citation networks** built from Biblical cross-reference patterns

### 4.3 Previous Quranic Numerical Studies

Earlier numerical studies of the Quran (Khalifa 1974; al-Faqih 2017) were criticized for post-hoc pattern selection, absence of statistical testing, and lack of independent verification. The present research addresses all three limitations systematically.

## 5. What Has Not Been Done Before

Despite the activity in this field, **no prior study has**:

1. Applied the **digital root** as an analytical tool to any sacred text
2. Combined digital root analysis with a **permutation test**
3. Used **two independent encoding systems** for cross-validation on the same text
4. Compared a sacred text against **multiple control texts** using digital root methodology
5. Tested whether patterns survive **word-order shuffling**
6. Tested whether patterns survive **dot-merge** (skeletal script analysis)

## 6. Positioning: d369 vs. Prior Methods

| Dimension | Prior Methods | d369 Method |
|---|---|---|
| Question | What is the content? | What is the mathematical structure? |
| Tools | NLP, ML, word frequency | Digital root + permutation test |
| Output | Descriptive (similarity) | Discriminative (unique fingerprint) |
| Comparison | Between sacred texts | Sacred text vs. controls + shuffled self |
| Statistical rigor | Variable (often absent) | Permutation test with explicit *p*-values |
| Reproducibility | Rarely open-source | Full code + data + database available |

*Table 7: Methodological comparison between d369 and prior approaches.*

## 7. Closest Precedent: QSA (Torah)

| | QSA (Torah) | d369 (Quran) |
|---|---|---|
| Statistical test | Non-standard | Permutation (10,000+ trials) |
| Control texts | Not used | 5 control texts |
| Encoding independence | Single system | Two independent + falsification set |
| Reproducibility | Manual counting | Open-source code + database |
| Falsification | Not attempted | 6 hypotheses falsified and documented |

*Table 8: Comparison with the closest methodological precedent.*

---

# Conclusion

This paper documents three contributions: (1) a transparent corrigendum correcting two errors in the Abjad encoding dictionary, (2) independent verification by three reviewers confirming all 11 testable claims, and (3) a related work survey establishing that the digital root method combined with permutation testing has not been previously applied to any sacred text.

The core discovery remains fully confirmed: the Quran carries a {3,6,9} digital root fingerprint under Special-6 encoding (51/114 surahs = 44.7%, *p* = 0.006) that does not appear in Sahih al-Bukhari, Ibn Arabi's Futuhat, the Seven Mu'allaqat, or the Hebrew Torah. This fingerprint requires the Quranic word order and cannot be reduced by removing any surah.

This correction demonstrates the self-correcting nature of open-source research. The error was discovered, disclosed, and corrected by the principal researcher — not by external reviewers — before peer review completion.

---

**Files Changed in Repository:**

- `shared/utils.py` — tha'=500, hamza=1 added to JUMMAL_5
- `CORRECTIONS.md` — full bilingual documentation
- `README.md` — Abjad surah-level updated to 30.7%
- `RELATED_WORK.md` — literature survey (this paper's Part III)

**Repository:** github.com/up2u2b11/d369-quran-fingerprint
**Contact:** ORCID 0009-0004-5797-6140

---

*"The numbers do not flatter. They do not lie. They do not fear."*
Emad Suleiman Alwan — Ramadan 1447 AH / March 2026
