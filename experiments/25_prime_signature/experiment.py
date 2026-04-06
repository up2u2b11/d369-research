"""
Experiment 25 — Prime Signature of Quranic Word Values
=======================================================

Date: April 7, 2026
Systems: Classical Abjad (taa=5) + Special-6
Unit of analysis: 78,248 words -> primality classification

THE QUESTION (inspired by Spider Mind analysis):

Primes > 3 NEVER have digital root in {3, 6, 9}.
The Quran's digital root fingerprint is DOMINATED by {3, 6, 9}.

These are complementary structures:
  - Primes AVOID {3,6,9} (because any number with DR in {3,6,9} is divisible by 3)
  - The Quran ATTRACTS {3,6,9}

QUESTION: Is the distribution of prime vs. composite word values
in the Quran different from other Arabic texts?

TESTS:
  A - Word-level primality analysis (prime vs composite proportions)
  B - Divisible-by-3 density (the mechanism behind {3,6,9})
  C - Per-Surah composite ratio (uniform or concentrated?)
  D - Permutation test (is the excess significant?)
  E - 6n+/-1 bridge (mod 6 distribution)

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sqlite3
import re
import math
import json
import random
from collections import defaultdict, Counter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import JUMMAL_5, KHASS_6, digit_root, word_value

random.seed(369)

DB_PATH = os.environ.get("D369_DB", "/home/emad/d369-quran-fingerprint/data/d369_research.db")
DATA_DIR = os.environ.get("D369_DATA", "/home/emad/d369-quran-fingerprint/data")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


# ──────────────────────────────────────────────────
# Primality testing
# ──────────────────────────────────────────────────

def is_prime(n: int) -> bool:
    """Deterministic primality test (sufficient for Abjad range 1-50,000)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


# ──────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────

def load_quran_words(db_path: str) -> list:
    """Load all Quranic words from the words table."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, text_uthmani
        FROM words
        ORDER BY word_pos_in_quran
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def load_text_words(path: str) -> list:
    """Load words from a plain text file."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return re.findall(r'[\u0600-\u06FF\u0750-\u077F]{2,}', text)


def compute_word_values(words: list, system: dict, is_db: bool = True) -> list:
    """Compute numerical values for a list of words."""
    results = []
    for item in words:
        if is_db:
            surah_id, text = item
        else:
            surah_id = 0
            text = item
        val = word_value(text, system)
        if val == 0:
            continue
        dr = digit_root(val)
        results.append({
            'surah_id': surah_id,
            'text': text,
            'value': val,
            'dr': dr,
            'is_prime': is_prime(val),
            'div_by_3': val % 3 == 0
        })
    return results


# ──────────────────────────────────────────────────
# Test A — Prime vs Composite proportions
# ──────────────────────────────────────────────────

