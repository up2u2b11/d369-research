"""
التجربة ٣ — بصمة الجذر الرقمي على مستوى الكلمات (5 نصوص)
============================================================
السؤال: هل نسبة الكلمات ذات الجذر من {3,6,9} في القرآن غير عادية
         مقارنة بنصوص عربية أخرى؟

المنهج:
  1. لكل كلمة: حساب جُمَّلها ثم جذرها الرقمي
  2. حساب نسبة {3,6,9} في كل نص
  3. Chi-Square لاختبار التوزيع

النصوص المختبَرة:
  - القرآن الكريم (78,248 كلمة)
  - صحيح البخاري (عيّنة)
  - صحيح مسلم (عيّنة)
  - فتوحات ابن عربي (عيّنة)
  - المعلقات السبع

الملكية الفكرية: عماد سليمان علوان
"""

import sqlite3
import re
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from utils import JUMMAL_5, digit_root, word_value

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")
DATA_DIR = os.environ.get("D369_DATA", "/root/d369/data")


def analyze_words_from_db(db_path: str) -> dict:
    """تحليل كلمات القرآن من قاعدة البيانات"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT jummal_value FROM words WHERE jummal_value > 0")
    values = [r[0] for r in c.fetchall()]
    conn.close()

    roots = [digit_root(v) for v in values]
    cnt = Counter(roots)
    n = len(roots)
    count_369 = cnt[3] + cnt[6] + cnt[9]
    return {"n": n, "count_369": count_369, "pct": count_369/n*100, "distribution": dict(cnt)}


def analyze_text_file(path: str, label: str) -> dict:
    """تحليل ملف نصي"""
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        return {"label": label, "error": f"ملف غير موجود: {path}"}

    words = re.findall(r'[\u0600-\u06FF]{2,}', text)
    roots = [digit_root(word_value(w, JUMMAL_5)) for w in words if word_value(w, JUMMAL_5) > 0]
    if not roots:
        return {"label": label, "error": "لا كلمات صالحة"}

    cnt = Counter(roots)
    n = len(roots)
    count_369 = cnt[3] + cnt[6] + cnt[9]
    return {"label": label, "n": n, "count_369": count_369, "pct": count_369/n*100, "distribution": dict(cnt)}


def chi_square_test(distribution: dict, n: int) -> tuple:
    """Chi-Square: هل التوزيع يختلف عن المتساوي؟"""
    try:
        from scipy import stats
        observed = [distribution.get(r, 0) for r in range(1, 10)]
        expected = [n / 9] * 9
        chi2, p = stats.chisquare(observed, expected)
        return chi2, p
    except ImportError:
        return None, None


def run(db_path: str = DB_PATH, data_dir: str = DATA_DIR) -> list:
    print("=" * 60)
    print("التجربة ٣ — بصمة الجذر الرقمي على مستوى الكلمات")
    print("الجُمَّل ة=5 — 5 نصوص")
    print("=" * 60)

    results = []

    # القرآن من DB
    quran = analyze_words_from_db(db_path)
    quran["label"] = "القرآن الكريم"
    results.append(quran)

    # النصوص الأخرى
    texts = [
        (os.path.join(data_dir, "bukhari_sample.txt"), "صحيح البخاري"),
        (os.path.join(data_dir, "muslim_sample.txt"), "صحيح مسلم"),
        (os.path.join(data_dir, "futuhat_v1.txt"), "فتوحات ابن عربي"),
        (os.path.join(data_dir, "muallaqat.txt"), "المعلقات السبع"),
    ]
    for path, label in texts:
        results.append(analyze_text_file(path, label))

    # عرض النتائج
    print(f"\n{'النص':>20} | {'الكلمات':>8} | {{3,6,9}} | النسبة | Chi-Sq p")
    print("─" * 70)
    for r in results:
        if "error" in r:
            print(f"  {r['label']:>18} | ⚠️ {r['error']}")
            continue
        chi2, p = chi_square_test(r["distribution"], r["n"])
        p_str = f"{p:.3f}" if p is not None else "N/A"
        star = "✅" if p is not None and p < 0.05 else ""
        print(f"  {r['label']:>18} | {r['n']:>7,} | {r['count_369']:>6} | {r['pct']:>5.1f}%  | {p_str} {star}")

    # التوزيع التفصيلي للقرآن
    print(f"\nتوزيع جذور كلمات القرآن:")
    dist = results[0].get("distribution", {})
    n = results[0].get("n", 1)
    for r in range(1, 10):
        bar = "█" * int(dist.get(r, 0) / n * 100)
        mark = " ← {3,6,9}" if r in (3, 6, 9) else ""
        print(f"  {r}: {dist.get(r,0):>6} ({dist.get(r,0)/n*100:.1f}%) {bar}{mark}")

    return results


if __name__ == "__main__":
    run()
