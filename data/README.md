# البيانات المستخدمة في التجارب

## d369_research.db

قاعدة بيانات SQLite تحتوي على جدول `words` — 78,248 كلمة قرآنية.

### الحقول

| الحقل | النوع | الوصف |
|-------|-------|-------|
| `word_id` | INTEGER | معرّف الكلمة |
| `surah_id` | INTEGER | رقم السورة (1-114) |
| `ayah_number` | INTEGER | رقم الآية |
| `word_position` | INTEGER | موضع الكلمة في الآية |
| `word_pos_in_quran` | INTEGER | موضع الكلمة في القرآن كاملاً |
| `text_uthmani` | TEXT | النص العثماني بالتشكيل |
| `text_clean` | TEXT | النص المُبسَّط |
| `jummal_value` | INTEGER | قيمة الجُمَّل الكبير (ة=5) |
| `digit_root` | INTEGER | الجذر الرقمي لقيمة الجُمَّل |
| `jummal_special_6` | TEXT | قيمة الحساب الخاص-6 |

### مثال

```python
import sqlite3
conn = sqlite3.connect("data/d369_research.db")
c = conn.cursor()

# أول 5 كلمات
c.execute("SELECT text_clean, jummal_value, jummal_special_6 FROM words LIMIT 5")
for row in c.fetchall():
    print(row)
```

---

## النصوص المقارنة

| الملف | المصدر | الحجم |
|-------|--------|-------|
| `quran_simple.txt` | القرآن الكريم — نص مبسط | ~1.3 MB |
| `bukhari_sample.txt` | صحيح البخاري — عيّنة | ~1.0 MB |
| `futuhat_v1.txt` | فتوحات ابن عربي — مج.1 | ~1.8 MB |
| `muallaqat.txt` | المعلقات السبع | ~7 KB |

### استخدام النصوص في التجارب

```python
import os
os.environ["D369_DB"]   = "data/d369_research.db"
os.environ["D369_DATA"] = "data/"
```
