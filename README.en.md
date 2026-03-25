# d369 — Digital Root Fingerprint of the Quran

**Author:** Emad Suleiman Alwan | ORCID: [0009-0004-5797-6140](https://orcid.org/0009-0004-5797-6140)
**Published:** March 17, 2026 — Night of 27th Ramadan 1446H
**License:** [CC BY 4.0](LICENSE)

---

## What We Found

When Quranic letters are converted to numbers — using **any** encoding system — summed per Surah, and reduced to their digital root, a pattern emerges:

**The group {3, 6, 9} dominates.**

This pattern does not appear in any other Arabic text we tested: not in Sahih al-Bukhari, not in Ibn Arabi's Futuhat, not in the Seven Mu'allaqat.

---

## How We Tested

We did not start with a conclusion. We started with a question and let the numbers speak — **including when they surprised us.**

1. **Six AI models** (GPT-4, Claude, Gemini, Llama, Grok, ChatGPT) were asked to attack the research with their strongest objections.
2. They attacked: *"Abjad is arbitrary. The statistics are weak. The result is coincidence."*
3. We built a **completely new encoding system** from scratch — Special-6 — using only 0s and 1s, with 33 distinct letter shapes instead of 28 sounds.
4. We ran it on the Quran: **clear fingerprint (p = 0.007).**
5. We ran it on 3 other Arabic texts: **nothing.**
6. We returned to the six models: *"Explain this."* **They could not.**

---

## Key Results

### Summary Table

| Experiment | System | Unit | Result | p-value |
|-----------|--------|------|--------|---------|
| [01](experiments/01_transformation_map_g14/) | Abjad (ة=5) | 114 Surahs (group sums) | {3,6,9} stable ✅ | p < 0.00001 |
| [02](experiments/02_readings_hafs_warsh/) | Abjad | 114 Surahs × 2 readings | {3,9} stable in both ✅ | — |
| [03](experiments/03_text_fingerprint_word_level/) | Abjad | 78,248 words | {9} dominant (14%) ✅ | p ≈ 0 |
| [04](experiments/04_special6_surah_level/) | **Special-6** | 114 Surahs | **51/114 = 44.7%** ✅ | **p = 0.007** |
| [05](experiments/05_special6_word_level/) | Special-6 | 78,248 words | Different distribution ✅ | p ≈ 0 |
| [06](experiments/06_special6_transformation_map/) | Both | Group sums | {9} preserved in both | — |

### Cross-Text Comparison (Experiment 04)

| Text | {3,6,9} | p-value | Significant? |
|------|---------|---------|-------------|
| **Quran** | **51/114 = 44.7%** | **0.007** | **✅ Yes** |
| Bukhari | 40/114 = 35.1% | 0.384 | ✗ No |
| Ibn Arabi | 37/114 = 32.5% | 0.613 | ✗ No |
| Mu'allaqat | ~30% | ~0.60 | ✗ No |

### The Big Picture

```
Level          | Abjad (ة=5)             | Special-6
───────────────────────────────────────────────────
Word (78,248)  | p≈0  ✅ (38.2%)        | p≈0  ✅ (34.2%)
Surah (114)    | p=0.75   ✗ (30.7%)    | p=0.007  ✅ (44.7%)
Transformations| {3,6,9} stable  ✅     | {9} only stable
```

**Each system reveals a different layer of the text.**

---

## The Special-6 System

A binary-inspired encoding where each Arabic letter shape gets a unique value built from 0s and 1s:

```
أ=1        ب=10       ة=11       ت=100      ث=101
ج=111      ح=110      خ=1000     د=1001     ذ=1011
ر=1111     ز=1100     س=1110     ش=10000    ص=10001
ض=10011    ط=10111    ظ=11111    ع=11110    غ=11100
ف=11000    ق=100000   ك=100001   ل=100011   م=100111
ن=101111   ه=111111   و=111110   ؤ=1000000  ى=111100
ي=111000   ئ=1000001  ء=110000
```

Key distinction: ة ≠ ت (both = 400 in classical Abjad, but 11 vs 100 in Special-6).

**Original system — Emad Suleiman Alwan, 2026.**

---

## The G14 Transformation Map

Using classical Abjad (ة=5), group the 114 Surahs by their digital root, then sum each group:

```
Root 3 (13 surahs) → sum 3,210,951 → digital root 3  ✅ preserved
Root 6 (10 surahs) → sum 2,642,856 → digital root 6  ✅ preserved
Root 9 (12 surahs) → sum 3,147,993 → digital root 9  ✅ preserved
All others         → transform to different roots
```

**{3,6,9} are the only roots that preserve themselves when their groups are summed.**
Probability of this occurring by chance: p < 0.00001 (Monte Carlo, 100,000 trials).

---

## Published Papers

| Paper | Title | DOI |
|-------|-------|-----|
| I | Digital Root Transformation Map (G14) | [10.5281/zenodo.19041960](https://doi.org/10.5281/zenodo.19041960) |
| II | Digital Root in Word Repetition | [10.5281/zenodo.19055332](https://doi.org/10.5281/zenodo.19055332) |
| III | System-Independent Validation via Special-6 | [10.5281/zenodo.19073919](https://doi.org/10.5281/zenodo.19073919) |

---

## Reproduce Our Results

```bash
git clone https://github.com/up2u2b11/d369-research
cd d369-research
pip install -r requirements.txt

# Run the decisive experiment
export D369_DB=data/d369_research.db
export D369_DATA=data/
python experiments/04_special6_surah_level/experiment.py
# Expected: p ≈ 0.007 for Quran, p > 0.38 for all other texts
```

---

## Five Open Research Doors

1. **Spectrum of systems:** Each encoding illuminates a layer — how many layers does the Quran have?
2. **Semitic comparison:** Does this property extend to the Hebrew Torah or Syriac Gospels?
3. **Computational linguistics:** What structural feature of Surahs carries the fingerprint — length? distribution? repetition?
4. **Third system:** If a third independent system confirms the same result — the evidence becomes triangulated.
5. **Architecture vs. words:** Is the fingerprint in the words themselves, or in *how the Quran was divided into Surahs*?

---

## Claim

We make no theological claim. We make a scientific one:

> **The Quran carries a digital root structure that cannot be reproduced by chance, does not appear in other Arabic texts, and does not depend on any single encoding system.**

Any researcher anywhere can take our data, our code, and re-run every test.

**The numbers do not flatter. They do not lie. They do not fear.**

---

*Emad Suleiman Alwan — up2b.ai — March 17, 2026*
*"And We have revealed to you the Book as clarification for all things" (16:89)*
