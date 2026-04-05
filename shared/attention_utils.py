"""
shared/attention_utils.py — Utilities for self-attention experiments (21-23)
============================================================================

Provides:
  - load_arabert()                  : Load AraBERT v2 model and tokenizer
  - word_to_subtoken_map()          : Map word indices to subtoken ranges
  - aggregate_subtoken_attention()  : Convert subtoken attention to word-level
  - load_quran_ayahs()              : Load ayahs with word metadata from DB
  - load_surah_sequences()          : Load per-surah digital root sequences
  - load_unique_words()             : Load unique words with digit roots
  - load_control_text()             : Load control text with digit roots

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sqlite3
import re
import os
import numpy as np
from collections import defaultdict

from utils import JUMMAL_5, KHASS_6, digit_root, word_value

# ──────────────────────────────────────────────────────────────
# Database paths
# ──────────────────────────────────────────────────────────────
DB_PATH = os.environ.get("D369_DB", "/home/emad/d369-quran-fingerprint/data/d369_research.db")
DATA_DIR = os.environ.get("D369_DATA", "/home/emad/d369-quran-fingerprint/data")


def load_arabert():
    """
    Load AraBERT v2 model and tokenizer.
    Returns: (model, tokenizer)
    """
    from transformers import AutoModel, AutoTokenizer
    model_name = "aubmindlab/bert-base-arabertv2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name, output_attentions=True)
    model.eval()
    return model, tokenizer


def word_to_subtoken_map(words, tokenizer):
    """
    Map word indices to subtoken index ranges in BERT tokenization.

    Args:
        words: list of Arabic words
        tokenizer: BERT tokenizer

    Returns:
        list of (start, end) tuples — subtoken index range for each word
        (indices are relative to the token sequence INCLUDING [CLS] and [SEP])
    """
    mapping = []
    current_pos = 1  # skip [CLS]

    for word in words:
        tokens = tokenizer.tokenize(word)
        n_tokens = len(tokens) if tokens else 1
        mapping.append((current_pos, current_pos + n_tokens))
        current_pos += n_tokens

    return mapping


def aggregate_subtoken_attention(attention, word_map, n_words):
    """
    Convert subtoken-level attention to word-level attention.

    Strategy: average rows (queries) and sum columns (keys) for subtokens
    belonging to the same word. This preserves attention mass.

    Args:
        attention: numpy array of shape (seq_len, seq_len) — one head's attention
        word_map: list of (start, end) tuples from word_to_subtoken_map
        n_words: number of words

    Returns:
        numpy array of shape (n_words, n_words) — word-level attention
    """
    word_attn = np.zeros((n_words, n_words), dtype=np.float32)

    for i, (si, ei) in enumerate(word_map):
        for j, (sj, ej) in enumerate(word_map):
            if si < attention.shape[0] and sj < attention.shape[1]:
                ei_c = min(ei, attention.shape[0])
                ej_c = min(ej, attention.shape[1])
                block = attention[si:ei_c, sj:ej_c]
                if block.size > 0:
                    word_attn[i, j] = block.mean()

    # Normalize rows to sum to 1
    row_sums = word_attn.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    word_attn = word_attn / row_sums

    return word_attn


def load_quran_ayahs(db_path=None):
    """
    Load all ayahs with word-level metadata.

    Returns: list of dicts, each containing:
        - surah_id, ayah_number
        - words: list of dicts with text_clean, digit_root, k6_value
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, ayah_number, text_clean, digit_root,
               CAST(jummal_special_6 AS INTEGER)
        FROM words
        ORDER BY surah_id, ayah_number, word_position
    """)
    rows = c.fetchall()
    conn.close()

    ayahs = []
    current_key = None
    current_ayah = None

    for surah_id, ayah_num, text, dr, k6 in rows:
        key = (surah_id, ayah_num)
        if key != current_key:
            if current_ayah is not None:
                ayahs.append(current_ayah)
            current_ayah = {
                'surah_id': surah_id,
                'ayah_number': ayah_num,
                'words': []
            }
            current_key = key
        current_ayah['words'].append({
            'text_clean': text,
            'digit_root': dr,
            'k6_value': k6
        })

    if current_ayah is not None:
        ayahs.append(current_ayah)

    return ayahs


def load_surah_sequences(db_path=None):
    """
    Load per-surah digital root sequences for custom attention experiments.

    Returns: list of 114 dicts with surah_id, digit_roots, k6_digit_roots,
             surah_total_dr, surah_total_k6_dr, is_d369_abjad, is_d369_k6
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT surah_id, jummal_value, CAST(jummal_special_6 AS INTEGER), digit_root
        FROM words
        ORDER BY surah_id, word_pos_in_quran
    """)
    rows = c.fetchall()
    conn.close()

    surah_data = defaultdict(lambda: {'abjad': [], 'k6': [], 'dr': []})
    for surah_id, jv, k6, dr in rows:
        surah_data[surah_id]['abjad'].append(jv)
        surah_data[surah_id]['k6'].append(k6)
        surah_data[surah_id]['dr'].append(dr)

    sequences = []
    for sid in sorted(surah_data.keys()):
        data = surah_data[sid]
        abjad_total = sum(data['abjad'])
        k6_total = sum(data['k6'])

        sequences.append({
            'surah_id': sid,
            'digit_roots': np.array(data['dr'], dtype=np.int32),
            'k6_digit_roots': np.array([digit_root(v) for v in data['k6']], dtype=np.int32),
            'surah_total_dr': digit_root(abjad_total),
            'surah_total_k6_dr': digit_root(k6_total),
            'is_d369_abjad': digit_root(abjad_total) in {3, 6, 9},
            'is_d369_k6': digit_root(k6_total) in {3, 6, 9},
        })

    return sequences


def load_unique_words(db_path=None):
    """
    Load unique words with their digit roots (for embedding experiments).

    Returns: list of dicts with text_clean, digit_root, k6_digit_root, count
    """
    if db_path is None:
        db_path = DB_PATH

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT text_clean, digit_root, CAST(jummal_special_6 AS INTEGER), COUNT(*)
        FROM words
        GROUP BY text_clean
        ORDER BY COUNT(*) DESC
    """)
    rows = c.fetchall()
    conn.close()

    return [
        {
            'text_clean': text,
            'digit_root': dr,
            'k6_digit_root': digit_root(k6),
            'count': count
        }
        for text, dr, k6, count in rows
    ]


def load_control_text(filename):
    """
    Load a control text file and compute word values and digit roots.

    Args:
        filename: name of the text file in DATA_DIR (e.g., 'bukhari_sample.txt')

    Returns: list of dicts with text, digit_root, k6_digit_root
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    diacritics = re.compile(
        r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]'
    )
    clean = diacritics.sub('', text)
    raw_words = clean.split()

    arabic_re = re.compile(r'^[\u0600-\u06FF]+$')
    words = []
    for w in raw_words:
        if arabic_re.match(w):
            jv = word_value(w, JUMMAL_5)
            k6v = word_value(w, KHASS_6)
            if jv > 0:
                words.append({
                    'text': w,
                    'digit_root': digit_root(jv),
                    'k6_digit_root': digit_root(k6v),
                })

    return words