def test_a_primality_distribution(word_data: list, label: str) -> dict:
    """Analyze prime vs composite distribution of word values."""
    n = len(word_data)
    primes = [w for w in word_data if w['is_prime']]
    composites = [w for w in word_data if not w['is_prime']]
    n_prime = len(primes)
    n_composite = len(composites)

    print(f"\n  Test A — Primality Distribution: {label}")
    print(f"  {'─'*50}")
    print(f"  Total words:     {n:,}")
    print(f"  Prime values:    {n_prime:,}  ({n_prime/n*100:.2f}%)")
    print(f"  Composite values:{n_composite:,}  ({n_composite/n*100:.2f}%)")
    print(f"  Ratio C/P:       {n_composite/max(n_prime,1):.2f}")

    prime_drs = Counter(w['dr'] for w in primes)
    comp_drs = Counter(w['dr'] for w in composites)

    print(f"\n  DR distribution of PRIME-valued words:")
    for dr in range(1, 10):
        cnt = prime_drs.get(dr, 0)
        pct = cnt / max(n_prime, 1) * 100
        bar = '#' * int(pct / 2)
        marker = ' <-- impossible for p>3' if dr in (3, 6, 9) else ''
        print(f"    DR={dr}: {cnt:5,}  ({pct:5.1f}%) {bar}{marker}")

    print(f"\n  DR distribution of COMPOSITE-valued words:")
    for dr in range(1, 10):
        cnt = comp_drs.get(dr, 0)
        pct = cnt / max(n_composite, 1) * 100
        bar = '#' * int(pct / 2)
        marker = ' <<< {3,6,9}' if dr in (3, 6, 9) else ''
        print(f"    DR={dr}: {cnt:5,}  ({pct:5.1f}%) {bar}{marker}")

    comp_369 = sum(comp_drs.get(dr, 0) for dr in (3, 6, 9))
    comp_369_pct = comp_369 / max(n_composite, 1) * 100

    print(f"\n  {{3,6,9}} in composites: {comp_369:,}/{n_composite:,} = {comp_369_pct:.1f}%")
    print(f"  Expected by chance:    {n_composite/3:,.0f} = 33.3%")

    return {
        'label': label, 'n': n, 'n_prime': n_prime, 'n_composite': n_composite,
        'pct_prime': round(n_prime / n * 100, 2),
        'pct_composite': round(n_composite / n * 100, 2),
        'ratio_cp': round(n_composite / max(n_prime, 1), 2),
        'prime_drs': {str(k): v for k, v in sorted(prime_drs.items())},
        'composite_drs': {str(k): v for k, v in sorted(comp_drs.items())},
        'comp_369_pct': round(comp_369_pct, 2)
    }


# ──────────────────────────────────────────────────
# Test B — Divisible-by-3 density
# ──────────────────────────────────────────────────

def test_b_div3_density(word_data: list, label: str) -> dict:
    """What fraction of word values are divisible by 3?"""
    n = len(word_data)
    div3 = sum(1 for w in word_data if w['div_by_3'])
    pct = div3 / n * 100

    print(f"\n  Test B — Divisible-by-3 Density: {label}")
    print(f"  {'─'*50}")
    print(f"  Words divisible by 3:  {div3:,}/{n:,} = {pct:.2f}%")
    print(f"  Expected by chance:    {n/3:,.0f} = 33.33%")
    print(f"  Excess:                {pct - 33.33:+.2f}%")

    return {'label': label, 'n': n, 'div3': div3, 'pct_div3': round(pct, 2),
            'excess': round(pct - 33.33, 2)}


# ──────────────────────────────────────────────────
# Test C — Per-Surah composite ratio
# ──────────────────────────────────────────────────

def test_c_surah_composite_ratio(word_data: list) -> dict:
    """Compute composite/prime ratio per Surah."""
    surah_data = defaultdict(lambda: {'prime': 0, 'composite': 0})
    for w in word_data:
        if w['is_prime']:
            surah_data[w['surah_id']]['prime'] += 1
        else:
            surah_data[w['surah_id']]['composite'] += 1

    print(f"\n  Test C — Per-Surah Composite Ratio")
    print(f"  {'─'*50}")

    ratios = []
    for sid in sorted(surah_data.keys()):
        d = surah_data[sid]
        total = d['prime'] + d['composite']
        ratios.append(d['composite'] / total * 100 if total > 0 else 0)

    print(f"  Average composite %:  {sum(ratios)/len(ratios):.1f}%")
    print(f"  Min composite %:      {min(ratios):.1f}%")
    print(f"  Max composite %:      {max(ratios):.1f}%")
    print(f"  Std deviation:        {(sum((r - sum(ratios)/len(ratios))**2 for r in ratios)/len(ratios))**0.5:.1f}%")

    return {'avg_composite_pct': round(sum(ratios)/len(ratios), 1),
            'min': round(min(ratios), 1), 'max': round(max(ratios), 1),
            'high_composite_count': sum(1 for r in ratios if r > 80)}


# ──────────────────────────────────────────────────
# Test D — Permutation test for div-by-3 excess
# ──────────────────────────────────────────────────

