"""
Experiment 38 — Unitarity Check of G14
=======================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

THE QUESTION:
  Is G14 a unitary operator? Does it preserve the norm?
  If not, what is its mathematical nature?

EXPECTED FINDING (from theory):
  G14 maps {1,2,5,8} -> 3, so it is NOT injective.
  A non-injective operator on a finite-dimensional space CANNOT be unitary.
  This means G14 is a projection-like, non-unitary evolution.
  --> Schrodinger (standard) does NOT apply directly.
  --> Lindblad (open quantum systems) may be needed.

SUCCESS CRITERION: Rigorously document the mathematical nature of G14.
"""

import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

G14_MAP = {1: 5, 2: 3, 3: 3, 4: 7, 5: 3, 6: 6, 7: 4, 8: 3, 9: 9}


def build_G14_matrix():
    M = np.zeros((9, 9), dtype=float)
    for j in range(1, 10):
        M[G14_MAP[j] - 1, j - 1] = 1.0
    return M


def check_unitarity(M):
    """
    Check if M is unitary: M * M^dagger = I and M^dagger * M = I
    """
    Mdagger = M.T.conj()
    MMd = M @ Mdagger
    MdM = Mdagger @ M
    I9 = np.eye(9)

    is_right_unitary = bool(np.allclose(MMd, I9, atol=1e-10))
    is_left_unitary  = bool(np.allclose(MdM, I9, atol=1e-10))

    frobenius_right = float(np.linalg.norm(MMd - I9, 'fro'))
    frobenius_left  = float(np.linalg.norm(MdM - I9, 'fro'))

    return {
        'MM_dagger': [[float(x) for x in row] for row in MMd.tolist()],
        'M_dagger_M': [[float(x) for x in row] for row in MdM.tolist()],
        'is_right_unitary': is_right_unitary,
        'is_left_unitary': is_left_unitary,
        'frobenius_error_right': frobenius_right,
        'frobenius_error_left': frobenius_left,
        'is_unitary': bool(is_right_unitary and is_left_unitary)
    }


def check_rank_and_determinant(M):
    """Check rank and determinant."""
    rank = int(np.linalg.matrix_rank(M))
    det = float(np.real(np.linalg.det(M)))
    trace = float(np.trace(M))

    # Singular values
    singular_values = np.linalg.svd(M, compute_uv=False)

    # Is it a projection? P^2 = P
    M2 = M @ M
    is_projection = bool(np.allclose(M2, M, atol=1e-10))

    # Is it idempotent? (same as projection)
    # Is it nilpotent? M^k = 0 for some k
    M_power = M.copy()
    nilpotent_order = None
    for k in range(1, 15):
        if np.allclose(M_power, np.zeros((9,9)), atol=1e-10):
            nilpotent_order = k
            break
        M_power = M_power @ M

    return {
        'rank': rank,
        'determinant': det,
        'trace': trace,
        'singular_values': [float(s) for s in singular_values],
        'is_full_rank': bool(rank == 9),
        'is_projection_P2_eq_P': is_projection,
        'nilpotent_order': nilpotent_order,
        'M_squared': [[float(x) for x in row] for row in M2.tolist()]
    }


