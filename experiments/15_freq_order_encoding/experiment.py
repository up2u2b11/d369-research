#!/usr/bin/env python3
"""
Experiment 15 — Frequency Order Encoding (System 3)
====================================================
A THIRD independent encoding system based on letter frequency rank.

Principle: Most frequent letter = 1, next = 2, ... least = 6000
Values follow the Abjad scale pattern (1-9, 10-90, 100-900, 1000-6000)
but assigned by FREQUENCY rank, not alphabetical order.

This is structurally independent from both Abjad (historical order)
and Special-6 (visual shape). If the fingerprint appears here too —
three independent systems confirm the same phenomenon.

Key property: 11/33 letters (33.3%) have DR in {3,6,9} — EXACTLY
at chance level. No letter-level bias. Any Surah-level result is pure.

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sqlite3
import random
from collections import defaultdict

random.seed(42)

# ═══════════════════════════════════════════════════════
# FREQUENCY ORDER ENCODING — System 3
# ═══════════════════════════════════════════════════════

FREQ_ORDER = {
    "ا": 1,    "أ": 1,    "إ": 1,    "آ": 1,    "ٱ": 1,
    "ل": 2,
    "ن": 3,
    "م": 4,
    "و": 5,
    "ي": 6,
    "ه": 7,
    "ر": 8,
    "ب": 9,
    "ت": 10,
    "ك": 20,
    "ع": 30,
    "ف": 40,
    "ق": 50,
    "ى": 60,
    "س": 70,
    "د": 80,
    "ذ": 90,
    "ح": 100,
    "ء": 200,
    "ج": 300,
    "خ": 400,
    "ة": 500,
    "ش": 600,
    "ص": 700,
    "ض": 800,
    "ز": 900,
    "ث": 1000,
    "ظ": 2000,
    "غ": 3000,
    "ئ": 4000,
    "ط": 5000,
    "ؤ": 6000,
}


def digit_root(n):
    if n <= 0:
        return 0
    return 1 + (n - 1) % 9


# ═══════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════

DB_PATH = "/root/d369/d369.db"

def load_surah_sums(db_path, encoding):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT surah_id, text_uthmani FROM words ORDER BY surah_id, word_pos_in_quran")
    rows = c.fetchall()
    conn.close()
    sums = defaultdict(int)
    for sid, text in rows:
        for ch in text:
            sums[sid] += encoding.get(ch, 0)
    return dict(sums)


def load_word_values(db_path, encoding):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT surah_id, text_uthmani FROM words ORDER BY surah_id, word_pos_in_quran")
    rows = c.fetchall()
    conn.close()
    values = []
    sizes = defaultdict(int)
    for sid, text in rows:
        val = sum(encoding.get(ch, 0) for ch in text)
        values.append(val)
        sizes[sid] += 1
    return values, [sizes[s] for s in sorted(sizes.keys())]


# ═══════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════

def count_369(values, sizes):
    count = 0
    idx = 0
    for s in sizes:
        total = sum(values[idx:idx + s])
        if digit_root(total) in (3, 6, 9):
            count += 1
        idx += s
    return count


def permutation_test(values, sizes, observed, trials=10000):
    count = 0
    for _ in range(trials):
        shuffled = values[:]
        random.shuffle(shuffled)
        if count_369(shuffled, sizes) >= observed:
            count += 1
    return count / trials


def build_transformation_map(surah_sums):
    groups = defaultdict(lambda: {"sum": 0, "count": 0})
    for sid, total in sorted(surah_sums.items()):
        dr = digit_root(total)
        groups[dr]["sum"] += total
        groups[dr]["count"] += 1
    result = {}
    for dr in range(1, 10):
        g = groups[dr]
        group_dr = digit_root(g["sum"]) if g["sum"] > 0 else 0
        result[dr] = {
            "count": g["count"],
            "group_sum": g["sum"],
            "group_dr": group_dr,
            "preserves": group_dr == dr and g["count"] > 0,
        }
    return result


# ═══════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("Experiment 15 — Frequency Order Encoding (System 3)")
    print("=" * 65, flush=True)

    # --- Battery A: Surah-level {3,6,9} proportion ---
    print("\n--- Battery A: Surah-Level {3,6,9} Proportion ---\n", flush=True)
    surah_sums = load_surah_sums(DB_PATH, FREQ_ORDER)
    n_surahs = len(surah_sums)

    count_in_369 = sum(1 for s, t in surah_sums.items() if digit_root(t) in (3, 6, 9))
    pct = count_in_369 / n_surahs * 100

    print(f"  Surahs in {{3,6,9}}: {count_in_369}/{n_surahs} = {pct:.1f}%")
    print(f"  Expected by chance: 33.3%", flush=True)

    # Permutation test
    values, sizes = load_word_values(DB_PATH, FREQ_ORDER)
    print(f"  Total words: {len(values):,}")
    print(f"  Running permutation test (10,000 trials)...", flush=True)
    p_val = permutation_test(values, sizes, count_in_369, 10000)
    print(f"  p-value: {p_val:.4f}  {'SIGNIFICANT' if p_val < 0.05 else 'not significant'}", flush=True)

    # --- Battery B: Word-level {3,6,9} proportion ---
    print("\n--- Battery B: Word-Level {3,6,9} Proportion ---\n", flush=True)
    word_369 = sum(1 for v in values if digit_root(v) in (3, 6, 9))
    word_pct = word_369 / len(values) * 100
    print(f"  Words in {{3,6,9}}: {word_369}/{len(values):,} = {word_pct:.1f}%", flush=True)

    # --- Battery C: Transformation Map (G14-style) ---
    print("\n--- Battery C: Transformation Map ---\n", flush=True)
    tmap = build_transformation_map(surah_sums)
    preserving = []
    print(f"  {'Root':>4} {'Count':>6} {'Group Sum':>12} {'DR(Sum)':>8} {'Preserves?':>10}")
    print("  " + "-" * 48)
    for dr in range(1, 10):
        t = tmap[dr]
        p = "YES" if t["preserves"] else ""
        if t["preserves"]:
            preserving.append(dr)
        print(f"  {dr:>4} {t['count']:>6} {t['group_sum']:>12,} {t['group_dr']:>8} {p:>10}")

    print(f"\n  Self-preserving roots: {preserving}")
    print(f"  Count: {len(preserving)}")
    print(f"  {{3,6,9}} all preserve? {'YES' if all(d in preserving for d in [3,6,9]) else 'NO'}", flush=True)

    # Monte Carlo for transformation map
    print(f"\n  Running Monte Carlo (100,000 trials)...", flush=True)
    surah_values = list(surah_sums.values())
    n_preserving = len(preserving)
    mc_count = 0
    for _ in range(100000):
        groups = defaultdict(int)
        for val in surah_values:
            g = random.randint(1, 9)
            groups[g] += val
        sp = sum(1 for g in range(1, 10) if groups[g] > 0 and digit_root(groups[g]) == g)
        if sp >= n_preserving:
            mc_count += 1
    mc_p = mc_count / 100000
    print(f"  p-value ({n_preserving}+ self-preserving): {mc_p:.5f}", flush=True)

    # --- Summary ---
    print("\n" + "=" * 65)
    print("SUMMARY — System 3 (Frequency Order)")
    print("=" * 65)
    print(f"""
  Surah-level:  {count_in_369}/114 = {pct:.1f}%  |  p = {p_val:.4f}
  Word-level:   {word_369}/{len(values):,} = {word_pct:.1f}%
  Transform:    {preserving} self-preserve  |  p = {mc_p:.5f}

  Comparison:
  {'System':<20} {'Surah %':>8} {'p-value':>10} {'Self-preserving':>16}
  {'-'*58}
  {'Abjad (historical)':<20} {'29.8%':>8} {'0.817':>10} {'{1,3,6,9}':>16}
  {'Special-6 (shape)':<20} {'44.7%':>8} {'0.007':>10} {'{9} only':>16}
  {'Freq-Order (System3)':<20} {f'{pct:.1f}%':>8} {f'{p_val:.4f}':>10} {str(preserving):>16}
""", flush=True)
