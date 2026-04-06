"""
Experiment 25 — Prime Signature of Quranic Word Values
=======================================================

Date: April 7, 2026
Systems: Classical Abjad (taa=5) + Special-6
Unit of analysis: 78,248 words -> primality classification

THEORETICAL FOUNDATION — Digital Root & Primality:

  DR(n) in {3,6,9}  <=>  n is divisible by 3
  n divisible by 3 and n > 3  =>  n is NOT prime
  Therefore: NO prime > 3 can EVER have DR in {3, 6, 9}

  This is a mathematical THEOREM, not a heuristic.
  DR(p) in {1, 2, 4, 5, 7, 8}  for all primes p > 3

THE QUESTION (inspired by Spider Mind analysis):

  Primes > 3 NEVER have digital root in {3, 6, 9}.
  The Quran's digital root fingerprint is DOMINATED by {3, 6, 9}.
  These are COMPLEMENTARY structures.

  QUESTION: Is the distribution of prime vs. composite word values
  in the Quran different from other Arabic texts?

TESTS:
  A - Word-level primality (prime vs composite proportions + DR distribution)
  B - Divisible-by-3 density (mechanism behind {3,6,9}) + Bootstrap CI
  C - Per-Surah composite ratio (uniform or concentrated?)
  D - Permutation test (is the excess significant?) + Cohen's h
  E - 6n+/-1 bridge (mod 6 distribution — where primes and {3,6,9} meet)

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
ORCID: 0009-0004-5797-6140
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
    """
    Deterministic primality test using 6k+/-1 optimization.
    All primes > 3 are of the form 6k+/-1 because:
      6k+0 = div by 6, 6k+2 = div by 2, 6k+3 = div by 3, 6k+4 = div by 2
      Only residues 1 and 5 (mod 6) remain as prime candidates.
    """
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


def verify_dr_prime_theorem():
    """
    Verify: no prime > 3 has DR in {3, 6, 9}.
    Proof: DR(n) in {3,6,9} => n = 0 (mod 3) => composite if n > 3.
    Empirical check for all primes up to 100,000 as sanity.
    """
    violations = []
    for n in range(4, 100_001):
        if is_prime(n):
            dr = digit_root(n)
            if dr in (3, 6, 9):
                violations.append((n, dr))
    return violations


# ──────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────

def load_quran_words(db_path: str) -> list:
    """Load all Quranic words. Returns list of (surah_id, text)."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT surah_id, text_uthmani FROM words ORDER BY word_pos_in_quran")
    rows = c.fetchall()
    conn.close()
    return rows


