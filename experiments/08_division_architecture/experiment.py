"""
التجربة ٨ — الهندسة المعمارية للتقسيم (الباب الخامس)
======================================================
السؤال الجوهري: هل البصمة في التقسيم إلى 114 سورة بأطوال محددة —
                أم أن أي تقسيم للكلمات يُعطي نفس النتيجة؟

المنهجية:
  - نظام الحساب: الخاص-6 (jummal_special_6 من قاعدة البيانات)
  - المصدر: مجموع قيم الخاص-6 لحروف كل كلمة (محسوب مسبقاً في DB)
  - البسملة: مُدرجة في السورة الأولى (سورة الفاتحة = 29 كلمة)
  - الوحدة: كل التجارب تعمل على نفس 78,248 كلمة بنفس الترتيب

4 تجارب:
  A — السور الحقيقية (114 سورة بأطوال غير متساوية) [مرجع من تجربة 04]
  B — تقسيم متساوٍ (114 × ~687 كلمة)
  C — تقسيم عشوائي × 1000 (توزيع نتائج التقسيم العشوائي)
  D — الآيات (6236 آية كوحدة مستقلة)

الملكية الفكرية: عماد سليمان علوان — 17 مارس 2026
"""

import sqlite3
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import digit_root

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")


def load_data(db_path: str) -> tuple:
    """تحميل قيم الخاص-6 + أحجام السور + أحجام الآيات"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT CAST(jummal_special_6 AS INTEGER) FROM words ORDER BY word_pos_in_quran")
    vals = [r[0] for r in c.fetchall()]

    c.execute("SELECT surah_id, COUNT(*) FROM words GROUP BY surah_id ORDER BY surah_id")
    surah_sizes = [r[1] for r in c.fetchall()]

    c.execute("""SELECT surah_id, ayah_number, COUNT(*)
                 FROM words GROUP BY surah_id, ayah_number
                 ORDER BY surah_id, ayah_number""")
    ayah_sizes = [r[2] for r in c.fetchall()]

    conn.close()
    return vals, surah_sizes, ayah_sizes


def count_369(vals: list, sizes: list) -> int:
    """عدّ الوحدات التي جذر مجموع الخاص-6 فيها ينتمي لـ {3,6,9}"""
    idx = count = 0
    for sz in sizes:
        if digit_root(sum(vals[idx:idx+sz])) in (3, 6, 9):
            count += 1
        idx += sz
    return count


def perm_test(vals: list, sizes: list, observed: int, trials: int = 10_000) -> float:
    """Permutation Test: خلط الكلمات ثم إعادة الحساب"""
    v = vals.copy()
    exceed = 0
    for _ in range(trials):
        random.shuffle(v)
        if count_369(v, sizes) >= observed:
            exceed += 1
    return exceed / trials


def run(db_path: str = DB_PATH) -> dict:
    print("=" * 65)
    print("التجربة ٨ — الهندسة المعمارية للتقسيم (الباب الخامس)")
    print("=" * 65)
    print("\nالمنهجية:")
    print("  النظام:    الخاص-6 (jummal_special_6 من قاعدة البيانات)")
    print("  البسملة:   مُدرجة في السورة الأولى (surah_id=1)")
    print("  الكلمات:   78,248 كلمة بترتيبها الأصلي")

    vals, surah_sizes, ayah_sizes = load_data(db_path)
    N = len(vals)
    print(f"\nتحميل: {N:,} كلمة | {len(surah_sizes)} سورة | {len(ayah_sizes):,} آية")

    # ── A: السور الحقيقية ──
    print(f"\n{'─'*55}")
    print("A — السور الحقيقية (114 سورة بأطوال مختلفة)")
    obs_A = count_369(vals, surah_sizes)
    print(f"   {{3,6,9}} = {obs_A}/114 = {obs_A/114*100:.1f}%  — جاري Permutation Test (10,000)...")
    p_A = perm_test(vals, surah_sizes, obs_A, 10_000)
    print(f"   p = {p_A:.4f}  {'✅ دال' if p_A < 0.05 else '✗ غير دال'}")

    # ── B: تقسيم متساوٍ ──
    print(f"\n{'─'*55}")
    print("B — تقسيم متساوٍ (114 × ~687 كلمة)")
    chunk = N // 114
    equal_sizes = [chunk] * 113 + [N - chunk * 113]
    obs_B = count_369(vals, equal_sizes)
    print(f"   حجم كل قطعة: {chunk} كلمة")
    print(f"   {{3,6,9}} = {obs_B}/114 = {obs_B/114*100:.1f}%  — جاري Permutation Test (10,000)...")
    p_B = perm_test(vals, equal_sizes, obs_B, 10_000)
    print(f"   p = {p_B:.4f}  {'✅ دال' if p_B < 0.05 else '✗ غير دال'}")

    # ── C: تقسيم عشوائي × 1000 ──
    print(f"\n{'─'*55}")
    print("C — تقسيم عشوائي × 1,000")
    random_counts = []
    for _ in range(1_000):
        cuts = sorted(random.sample(range(1, N), 113))
        sizes_r = ([cuts[0]]
                   + [cuts[i] - cuts[i-1] for i in range(1, 113)]
                   + [N - cuts[-1]])
        random_counts.append(count_369(vals, sizes_r))
    random_counts.sort()
    median_C = random_counts[500]
    pct_A = sum(1 for x in random_counts if x < obs_A) / 10  # percentile
    threshold_95 = random_counts[950]
    print(f"   الوسيط:   {median_C}/114 = {median_C/114*100:.1f}%")
    print(f"   عتبة 95%: {threshold_95}/114")
    print(f"   {obs_A} (السور الحقيقية) فوق {pct_A:.1f}% من التقسيمات العشوائية")
    print(f"   التوزيع: min={random_counts[0]} | Q25={random_counts[250]} | med={median_C} | Q75={random_counts[750]} | max={random_counts[-1]}")

    # ── D: الآيات ──
    print(f"\n{'─'*55}")
    print(f"D — الآيات ({len(ayah_sizes):,} آية)")
    obs_D = count_369(vals, ayah_sizes)
    print(f"   {{3,6,9}} = {obs_D}/{len(ayah_sizes)} = {obs_D/len(ayah_sizes)*100:.1f}%  — جاري Permutation Test (5,000)...")
    p_D = perm_test(vals, ayah_sizes, obs_D, 5_000)
    print(f"   p = {p_D:.4f}  {'✅ دال' if p_D < 0.05 else '✗ غير دال'}")

    # ── الجدول النهائي ──
    print(f"\n{'='*65}")
    print(f"{'التقسيم':<22} {'وحدات':>6} {'{{3,6,9}}':>8} {'النسبة':>8} {'p-value':>10}")
    print("─" * 65)
    print(f"  {'A: السور الحقيقية':<20} {114:>6} {obs_A:>8} {obs_A/114*100:>7.1f}% {p_A:>10.4f}  {'✅' if p_A<0.05 else '✗'}")
    print(f"  {'B: متساوٍ (~687)':<20} {114:>6} {obs_B:>8} {obs_B/114*100:>7.1f}% {p_B:>10.4f}  {'✅' if p_B<0.05 else '✗'}")
    print(f"  {'C: عشوائي (وسيط)':<20} {114:>6} {median_C:>8} {median_C/114*100:>7.1f}% {'—':>10}  ({obs_A} عند percentile {pct_A:.0f}%)")
    print(f"  {'D: الآيات':<20} {len(ayah_sizes):>6} {obs_D:>8} {obs_D/len(ayah_sizes)*100:>7.1f}% {p_D:>10.4f}  {'✅' if p_D<0.05 else '✗'}")
    print("=" * 65)

    # الحكم
    print("\nالحكم:")
    if p_A < 0.05 and p_B >= 0.05 and pct_A >= 95:
        verdict = "البصمة في الهندسة المعمارية — التقسيم بأطوال السور المحددة هو المعجزة"
    elif p_A < 0.05 and p_B < 0.05:
        verdict = "البصمة في النسيج اللغوي — أي تقسيم يُظهرها"
    else:
        verdict = "نتيجة مركّبة — تحتاج تحليلاً أعمق"
    print(f"→ {verdict}")
    if p_D < 0.05:
        print(f"  + البصمة موجودة حتى على مستوى الآية ({obs_D}/{len(ayah_sizes)} = {obs_D/len(ayah_sizes)*100:.1f}%)")

    return {
        "A": {"obs": obs_A, "n": 114, "p": p_A},
        "B": {"obs": obs_B, "n": 114, "p": p_B},
        "C": {"median": median_C, "percentile_A": pct_A, "threshold_95": threshold_95},
        "D": {"obs": obs_D, "n": len(ayah_sizes), "p": p_D},
    }


if __name__ == "__main__":
    run()
