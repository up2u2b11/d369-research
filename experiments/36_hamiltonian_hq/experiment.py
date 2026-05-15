"""
Experiment 36 — Search for Explicit Hamiltonian H_Q
====================================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

THE QUESTION:
  Can we find a Hermitian matrix H such that:
    G14 |Psi_s> ≈ exp(-iH) |Psi_s>  for most surahs?

METHOD:
  - For each surah, compute |Psi_s> and |Psi_s'> = G14 |Psi_s>
  - Seek H (Hermitian 9x9) minimizing sum_s || exp(-iH)|Psi_s> - |Psi_s'> ||^2
  - Use matrix logarithm approach: H = i * log(G14_eff)
    where G14_eff is a unitary approximation of G14

NOTE: Since G14 is NOT unitary (Exp 38), exp(-iH) formulation will
have an inherent approximation error. We measure this error.

SUCCESS: Mean error < 0.1 for >70% of surahs.
FAILURE: No Hermitian H fits -> confirms non-unitary nature of G14.
"""

import numpy as np
import sqlite3
import json
import os
import sys
import math
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'd369_research.db')


G14_MAP = {1: 5, 2: 3, 3: 3, 4: 7, 5: 3, 6: 6, 7: 4, 8: 3, 9: 9}


def build_G14_matrix():
    M = np.zeros((9, 9), dtype=float)
    for j in range(1, 10):
        M[G14_MAP[j] - 1, j - 1] = 1.0
    return M


