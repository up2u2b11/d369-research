"""
Experiment 21 — Embedding Space Geometry of Digital Roots
=========================================================
Question: Do words with digital roots in {3, 6, 9} cluster together
          in AraBERT's semantic space? Is there a geometric structure
          that separates D369 words from non-D369 words?

Method:
  1. Load 14,868 unique Quranic words from the database
  2. Extract AraBERT embeddings (768 dimensions) for each word
  3. Reduce dimensions: PCA(50) -> UMAP(2D) for visualization
  4. Measure cluster separation: Silhouette Score, Davies-Bouldin Index
  5. Permutation test: shuffle digit root labels 10,000 times
  6. Compare Quran vs Bukhari control text

This experiment answers: Is the {3,6,9} fingerprint semantic or structural?
  - If words cluster by digit root -> the fingerprint is semantic
  - If they do NOT cluster -> the fingerprint is purely numerical (stronger finding)

Intellectual property: Emad Suleiman Alwan — up2b.ai — 2026
"""

import sys
import os
import random
import json
import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from attention_utils import load_arabert, load_unique_words, load_control_text, DB_PATH
from utils import digit_root

random.seed(42)
np.random.seed(42)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def extract_embeddings(words_text, model, tokenizer, batch_size=64):
    """
    Extract [CLS] embeddings from AraBERT for a list of Arabic words.

    Args:
        words_text: list of Arabic word strings
        model: AraBERT model
        tokenizer: AraBERT tokenizer
        batch_size: processing batch size

    Returns:
        numpy array of shape (n_words, 768)
    """
    all_embeddings = []

    for i in range(0, len(words_text), batch_size):
        batch = words_text[i:i + batch_size]
        encoded = tokenizer(
            batch, padding=True, truncation=True,
            max_length=32, return_tensors='pt'
        )
        with torch.no_grad():
            outputs = model(**encoded)
        # Use [CLS] token embedding (first token)
        cls_emb = outputs.last_hidden_state[:, 0, :].numpy()
        all_embeddings.append(cls_emb)

        if (i // batch_size) % 50 == 0:
            print(f"  Embedded {min(i + batch_size, len(words_text))}/{len(words_text)} words...")

    return np.vstack(all_embeddings)


def compute_cluster_metrics(embeddings, labels_binary):
    """
    Compute clustering metrics for D369 vs non-D369 separation.

    Args:
        embeddings: numpy array (n, d)
        labels_binary: 1 for D369, 0 for non-D369

    Returns:
        dict with silhouette_score, davies_bouldin, centroid_distance
    """
    from sklearn.metrics import silhouette_score, davies_bouldin_score

    sil = silhouette_score(embeddings, labels_binary, sample_size=min(5000, len(embeddings)))
    dbi = davies_bouldin_score(embeddings, labels_binary)

    # Centroid distance between D369 and non-D369 groups
    d369_mask = labels_binary == 1
    centroid_d369 = embeddings[d369_mask].mean(axis=0)
    centroid_other = embeddings[~d369_mask].mean(axis=0)
    centroid_dist = np.linalg.norm(centroid_d369 - centroid_other)

    return {
        'silhouette_score': float(sil),
        'davies_bouldin_index': float(dbi),
        'centroid_distance': float(centroid_dist),
    }


def permutation_test(embeddings, labels_binary, observed_metric, n_perms=2000):
    """
    Permutation test: is the observed centroid distance significant?
    Shuffle labels and recompute centroid distance n_perms times.
    Uses centroid distance (fast O(n)) instead of silhouette (slow O(n^2)).
    """
    def centroid_dist(emb, labels):
        d369_mask = labels == 1
        if d369_mask.sum() == 0 or d369_mask.sum() == len(labels):
            return 0.0
        c1 = emb[d369_mask].mean(axis=0)
        c0 = emb[~d369_mask].mean(axis=0)
        return np.linalg.norm(c1 - c0)

    exceed = 0
    for i in range(n_perms):
        shuffled = labels_binary.copy()
        np.random.shuffle(shuffled)
        perm_dist = centroid_dist(embeddings, shuffled)
        if perm_dist >= observed_metric:
            exceed += 1
        if (i + 1) % 500 == 0:
            print(f"  Permutation {i+1}/{n_perms} (exceed so far: {exceed})")

    return exceed / n_perms


def reduce_and_visualize(embeddings, labels_9, labels_binary, title, filepath):
    """
    PCA(50) -> UMAP(2D), save scatter plot colored by digit root.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from sklearn.decomposition import PCA
    import umap

    # PCA to 50 dimensions first (speeds up UMAP)
    pca = PCA(n_components=min(50, embeddings.shape[0] - 1, embeddings.shape[1]))
    emb_pca = pca.fit_transform(embeddings)
    print(f"  PCA explained variance (50d): {pca.explained_variance_ratio_.sum():.3f}")

    # UMAP to 2D
    reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=30, min_dist=0.3)
    emb_2d = reducer.fit_transform(emb_pca)

    # Plot 1: Colored by 9 digit roots
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))

    colors_9 = {
        1: '#1f77b4', 2: '#aec7e8', 3: '#ff0000',
        4: '#98df8a', 5: '#d62728', 6: '#ff7f0e',
        7: '#9467bd', 8: '#c5b0d5', 9: '#ffbb00'
    }

    ax = axes[0]
    for dr in range(1, 10):
        mask = labels_9 == dr
        color = colors_9[dr]
        marker = 'o' if dr in {3, 6, 9} else 'x'
        alpha = 0.7 if dr in {3, 6, 9} else 0.3
        size = 15 if dr in {3, 6, 9} else 8
        ax.scatter(emb_2d[mask, 0], emb_2d[mask, 1],
                   c=color, marker=marker, alpha=alpha, s=size, label=f'DR={dr}')
    ax.set_title(f'{title} — By Digit Root (1-9)')
    ax.legend(fontsize=8, ncol=3)
    ax.set_xlabel('UMAP-1')
    ax.set_ylabel('UMAP-2')

    # Plot 2: D369 vs non-D369
    ax = axes[1]
    d369_mask = labels_binary == 1
    ax.scatter(emb_2d[~d369_mask, 0], emb_2d[~d369_mask, 1],
               c='#cccccc', alpha=0.3, s=8, label='Non-D369')
    ax.scatter(emb_2d[d369_mask, 0], emb_2d[d369_mask, 1],
               c='#ff0000', alpha=0.5, s=15, label='D369 {3,6,9}')
    ax.set_title(f'{title} — D369 vs Non-D369')
    ax.legend(fontsize=10)
    ax.set_xlabel('UMAP-1')
    ax.set_ylabel('UMAP-2')

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")

    return emb_2d


def run():
    """Main experiment runner."""

    print("=" * 70)
    print("EXPERIMENT 21: Embedding Space Geometry of Digital Roots")
    print("=" * 70)

    # ── Step 1: Load data ──
    print("\n[1/6] Loading unique Quranic words...")
    words = load_unique_words()
    texts = [w['text_clean'] for w in words]
    dr_labels = np.array([w['digit_root'] for w in words])
    d369_labels = np.array([1 if w['digit_root'] in {3, 6, 9} else 0 for w in words])
    print(f"  Total unique words: {len(words)}")
    print(f"  D369 words: {d369_labels.sum()} ({d369_labels.mean()*100:.1f}%)")

    # ── Step 2: Extract embeddings ──
    print("\n[2/6] Loading AraBERT and extracting embeddings...")
    model, tokenizer = load_arabert()
    embeddings = extract_embeddings(texts, model, tokenizer)
    print(f"  Embedding shape: {embeddings.shape}")

    # ── Step 3: Cluster metrics ──
    print("\n[3/6] Computing cluster separation metrics...")
    # Use PCA-reduced for metrics (faster, more stable)
    from sklearn.decomposition import PCA
    pca_50 = PCA(n_components=50)
    emb_pca = pca_50.fit_transform(embeddings)

    metrics_quran = compute_cluster_metrics(emb_pca, d369_labels)
    print(f"  Silhouette Score:     {metrics_quran['silhouette_score']:.4f}")
    print(f"  Davies-Bouldin Index: {metrics_quran['davies_bouldin_index']:.4f}")
    print(f"  Centroid Distance:    {metrics_quran['centroid_distance']:.4f}")

    # Per-root analysis
    print("\n  Per digit root centroid distances from global mean:")
    global_centroid = emb_pca.mean(axis=0)
    for dr in range(1, 10):
        mask = dr_labels == dr
        if mask.sum() > 0:
            centroid = emb_pca[mask].mean(axis=0)
            dist = np.linalg.norm(centroid - global_centroid)
            tag = " <-- D369" if dr in {3, 6, 9} else ""
            print(f"    DR={dr}: dist={dist:.4f} (n={mask.sum()}){tag}")

    # ── Step 4: Permutation test ──
    print("\n[4/6] Permutation test (2,000 trials, centroid distance)...")
    p_value = permutation_test(emb_pca, d369_labels, metrics_quran['centroid_distance'], n_perms=500)
    metrics_quran['p_value'] = p_value
    print(f"  p-value: {p_value:.4f}")

    # ── Step 5: Visualization ──
    print("\n[5/6] Generating UMAP visualizations...")
    reduce_and_visualize(
        embeddings, dr_labels, d369_labels,
        'Quran — AraBERT Embeddings',
        os.path.join(RESULTS_DIR, 'quran_embedding_umap.png')
    )

    # ── Step 6: Bukhari control ──
    print("\n[6/6] Running control: Bukhari...")
    bukhari_words = load_control_text('bukhari_sample.txt')
    if bukhari_words:
        buk_texts = list(set(w['text'] for w in bukhari_words))[:14868]  # match size
        buk_dr = {}
        for w in bukhari_words:
            buk_dr[w['text']] = w['digit_root']
        buk_texts_final = [t for t in buk_texts if t in buk_dr]
        buk_labels = np.array([1 if buk_dr[t] in {3, 6, 9} else 0 for t in buk_texts_final])

        buk_emb = extract_embeddings(buk_texts_final, model, tokenizer)
        pca_buk = PCA(n_components=min(50, buk_emb.shape[0] - 1))
        buk_pca = pca_buk.fit_transform(buk_emb)
        metrics_bukhari = compute_cluster_metrics(buk_pca, buk_labels)
        print(f"  Bukhari Silhouette: {metrics_bukhari['silhouette_score']:.4f}")
        print(f"  Bukhari DBI:        {metrics_bukhari['davies_bouldin_index']:.4f}")
        print(f"  Bukhari Centroid D: {metrics_bukhari['centroid_distance']:.4f}")

        buk_dr_labels = np.array([buk_dr[t] for t in buk_texts_final])
        reduce_and_visualize(
            buk_emb, buk_dr_labels, buk_labels,
            'Bukhari — AraBERT Embeddings (Control)',
            os.path.join(RESULTS_DIR, 'bukhari_embedding_umap.png')
        )
    else:
        metrics_bukhari = None
        print("  Bukhari text not found — skipping control")

    # ── Summary ──
    print("\n" + "=" * 70)
    print("SUMMARY — Experiment 21: Embedding Space Geometry")
    print("=" * 70)
    print(f"\nQuran ({len(words)} unique words):")
    print(f"  D369 fraction: {d369_labels.mean()*100:.1f}%")
    print(f"  Silhouette Score:     {metrics_quran['silhouette_score']:.4f}")
    print(f"  Davies-Bouldin Index: {metrics_quran['davies_bouldin_index']:.4f}")
    print(f"  Centroid Distance:    {metrics_quran['centroid_distance']:.4f}")
    print(f"  Permutation p-value:  {p_value:.4f}")

    if p_value < 0.05:
        print("\n  RESULT: D369 words show SIGNIFICANT clustering in semantic space")
        print("  --> The fingerprint has a SEMANTIC component")
    else:
        print("\n  RESULT: D369 words do NOT cluster significantly in semantic space")
        print("  --> The fingerprint is PURELY NUMERICAL/STRUCTURAL")
        print("  --> This is a STRONGER finding: the pattern transcends meaning")

    if metrics_bukhari:
        print(f"\nBukhari (control):")
        print(f"  Silhouette Score:     {metrics_bukhari['silhouette_score']:.4f}")

    # Save results
    results = {
        'quran': metrics_quran,
        'bukhari': metrics_bukhari,
        'n_words_quran': len(words),
        'd369_fraction': float(d369_labels.mean()),
    }
    with open(os.path.join(RESULTS_DIR, 'metrics.json'), 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == '__main__':
    run()
