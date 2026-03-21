#!/usr/bin/env python3
"""
Experiment 14 — Random Encoding Stress Test (v2 — word-level shuffle)
======================================================================
33 random encodings × 5,000 permutations each.
Word-level shuffle (matching methodology of Experiments 4-9).
Each encoding assigns UNIQUE values to 33 Arabic letter shapes.

IP: Emad Suleiman Alwan — UP2U2B LLC — 2026
"""

import sqlite3, random, re, json
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone, timedelta

DB_PATH = "/root/d369/d369.db"
RESULTS_DIR = Path(__file__).parent
DIAC = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]')

SHAPES = sorted(set([
    'ء','آ','أ','إ','ؤ','ئ','ا','ب','ة','ت','ث','ج','ح','خ','د','ذ',
    'ر','ز','س','ش','ص','ض','ط','ظ','ع','غ','ف','ق','ك','ل','م','ن',
    'ه','و','ى','ي','ٱ',
]))


def digit_root(n):
    if n == 0: return 0
    r = n % 9
    return r if r else 9


def load_words():
    """Load word texts grouped by Surah."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT surah_id, text_uthmani FROM words ORDER BY surah_id, word_pos_in_quran")
    rows = c.fetchall()
    conn.close()
    surah_words = defaultdict(list)
    for sid, txt in rows:
        surah_words[sid].append(DIAC.sub('', txt))
    return dict(surah_words)


def word_value(word, enc):
    return sum(enc.get(ch, 0) for ch in word)


def make_encoding(seed, vmin=1, vmax=10000):
    rng = random.Random(seed)
    vals = rng.sample(range(vmin, vmax+1), len(SHAPES))
    return dict(zip(SHAPES, vals))


def test_one(surah_words, enc, n_trials=5000, rng_seed=42):
    """Test one encoding: compute {3,6,9} count + permutation test."""
    # Compute word values per Surah
    all_vals = []
    sizes = []
    for sid in sorted(surah_words.keys()):
        wvals = [word_value(w, enc) for w in surah_words[sid]]
        all_vals.extend(wvals)
        sizes.append(len(wvals))

    # Observed count
    idx = 0
    observed = 0
    for size in sizes:
        s = sum(all_vals[idx:idx+size])
        if digit_root(s) in (3, 6, 9):
            observed += 1
        idx += size

    pct = observed / 114 * 100

    # Permutation test
    random.seed(rng_seed)
    exceed = 0
    for _ in range(n_trials):
        random.shuffle(all_vals)
        idx = 0
        count = 0
        for size in sizes:
            if digit_root(sum(all_vals[idx:idx+size])) in (3, 6, 9):
                count += 1
            idx += size
        if count >= observed:
            exceed += 1

    return observed, pct, exceed / n_trials


def main():
    KSA = timezone(timedelta(hours=3))
    now = datetime.now(KSA).strftime("%Y-%m-%d %H:%M KSA")

    print("=" * 70)
    print("  Experiment 14 — Random Encoding Stress Test")
    print(f"  Date: {now}")
    print("=" * 70, flush=True)

    surah_words = load_words()
    n_words = sum(len(w) for w in surah_words.values())
    print(f"  {len(surah_words)} Surahs, {n_words:,} words\n", flush=True)

    # Phase 1: System 3
    print("  Phase 1: System 3 (seed=2026, unique 1-5000)", flush=True)
    enc3 = make_encoding(2026, 1, 5000)
    c3, p3, pv3 = test_one(surah_words, enc3, n_trials=10000, rng_seed=42)
    print(f"    {3,6,9} = {c3}/114 = {p3:.1f}%  |  p = {pv3:.4f}  |  {'SIG' if pv3<0.05 else 'NS'}", flush=True)

    # Phase 2: 33 random encodings
    print(f"\n  Phase 2: 33 random encodings (5,000 trials each)", flush=True)
    results = []
    sig5 = sig1 = sig07 = above44 = 0

    for i in range(33):
        enc = make_encoding(10000 + i)
        c, pct, p = test_one(surah_words, enc, n_trials=5000, rng_seed=42+i)
        results.append({'seed': 10000+i, 'count': c, 'pct': round(pct,1), 'p': round(p,4)})
        if p < 0.05: sig5 += 1
        if p < 0.01: sig1 += 1
        if p < 0.007: sig07 += 1
        if pct >= 44.7: above44 += 1
        mark = ' ***' if p < 0.05 else ''
        print(f"    [{i+1:>2}/33] seed={10000+i}: {c}/114 = {pct:>5.1f}%  p={p:.4f}{mark}", flush=True)

    # Summary
    pcts = [r['pct'] for r in results]
    print(f"\n{'='*70}")
    print(f"  RESULTS — 33 Random Encodings")
    print(f"{'='*70}")
    print(f"  {{3,6,9}} proportion: mean={sum(pcts)/len(pcts):.1f}%, min={min(pcts):.1f}%, max={max(pcts):.1f}%")
    print(f"  >= 44.7% (Special-6 level): {above44}/33")
    print(f"  p < 0.05:  {sig5}/33 ({sig5/33*100:.0f}%)")
    print(f"  p < 0.01:  {sig1}/33 ({sig1/33*100:.0f}%)")
    print(f"  p < 0.007: {sig07}/33 ({sig07/33*100:.0f}%) — beating Special-6")
    print(f"  Expected by chance (p<0.05): ~2/33 (5%)")

    print(f"\n  {'System':<30} | {'{3,6,9}':>8} | {'p':>8}")
    print(f"  {'-'*55}")
    print(f"  {'Abjad (ة=5)':<30} | {'29.8%':>8} | {'0.817':>8}")
    print(f"  {'Special-6 (designed)':<30} | {'44.7%':>8} | {'0.007':>8}")
    print(f"  {'System 3 (random)':<30} | {p3:>7.1f}% | {pv3:>8.4f}")
    print(f"  {'Mean 33 random':<30} | {sum(pcts)/len(pcts):>7.1f}% | {'varies':>8}")

    print(f"\n  CONCLUSION:")
    if sig07 == 0:
        print(f"  ZERO random encodings beat Special-6 (p < 0.007).")
        print(f"  Special-6's result is genuinely exceptional.")
    elif sig07 <= 2:
        print(f"  Only {sig07}/33 beat Special-6. The fingerprint is rare but not unique to designed encodings.")
    elif sig5 > 10:
        print(f"  {sig5}/33 are significant (p<0.05) — {sig5/33*100:.0f}% vs 5% expected.")
        print(f"  The Quran carries a {3,6,9} bias under MANY encodings.")
        print(f"  This is a deeper property of the TEXT, not the encoding system.")
    else:
        print(f"  {sig5}/33 significant — near the 5% chance rate.")

    print(f"\n{'='*70}", flush=True)

    with open(RESULTS_DIR / "results.json", 'w') as f:
        json.dump({
            'system3': {'count': c3, 'pct': p3, 'p': pv3},
            'n_encodings': 33, 'n_trials': 5000,
            'sig_005': sig5, 'sig_001': sig1, 'sig_0007': sig07,
            'above_44': above44, 'mean_pct': round(sum(pcts)/len(pcts),1),
            'results': results,
        }, f, indent=2)
    print(f"  Saved: {RESULTS_DIR / 'results.json'}")


if __name__ == "__main__":
    main()
