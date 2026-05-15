"""
Experiment 33 — Spectral Analysis of G14 (Schrodinger Framework)
=================================================================
Date: May 15, 2026
Author: Emad Suleiman Alwan (ORCID: 0009-0004-5797-6140)
Phase: Internal Research — NO PUBLICATION

THE QUESTION:
  Does G14 have exactly 3 eigenstates with eigenvalue=1,
  and are they exactly {|3>, |6>, |9>}?

G14 MAP:
  G(1)=5, G(2)=3, G(3)=3, G(4)=7
  G(5)=3, G(6)=6, G(7)=4, G(8)=3, G(9)=9

HYPOTHESES:
  H1: G14 has exactly 3 eigenstates with eigenvalue=1 -> {|3>,|6>,|9>}
  H2: These form a closed invariant subspace

SUCCESS: Exactly 3 eigenvalues=1, corresponding to basis vectors |3>,|6>,|9>
FAILURE: eigenvalue=1 appears outside {3,6,9}, or not all of {3,6,9} are eigenstates=1
"""

import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared'))

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

# G14 map: digit -> digit
G14_MAP = {1: 5, 2: 3, 3: 3, 4: 7, 5: 3, 6: 6, 7: 4, 8: 3, 9: 9}


def build_G14_matrix():
    """
    Build G14 as a 9x9 linear operator on C^9.
    M[i,j] = 1 if G(j+1) = i+1  (0-indexed)
    Action: M|j> = |G(j)>
    """
    M = np.zeros((9, 9), dtype=float)
    for j in range(1, 10):
        gi = G14_MAP[j]
        M[gi - 1, j - 1] = 1.0
    return M


def find_eigenvalue_1_states(eigenvalues, eigenvectors, tol=1e-8):
    """Find eigenstates with eigenvalue = 1."""
    fixed = []
    for i, ev in enumerate(eigenvalues):
        if abs(ev - 1.0) < tol:
            vec = eigenvectors[:, i]
            dominant = int(np.argmax(np.abs(vec))) + 1  # 1-indexed
            fixed.append({
                'index': i,
                'eigenvalue_real': float(np.real(ev)),
                'eigenvalue_imag': float(np.imag(ev)),
                'dominant_basis_state': dominant,
                'eigenvector_real': [float(x) for x in vec.real],
                'eigenvector_imag': [float(x) for x in vec.imag],
                'norm': float(np.linalg.norm(vec))
            })
    return fixed


def verify_basis_vectors_directly(M):
    """Direct verification: is M|k> = |k> for k in {3,6,9} and not for others?"""
    results = {}
    for k in range(1, 10):
        e_k = np.zeros(9)
        e_k[k - 1] = 1.0
        result = M @ e_k
        is_fixed = bool(np.allclose(result, e_k, atol=1e-10))
        maps_to = int(np.argmax(result)) + 1 if np.max(result) > 1e-10 else None
        results[k] = {
            'is_eigenstate_1': is_fixed,
            'maps_to': maps_to,
            'result_vector': [float(x) for x in result]
        }
    return results


def analyze_subspace_closure(M):
    """
    H2: Does {|3>,|6>,|9>} form a closed invariant subspace?
    Condition: M * span({|3>,|6>,|9>}) subseteq span({|3>,|6>,|9>})
    Equivalently: P * M * P = M * P  where P = projector onto {3,6,9}
    """
    subspace_idx = [2, 5, 8]  # 0-indexed: states 3,6,9
    P = np.zeros((9, 9))
    for i in subspace_idx:
        P[i, i] = 1.0

    MP = M @ P
    PMP = P @ M @ P
    is_closed = bool(np.allclose(MP, PMP, atol=1e-10))

    # Verify each subspace basis vector maps within subspace
    closure_details = {}
    for k in [3, 6, 9]:
        e_k = np.zeros(9); e_k[k-1] = 1.0
        result = M @ e_k
        # Is result in span of {3,6,9}?
        outside_component = np.sum(np.abs(result[[0,1,3,4,6,7]]))
        closure_details[k] = {
            'stays_in_subspace': bool(outside_component < 1e-10),
            'result': [float(x) for x in result]
        }

    return {
        'is_invariant_subspace': is_closed,
        'closure_per_state': closure_details
    }


def analyze_cycle_4_7(M):
    """Analyze the 2-cycle 4->7->4."""
    e4 = np.zeros(9); e4[3] = 1.0
    e7 = np.zeros(9); e7[6] = 1.0

    v_plus  = (e4 + e7) / np.sqrt(2)   # should have eigenvalue +1
    v_minus = (e4 - e7) / np.sqrt(2)   # should have eigenvalue -1

    Mv_plus  = M @ v_plus
    Mv_minus = M @ v_minus

    ev_plus  = float(np.dot(v_plus, Mv_plus))
    ev_minus = float(np.dot(v_minus, Mv_minus))

    return {
        'cycle': '4->7->4',
        'v_plus_eigenvalue':       ev_plus,
        'v_minus_eigenvalue':      ev_minus,
        'v_plus_is_eigenstate_1':  bool(np.allclose(Mv_plus,  v_plus,  atol=1e-10)),
        'v_minus_is_eigenstate_n1': bool(np.allclose(Mv_minus, -v_minus, atol=1e-10))
    }


def analyze_collapse_chain(M):
    """Trace the collapse chains: 1->5->3, 2->3, 8->3."""
    chains = {}
    for start in [1, 2, 8]:
        chain = [start]
        current = start
        for _ in range(5):
            nxt = G14_MAP[current]
            chain.append(nxt)
            if nxt == current or nxt in [3, 6, 9]:
                break
            current = nxt
        chains[start] = chain
    return chains