def test_d_permutation(word_data: list, comparison_data: list, label: str,
                        trials: int = 5000) -> dict:
    """Permutation test: is the Quran's div-by-3 density significantly different?"""
    quran_div3 = sum(1 for w in word_data if w['div_by_3'])
    quran_n = len(word_data)
    comp_div3 = sum(1 for w in comparison_data if w['div_by_3'])
    comp_n = len(comparison_data)

    observed_diff = (quran_div3 / quran_n) - (comp_div3 / comp_n)

    all_flags = ([1] * quran_div3 + [0] * (quran_n - quran_div3) +
                 [1] * comp_div3 + [0] * (comp_n - comp_div3))

    exceed = 0
    for _ in range(trials):
        random.shuffle(all_flags)
        perm_q = sum(all_flags[:quran_n]) / quran_n
        perm_c = sum(all_flags[quran_n:]) / comp_n
        if abs(perm_q - perm_c) >= abs(observed_diff):
            exceed += 1

    p_value = exceed / trials

    # Cohen's h
    p1, p2 = quran_div3 / quran_n, comp_div3 / comp_n
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))

    print(f"\n  Test D — Permutation Test: Quran vs {label}")
    print(f"  {'─'*50}")
    print(f"  Quran div-by-3:      {p1*100:.2f}%")
    print(f"  {label} div-by-3:    {p2*100:.2f}%")
    print(f"  Observed difference: {observed_diff*100:+.2f}%")
    print(f"  p-value (two-sided): {p_value:.4f}  {'** significant' if p_value < 0.05 else 'not significant'}")
    print(f"  Cohen's h:           {h:.4f}  ({'small' if abs(h)<0.3 else 'medium' if abs(h)<0.8 else 'large'})")

    return {'quran_pct': round(p1*100, 2), 'comp_pct': round(p2*100, 2),
            'diff': round(observed_diff*100, 2), 'p_value': p_value,
            'cohens_h': round(h, 4)}


# ──────────────────────────────────────────────────
# Test E — The 6n+/-1 Bridge
# ──────────────────────────────────────────────────

def test_e_6n_analysis(word_data: list, label: str) -> dict:
    """Analyze word values modulo 6."""
    mod6_counts = Counter(w['value'] % 6 for w in word_data)
    n = len(word_data)

    print(f"\n  Test E — Value mod 6 Distribution: {label}")
    print(f"  {'─'*50}")
    print(f"  (Primes > 3 can ONLY be in residues 1 or 5)")
    print(f"  (Divisible by 3 -> residues 0 or 3)")
    print()

    for r in range(6):
        cnt = mod6_counts.get(r, 0)
        pct = cnt / n * 100
        bar = '#' * int(pct / 2)
        note = ''
        if r in (1, 5): note = ' <-- prime-eligible'
        elif r in (0, 3): note = ' <<< div-by-3 (-> DR in {3,6,9})'
        elif r in (2, 4): note = ' <-- even, not div-by-3'
        print(f"    mod 6 = {r}: {cnt:6,}  ({pct:5.1f}%) {bar}{note}")

    div3_r = mod6_counts.get(0, 0) + mod6_counts.get(3, 0)
    prime_r = mod6_counts.get(1, 0) + mod6_counts.get(5, 0)

    print(f"\n  Div-by-3 eligible (0,3):     {div3_r:,} ({div3_r/n*100:.1f}%)")
    print(f"  Prime-eligible (1,5):        {prime_r:,} ({prime_r/n*100:.1f}%)")

    return {'label': label, 'mod6': {str(k): v for k, v in sorted(mod6_counts.items())},
            'div3_pct': round(div3_r/n*100, 2), 'prime_eligible_pct': round(prime_r/n*100, 2)}


# ──────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────