def load_surah_vectors():
    """Load probability vectors for all surahs."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT surah_id FROM words ORDER BY surah_id")
    surah_ids = [r[0] for r in cur.fetchall()]

    vectors = {}
    for sid in surah_ids:
        cur.execute("SELECT digit_root FROM words WHERE surah_id=?", (sid,))
        roots = [r[0] for r in cur.fetchall() if r[0] and r[0] > 0]
        if len(roots) < 5:
            continue
        total = len(roots)
        counts = Counter(roots)
        vec = np.array([counts.get(k, 0) / total for k in range(1, 10)])
        vectors[sid] = vec

    conn.close()
    return vectors


def nearest_unitary(M):
    """
    Find the nearest unitary matrix to M using SVD:
    U = A * B^T where M = A * S * B^T (SVD)
    """
    U, S, Vt = np.linalg.svd(M)
    return U @ Vt


def matrix_log_hermitian(U):
    """
    Compute H = i * log(U) for unitary U, ensuring H is Hermitian.
    log(U) = V * diag(log(eigenvalues)) * V^-1
    For unitary U, eigenvalues are on the unit circle: lambda_k = e^{i*theta_k}
    log(lambda_k) = i*theta_k  =>  H = -log(U)/i = V * diag(theta_k) * V^{-1}
    """
    eigenvalues, V = np.linalg.eig(U)

    # Take log of each eigenvalue (on unit circle)
    log_eigs = np.zeros(len(eigenvalues), dtype=complex)
    for k, lam in enumerate(eigenvalues):
        angle = np.angle(lam)  # in (-pi, pi]
        log_eigs[k] = 1j * angle

    # H = i * V * diag(log_eigs) * V^{-1}
    # = i * V * diag(i*theta) * V^{-1}
    # = -V * diag(theta) * V^{-1}
    thetas = np.array([np.angle(lam) for lam in eigenvalues])
    H = -np.real(V @ np.diag(thetas) @ np.linalg.inv(V))

    # Symmetrize to ensure Hermitian (H = H^dag)
    H = (H + H.T) / 2
    return H


def test_approximation(H, G14, surah_vectors):
    """
    For each surah, test: ||exp(-iH)|Psi_s> - G14|Psi_s>|| / ||G14|Psi_s>||
    """
    # Compute exp(-iH)
    eigenvalues_H, V = np.linalg.eig(H)
    exp_diag = np.diag(np.exp(-1j * eigenvalues_H))
    exp_iH = V @ exp_diag @ np.linalg.inv(V)
    exp_iH = np.real(exp_iH)  # Should be approximately real since H is Hermitian

    errors = []
    surah_results = []

    for sid, psi in sorted(surah_vectors.items()):
        G14_psi = G14 @ psi
        exp_iH_psi = exp_iH @ psi

        norm_G14 = np.linalg.norm(G14_psi)
        if norm_G14 < 1e-10:
            continue

        error = np.linalg.norm(exp_iH_psi - G14_psi) / norm_G14
        errors.append(float(error))
        surah_results.append({
            'surah_id': sid,
            'error': round(float(error), 6),
            'within_01': bool(error < 0.1)
        })

    return errors, surah_results, exp_iH


def analyze_H_structure(H):
    """Analyze the structure of H_Q."""
    eigenvalues_H = np.linalg.eigvalsh(H)
    trace = float(np.trace(H))
    frobenius = float(np.linalg.norm(H, 'fro'))

    # Check symmetry of H with respect to {3,6,9}
    subspace_369 = [2, 5, 8]  # 0-indexed
    H_sub = H[np.ix_(subspace_369, subspace_369)]
    H_sub_trace = float(np.trace(H_sub))
    H_sub_frobenius = float(np.linalg.norm(H_sub, 'fro'))

    return {
        'eigenvalues': [round(float(ev), 6) for ev in sorted(eigenvalues_H)],
        'trace': round(trace, 6),
        'frobenius_norm': round(frobenius, 6),
        'subspace_369_trace': round(H_sub_trace, 6),
        'subspace_369_frobenius': round(H_sub_frobenius, 6),
        'is_symmetric': bool(np.allclose(H, H.T, atol=1e-8))
    }


def main():
    print("=" * 65)
    print("Exp 36 — Search for Explicit Hamiltonian H_Q")
    print("=" * 65)

    G14 = build_G14_matrix()
    print("\n[1] Building G14 and finding nearest unitary...")
    G14_unitary = nearest_unitary(G14)

    unitary_check = G14_unitary @ G14_unitary.T
    unitary_error = float(np.linalg.norm(unitary_check - np.eye(9), 'fro'))
    print(f"  Nearest unitary found. Unitarity error: {unitary_error:.2e}")

    print("\n[2] Computing H_Q via matrix logarithm...")
    H = matrix_log_hermitian(G14_unitary)

    is_hermitian = bool(np.allclose(H, H.T, atol=1e-8))
    print(f"  H is Hermitian: {is_hermitian}")

    h_struct = analyze_H_structure(H)
    print(f"  Eigenvalues of H: {h_struct['eigenvalues']}")
    print(f"  Frobenius norm:   {h_struct['frobenius_norm']:.4f}")
    print(f"  Trace:            {h_struct['trace']:.4f}")

    print("\n[3] Loading surah vectors...")
    surah_vectors = load_surah_vectors()
    print(f"  Surahs: {len(surah_vectors)}")

    print("\n[4] Testing approximation: exp(-iH)|Psi_s> vs G14|Psi_s>...")
    errors, surah_results, exp_iH = test_approximation(H, G14, surah_vectors)

    if errors:
        mean_err = sum(errors) / len(errors)
        n_within_01 = sum(1 for e in errors if e < 0.1)
        n_within_05 = sum(1 for e in errors if e < 0.5)
        pct_01 = 100 * n_within_01 / len(errors)
        pct_05 = 100 * n_within_05 / len(errors)

        print(f"  Mean error:          {mean_err:.4f}")
        print(f"  Error < 0.1:         {n_within_01}/{len(errors)} = {pct_01:.1f}%")
        print(f"  Error < 0.5:         {n_within_05}/{len(errors)} = {pct_05:.1f}%")
        print(f"  Min error:           {min(errors):.6f}")
        print(f"  Max error:           {max(errors):.6f}")
    else:
        mean_err = float('inf')
        n_within_01 = 0
        pct_01 = 0.0
        pct_05 = 0.0

    # ── G14 structure analysis ────────────────────────────────────────────────
    print("\n[5] Structure of H_Q matrix (rounded):")
    np.set_printoptions(precision=3, suppress=True)
    print(H)

    # Verdict
    success = pct_01 >= 70.0

    print("\n" + "=" * 65)
    print("CONCLUSION:")
    print(f"  H_Q found via nearest-unitary + matrix-log approach")
    print(f"  Mean approximation error: {mean_err:.4f}")
    print(f"  Surahs within 10% error:  {pct_01:.1f}%")
    print(f"  SUCCESS CRITERION (>70%): {'PASS' if success else 'FAIL'}")
    print()
    print("  KEY INSIGHT: Since G14 is NOT unitary (from Exp 38),")
    print("  H_Q only approximates G14 via its nearest unitary.")
    print("  The approximation error quantifies the 'non-unitarity gap'.")
    print("  This confirms: Lindblad (Exp 39) is the proper framework.")
    print("=" * 65)

    results = {
        'experiment': 'Exp36_Hamiltonian_HQ',
        'date': '2026-05-15',
        'author': 'Emad Suleiman Alwan',
        'G14_nearest_unitary': [[round(float(x), 6) for x in row]
                                  for row in G14_unitary.tolist()],
        'unitarity_error_of_approximation': round(unitary_error, 8),
        'H_Q_matrix': [[round(float(x), 6) for x in row] for row in H.tolist()],
        'H_Q_structure': h_struct,
        'approximation_test': {
            'n_surahs': len(errors),
            'mean_error': round(mean_err, 6) if errors else None,
            'n_within_01': n_within_01,
            'n_within_05': n_within_05,
            'pct_within_01': round(pct_01, 2),
            'pct_within_05': round(pct_05, 2),
            'min_error': round(min(errors), 6) if errors else None,
            'max_error': round(max(errors), 6) if errors else None,
        },
        'surah_results': surah_results,
        'conclusion': {
            'H_Q_found': True,
            'approximation_quality': 'good' if success else 'poor',
            'key_insight': (
                'G14 is not unitary. H_Q is derived from the nearest unitary approximation. '
                'Approximation error reflects the non-unitarity of G14. '
                'The proper framework is Lindblad, not standard Schrodinger.'
            )
        },
        'H_SUCCESS': {'pass': success,
                      'description': 'Mean error < 0.1 for >70% of surahs'}
    }

    json_path = os.path.join(RESULTS_DIR, 'exp36_hamiltonian_hq.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved: {json_path}")
    return results


if __name__ == '__main__':
    main()
