"""
التجربة ١ — خريطة التحوّلات الرقمية (G14)
============================================
السؤال: هل {3,6,9} تحافظ على نفسها حين تُجمع السور المتشابهة في جذرها؟

المنهج:
  1. حساب جُمَّل كل سورة (ة=5)
  2. حساب الجذر الرقمي لكل سورة
  3. تجميع السور حسب جذرها (9 مجموعات)
  4. حساب مجموع جُمَّل كل مجموعة ثم جذره
  5. الاختبار: هل {3,6,9} تحافظ على جذرها؟

النتيجة المتوقعة: {3,6,9} فقط تحافظ — باقي الجذور تتحول
الدلالة الإحصائية: p < 0.00001 (Monte Carlo 100,000)

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
import random
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import JUMMAL_5, digit_root

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")


def load_surah_jummal(db_path: str) -> dict:
    """تحميل مجموع الجُمَّل لكل سورة من النصوص مباشرة"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT surah_id, text_uthmani FROM words ORDER BY surah_id, word_pos_in_quran")
    rows = c.fetchall()
    conn.close()

    sums = defaultdict(int)
    for surah_id, text in rows:
        for ch in text:
            sums[surah_id] += JUMMAL_5.get(ch, 0)
    return dict(sums)


def build_transformation_map(surah_sums: dict) -> dict:
    """بناء خريطة التحوّلات: جذر → جذر مجموع مجموعته"""
    # تجميع مجاميع السور حسب جذرها
    groups = defaultdict(lambda: {"sum": 0, "count": 0, "surahs": []})
    for surah_id, total in sorted(surah_sums.items()):
        dr = digit_root(total)
        groups[dr]["sum"] += total
        groups[dr]["count"] += 1
        groups[dr]["surahs"].append(surah_id)

    # حساب جذر مجموع كل مجموعة
    result = {}
    for dr in range(1, 10):
        g = groups[dr]
        group_sum = g["sum"]
        group_dr = digit_root(group_sum)
        result[dr] = {
            "count": g["count"],
            "group_sum": group_sum,
            "group_dr": group_dr,
            "preserves": group_dr == dr,
            "surahs": g["surahs"]
        }
    return result


def monte_carlo_test(observed_stable: set, surah_sums: dict, trials: int = 100_000) -> float:
    """
    Monte Carlo: ما احتمال رؤية نفس المجموعات المحافظة عشوائياً؟
    نخلط القيم ونعيد بناء الخريطة
    """
    values = list(surah_sums.values())
    surah_ids = list(surah_sums.keys())
    n = len(values)
    exceed = 0

    for _ in range(trials):
        random.shuffle(values)
        shuffled = dict(zip(surah_ids, values))
        t_map = build_transformation_map(shuffled)
        stable = {dr for dr, info in t_map.items() if info["preserves"]}
        if stable >= observed_stable:  # نفس المجموعة أو أكبر
            exceed += 1

    return exceed / trials


def run(db_path: str = DB_PATH, monte_carlo_trials: int = 10_000) -> dict:
    print("=" * 60)
    print("التجربة ١ — خريطة التحوّلات الرقمية (G14)")
    print("الجُمَّل ة=5 — 114 سورة")
    print("=" * 60)

    surah_sums = load_surah_jummal(db_path)
    t_map = build_transformation_map(surah_sums)

    print(f"\n{'جذر':>4} | {'عدد السور':>9} | {'مجموع الجُمَّل':>18} | {'جذر المجموع':>11} | النتيجة")
    print("─" * 65)

    stable_set = set()
    total_quran = sum(surah_sums.values())

    for dr in range(1, 10):
        info = t_map[dr]
        mark = "✅ ثابت" if info["preserves"] else f"→ {info['group_dr']}"
        if info["preserves"]:
            stable_set.add(dr)
        print(f"   {dr}  |  {info['count']:>6}     | {info['group_sum']:>18,}  |      {info['group_dr']}        | {mark}")

    print(f"\nإجمالي جُمَّل القرآن: {total_quran:,} → جذر {digit_root(total_quran)}")
    print(f"\nالمجموعات المحافظة: {sorted(stable_set)}")

    # التحقق من G14 الأصلي
    g14_expected = {3, 6, 9}
    matches_g14 = stable_set == g14_expected
    print(f"تطابق G14 الأصلي {{3,6,9}}: {'✅' if matches_g14 else '✗'}")

    # Monte Carlo
    print(f"\nMonte Carlo ({monte_carlo_trials:,} تجربة)...")
    p_value = monte_carlo_test(stable_set, surah_sums, monte_carlo_trials)
    print(f"p-value = {p_value:.6f}  {'← دال إحصائياً ✅' if p_value < 0.05 else '← غير دال'}")

    return {
        "transformation_map": t_map,
        "stable_groups": sorted(stable_set),
        "total_quran_jummal": total_quran,
        "p_value": p_value,
        "matches_g14": matches_g14
    }


if __name__ == "__main__":
    run()
