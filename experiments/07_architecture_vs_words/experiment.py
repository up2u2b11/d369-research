"""
التجربة ٧ — الهندسة المعمارية أم الكلمات؟
==========================================
السؤال الجوهري: هل البصمة في كلمات القرآن — أم في كيف قُسّمت إلى 114 سورة؟

المنهج:
  إذا أخذنا البخاري وقسّمناه بنفس أطوال السور القرآنية (عدد كلمات كل سورة)،
  هل تظهر البصمة؟

  - إذا ظهرت → البصمة في التقسيم (الهندسة المعمارية)
  - إذا لم تظهر → البصمة في الكلمات القرآنية نفسها

الاختبارات:
  أ) البخاري مقسَّم بأطوال سور القرآن
  ب) كلمات القرآن مُرتَّبة عشوائياً ثم مقسَّمة بنفس الأطوال
  ج) كلمات القرآن بترتيبها الأصلي (المرجع)

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

random.seed(42)  # Fixed seed for bitwise reproducibility

DB_PATH = os.environ.get("D369_DB", "/root/d369/d369.db")
DATA_DIR = os.environ.get("D369_DATA", "/root/d369/data")


def get_surah_sizes(db_path: str) -> list:
    """أحجام السور بعدد الكلمات (بترتيب السورة 1-114)"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, COUNT(*) as word_count
        FROM words GROUP BY surah_id ORDER BY surah_id
    """)
    sizes = [row[1] for row in c.fetchall()]
    conn.close()
    return sizes


def get_quran_k6(db_path: str) -> list:
    """قيم الخاص-6 لكلمات القرآن بترتيبها"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT CAST(jummal_special_6 AS INTEGER)
        FROM words ORDER BY word_pos_in_quran
    """)
    vals = [r[0] for r in c.fetchall()]
    conn.close()
    return vals


def get_text_k6(path: str) -> list:
    """قيم الخاص-6 لكلمات نص خارجي"""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    words = re.findall(r'[\u0600-\u06FF]{2,}', text)
    return [word_value(w, KHASS_6) for w in words]


def count_369_with_sizes(values: list, sizes: list) -> tuple:
    """عدّ {3,6,9} مع الأطوال المحددة"""
    # إذا البيانات أقل من المطلوب، نُعيد الاستخدام دورياً
    idx = 0
    count = 0
    details = []
    n = len(values)
    for sz in sizes:
        chunk = [values[(idx + i) % n] for i in range(sz)]
        total = sum(chunk)
        dr = digit_root(total)
        if dr in (3, 6, 9):
            count += 1
        details.append(dr)
        idx = (idx + sz) % n
    return count, details


def permutation_test(values: list, sizes: list, observed: int, trials: int = 3000) -> float:
    vc = values.copy()
    exceed = 0
    for _ in range(trials):
        random.shuffle(vc)
        cnt, _ = count_369_with_sizes(vc, sizes)
        if cnt >= observed:
            exceed += 1
    return exceed / trials


def run(db_path: str = DB_PATH, data_dir: str = DATA_DIR) -> dict:
    print("=" * 65)
    print("التجربة ٧ — الهندسة المعمارية أم الكلمات؟")
    print("هل البصمة في التقسيم إلى 114 سورة — أم في الكلمات نفسها؟")
    print("=" * 65)

    sizes = get_surah_sizes(db_path)
    n_surahs = len(sizes)
    print(f"\nأطوال السور: {n_surahs} سورة | إجمالي {sum(sizes):,} كلمة")
    print(f"  أقصر سورة: {min(sizes)} كلمة (الكوثر) | أطول سورة: {max(sizes)} كلمة (البقرة)")

    # ── أ) القرآن بترتيبه الأصلي (المرجع) ──
    print(f"\n{'─'*55}")
    print("أ) القرآن — بترتيبه الأصلي (المرجع)")
    quran_vals = get_quran_k6(db_path)
    obs_quran, _ = count_369_with_sizes(quran_vals, sizes)
    p_quran = permutation_test(quran_vals, sizes, obs_quran, 3000)
    print(f"   {{3,6,9}} = {obs_quran}/{n_surahs} = {obs_quran/n_surahs*100:.1f}%  |  p = {p_quran:.4f}  {'✅ دال' if p_quran<0.05 else '✗'}")

    # ── ب) كلمات القرآن — مُرتَّبة عشوائياً ──
    print(f"\n{'─'*55}")
    print("ب) كلمات القرآن — مُخلَّطة عشوائياً ثم مقسَّمة بنفس الأطوال")
    shuffled_quran = quran_vals.copy()
    random.shuffle(shuffled_quran)
    obs_shuffled, _ = count_369_with_sizes(shuffled_quran, sizes)
    p_shuffled = permutation_test(shuffled_quran, sizes, obs_shuffled, 3000)
    print(f"   {{3,6,9}} = {obs_shuffled}/{n_surahs} = {obs_shuffled/n_surahs*100:.1f}%  |  p = {p_shuffled:.4f}  {'✅ دال' if p_shuffled<0.05 else '✗'}")

    # ── ج) البخاري — مقسَّم بأطوال سور القرآن ──
    bukhari_path = os.path.join(data_dir, "bukhari_sample.txt")
    print(f"\n{'─'*55}")
    print("ج) البخاري — مقسَّم بنفس أطوال السور القرآنية")
    try:
        bukhari_vals = get_text_k6(bukhari_path)
        print(f"   البخاري: {len(bukhari_vals):,} كلمة")
        obs_bukhari, _ = count_369_with_sizes(bukhari_vals, sizes)
        p_bukhari = permutation_test(bukhari_vals, sizes, obs_bukhari, 3000)
        print(f"   {{3,6,9}} = {obs_bukhari}/{n_surahs} = {obs_bukhari/n_surahs*100:.1f}%  |  p = {p_bukhari:.4f}  {'✅ دال' if p_bukhari<0.05 else '✗'}")
    except FileNotFoundError:
        print("   ⚠️ ملف البخاري غير موجود")
        p_bukhari = None

    # ── الحكم ──
    print(f"\n{'='*55}")
    print("الحكم")
    print(f"{'='*55}")
    print(f"  القرآن (الترتيب الأصلي):    p = {p_quran:.4f}  {'✅ دال' if p_quran<0.05 else '✗'}")
    print(f"  القرآن (مُخلَّط):           p = {p_shuffled:.4f}  {'✅ دال' if p_shuffled<0.05 else '✗'}")
    if p_bukhari is not None:
        print(f"  البخاري (بأطوال القرآن):   p = {p_bukhari:.4f}  {'✅ دال' if p_bukhari<0.05 else '✗'}")

    print()
    if p_quran < 0.05 and p_shuffled >= 0.05 and (p_bukhari is None or p_bukhari >= 0.05):
        print("→ البصمة في الترتيب الأصلي للكلمات — لا في مجرد التقسيم")
        print("  الكلمات نفسها تحمل البصمة بترتيبها الذي نزل")
    elif p_quran < 0.05 and p_bukhari is not None and p_bukhari < 0.05:
        print("→ البصمة في التقسيم (الهندسة المعمارية)")
        print("  أي نص مقسَّم بهذه الأطوال يُعطي نفس النتيجة")
    else:
        print("→ النتيجة مركّبة — تحتاج تحليلاً أعمق")

    return {
        "quran_original": {"obs": obs_quran, "p": p_quran},
        "quran_shuffled": {"obs": obs_shuffled, "p": p_shuffled},
        "bukhari_quran_sizes": {"p": p_bukhari}
    }


if __name__ == "__main__":
    run()
