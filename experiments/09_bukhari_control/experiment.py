"""
التجربة ٩ — البخاري كمجموعة ضابطة (الباب السادس)
==================================================
السؤال: هل البصمة خاصية القرآن وحده — أم خاصية أي نص عربي ديني؟

المنهج: نفس البطارية الرباعية من الباب الخامس — على البخاري.
الفارق المنطقي: البخاري عربي أصيل + ديني + عن النبي.
              لكن تقسيمه (97 كتاباً، آلاف الأبواب) وضعه الإمام البخاري.

المتغير الوحيد بين القرآن والبخاري: من رسم الحدود.

هيكل البخاري في الملف: كل سطر = حديث واحد (1000 حديث | 66,349 كلمة)

التجارب:
  A — الأحاديث (1000 حديث — التقسيم الطبيعي)
  B — تقسيم متساوٍ (1000 × ~66 كلمة)
  C — تقسيم عشوائي × 1000
  D — البخاري بأطوال السور القرآنية (للمقارنة المباشرة)

الملكية الفكرية: عماد سليمان علوان — 17 مارس 2026
"""

import sqlite3
import random
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import KHASS_6, digit_root, word_value

random.seed(42)  # Fixed seed for bitwise reproducibility

DB_PATH      = os.environ.get("D369_DB",   "/root/d369/d369.db")
BUKHARI_PATH = os.environ.get("D369_DATA", "/root/d369/data") + "/bukhari_sample.txt"


def load_bukhari(path: str) -> tuple:
    """كل سطر = حديث. يُعيد قيم الخاص-6 + أحجام الأحاديث."""
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    all_vals, hadith_sizes = [], []
    for line in lines:
        words = re.findall(r'[\u0600-\u06FF]{2,}', line)
        vals  = [word_value(w, KHASS_6) for w in words]
        all_vals.extend(vals)
        hadith_sizes.append(len(vals))
    return all_vals, hadith_sizes


