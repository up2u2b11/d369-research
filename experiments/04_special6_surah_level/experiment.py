"""
التجربة ٤ — الخاص-6 على مستوى السور (الاختبار الحاسم)
=========================================================
السؤال: هل الحساب الخاص-6 (ترميز شبه ثنائي) يرى بصمة {3,6,9}
         في 114 سورة؟ وهل هذه البصمة خاصة بالقرآن؟

الخاص-6: نظام مستقل تماماً عن الجُمَّل — يعتمد على 0 و1 فقط
          33 شكلاً مستقلاً (لا 28 صوتاً) → ة≠ت، ؤ≠و، ئ≠ي

المنهج:
  1. حساب مجموع الخاص-6 لكل سورة
  2. حساب الجذر الرقمي لكل سورة
  3. عدّ السور التي جذرها في {3,6,9}
  4. Permutation Test (10,000): خلط الكلمات بين السور
  5. تكرار على 3 نصوص أخرى للمقارنة

الاكتشاف: p = 0.007 للقرآن | p > 0.38 لكل نص آخر

الملكية الفكرية: عماد سليمان علوان — 17 مارس 2026
"""

import sqlite3
import re
import random
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import KHASS_6, digit_root, word_value

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")
DATA_DIR = os.environ.get("D369_DATA", "/root/d369/data")


def load_quran_k6(db_path: str) -> tuple:
    """تحميل قيم الخاص-6 لكل كلمة مع معرّف سورتها"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, CAST(jummal_special_6 AS INTEGER)
        FROM words
        WHERE jummal_special_6 != '0'
        ORDER BY surah_id, word_pos_in_quran
    """)
    rows = c.fetchall()
    conn.close()

    surah_ids = [r[0] for r in rows]
    k6_values = [r[1] for r in rows]

    # أحجام السور
    sizes = defaultdict(int)
    for sid in surah_ids:
        sizes[sid] += 1

    return k6_values, [sizes[s] for s in sorted(sizes)]


def count_369(values: list, sizes: list) -> int:
    """عدّ السور التي جذر مجموع الخاص-6 فيها ينتمي لـ {3,6,9}"""
    idx = 0
    count = 0
    for sz in sizes:
        total = sum(values[idx:idx+sz])
        if digit_root(total) in (3, 6, 9):
            count += 1
        idx += sz
    return count


def permutation_test(values: list, sizes: list, observed: int, trials: int = 10_000) -> float:
    """Permutation Test: خلط الكلمات عشوائياً بين السور"""
    vc = values.copy()
    exceed = 0
    for _ in range(trials):
        random.shuffle(vc)
        if count_369(vc, sizes) >= observed:
            exceed += 1
    return exceed / trials


def test_text_file(path: str, label: str, n_chunks: int = 114, trials: int = 2_000) -> dict:
    """اختبار نص خارجي بتقسيمه لـ n_chunks وحدة"""
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        return {"label": label, "error": "ملف غير موجود"}

    words = re.findall(r'[\u0600-\u06FF]{2,}', text)
    if len(words) < n_chunks * 10:
        n_chunks = max(10, len(words) // 50)

    k6_vals = [word_value(w, KHASS_6) for w in words]
    sz = len(k6_vals) // n_chunks
    sizes = [sz] * (n_chunks - 1) + [len(k6_vals) - sz * (n_chunks - 1)]

    obs = count_369(k6_vals, sizes)
    p = permutation_test(k6_vals, sizes, obs, trials)

    return {
        "label": label,
        "n_words": len(words),
        "n_chunks": n_chunks,
        "observed": obs,
        "pct": obs / n_chunks * 100,
        "p_value": p
    }


def run(db_path: str = DB_PATH, data_dir: str = DATA_DIR,
        perm_trials: int = 10_000) -> dict:
    print("=" * 60)
    print("التجربة ٤ — الخاص-6 على مستوى السور")
    print("الاختبار الحاسم: هل البصمة خاصة بالقرآن؟")
    print("=" * 60)

    # ── القرآن ──
    print("\nجاري تحميل بيانات القرآن...")
    k6_values, sizes = load_quran_k6(db_path)
    obs_quran = count_369(k6_values, sizes)
    n_surahs = len(sizes)

    print(f"القرآن: {sum(sizes):,} كلمة | {n_surahs} سورة")
    print(f"  {{3,6,9}} = {obs_quran}/{n_surahs} = {obs_quran/n_surahs*100:.1f}%")
    print(f"  جاري Permutation Test ({perm_trials:,} تجربة)...")

    p_quran = permutation_test(k6_values, sizes, obs_quran, perm_trials)
    print(f"  p = {p_quran:.5f}  {'✅ دال (p<0.05)' if p_quran < 0.05 else '✗ غير دال'}")

    # ── النصوص المقارنة ──
    comparisons = [
        (os.path.join(data_dir, "bukhari_sample.txt"), "صحيح البخاري", 114),
        (os.path.join(data_dir, "futuhat_v1.txt"), "ابن عربي (الفتوحات)", 114),
        (os.path.join(data_dir, "muallaqat.txt"), "المعلقات السبع", 20),
    ]

    print(f"\n{'─'*55}")
    print("مقارنة مع نصوص أخرى (2,000 تجربة لكل نص):")
    print(f"{'─'*55}")

    comparison_results = []
    for path, label, chunks in comparisons:
        r = test_text_file(path, label, chunks, 2_000)
        if "error" in r:
            print(f"  {label}: ⚠️ {r['error']}")
        else:
            print(f"  {label}: {r['observed']}/{r['n_chunks']} = {r['pct']:.1f}%  |  p = {r['p_value']:.4f}  {'✅' if r['p_value']<0.05 else '✗'}")
        comparison_results.append(r)

    # ── الملخص ──
    print(f"\n{'='*55}")
    print("الملخص")
    print(f"{'='*55}")
    print(f"{'النص':>22} | {{3,6,9}} | p-value | الحكم")
    print("─" * 55)
    print(f"  {'القرآن الكريم':>20} | {obs_quran}/{n_surahs}={obs_quran/n_surahs*100:.1f}% | {p_quran:.4f}  | {'✅ دال' if p_quran<0.05 else '✗'}")
    for r in comparison_results:
        if "error" not in r:
            pct_str = f"{r['observed']}/{r['n_chunks']}={r['pct']:.1f}%"
            print(f"  {r['label']:>20} | {pct_str:>15} | {r['p_value']:.4f}  | {'✅' if r['p_value']<0.05 else '✗'}")

    return {
        "quran": {"observed": obs_quran, "n_surahs": n_surahs, "p_value": p_quran},
        "comparisons": comparison_results
    }


if __name__ == "__main__":
    run()