def run():
    print("=" * 65)
    print("  Experiment 25 — Prime Signature of Quranic Word Values")
    print("  Primes avoid {3,6,9}. The Quran embraces {3,6,9}.")
    print("  Are these complementary structures — or coincidence?")
    print("=" * 65)

    # Load Quran
    print("\n>> Loading Quran words...")
    quran_words = load_quran_words(DB_PATH)
    quran_abjad = compute_word_values(quran_words, JUMMAL_5, is_db=True)
    quran_k6 = compute_word_values(quran_words, KHASS_6, is_db=True)
    print(f"  {len(quran_abjad):,} words (Abjad), {len(quran_k6):,} words (K6)")

    # Load comparisons
    print("\n>> Loading comparison texts...")
    comparisons = {}
    for name, fname in [("Bukhari", "bukhari_sample.txt"), ("Muallaqat", "muallaqat.txt")]:
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            words = load_text_words(path)
            comparisons[name] = compute_word_values(words, JUMMAL_5, is_db=False)
            print(f"  {name}: {len(comparisons[name]):,} words")
        else:
            print(f"  {name}: NOT FOUND")

    all_results = {}

    # TEST A
    print(f"\n{'='*65}")
    print("  TEST A — PRIMALITY DISTRIBUTION")
    print(f"{'='*65}")
    all_results['test_a'] = {}
    all_results['test_a']['quran_abjad'] = test_a_primality_distribution(quran_abjad, "Quran (Abjad)")
    all_results['test_a']['quran_k6'] = test_a_primality_distribution(quran_k6, "Quran (K6)")
    for name, data in comparisons.items():
        all_results['test_a'][name] = test_a_primality_distribution(data, f"{name} (Abjad)")

    # TEST B
    print(f"\n{'='*65}")
    print("  TEST B — DIVISIBLE-BY-3 DENSITY")
    print(f"{'='*65}")
    all_results['test_b'] = {}
    all_results['test_b']['quran'] = test_b_div3_density(quran_abjad, "Quran (Abjad)")
    for name, data in comparisons.items():
        all_results['test_b'][name] = test_b_div3_density(data, f"{name} (Abjad)")

    # TEST C
    print(f"\n{'='*65}")
    print("  TEST C — PER-SURAH COMPOSITE RATIO")
    print(f"{'='*65}")
    all_results['test_c'] = test_c_surah_composite_ratio(quran_abjad)

    # TEST D
    print(f"\n{'='*65}")
    print("  TEST D — PERMUTATION TEST")
    print(f"{'='*65}")
    all_results['test_d'] = {}
    for name, data in comparisons.items():
        all_results['test_d'][name] = test_d_permutation(quran_abjad, data, name)

    # TEST E
    print(f"\n{'='*65}")
    print("  TEST E — THE 6n+/-1 BRIDGE")
    print(f"{'='*65}")
    all_results['test_e'] = {}
    all_results['test_e']['quran'] = test_e_6n_analysis(quran_abjad, "Quran (Abjad)")
    for name, data in comparisons.items():
        all_results['test_e'][name] = test_e_6n_analysis(data, f"{name} (Abjad)")

    # SYNTHESIS
    print(f"\n{'='*65}")
    print("  SYNTHESIS — The Prime-Fingerprint Complementarity")
    print(f"{'='*65}")

    q = all_results['test_a']['quran_abjad']
    b = all_results['test_b']['quran']

    print(f"""
  Mathematical law:
    Primes > 3 can NEVER have digital root in {{3, 6, 9}}
    (because DR in {{3,6,9}} => divisible by 3 => not prime)

  Observed in the Quran (Abjad):
    Prime-valued words:       {q['pct_prime']}%
    Divisible-by-3 words:     {b['pct_div3']}%
    {{3,6,9}} in composites:   {q['comp_369_pct']}%
""")

    for name, res in all_results['test_d'].items():
        sig = '** SIGNIFICANT' if res['p_value'] < 0.05 else 'not significant'
        print(f"  Quran vs {name}: diff = {res['diff']:+.2f}%, p = {res['p_value']:.4f}, h = {res['cohens_h']:.4f} -> {sig}")

    # Save
    with open(os.path.join(RESULTS_DIR, 'results.json'), 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved to {RESULTS_DIR}/results.json")
    print(f"\n{'='*65}")
    print("  END OF EXPERIMENT 25 — PRIME SIGNATURE")
    print(f"{'='*65}")


if __name__ == '__main__':
    run()