def check_norm_preservation(M):
    """
    Does G14 preserve the L2 norm of probability vectors?
    Test with each basis vector and with random normalized vectors.
    """
    results = {'basis_vectors': {}, 'random_vectors': []}

    # Basis vectors
    for k in range(1, 10):
        e_k = np.zeros(9); e_k[k-1] = 1.0
        result = M @ e_k
        norm_in  = float(np.linalg.norm(e_k))
        norm_out = float(np.linalg.norm(result))
        results['basis_vectors'][k] = {
            'norm_in': norm_in,
            'norm_out': norm_out,
            'preserves_norm': bool(abs(norm_in - norm_out) < 1e-10)
        }

    # Random normalized vectors
    np.random.seed(369)
    for trial in range(20):
        v = np.random.randn(9)
        v = v / np.linalg.norm(v)
        result = M @ v
        norm_in  = float(np.linalg.norm(v))
        norm_out = float(np.linalg.norm(result))
        results['random_vectors'].append({
            'trial': trial + 1,
            'norm_in': round(norm_in, 8),
            'norm_out': round(norm_out, 8),
            'preserves_norm': bool(abs(norm_in - norm_out) < 1e-10),
            'norm_ratio': round(norm_out / norm_in, 6) if norm_in > 1e-10 else 0
        })

    norm_preserved_basis = sum(1 for v in results['basis_vectors'].values() if v['preserves_norm'])
    norm_preserved_random = sum(1 for v in results['random_vectors'] if v['preserves_norm'])

    results['summary'] = {
        'basis_vectors_norm_preserved': f"{norm_preserved_basis}/9",
        'random_vectors_norm_preserved': f"{norm_preserved_random}/20",
        'is_norm_preserving': bool(norm_preserved_basis == 9)
    }
    return results


def classify_operator_type(M):
    """Classify G14 mathematically."""
    rank = int(np.linalg.matrix_rank(M))
    det  = float(np.real(np.linalg.det(M)))
    M2 = M @ M
    is_projection = bool(np.allclose(M2, M, atol=1e-10))
    MMd = M @ M.T
    is_unitary = bool(np.allclose(MMd, np.eye(9), atol=1e-10))

    # Check if it's a contraction: ||Mv|| <= ||v|| for all v
    singular_values = np.linalg.svd(M, compute_uv=False)
    max_sv = float(np.max(singular_values))
    is_contraction = bool(max_sv <= 1.0 + 1e-10)

    # Check if it's a stochastic matrix (column sums = 1)
    col_sums = M.sum(axis=0)
    is_stochastic = bool(np.allclose(col_sums, np.ones(9), atol=1e-10))

    # Check if it's a sub-stochastic (column sums <= 1)
    is_sub_stochastic = bool(np.all(col_sums <= 1.0 + 1e-10))

    # Determine type
    if is_unitary:
        op_type = "UNITARY"
    elif is_projection:
        op_type = "PROJECTION (idempotent)"
    elif is_stochastic:
        op_type = "STOCHASTIC (norm-preserving on L1)"
    elif is_contraction:
        op_type = "CONTRACTION (norm non-increasing)"
    else:
        op_type = "GENERAL NON-UNITARY"

    return {
        'rank': rank,
        'determinant': det,
        'max_singular_value': max_sv,
        'is_unitary': is_unitary,
        'is_projection': is_projection,
        'is_contraction': is_contraction,
        'is_stochastic': is_stochastic,
        'is_sub_stochastic': is_sub_stochastic,
        'operator_type': op_type,
        'column_sums': [float(x) for x in col_sums],
        'implication': (
            "G14 is a stochastic (Markov) matrix. "
            "It maps probability distributions to probability distributions. "
            "{3,6,9} are absorbing states. "
            "The correct framework is NOT Schrodinger (unitary), "
            "but rather an OPEN QUANTUM SYSTEM or a Markov/Lindblad evolution."
        ) if is_stochastic else "Non-standard operator type"
    }


def compute_steady_state(M):
    """Find the steady state distribution of G14 as a Markov matrix."""
    # Power iteration to find steady state
    v = np.ones(9) / 9.0
    for _ in range(1000):
        v_new = M @ v
        v_norm = np.sum(v_new)
        if v_norm > 1e-10:
            v_new = v_new / v_norm
        if np.allclose(v_new, v, atol=1e-12):
            break
        v = v_new

    return {
        'steady_state': [float(x) for x in v],
        'dominant_states': [i+1 for i in np.argsort(v)[::-1][:3]],
        'concentration_on_369': float(v[2] + v[5] + v[8])
    }