def load_text_words(path: str) -> list:
    """Load Arabic words (2+ chars) from plain text file."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return re.findall(r'[\u0600-\u06FF\u0750-\u077F]{2,}', text)


def compute_word_values(words: list, system: dict, is_db: bool = True) -> list:
    """Compute numerical values, digital roots, primality, div-by-3 for each word."""
    results = []
    for item in words:
        if is_db:
            surah_id, text = item
        else:
            surah_id, text = 0, item
        val = word_value(text, system)
        if val == 0:
            continue
        results.append({
            'surah_id': surah_id, 'text': text, 'value': val,
            'dr': digit_root(val), 'is_prime': is_prime(val),
            'div_by_3': val % 3 == 0
        })
    return results


# ──────────────────────────────────────────────────
# Test A — Prime vs Composite proportions
# ──────────────────────────────────────────────────

def test_a_primality_distribution(word_data: list, label: str) -> dict:
    """Analyze prime vs composite distribution + DR breakdown."""
    n = len(word_data)
    primes = [w for w in word_data if w['is_prime']]
    composites = [w for w in word_data if not w['is_prime']]
    n_prime, n_composite = len(primes), len(composites)

    print(f"\n  Test A — Primality Distribution: {label}")
    print(f"  {'─'*50}")
    print(f"  Total words:     {n:,}")
    print(f"  Prime values:    {n_prime:,}  ({n_prime/n*100:.2f}%)")
    print(f"  Composite values:{n_composite:,}  ({n_composite/n*100:.2f}%)")
    print(f"  Ratio C/P:       {n_composite/max(n_prime,1):.2f}")

    prime_drs = Counter(w['dr'] for w in primes)
    comp_drs = Counter(w['dr'] for w in composites)

    # Verify theorem: primes > 3 must NOT have DR in {3,6,9}
    primes_gt3_369 = sum(1 for w in primes if w['value'] > 3 and w['dr'] in (3, 6, 9))

    print(f"\n  DR distribution of PRIME-valued words:")
    print(f"  (Theorem: DR in {{3,6,9}} impossible for primes > 3)")
    for dr in range(1, 10):
        cnt = prime_drs.get(dr, 0)
        pct = cnt / max(n_prime, 1) * 100
        bar = '#' * int(pct / 2)
        marker = f' <-- {cnt} words (only p=3 allowed)' if dr in (3, 6, 9) else ''
        print(f"    DR={dr}: {cnt:5,}  ({pct:5.1f}%) {bar}{marker}")
    print(f"  Theorem check: primes > 3 with DR in {{3,6,9}}: {primes_gt3_369} (must be 0)")

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
    print(f"  Expected by chance: 33.3%")

    return {
        'label': label, 'n': n, 'n_prime': n_prime, 'n_composite': n_composite,
        'pct_prime': round(n_prime / n * 100, 2),
        'pct_composite': round(n_composite / n * 100, 2),
        'ratio_cp': round(n_composite / max(n_prime, 1), 2),
        'prime_drs': {str(k): v for k, v in sorted(prime_drs.items())},
        'composite_drs': {str(k): v for k, v in sorted(comp_drs.items())},
        'comp_369_pct': round(comp_369_pct, 2),
        'theorem_violations': primes_gt3_369
    }


# ──────────────────────────────────────────────────
# Test B — Divisible-by-3 density + Bootstrap CI
# ──────────────────────────────────────────────────

def test_b_div3_density(word_data: list, label: str) -> dict:
    """Fraction of word values divisible by 3 — the MECHANISM behind {3,6,9}.
    Includes Bootstrap 95% confidence interval."""
    n = len(word_data)
    div3 = sum(1 for w in word_data if w['div_by_3'])
    pct = div3 / n * 100

    # Bootstrap 95% CI
    boot_pcts = []
    for _ in range(2000):
        sample = random.choices(word_data, k=n)
        boot_pcts.append(sum(1 for w in sample if w['div_by_3']) / n * 100)
    boot_pcts.sort()
    ci_low = boot_pcts[int(0.025 * len(boot_pcts))]
    ci_high = boot_pcts[int(0.975 * len(boot_pcts))]

    print(f"\n  Test B — Divisible-by-3 Density: {label}")
    print(f"  {'─'*50}")
    print(f"  Words divisible by 3:  {div3:,}/{n:,} = {pct:.2f}%")
    print(f"  Expected by chance:    {n/3:,.0f} = 33.33%")
    print(f"  Excess:                {pct - 33.33:+.2f}%")
    print(f"  95% Bootstrap CI:      [{ci_low:.2f}%, {ci_high:.2f}%]")

    return {'label': label, 'n': n, 'div3': div3, 'pct_div3': round(pct, 2),
            'excess': round(pct - 33.33, 2), 'ci_95': [round(ci_low, 2), round(ci_high, 2)]}


# ──────────────────────────────────────────────────
# Test C — Per-Surah composite ratio
# ──────────────────────────────────────────────────

def test_c_surah_composite_ratio(word_data: list) -> dict:
    """Composite and div-by-3 ratio per Surah — uniform or concentrated?"""
    surah_data = defaultdict(lambda: {'prime': 0, 'composite': 0, 'div3': 0, 'total': 0})
    for w in word_data:
        sid = w['surah_id']
        surah_data[sid]['total'] += 1
        if w['is_prime']:
            surah_data[sid]['prime'] += 1
        else:
            surah_data[sid]['composite'] += 1
        if w['div_by_3']:
            surah_data[sid]['div3'] += 1

    print(f"\n  Test C — Per-Surah Composite Ratio")
    print(f"  {'─'*50}")

    ratios, div3_ratios = [], []
    high_div3 = []
    for sid in sorted(surah_data.keys()):
        d = surah_data[sid]
        if d['total'] == 0:
            continue
        comp_pct = d['composite'] / d['total'] * 100
        d3_pct = d['div3'] / d['total'] * 100
        ratios.append(comp_pct)
        div3_ratios.append(d3_pct)
        if d3_pct > 45:
            high_div3.append((sid, round(d3_pct, 1)))

    avg_r = sum(ratios) / len(ratios)
    avg_d3 = sum(div3_ratios) / len(div3_ratios)
    std_d3 = (sum((r - avg_d3)**2 for r in div3_ratios) / len(div3_ratios))**0.5

    print(f"  Composite %: avg={avg_r:.1f}%, min={min(ratios):.1f}%, max={max(ratios):.1f}%")
    print(f"  Div-by-3 %:  avg={avg_d3:.1f}%, min={min(div3_ratios):.1f}%, max={max(div3_ratios):.1f}%, std={std_d3:.1f}%")
    print(f"  Surahs with >45% div-by-3:  {len(high_div3)}")
    if high_div3:
        for sid, pct in sorted(high_div3, key=lambda x: -x[1])[:10]:
            print(f"    Surah {sid:3d}: {pct}%")

    return {'avg_composite_pct': round(avg_r, 1), 'avg_div3_pct': round(avg_d3, 1),
            'std_div3': round(std_d3, 1), 'min_composite': round(min(ratios), 1),
            'max_composite': round(max(ratios), 1),
            'high_div3_surahs': high_div3}


# ──────────────────────────────────────────────────
# Test D — Permutation test
# ──────────────────────────────────────────────────

def test_d_permutation(word_data: list, comparison_data: list, label: str,
                        trials: int = 5000) -> dict:
    """Permutation test: is Quran's div-by-3 excess significant vs comparison?
    Two-sided test + Cohen's h effect size."""
    q_div3 = sum(1 for w in word_data if w['div_by_3'])
    q_n = len(word_data)
    c_div3 = sum(1 for w in comparison_data if w['div_by_3'])
    c_n = len(comparison_data)

    obs_diff = (q_div3 / q_n) - (c_div3 / c_n)
    all_flags = [1]*q_div3 + [0]*(q_n - q_div3) + [1]*c_div3 + [0]*(c_n - c_div3)

    exceed = 0
    for _ in range(trials):
        random.shuffle(all_flags)
        perm_diff = sum(all_flags[:q_n])/q_n - sum(all_flags[q_n:])/c_n
        if abs(perm_diff) >= abs(obs_diff):
            exceed += 1

    p_val = exceed / trials
    p1, p2 = q_div3/q_n, c_div3/c_n
    h = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))

    print(f"\n  Test D — Permutation Test: Quran vs {label}")
    print(f"  {'─'*50}")
    print(f"  Quran div-by-3:      {p1*100:.2f}%")
    print(f"  {label} div-by-3:    {p2*100:.2f}%")
    print(f"  Observed difference: {obs_diff*100:+.2f}%")
    print(f"  p-value (two-sided): {p_val:.4f}  {'** significant' if p_val < 0.05 else 'not significant'}")
    print(f"  Cohen's h:           {h:.4f}  ({'small' if abs(h)<0.3 else 'medium' if abs(h)<0.8 else 'large'})")

    return {'quran_pct': round(p1*100, 2), 'comp_pct': round(p2*100, 2),
            'diff': round(obs_diff*100, 2), 'p_value': p_val, 'cohens_h': round(h, 4)}