def load_quran_surah_sizes(db_path: str) -> list:
    """أحجام السور القرآنية بعدد الكلمات."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM words GROUP BY surah_id ORDER BY surah_id")
    sizes = [r[0] for r in c.fetchall()]
    conn.close()
    return sizes


def count_369(vals: list, sizes: list) -> int:
    idx = count = 0
    for sz in sizes:
        if digit_root(sum(vals[idx:idx+sz])) in (3, 6, 9): count += 1
        idx += sz
    return count


def count_369_wrap(vals: list, sizes: list) -> int:
    """حساب مع التفاف دوري إذا كانت القيم أقل من المطلوب."""
    n = len(vals)
    idx = count = 0
    for sz in sizes:
        chunk = [vals[(idx + i) % n] for i in range(sz)]
        if digit_root(sum(chunk)) in (3, 6, 9): count += 1
        idx = (idx + sz) % n
    return count


def perm_test(vals: list, sizes: list, observed: int, trials: int = 10_000) -> float:
    v = vals.copy(); exceed = 0
    for _ in range(trials):
        random.shuffle(v)
        if count_369(v, sizes) >= observed: exceed += 1
    return exceed / trials


def perm_test_wrap(vals: list, sizes: list, observed: int, trials: int = 5_000) -> float:
    v = vals.copy(); exceed = 0
    for _ in range(trials):
        random.shuffle(v)
        if count_369_wrap(v, sizes) >= observed: exceed += 1
    return exceed / trials


def random_dist(vals: list, n_units: int, trials: int = 1_000) -> list:
    N = len(vals); counts = []
    for _ in range(trials):
        cuts = sorted(random.sample(range(1, N), n_units - 1))
        sizes = ([cuts[0]]
                 + [cuts[i] - cuts[i-1] for i in range(1, n_units - 1)]
                 + [N - cuts[-1]])
        counts.append(count_369(vals, sizes))
    counts.sort()
    return counts


def run(db_path: str = DB_PATH, bukhari_path: str = BUKHARI_PATH) -> dict:
    print("=" * 65)
    print("التجربة ٩ — البخاري كمجموعة ضابطة (الباب السادس)")
    print("=" * 65)

    buk_vals, hadith_sizes = load_bukhari(bukhari_path)
    surah_sizes = load_quran_surah_sizes(db_path)
    N = len(buk_vals)
    n_hadith = len(hadith_sizes)

    print(f"\nالبخاري: {N:,} كلمة | {n_hadith:,} حديث")
    print(f"المنهجية: كل سطر = حديث | قيم الخاص-6 من KHASS_6")

    # ── A: الأحاديث ──
    print(f"\n{'─'*55}")
    print(f"A — الأحاديث ({n_hadith:,} حديث — التقسيم الطبيعي)")
    obs_A = count_369(buk_vals, hadith_sizes)
    print(f"   {{3,6,9}} = {obs_A}/{n_hadith} = {obs_A/n_hadith*100:.1f}%  — Permutation Test (10,000)...")
    p_A = perm_test(buk_vals, hadith_sizes, obs_A, 10_000)
    print(f"   p = {p_A:.4f}  {'✅ دال' if p_A<0.05 else '✗ غير دال'}")

    # ── B: متساوٍ ──
    print(f"\n{'─'*55}")
    chunk = N // n_hadith
    equal_sizes = [chunk] * (n_hadith - 1) + [N - chunk * (n_hadith - 1)]
    print(f"B — تقسيم متساوٍ ({n_hadith} × ~{chunk} كلمة)")
    obs_B = count_369(buk_vals, equal_sizes)
    print(f"   {{3,6,9}} = {obs_B}/{n_hadith} = {obs_B/n_hadith*100:.1f}%  — Permutation Test (5,000)...")
    p_B = perm_test(buk_vals, equal_sizes, obs_B, 5_000)
    print(f"   p = {p_B:.4f}  {'✅ دال' if p_B<0.05 else '✗ غير دال'}")

    # ── C: عشوائي ──
    print(f"\n{'─'*55}")
    print(f"C — تقسيم عشوائي × 1,000 ({n_hadith} وحدة)")
    rand_counts = random_dist(buk_vals, n_hadith, 1_000)
    median_C = rand_counts[500]
    pct_A    = sum(1 for x in rand_counts if x < obs_A) / 10
    thr95    = rand_counts[950]
    print(f"   الوسيط:   {median_C}/{n_hadith} = {median_C/n_hadith*100:.1f}%")
    print(f"   عتبة 95%: {thr95}/{n_hadith}")
    print(f"   {obs_A} (أحاديث طبيعية) عند percentile {pct_A:.1f}%")

    # ── D: بأطوال السور القرآنية ──
    print(f"\n{'─'*55}")
    print("D — البخاري مقسَّم بأطوال السور القرآنية (114 وحدة)")
    obs_D = count_369_wrap(buk_vals, surah_sizes)
    print(f"   {{3,6,9}} = {obs_D}/114 = {obs_D/114*100:.1f}%  — Permutation Test (5,000)...")
    p_D = perm_test_wrap(buk_vals, surah_sizes, obs_D, 5_000)
    print(f"   p = {p_D:.4f}  {'✅ دال' if p_D<0.05 else '✗ غير دال'}")

    # ── الجدول النهائي ──
    print(f"\n{'='*65}")
    print(f"{'التقسيم':<30} {'وحدات':>7} {'{{3,6,9}}':>9} {'النسبة':>8} {'p-value':>10}")
    print("─" * 65)
    print(f"  {'A: أحاديث (طبيعي)':<28} {n_hadith:>7} {obs_A:>9} {obs_A/n_hadith*100:>7.1f}% {p_A:>10.4f}  {'✅' if p_A<0.05 else '✗'}")
    print(f"  {'B: متساوٍ (~66 كلمة)':<28} {n_hadith:>7} {obs_B:>9} {obs_B/n_hadith*100:>7.1f}% {p_B:>10.4f}  {'✅' if p_B<0.05 else '✗'}")
    print(f"  {'C: عشوائي (وسيط)':<28} {n_hadith:>7} {median_C:>9} {median_C/n_hadith*100:>7.1f}% {'—':>10}  ({obs_A} عند {pct_A:.0f}%)")
    print(f"  {'D: بأطوال السور القرآنية':<28} {114:>7} {obs_D:>9} {obs_D/114*100:>7.1f}% {p_D:>10.4f}  {'✅' if p_D<0.05 else '✗'}")
    print("=" * 65)

    print(f"\nللمقارنة — القرآن:")
    print(f"  السور الحقيقية:  51/114 = 44.7%  p=0.007  ✅  (التقسيم الإلهي)")
    print(f"  الآيات:        2164/6236 = 34.7%  p=0.010  ✅")
    print(f"  البخاري/أحاديث: {obs_A}/{n_hadith} = {obs_A/n_hadith*100:.1f}%  p={p_A:.3f}  {'✅' if p_A<0.05 else '✗'}  (التقسيم البشري)")

    print("\nالحكم:")
    if p_A >= 0.05 and p_B >= 0.05 and p_D >= 0.05:
        print("→ البخاري لا يُظهر بصمة في أي تقسيم")
        print("  الخاصية للقرآن وحده — المتغير الوحيد: من رسم الحدود")
    elif p_A < 0.05:
        print("→ البخاري يُظهر بصمة في تقسيمه الطبيعي")
    else:
        print("→ نتيجة مركّبة")

    return {
        "A": {"obs": obs_A, "n": n_hadith, "p": p_A},
        "B": {"obs": obs_B, "n": n_hadith, "p": p_B},
        "C": {"median": median_C, "percentile_A": pct_A, "threshold_95": thr95},
        "D": {"obs": obs_D, "n": 114, "p": p_D},
    }


if __name__ == "__main__":
    run()