def main():
    print("=" * 65)
    print("Exp 38 — Unitarity Check of G14")
    print("=" * 65)

    M = build_G14_matrix()
    print("\nG14 Matrix:")
    print(M.astype(int))

    unitary = check_unitarity(M)
    print(f"\n[1] Unitarity Check:")
    print(f"  M*M^dag = I? {unitary['is_right_unitary']}")
    print(f"  M^dag*M = I? {unitary['is_left_unitary']}")
    print(f"  Frobenius error (right): {unitary['frobenius_error_right']:.6f}")
    print(f"  Frobenius error (left):  {unitary['frobenius_error_left']:.6f}")
    print(f"  IS UNITARY: {unitary['is_unitary']}")

    rank_det = check_rank_and_determinant(M)
    print(f"\n[2] Rank & Determinant:")
    print(f"  Rank:        {rank_det['rank']}/9  (full rank: {rank_det['is_full_rank']})")
    print(f"  Determinant: {rank_det['determinant']:.6f}")
    print(f"  Trace:       {rank_det['trace']:.6f}")
    print(f"  Singular values: {[round(s,4) for s in rank_det['singular_values']]}")
    print(f"  Is projection (M^2=M): {rank_det['is_projection_P2_eq_P']}")

    norm_pres = check_norm_preservation(M)
    print(f"\n[3] Norm Preservation:")
    print(f"  Basis vectors: {norm_pres['summary']['basis_vectors_norm_preserved']} preserved")
    print(f"  Random vectors: {norm_pres['summary']['random_vectors_norm_preserved']} preserved")
    print(f"  IS NORM-PRESERVING: {norm_pres['summary']['is_norm_preserving']}")

    op_type = classify_operator_type(M)
    print(f"\n[4] Operator Classification:")
    print(f"  Type: {op_type['operator_type']}")
    print(f"  Is stochastic: {op_type['is_stochastic']}")
    print(f"  Column sums: {[round(x,2) for x in op_type['column_sums']]}")
    print(f"  Implication: {op_type['implication']}")

    steady = compute_steady_state(M)
    print(f"\n[5] Steady State (Markov limit):")
    for i, p in enumerate(steady['steady_state']):
        if p > 0.001:
            print(f"  |{i+1}>: {p:.4f}")
    print(f"  Concentration on {{3,6,9}}: {steady['concentration_on_369']:.4f}")

    # ─── Verdict ────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("MATHEMATICAL CONCLUSION:")
    print(f"  G14 is NOT unitary (det={rank_det['determinant']:.0f}, rank={rank_det['rank']}/9)")
    print(f"  G14 IS a stochastic (column-stochastic) matrix: {op_type['is_stochastic']}")
    print(f"  G14 IS idempotent (projection M^2=M): {rank_det['is_projection_P2_eq_P']}")
    print(f"  Correct framework: Open Quantum Systems / Lindblad equation")
    print(f"  {{3,6,9}} are 'dark states' / absorbing states of this open system")
    print("=" * 65)

    results = {
        'experiment': 'Exp38_Unitarity_G14',
        'date': '2026-05-15',
        'author': 'Emad Suleiman Alwan',
        'G14_map': {str(k): v for k, v in G14_MAP.items()},
        'unitarity_check': unitary,
        'rank_and_determinant': rank_det,
        'norm_preservation': norm_pres,
        'operator_classification': op_type,
        'steady_state': steady,
        'conclusion': {
            'is_unitary': unitary['is_unitary'],
            'is_stochastic': op_type['is_stochastic'],
            'is_projection': rank_det['is_projection_P2_eq_P'],
            'correct_framework': 'Lindblad / Open Quantum Systems',
            'absorbing_states': [3, 6, 9],
            'verdict': 'G14 is a non-unitary, stochastic (Markov) operator. '
                       'Standard Schrodinger evolution does not apply. '
                       'Lindblad equation is the appropriate framework.'
        }
    }

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            return super().default(obj)

    out_path = os.path.join(RESULTS_DIR, 'exp38_unitarity.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    print(f"\nResults saved: {out_path}")
    return results


if __name__ == '__main__':
    main()