# ──────────────────────────────────────────────────
# Test E — The 6n+/-1 Bridge
# ──────────────────────────────────────────────────

def test_e_6n_analysis(word_data: list, label: str) -> dict:
    """Word values mod 6 — where primes (1,5) and {3,6,9} fingerprint (0,3) meet."""
    mod6 = Counter(w['value'] % 6 for w in word_data)
    n = len(word_data)

    print(f"\n  Test E — Value mod 6 Distribution: {label}")
    print(f"  {'─'*50}")
    print(f"  Primes > 3: only residues 1 or 5 | Div-by-3: residues 0 or 3")
    print()

    notes = {0: ' <<< div-by-3 -> DR in {3,6,9}', 1: ' <-- prime-eligible (6n+1)',
             2: ' <-- even, not div-by-3', 3: ' <<< div-by-3 -> DR in {3,6,9}',
             4: ' <-- even, not div-by-3', 5: ' <-- prime-eligible (6n-1)'}
    for r in range(6):
        cnt = mod6.get(r, 0)
        pct = cnt / n * 100
        bar = '#' * int(pct / 2)
        print(f"    mod 6 = {r}: {cnt:6,}  ({pct:5.1f}%) {bar}{notes[r]}")

    div3_r = mod6.get(0, 0) + mod6.get(3, 0)
    prime_r = mod6.get(1, 0) + mod6.get(5, 0)
    print(f"\n  Div-by-3 zone (0,3):   {div3_r:,} ({div3_r/n*100:.1f}%) -> feeds {{3,6,9}}")
    print(f"  Prime zone (1,5):      {prime_r:,} ({prime_r/n*100:.1f}%) -> avoids {{3,6,9}}")

    return {'label': label, 'mod6': {str(k): v for k, v in sorted(mod6.items())},
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

    # Verify theorem
    print("\n>> Verifying theorem: no prime > 3 has DR in {3,6,9}...")
    violations = verify_dr_prime_theorem()
    if violations:
        print(f"  THEOREM VIOLATED — {len(violations)} counterexamples!")
    else:
        print(f"  Verified for all primes in [4, 100,000]: zero violations")

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
            comparisons[name] = compute_word_values(load_text_words(path), JUMMAL_5, is_db=False)
            print(f"  {name}: {len(comparisons[name]):,} words")

    all_results = {}

    # TEST A
    print(f"\n{'='*65}\n  TEST A — PRIMALITY DISTRIBUTION\n{'='*65}")
    all_results['test_a'] = {}
    all_results['test_a']['quran_abjad'] = test_a_primality_distribution(quran_abjad, "Quran (Abjad)")
    all_results['test_a']['quran_k6'] = test_a_primality_distribution(quran_k6, "Quran (K6)")
    for name, data in comparisons.items():
        all_results['test_a'][name] = test_a_primality_distribution(data, f"{name} (Abjad)")

    # TEST B
    print(f"\n{'='*65}\n  TEST B — DIVISIBLE-BY-3 DENSITY (mechanism behind {{3,6,9}})\n{'='*65}")
    all_results['test_b'] = {}
    all_results['test_b']['quran'] = test_b_div3_density(quran_abjad, "Quran (Abjad)")
    for name, data in comparisons.items():
        all_results['test_b'][name] = test_b_div3_density(data, f"{name} (Abjad)")

    # TEST C
    print(f"\n{'='*65}\n  TEST C — PER-SURAH COMPOSITE RATIO\n{'='*65}")
    all_results['test_c'] = test_c_surah_composite_ratio(quran_abjad)

    # TEST D
    print(f"\n{'='*65}\n  TEST D — PERMUTATION TEST\n{'='*65}")
    all_results['test_d'] = {}
    for name, data in comparisons.items():
        all_results['test_d'][name] = test_d_permutation(quran_abjad, data, name)

    # TEST E
    print(f"\n{'='*65}\n  TEST E — THE 6n+/-1 BRIDGE\n{'='*65}")
    all_results['test_e'] = {}
    all_results['test_e']['quran'] = test_e_6n_analysis(quran_abjad, "Quran (Abjad)")
    for name, data in comparisons.items():
        all_results['test_e'][name] = test_e_6n_analysis(data, f"{name} (Abjad)")

    # SYNTHESIS
    print(f"\n{'='*65}\n  SYNTHESIS\n{'='*65}")
    qa = all_results['test_a']['quran_abjad']
    qb = all_results['test_b']['quran']

    print(f"""
  Mathematical chain:
    DR(n) in {{3,6,9}} <=> n divisible by 3
    n div by 3 and n > 3 => n is NOT prime
    Therefore: primes and {{3,6,9}} are MUTUALLY EXCLUSIVE

  Quran (Abjad):
    Prime-valued words:     {qa['pct_prime']}%
    Divisible-by-3 words:   {qb['pct_div3']}%  (95% CI: {qb['ci_95']})
    {{3,6,9}} in composites: {qa['comp_369_pct']}%
    Theorem violations:     {qa['theorem_violations']} (expected: 0)

  Fingerprint = Material (div-by-3 excess) x Architecture (Surah order)
""")

    for name, res in all_results['test_d'].items():
        sig = '** SIGNIFICANT' if res['p_value'] < 0.05 else 'not significant'
        print(f"  Quran vs {name}: diff={res['diff']:+.2f}%, p={res['p_value']:.4f}, h={res['cohens_h']:.4f} -> {sig}")

    # Save
    with open(os.path.join(RESULTS_DIR, 'results.json'), 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Results saved to {RESULTS_DIR}/results.json")
    print(f"\n{'='*65}\n  END OF EXPERIMENT 25\n{'='*65}")


if __name__ == '__main__':
    run()
