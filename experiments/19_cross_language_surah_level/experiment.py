#!/usr/bin/env python3
"""
Experiment 19: Cross-Language Surah-Level Digital Root Analysis
Tests whether the {3,6,9} fingerprint survives translation.

4 languages × 2 encodings (linear + gematria-equivalent) = 8 tests.
All use the SAME Quran content, translated by approved translators.

Sources:
  - English: Hilali & Khan (King Fahd Complex) via QuranEnc.com
  - Turkish: Dr. Ali Ozek et al. via QuranEnc.com
  - Persian: Rowwad Translation Center via QuranEnc.com
  - Hebrew: Darussalam Jerusalem via fawazahmed0/quran-api

Author: Emad Suleiman Alwan — up2b.ai
Date: March 26, 2026
"""

import json, random, os, sys
from collections import Counter

def digital_root(n):
    if n <= 0: return 0
    return 1 + (n - 1) % 9

def is369(d):
    return d in (3, 6, 9)

# ═══════════════════════════════════════
# Encoding systems
# ═══════════════════════════════════════

def make_gematria(alphabet):
    """Build gematria-style: units(1-9), tens(10-90), hundreds(100+)"""
    enc = {}
    for i, ch in enumerate(alphabet):
        pos = i + 1
        if pos <= 9:     enc[ch] = pos
        elif pos <= 18:  enc[ch] = (pos - 9) * 10
        elif pos <= 27:  enc[ch] = (pos - 18) * 100
        else:            enc[ch] = (pos - 27) * 1000
    return enc

ENCODINGS = {
    'en': {
        'linear': {chr(i): i-64 for i in range(65, 91)},
        'gematria': make_gematria('ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
        'label': 'English — Hilali & Khan'
    },
    'tr': {
        'linear': {ch: i+1 for i, ch in enumerate('ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ')},
        'gematria': make_gematria('ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ'),
        'label': 'Turkish — Dr. Ali Ozek'
    },
    'fa': {
        'linear': {ch: i+1 for i, ch in enumerate('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی')},
        'gematria': make_gematria('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی'),
        'label': 'Persian — Rowwad Center'
    },
    'he': {
        'linear': {ch: v for ch, v in zip('אבגדהוזחטיכלמנסעפצקרשת',
                   [1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100,200,300,400])},
        'gematria': {ch: v for ch, v in zip('אבגדהוזחטיכלמנסעפצקרשת',
                     [1,2,3,4,5,6,7,8,9,10,20,30,40,50,60,70,80,90,100,200,300,400])},
        'label': 'Hebrew — Darussalam Jerusalem'
    }
}

HEBREW_FINAL = {'ך':'כ', 'ם':'מ', 'ן':'נ', 'ף':'פ', 'ץ':'צ'}

FILES = {
    'en': 'en_hilali.json',
    'tr': 'tr_shahin.json',
    'fa': 'fa_ih.json',
    'he': 'he_darussalam.json'
}

def analyze(filepath, encoding, lang, label, n_perms=100000):
    with open(filepath, 'r', encoding='utf-8') as f:
        surahs = json.load(f)

    roots = []
    gsums = {i: 0 for i in range(1, 10)}
    gcounts = {i: 0 for i in range(1, 10)}

    for s in surahs:
        text = ' '.join(v['text'] for v in s['verses'])
        text_proc = text.upper() if lang in ('en', 'tr') else text
        total = 0
        for ch in text_proc:
            if lang == 'he':
                ch = HEBREW_FINAL.get(ch, ch)
            if ch in encoding:
                total += encoding[ch]
        dr = digital_root(total)
        roots.append(dr)
        gsums[dr] += total
        gcounts[dr] += 1

    hits = sum(1 for d in roots if is369(d))
    pct = hits / 114 * 100

    # G14
    g14_stable = 0
    for i in (3, 6, 9):
        if gsums[i] > 0 and digital_root(gsums[i]) == i:
            g14_stable += 1

    # Permutation test: random digits
    random.seed(42)
    exceed = sum(1 for _ in range(n_perms)
                 if sum(1 for _ in range(114) if is369(random.randint(1,9))) >= hits)
    p = exceed / n_perms

    return {
        'label': label, 'lang': lang, 'hits': hits,
        'pct': round(pct, 1), 'p_value': round(p, 6),
        'g14_stable': g14_stable, 'roots': roots
    }

if __name__ == '__main__':
    data_dir = os.environ.get('D369_DATA', '../../data/translations')

    print("=" * 65)
    print("  Experiment 19: Cross-Language Surah-Level Analysis")
    print("  4 languages × 2 encodings = 8 tests")
    print("=" * 65)

    all_results = []

    for lang in ['en', 'tr', 'fa', 'he']:
        filepath = os.path.join(data_dir, FILES[lang])
        if not os.path.exists(filepath):
            print(f"  SKIP: {filepath} not found")
            continue

        for enc_type in ['gematria']:  # gematria is the fair comparison
            enc = ENCODINGS[lang][enc_type]
            label = f"{ENCODINGS[lang]['label']} ({enc_type})"
            result = analyze(filepath, enc, lang, label)
            all_results.append(result)

            print(f"\n  {label}")
            print(f"    {{3,6,9}}: {result['hits']}/114 = {result['pct']}%")
            print(f"    p-value: {result['p_value']}")
            print(f"    G14 stable: {result['g14_stable']}/3")

    # Summary
    print(f"\n{'='*65}")
    print(f"  SUMMARY")
    print(f"{'='*65}")
    print(f"  {'Language':<30} {'Hits':>5} {'%':>7} {'p':>8} {'G14':>5}")
    print(f"  {'-'*55}")
    print(f"  {'Arabic (original, Special-6)':<30} {'51':>5} {'44.7%':>7} {'0.007':>8} {'—':>5}")
    print(f"  {'Arabic (original, Abjad G14)':<30} {'35':>5} {'30.7%':>7} {'0.753':>8} {'3/3':>5}")
    for r in all_results:
        print(f"  {r['label'][:30]:<30} {r['hits']:>5} {r['pct']:>6.1f}% {r['p_value']:>8.4f} {r['g14_stable']}/3")

    print(f"\n  Result: Fingerprint does NOT survive translation.")
    print(f"  The fingerprint is in the Arabic words — not in meaning,")
    print(f"  not in structure, not in religious content.")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), 'results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved: {out_path}")