def main():
    print("=" * 65)
    print("Exp 33 — Spectral Analysis of G14")
    print("Schrodinger Framework Investigation")
    print("=" * 65)

    M = build_G14_matrix()

    print("\n[1] G14 Matrix (9x9):")
    print(M.astype(int))

    print("\n[2] Full Eigenspectrum:")
    eigenvalues, eigenvectors = np.linalg.eig(M)
    for i, ev in enumerate(eigenvalues):
        marker = " <-- eigenvalue=1" if abs(ev - 1.0) < 1e-8 else \
                 " <-- eigenvalue=-1" if abs(ev + 1.0) < 1e-8 else ""
        print(f"  lambda_{i+1:02d} = {ev.real:+.6f} {ev.imag:+.6f}i{marker}")

    fixed_states = find_eigenvalue_1_states(eigenvalues, eigenvectors)
    count_ev1 = len(fixed_states)
    fixed_dominant = [fp['dominant_basis_state'] for fp in fixed_states]
    print(f"\n[3] States with eigenvalue=1: {count_ev1}")
    for fp in fixed_states:
        print(f"  Dominant basis state: |{fp['dominant_basis_state']}>")

    print("\n[4] Direct verification of all 9 basis states:")
    direct = verify_basis_vectors_directly(M)
    for k in range(1, 10):
        v = direct[k]
        if v['is_eigenstate_1']:
            print(f"  M|{k}> = |{k}>  FIXED POINT (eigenvalue=1)")
        else:
            print(f"  M|{k}> = |{v['maps_to']}>  (not fixed)")

    subspace = analyze_subspace_closure(M)
    print(f"\n[5] H2 — Invariant subspace {{3,6,9}}: "
          f"{'CLOSED' if subspace['is_invariant_subspace'] else 'NOT CLOSED'}")
    for k, detail in subspace['closure_per_state'].items():
        print(f"  |{k}> maps within subspace: {detail['stays_in_subspace']}")

    cycle = analyze_cycle_4_7(M)
    print(f"\n[6] Cycle 4->7->4 analysis:")
    print(f"  (|4>+|7>)/sqrt(2): eigenvalue = {cycle['v_plus_eigenvalue']:+.4f}  "
          f"{'[eigenstate=+1]' if cycle['v_plus_is_eigenstate_1'] else ''}")
    print(f"  (|4>-|7>)/sqrt(2): eigenvalue = {cycle['v_minus_eigenvalue']:+.4f}  "
          f"{'[eigenstate=-1]' if cycle['v_minus_is_eigenstate_n1'] else ''}")

    chains = analyze_collapse_chain(M)
    print(f"\n[7] Collapse chains to attractor {{3,6,9}}:")
    for start, chain in chains.items():
        print(f"  |{start}> -> {' -> '.join(str(x) for x in chain)}")

    # ─── Evaluate hypotheses ─────────────────────────────────────────────────
    H1_pass = (count_ev1 == 3) and (set(fixed_dominant) == {3, 6, 9})
    H2_pass = subspace['is_invariant_subspace']

    # Count eigenvalues by rounded value
    ev_counts = {}
    for ev in eigenvalues:
        key = round(float(np.real(ev)), 4)
        ev_counts[key] = ev_counts.get(key, 0) + 1

    print("\n" + "=" * 65)
    print("RESULTS:")
    print(f"  Eigenvalue distribution: {dict(sorted(ev_counts.items()))}")
    print(f"  H1 (exactly 3 eigenvalues=1 -> {{3,6,9}}): {'PASS' if H1_pass else 'FAIL'}")
    print(f"  H2 ({{3,6,9}} is invariant subspace):       {'PASS' if H2_pass else 'FAIL'}")
    verdict = 'ACCEPT' if (H1_pass and H2_pass) else \
              'PARTIAL' if (H1_pass or H2_pass) else 'REJECT'
    print(f"  VERDICT: {verdict}")
    print("=" * 65)

    # ─── Save results ────────────────────────────────────────────────────────
    results = {
        'experiment': 'Exp33_SchrodingerSpectrum_G14',
        'date': '2026-05-15',
        'author': 'Emad Suleiman Alwan',
        'G14_map': {str(k): v for k, v in G14_MAP.items()},
        'G14_matrix': [[int(x) for x in row] for row in M.tolist()],
        'eigenspectrum': [
            {'real': float(np.real(ev)), 'imag': float(np.imag(ev))}
            for ev in eigenvalues
        ],
        'eigenvalue_distribution': {str(k): v for k, v in ev_counts.items()},
        'eigenvalue_1_count': count_ev1,
        'eigenvalue_1_states': fixed_states,
        'dominant_fixed_states': fixed_dominant,
        'direct_basis_verification': {str(k): v for k, v in direct.items()},
        'subspace_closure': subspace,
        'cycle_4_7': cycle,
        'collapse_chains': {str(k): v for k, v in chains.items()},
        'H1': {'pass': H1_pass,
               'description': 'G14 has exactly 3 eigenvalues=1 corresponding to {3,6,9}'},
        'H2': {'pass': H2_pass,
               'description': '{3,6,9} forms a closed invariant subspace under G14'},
        'verdict': verdict
    }

    out_path = os.path.join(RESULTS_DIR, 'exp33_spectrum.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved: {out_path}")
    return results


if __name__ == '__main__':
    main()
