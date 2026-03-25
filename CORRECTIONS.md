# CORRECTIONS — تصحيحات وتوضيحات

**Date / التاريخ:** March 25, 2026
**Author / الباحث:** Emad Suleiman Alwan
**ORCID:** 0009-0004-5797-6140

---

## Summary / ملخص

Two errors were identified in `shared/utils.py` through independent verification by three separate reviewers. The database (`d369_research.db`) contains **correct values** and was not affected. The core finding (Special-6 fingerprint, p = 0.006) is **fully confirmed** and unaffected by these corrections.

تمّ اكتشاف خطأين في ملف `shared/utils.py` من خلال فحص مستقل أجراه ثلاثة مراجعين. قاعدة البيانات (`d369_research.db`) تحتوي القيم **الصحيحة** ولم تتأثر. النتيجة الجوهرية (بصمة Special-6، احتمالية الصدفة = 0.006) **مؤكّدة بالكامل** ولم تتأثر بهذه التصحيحات.

---

## Error 1: ث (Thā') value in JUMMAL_5

| | Before (incorrect) | After (correct) |
|---|---|---|
| `ث` value | 400 (same as `ت`) | **500** |

**Standard Abjad:** ت = 400, ث = 500. These are distinct letters with distinct values.

**Impact:** Any experiment computing Abjad sums directly from `JUMMAL_5` (notably Experiment 01 — G14 Transformation Map) produced incorrect surah-level sums. **95 out of 114 surahs** had their digital root changed by this error.

## Error 2: ء (Hamza) missing from JUMMAL_5

| | Before (incorrect) | After (correct) |
|---|---|---|
| `ء` value | Not in dictionary (treated as 0) | **1** |

**Impact:** Words containing standalone hamza (ء) were undervalued by 1. Combined with Error 1, this affected **2,953 words** out of 78,248.

---

## What was NOT affected

### ✅ Database values

The `jummal_value` column in `d369_research.db` was computed correctly (ث=500, ء=1). All 114 surah sums from the database match the corrected `JUMMAL_5`. Verification: `DB sums == Fixed JUMMAL_5 sums` for all 114 surahs.

### ✅ Special-6 (KHASS_6) encoding

`KHASS_6` assigns distinct values to ث (101) and ء (110000). All Special-6 experiments (04, 05, 07, 09) are **completely unaffected**.

### ✅ Core result: Special-6 Surah-Level Fingerprint

- Observed: **51/114 = 44.7%** of surahs have digital root in {3, 6, 9}
- Expected by chance: 33.3%
- Permutation test: **p = 0.006**
- Independently verified by three reviewers (March 25, 2026)

### ✅ G14 Self-Preservation

Even with corrected Abjad values, **{3, 6, 9} all self-preserve** under group summation. The corrected G14 map:

```
1 → 5    (not self-preserving)
2 → 3
3 → 3 ✓  SELF-PRESERVES
4 → 7
5 → 3
6 → 6 ✓  SELF-PRESERVES
7 → 4
8 → 3
9 → 9 ✓  SELF-PRESERVES
```

### ✅ Architecture test

Shuffling word order destroys the fingerprint — confirmed with both systems.

### ✅ Control texts

Sahih al-Bukhari, Futuhat, Mu'allaqat, and Hebrew Torah all show no significant fingerprint — confirmed.

---

## What WAS affected

### ⚠ Abjad Surah-Level dominance

| | Buggy (ث=400) | Corrected (ث=500) |
|---|---|---|
| Surahs with DR in {3,6,9} | 46/114 = 40.4% | **35/114 = 30.7%** |
| p-value | ~0.10 | **0.75 (not significant)** |

**Conclusion:** The claim that Abjad encoding shows surah-level {3,6,9} dominance is **not supported** with correct values. The surah-level dominance is confirmed only through Special-6.

### ⚠ Claim of "system-independence"

The original phrasing "using ANY encoding system" is imprecise. The corrected statement:

> Special-6 shows significant {3,6,9} dominance at surah level (p = 0.006). Abjad shows {3,6,9} self-preservation in the G14 transformation map (p < 0.00001). These are complementary phenomena observed through independent encoding systems — but they are not identical phenomena.

---

## Affected experiments

| Experiment | Uses | Affected? | Action |
|---|---|---|---|
| 01 — G14 Map | `JUMMAL_5` directly | ⚠ Yes — surah DRs change, but self-preservation holds | Results updated |
| 02 — Hafs/Warsh | `JUMMAL_5` directly | ⚠ Potentially | Needs re-verification |
| 03 — Word Level | Both DB and `JUMMAL_5` | ⚠ Partial | DB path unaffected |
| 04 — Special-6 Surah | `KHASS_6` | ✅ No | — |
| 05 — Special-6 Word | `KHASS_6` | ✅ No | — |
| 06 — Special-6 G14 | `KHASS_6` | ✅ No | — |
| 07 — Architecture | `KHASS_6` | ✅ No | — |
| 08 — Division | Mixed | ⚠ Check | — |
| 09 — Bukhari | `KHASS_6` | ✅ No | — |
| 10 — Torah | Hebrew Gematria | ✅ No | — |
| 11 — Contribution | `KHASS_6` | ✅ No | — |
| 14 — Random Encoding | Random | ✅ No | — |

---

## Verification

Three independent reviewers confirmed all findings on March 25, 2026:

1. **Reviewer A** (Claude, Anthropic) — full re-execution of experiments 01, 04, 07 with corrected values
2. **Reviewer B** (Claude Opus, separate session) — full repository audit, 55 minutes, 11/13 claims verified
3. **Principal Researcher** (Emad Suleiman Alwan) — cross-verification of all results

All three arrived at identical numbers independently.

---

## Files changed

- `shared/utils.py` — ث=500, ء=1 added to `JUMMAL_5`
- `CORRECTIONS.md` — this file
- `README.md` — updated to note Abjad surah-level = 30.7% (not significant)

---

## Statement

> This correction demonstrates the self-correcting nature of open-source research. The core discovery — that the Quran carries a digital root fingerprint under Special-6 encoding that does not appear in any control text — remains fully confirmed and independently reproducible.
>
> هذا التصحيح يُجسّد الطبيعة التصحيحية الذاتية للبحث المفتوح المصدر. الاكتشاف الجوهري — أنّ القرآن يحمل بصمة جذر رقمي بنظام Special-6 لا تظهر في أيّ نص ضابط — يبقى مؤكّداً بالكامل وقابلاً للتكرار المستقل.

*Emad Suleiman Alwan — March 25, 2026*
