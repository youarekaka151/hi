#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Raw docstring: the run commands below contain Windows paths, so backslashes
# must survive verbatim rather than being read as escapes.
r"""
new_feature_selection_v20.py
============================
ELIMINATE PAST 50 AND KEEP THE BEST SET, NOT THE LAST ONE. Same search, same
scorer, same phases as v19. Two changes, both about where the search STOPS and
which set it RETURNS.

RUN COMMANDS
------------

  # ---- the v20 arm: run down to 10 features, return the best AUC seen ----
  python new_feature_selection_v20.py ^
      --ranking consensus --corr-agg quantile --corr-q 0.25 ^
      --ens-m 1 --stall-metric none --no-lookahead --tol 0.005 ^
      --genuine-scope enrolment+testing ^
      --min-features 10 --select-best auc ^
      --out features\v3_v2\selected_V20_BEST_AUC_CEILING_PROBE.json ^
      --curve-out reports\v20_auc_curve.csv

  # ---- evaluate the returned set ----
  python new_train_session_2.py ^
      --features features\v3_v2 ^
      --feature-list features\v3_v2\selected_V20_BEST_AUC_CEILING_PROBE.json ^
      --models models_ceiling_v20_best --plot-dir plots_ceiling_v20_best ^
      --calibrate-frr 0.05 --calibrate-method temporal

  # ---- then sweep the curve: evaluate EVERY recorded prefix, pick on DEPLOYED
  #      metrics rather than on selection AUC (this is the honest comparison) ----
  python new_feature_selection_v20.py --sweep-eval ^
      --curve features\v3_v2\selected_V20_BEST_AUC_CEILING_PROBE.json ^
      --features features\v3_v2 ^
      --sweep-out reports\v20_deployed_sweep.csv


WHY THIS FILE EXISTS
--------------------
The v19 CLEAN2 run stopped at 50 features and reported macro AUC 0.99969. Both
of those numbers are artefacts of the floor rather than findings, and the
elimination history proves it:

    n= 61  auc=0.99956
    n= 60  auc=0.99965
    n= 59  auc=0.99966
    n= 58  auc=0.99966
    n= 57  auc=0.99966
    n= 56  auc=0.99966
    n= 55  auc=0.99963
    n= 54  auc=0.99969   <-- PEAK
    n= 53  auc=0.99962
    n= 52  auc=0.99965
    n= 51  auc=0.99964
    n= 50  auc=0.99965   <-- what was RETURNED, because the floor is 50

Two separate problems, and this file fixes both.

PROBLEM 1 - THE FLOOR IS AN ARBITRARY BUDGET, NOT A STOPPING CRITERION.
    v4.MIN_FEATURES_KEPT = 50 (new_feature_selection_v4.py:270). The search is
    still removing features affordably when it hits it, so nothing below 50 was
    ever examined. "50 features" is the budget someone chose; it is not where
    the data says to stop. --min-features 10 lets the search run until the
    TOLERANCE stops it, which is a criterion the data controls.

PROBLEM 2 - BACKWARD ELIMINATION RETURNS THE LAST SET, NOT THE BEST ONE.
    v4_v3's loop accepts any removal within `tol` of the best AUC ever seen, so
    the returned set is merely the final one it could still afford - at n=50,
    AUC 0.99965 - while n=54 scored 0.99969 and was discarded on the way past.
    The acceptance rule guarantees "within tol of the peak", which is a weaker
    promise than "the peak".

    --select-best auc re-walks the recorded history and returns the set with the
    highest AUC. This costs nothing: the history already carries which feature
    was removed at every step, so the set at any n is reconstructible exactly by
    replaying the removals. No extra model fits.

WHAT --select-best DOES, PRECISELY
----------------------------------
    last    v19 behaviour: return the final set. The control arm.
    auc     return the set at the step with the highest macro AUC.
    gap     return the set at the step with the highest macro gap. The gap is
            median(genuine) - max(impostor) and is what AUC is blind to once
            saturated; at AUC ~0.9997 across 12 steps, the gap discriminates
            where AUC cannot.
    knee    the smallest set whose AUC is within --knee-tol of the peak. Prefers
            parsimony when the curve is flat, which it is here: 11 of the last
            12 steps sit inside 0.0001 of each other.

Ties go to the SMALLER set, on the principle that if two sets score the same the
one carrying fewer features is the better answer.

AND A WARNING ABOUT WHAT THIS CANNOT TELL YOU
---------------------------------------------
Picking the maximum of a noisy curve is itself a selection, and it is performed
on the same contaminated folds everything else here uses. AUC differences of
0.00004 - which is what separates n=54 from n=50 - are far below the resolution
of 8 users x ~16 genuine x ~74 impostor sessions. Treat the AUC-argmax as a
HINT, not a result.

That is why --curve-out and --sweep-eval exist. The curve records every (n, AUC,
gap, feature-set) the search passed through; the sweep then runs the real
evaluator over each recorded prefix and reports DEPLOYED EER/FAR/FRR per n. A
set chosen because its deployed EER is lowest is still optimistic (the probe saw
every impostor) but it is chosen on the quantity you actually care about rather
than on the fourth decimal of a saturated rank statistic.

Reference, from the v16 prefix sweep recorded in new_feature_selection_v17.py:

      k      TAR      FAR      EER
      5    0.8776   0.1363   0.1151
      8    0.8106   0.0791   0.1153
     12    0.7598   0.0666   0.1217
     30    0.7773   0.0514   0.0847
     50    0.7681   0.0559   0.0818

Deployed EER improved monotonically from 12 to 50 features there. If v20's
sweep shows the same shape, then going BELOW 50 will cost deployed performance
even where selection AUC improves, and the honest conclusion is that 50 was a
reasonable budget after all. If instead the sweep bottoms out near 43 - as was
seen in separate work - that is a real finding and the sweep is what establishes
it.

WHAT IS DELIBERATELY NOT CHANGED
--------------------------------
Everything else. Imported from v19/v18/v6, never copied:

    phase 0    load_enrolment                   (v4)
    phase 1    consensus_ranking                (prescreen_v3_device)
    phase 1a   load_all_attackers               (v4_v3)
    phase 1a2  load_test_genuine                (v19)
    phase 1b   build_folds_genuine              (v19)
    phase 2    correlation_clusters_robust       (v6)
    phase 3    stall_gated_eliminate            (v18)   <- unchanged search
    scorer     EnsembleScorer                   (v18)

The elimination loop itself is v18's, untouched. v20 changes only the floor it
is given and which entry of its returned history is then selected. So
--min-features 50 --select-best last reproduces v19 exactly, and that is the
control arm.

STILL A CEILING PROBE
---------------------
Unchanged. Under --genuine-scope enrolment+testing both axes are contaminated,
exactly as in v19; the JSON records genuine_contaminated. Every AUC, gap, EER
and FAR from this file is resubstitution. viable=false, deployable=false.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter

import numpy as np
import pandas as pd

import new_feature_selection_v4 as v4
from new_feature_selection_v4 import (
    MIN_USERS,
    VAL_FRAC,
    bucket_of,
    discover_users,
    load_enrolment,
    numeric_universe,
    pick_representatives,
    prescreen_v2,
    write_ranking,
)
from new_feature_selection_v4_v3 import PROTECTED_OUT, load_all_attackers
from new_feature_selection_v6 import (
    CORR_AGGREGATORS,
    DEFAULT_CORR_Q,
    DEFAULT_DISPERSION_MAX,
    correlation_audit,
    correlation_clusters_robust,
)
import new_feature_selection_v18 as v18
from new_feature_selection_v18 import (
    DEFAULT_ENS_FRAC,
    DEFAULT_ENS_M,
    DEFAULT_MAX_FLOATS,
    DEFAULT_STALL_TOL,
    DEFAULT_STALL_WINDOW,
    ENS_MODES,
    ENS_RULES,
    STALL_METRICS,
    EnsembleScorer,
    margins_ens,
    print_per_user,
    stall_gated_eliminate,
)
import new_feature_selection_v19 as v19
from new_feature_selection_v19 import (
    GENUINE_SCOPES,
    build_folds_genuine,
    load_test_genuine,
)
from new_feature_selection_v9 import DEFAULT_LOOKAHEAD_CAP, DEFAULT_LOOKAHEAD_K


# ============================== CONFIG ==============================

SELECT_BEST = ('last', 'auc', 'gap', 'knee')

# Default floor. 10 rather than v4's 50, because the whole point of this file is
# that 50 was never a stopping criterion. The tolerance stops the search before
# this in practice.
DEFAULT_MIN_FEATURES = 10

# --select-best knee: accept the smallest set whose AUC is within this of the
# peak. 1e-4 is chosen from the measured curve, where 11 of the last 12 steps
# sit inside 0.0001 of one another - so at this tolerance the knee rule will
# prefer the smallest of a genuinely indistinguishable group.
DEFAULT_KNEE_TOL = 1e-4


# ===================== REPLAY THE HISTORY =====================

def replay_history(start_feats, history):
    """
    The exact feature set at every recorded step, by replaying the removals.

    stall_gated_eliminate records, per accepted step, which feature(s) left
    ('removed', '|'-joined for a lookahead combination) or came back
    ('readmitted'). Replaying that from the starting set reconstructs each
    intermediate set exactly, with no extra model fits.

    Returns a list of dicts: {n, auc, gap, feats}. Raises nothing on a history
    entry it cannot interpret - it stops replaying and returns what it has, so a
    schema change downstream degrades to a shorter curve rather than a wrong one.
    """
    cur = list(start_feats)
    out = []
    for i, e in enumerate(history):
        if i > 0:
            rm = e.get('removed')
            ra = e.get('readmitted')
            if rm:
                for c in str(rm).split('|'):
                    if c in cur:
                        cur.remove(c)
                    else:
                        return out          # history and set disagree - stop
            if ra:
                if ra in cur:
                    return out
                cur.append(ra)
        if e.get('n') is not None and int(e['n']) != len(cur):
            return out                      # replay drifted - do not guess
        out.append({'n': len(cur), 'auc': float(e.get('auc', float('nan'))),
                    'gap': (float(e['stall_metric_value'])
                            if e.get('stall_metric_value') is not None
                            else float('nan')),
                    'mode': e.get('mode', ''),
                    'feats': list(cur)})
    return out


def choose(curve, how, knee_tol=DEFAULT_KNEE_TOL, verbose=True):
    """
    Pick one entry of the replayed curve.

    Ties break toward the SMALLER set: if two feature counts score the same, the
    smaller one is the better answer and the larger is carrying features that
    earned nothing.
    """
    ok = [c for c in curve if np.isfinite(c['auc'])]
    if not ok:
        return curve[-1], 'curve has no finite AUC - returning last'

    if how == 'last':
        return curve[-1], 'last set (v19 behaviour)'

    if how == 'auc':
        best = max(c['auc'] for c in ok)
        cand = [c for c in ok if c['auc'] >= best - 1e-12]
        pick = min(cand, key=lambda c: c['n'])
        return pick, f'highest macro AUC {best:.5f}'

    if how == 'gap':
        g = [c for c in ok if np.isfinite(c['gap'])]
        if not g:
            return curve[-1], 'no gap recorded (--stall-metric none) - last set'
        best = max(c['gap'] for c in g)
        cand = [c for c in g if c['gap'] >= best - 1e-12]
        pick = min(cand, key=lambda c: c['n'])
        return pick, f'highest macro gap {best:+.4f}'

    if how == 'knee':
        best = max(c['auc'] for c in ok)
        cand = [c for c in ok if c['auc'] >= best - knee_tol]
        pick = min(cand, key=lambda c: c['n'])
        return pick, (f'smallest set within {knee_tol} of peak AUC {best:.5f} '
                      f'({len(cand)} candidate(s))')

    raise ValueError(f'unknown --select-best {how!r}')


def print_curve(curve, pick_n=None, tail=28):
    print(f'  {"n":>4s} {"macroAUC":>9s} {"macroGAP":>9s}  mode')
    show = curve[-tail:] if len(curve) > tail else curve
    if len(curve) > tail:
        print(f'  ... {len(curve) - tail} earlier step(s) omitted')
    for c in show:
        mark = '  <== SELECTED' if pick_n is not None and c['n'] == pick_n else ''
        g = f'{c["gap"]:+9.4f}' if np.isfinite(c['gap']) else f'{"-":>9s}'
        print(f'  {c["n"]:4d} {c["auc"]:9.5f} {g}  {c["mode"]:<14s}{mark}')


# ===================== SWEEP: evaluate every n honestly =====================

def sweep_eval(curve_json, features_dir, out_csv=None, nu=0.05,
               target_frr=0.05, verbose=True):
    """
    Deployed EER/FAR/FRR for EVERY feature count on the recorded curve.

    This is the part that matters. Selection AUC at 0.9997 cannot distinguish
    n=50 from n=54, but deployed EER can, and deployed EER is the quantity the
    project is judged on. Each prefix is trained and scored exactly the way
    new_train_session_2.py does it - full enrolment fit, temporal threshold at
    target_frr, all impostor sessions - so the numbers are comparable to that
    script's output.

    Still resubstitution: every impostor session was visible during selection.
    This chooses a feature count on a contaminated metric; it does not make the
    metric honest.
    """
    from sklearn.svm import OneClassSVM
    from sklearn.preprocessing import StandardScaler
    from scipy.spatial.distance import pdist
    from new_feature_selection_v4 import normalise_label

    d = json.load(open(curve_json))
    curve = d.get('curve')
    if not curve:
        print('  this JSON has no "curve" block - rerun selection with v20')
        return None

    users = sorted({u for u in discover_users(features_dir)})
    cache = {}
    for u in users:
        tr = os.path.join(features_dir, f'{u}_training_sessions.csv')
        te = os.path.join(features_dir, f'{u}_testing_sessions.csv')
        if not (os.path.exists(tr) and os.path.exists(te)):
            continue
        TR = pd.read_csv(tr, low_memory=False)
        TE = pd.read_csv(te, low_memory=False)
        lc = next((c for c in ('test_type', 'session_label', 'label')
                   if c in TE.columns), None)
        if lc is None:
            continue
        lab = TE[lc].map(normalise_label)
        cache[u] = (TR, TE[lab == 'genuine'], TE[lab == 'impostor'])

    def gm(Z):
        dd = pdist(Z, 'sqeuclidean')
        dd = dd[dd > 0]
        return float(1.0 / np.median(dd)) if dd.size else 'scale'

    def fit_score(Xf, Xs):
        sc = StandardScaler().fit(Xf)
        Zf = sc.transform(Xf)
        m = OneClassSVM(kernel='rbf', nu=nu, gamma=gm(Zf)).fit(Zf)
        return m.decision_function(sc.transform(Xs))

    rows = []
    t0 = time.time()
    for j, c in enumerate(curve, 1):
        feats = c['feats']
        frr, far, eer = [], [], []
        for u, (TR, G, I) in cache.items():
            cols = [x for x in feats if x in TR.columns and x in G.columns
                    and x in I.columns]
            if len(cols) < 2 or len(G) == 0 or len(I) == 0:
                continue
            num = lambda df: (df[cols].apply(pd.to_numeric, errors='coerce')
                              .fillna(0.0).values)
            X = num(TR)
            sc = StandardScaler().fit(X)
            Z = sc.transform(X)
            m = OneClassSVM(kernel='rbf', nu=nu, gamma=gm(Z)).fit(Z)
            sg = m.decision_function(sc.transform(num(G)))
            si = m.decision_function(sc.transform(num(I)))
            pool, n = [], len(X)
            for fr in (0.60, 0.70, 0.80, 0.90):
                k = int(round(n * fr))
                if k < 4 or n - k < 1:
                    continue
                pool.extend(float(v) for v in fit_score(X[:k], X[k:]))
            if len(pool) < 3:
                continue
            pool = np.sort(pool)
            thr = float(pool[min(int(np.floor(target_frr * len(pool))),
                                 len(pool) - 1)])
            frr.append(float(np.mean(sg < thr)))
            far.append(float(np.mean(si >= thr)))
            allv = np.unique(np.concatenate([sg, si]))
            e = 1.0
            for t in allv:
                e = min(e, max(float(np.mean(sg < t)), float(np.mean(si >= t))))
            eer.append(e)
        if not frr:
            continue
        rows.append({'n': c['n'], 'selection_auc': c['auc'],
                     'selection_gap': c['gap'],
                     'deployed_macro_frr': float(np.mean(frr)),
                     'deployed_macro_far': float(np.mean(far)),
                     'deployed_macro_eer': float(np.mean(eer)),
                     'frr_plus_far': float(np.mean(frr) + np.mean(far))})
        if verbose and (j % 10 == 0 or j == len(curve)):
            el = time.time() - t0
            eta = (el / j) * (len(curve) - j)
            print(f'    swept {j}/{len(curve)} feature count(s)  '
                  f'({el:.0f}s elapsed, ~{eta / 60:.1f}m left)',
                  end='\r', flush=True)
    if verbose:
        print(' ' * 78, end='\r')

    df = pd.DataFrame(rows).sort_values('n')
    if out_csv:
        os.makedirs(os.path.dirname(out_csv) or '.', exist_ok=True)
        df.to_csv(out_csv, index=False)
        print(f'  deployed sweep -> {out_csv}')

    print()
    print('  DEPLOYED metrics by feature count  (resubstitution - all impostors '
          'were visible)')
    print(f'  {"n":>4s} {"selAUC":>9s} {"depEER":>9s} {"depFRR":>9s} '
          f'{"depFAR":>9s} {"FRR+FAR":>9s}')
    best_eer = df['deployed_macro_eer'].min() if len(df) else None
    best_sum = df['frr_plus_far'].min() if len(df) else None
    for _, r in df.iterrows():
        mk = ''
        if best_eer is not None and r['deployed_macro_eer'] <= best_eer + 1e-12:
            mk += '  <= best EER'
        if best_sum is not None and r['frr_plus_far'] <= best_sum + 1e-12:
            mk += '  <= best FRR+FAR'
        print(f'  {int(r["n"]):4d} {r["selection_auc"]:9.5f} '
              f'{r["deployed_macro_eer"]:9.4f} {r["deployed_macro_frr"]:9.4f} '
              f'{r["deployed_macro_far"]:9.4f} {r["frr_plus_far"]:9.4f}{mk}')
    if len(df):
        b = df.loc[df['deployed_macro_eer'].idxmin()]
        print()
        print(f'  LOWEST DEPLOYED EER at n={int(b["n"])}: '
              f'EER {b["deployed_macro_eer"]:.4f}, '
              f'FRR {b["deployed_macro_frr"]:.4f}, '
              f'FAR {b["deployed_macro_far"]:.4f}')
        print('  Read it as a hint: differences of a few 1e-4 are below the '
              'resolution of')
        print('  8 users x ~16 genuine x ~74 impostor sessions, and every '
              'impostor was')
        print('  visible during selection.')
    return df


# ============================== MAIN ==============================

def main(argv=None):
    ap = argparse.ArgumentParser(
        description='CEILING PROBE v20. v19 with the 50-feature floor removed '
                    'and best-set selection over the elimination curve. '
                    'Output is NOT deployable.')

    ap.add_argument('--features', default=os.path.join('features', 'v3_v2'))
    ap.add_argument('--out', default=os.path.join(
        'features', 'v3_v2', 'selected_V20_BEST_CEILING_PROBE.json'))
    ap.add_argument('--users', default=None)
    ap.add_argument('--prescreen', type=int, default=v4.PRESCREEN_KEEP)
    ap.add_argument('--corr', type=float, default=v4.CORR_THRESHOLD)
    ap.add_argument('--tol', type=float, default=v4.SBS_TOL)
    ap.add_argument('--min-features', type=int, default=DEFAULT_MIN_FEATURES,
                    help=f'floor for elimination. Default '
                         f'{DEFAULT_MIN_FEATURES}, NOT v4\'s 50 - the point of '
                         f'this file is that 50 was a budget, not a stopping '
                         f'criterion. Pass 50 to reproduce v19.')
    ap.add_argument('--sbs-cap', type=int, default=v4.SBS_CANDIDATE_CAP)
    ap.add_argument('--max-steps', type=int, default=v4.SBS_MAX_STEPS)
    ap.add_argument('--impostor-protocol',
                    choices=('same-device', 'cross-device'),
                    default='same-device')
    ap.add_argument('--seed', type=int, default=v4.RANDOM_SEED)
    ap.add_argument('--ranking-out', default='')
    ap.add_argument('--exclude-groups', default='')
    ap.add_argument('--drop-families', default='')
    ap.add_argument('--keep-families', default='')
    ap.add_argument('--focus', default='')
    ap.add_argument('--ranking', choices=('fisher', 'consensus'),
                    default='consensus')
    ap.add_argument('--w-crossdev', type=float, default=0.5)
    ap.add_argument('--device-veto', type=float, default=0.50)
    ap.add_argument('--device-diag-out', default='')
    ap.add_argument('--i-know-this-is-not-honest', action='store_true')

    g2 = ap.add_argument_group('phase 2: robust correlation aggregation (v6)')
    g2.add_argument('--corr-agg', choices=CORR_AGGREGATORS, default='quantile')
    g2.add_argument('--corr-q', type=float, default=DEFAULT_CORR_Q)
    g2.add_argument('--corr-fisher-z', dest='corr_fisher_z',
                    action='store_true', default=None)
    g2.add_argument('--no-corr-fisher-z', dest='corr_fisher_z',
                    action='store_false')
    g2.add_argument('--corr-dispersion', type=float,
                    default=DEFAULT_DISPERSION_MAX)
    g2.add_argument('--corr-diag-out', default='')

    ge = ap.add_argument_group('scorer (v18)')
    ge.add_argument('--ens-m', type=int, default=1)
    ge.add_argument('--ens-frac', type=float, default=DEFAULT_ENS_FRAC)
    ge.add_argument('--ens-mode', choices=ENS_MODES, default='overlap')
    ge.add_argument('--ens-rule', choices=ENS_RULES, default='min')
    ge.add_argument('--ens-diag-out', default='')

    gs = ap.add_argument_group('search (v18)')
    gs.add_argument('--stall-metric', choices=STALL_METRICS, default='none')
    gs.add_argument('--stall-window', type=int, default=DEFAULT_STALL_WINDOW)
    gs.add_argument('--stall-tol', type=float, default=DEFAULT_STALL_TOL)
    gs.add_argument('--max-floats', type=int, default=DEFAULT_MAX_FLOATS)
    gs.add_argument('--lookahead', dest='lookahead', action='store_true',
                    default=False)
    gs.add_argument('--no-lookahead', dest='lookahead', action='store_false')
    gs.add_argument('--lookahead-k', type=int, default=DEFAULT_LOOKAHEAD_K)
    gs.add_argument('--lookahead-cap', type=int, default=DEFAULT_LOOKAHEAD_CAP)
    gs.add_argument('--stall-diag-out', default='')

    gg = ap.add_argument_group('genuine-side scope (v19)')
    gg.add_argument('--genuine-scope', choices=GENUINE_SCOPES,
                    default='enrolment+testing')

    gn = ap.add_argument_group('NEW: best-set selection over the curve')
    gn.add_argument('--select-best', choices=SELECT_BEST, default='auc',
                    help="which set to RETURN. 'last' is v19's behaviour (the "
                         "final set). 'auc' (default) the highest-AUC step. "
                         "'gap' the highest-gap step. 'knee' the smallest set "
                         "within --knee-tol of the peak AUC. Ties go to the "
                         "smaller set.")
    gn.add_argument('--knee-tol', type=float, default=DEFAULT_KNEE_TOL)
    gn.add_argument('--curve-out', default='',
                    help='write the full (n, AUC, gap) curve to CSV')

    gw = ap.add_argument_group('NEW: deployed sweep over the curve')
    gw.add_argument('--sweep-eval', action='store_true',
                    help='do not run selection; instead read --curve and '
                         'report DEPLOYED EER/FAR/FRR for every feature count '
                         'on it. This is the honest way to pick n.')
    gw.add_argument('--curve', default='',
                    help='a v20 JSON carrying a "curve" block')
    gw.add_argument('--sweep-out', default='')
    gw.add_argument('--sweep-frr', type=float, default=0.05)

    args = ap.parse_args(argv)

    # ---------------- sweep mode: no selection, just evaluate ----------------
    if args.sweep_eval:
        src = args.curve or args.out
        if not os.path.exists(src):
            print(f'  --curve {src} not found')
            return 2
        print('=' * 74)
        print('  v20 DEPLOYED SWEEP over a recorded elimination curve')
        print(f'  curve: {src}')
        print(f'  target FRR {args.sweep_frr} (temporal, order rule - matches '
              f'new_train_session_2.py)')
        print('=' * 74)
        sweep_eval(src, args.features, out_csv=args.sweep_out or None,
                   target_frr=args.sweep_frr)
        return 0

    if args.corr_fisher_z is None:
        args.corr_fisher_z = (args.corr_agg != 'mean')
    if not (0.0 < args.corr_q < 1.0):
        print('  --corr-q must be strictly between 0 and 1')
        return 2
    if args.min_features < 2:
        print('  --min-features must be >= 2')
        return 2

    focus = ([x.strip() for x in args.focus.split(',') if x.strip()]
             if args.focus else ['Parthish', 'Teja', 'rohity', 'surya'])

    base_out = os.path.basename(args.out).lower()
    if any(base_out.startswith(p) for p in PROTECTED_OUT) \
            and not args.i_know_this_is_not_honest:
        print(f'REFUSING to write {args.out}')
        print('  Use a *_CEILING_PROBE.json name.')
        return 2

    if args.exclude_groups or args.drop_families or args.keep_families:
        import new_feature_registry as _reg
        if args.exclude_groups:
            grp = ([] if args.exclude_groups.strip().lower() in ('none', 'null')
                   else [x.strip() for x in args.exclude_groups.split(',')
                         if x.strip()])
            unknown = [x for x in grp if x not in _reg.GROUP_DEFINITIONS]
            if unknown:
                print(f'  unknown group(s) {unknown}')
                return 2
            _reg.EXCLUDE_GROUPS[:] = grp
        for p_ in (x.strip() for x in args.drop_families.split(',')):
            if p_:
                _reg.EXTRA_EXCLUDED_FAMILIES[p_] = 'set via --drop-families'
        _reg.refresh_exclusions()
        for p_ in (x.strip() for x in args.keep_families.split(',')):
            if p_:
                _reg.ACTIVE_EXCLUDED_FAMILIES.pop(p_, None)
                _reg.ACTIVE_EXCLUDED_REGEXES.pop(p_, None)
                _reg._ACTIVE_RX = [(rx, src) for rx, src in _reg._ACTIVE_RX
                                   if src != p_]

    gen_contaminated = (args.genuine_scope != 'enrolment')

    print('=' * 74)
    print('  CEILING PROBE v20 - ELIMINATE PAST 50, RETURN THE BEST SET')
    print(f'  floor: {args.min_features} feature(s)'
          + ('   (v19 used 50)' if args.min_features != 50 else '   == v19'))
    print(f'  return: --select-best {args.select_best.upper()}'
          + (f' (knee-tol {args.knee_tol})' if args.select_best == 'knee'
             else ''))
    print(f'  genuine scope: {args.genuine_scope}')
    if gen_contaminated:
        print('  ** BOTH AXES CONTAMINATED (v19 behaviour). **')
    print(f'  scorer: M={args.ens_m}   search: backward, tol={args.tol}, '
          f'lookahead=' + ('on' if args.lookahead else 'off'))
    print('  Selection AUC near 1.0 cannot resolve a few 1e-4. Use '
          '--sweep-eval afterwards')
    print('  to pick the feature count on DEPLOYED metrics instead.')
    print('=' * 74)

    t_run = time.time()
    users = discover_users(args.features)
    if args.users:
        with open(args.users) as fh:
            want = {l.split('#')[0].strip() for l in fh
                    if l.split('#')[0].strip()}
        users = [u for u in users if u in want]

    print('\nPhase 0  load enrolment')
    frames = load_enrolment(args.features, users)
    print(f'  {len(frames)} usable user(s): {sorted(frames)}')
    if len(frames) < MIN_USERS:
        print(f'\n  NOT VIABLE: {len(frames)} user(s)')
        return 2

    same_dev = args.impostor_protocol == 'same-device'
    print(f'\nPhase 1  pre-screen  ({args.impostor_protocol}, {args.ranking})')
    cols = numeric_universe(frames, same_device_impostors=same_dev)
    print(f'  {len(cols)} numeric candidates common to all users')
    if args.ranking == 'consensus':
        from prescreen_v3_device import consensus_ranking
        cand, fisher, viability, devdiag = consensus_ranking(
            frames, cols, args.features, keep_n=args.prescreen,
            restrict_to=None, w_crossdev=args.w_crossdev,
            device_veto=args.device_veto, verbose=True)
        if args.device_diag_out:
            os.makedirs(os.path.dirname(args.device_diag_out) or '.',
                        exist_ok=True)
            devdiag.to_csv(args.device_diag_out)
    else:
        cand, fisher, viability = prescreen_v2(frames, cols,
                                               keep_n=args.prescreen,
                                               per_user=False)

    _all_numeric = sorted(set().union(*[
        {c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])}
        for df in frames.values()])) if frames else []

    print('\nPhase 1a load ALL attackers')
    all_imp, all_att = load_all_attackers(args.features, sorted(frames), cand)
    if not all_imp:
        print('\n  NOT VIABLE: no usable impostor sessions')
        return 2

    print('\nPhase 1a2 load TEST GENUINE')
    if gen_contaminated:
        test_gen = load_test_genuine(args.features, sorted(frames), cand)
        if not test_gen:
            print('  !! no usable test genuine - aborting')
            return 2
    else:
        test_gen = {}
        print('  skipped: --genuine-scope enrolment')

    print('\nPhase 1b build folds')
    folds = build_folds_genuine(frames, cand, all_imp, test_gen,
                                args.genuine_scope)
    if len(folds) < MIN_USERS:
        print('  NOT VIABLE: too few users survived fold construction')
        return 2

    print(f'\nPhase 2  correlation clustering (|r| >= {args.corr}) '
          f'[{args.corr_agg}]')
    clusters, detail = correlation_clusters_robust(
        folds, cand, threshold=args.corr, agg=args.corr_agg,
        use_fisher_z=args.corr_fisher_z, q=args.corr_q,
        dispersion_max=args.corr_dispersion, return_detail=True)
    audit = None
    if detail['stack'] is not None:
        audit = correlation_audit(detail['stack'], detail['users'],
                                  detail['consensus'], detail['dispersion'],
                                  cand, args.corr,
                                  path=args.corr_diag_out or None)
    reps = pick_representatives(folds, clusters, fisher)

    scorer = EnsembleScorer(m=args.ens_m, frac=args.ens_frac,
                            mode=args.ens_mode, rule=args.ens_rule,
                            seed=args.seed)

    print(f'\nPhase 2a separability BEFORE elimination ({len(reps)} reps)')
    before = scorer.per_user(folds, reps, cand)
    print_per_user(f'{len(reps)} features:', before)

    print(f'\nPhase 3  backward elimination down to {args.min_features}')
    final, best_auc, history, problem, stall_events, attribution = \
        stall_gated_eliminate(
            folds, reps, cand, scorer,
            tol=args.tol, min_features=args.min_features,
            cap=args.sbs_cap, max_steps=args.max_steps,
            stall_metric=args.stall_metric, stall_window=args.stall_window,
            stall_tol=args.stall_tol, max_floats=args.max_floats,
            lookahead=args.lookahead, lookahead_k=args.lookahead_k,
            lookahead_cap=args.lookahead_cap)
    if problem:
        print(f'\n  NOT VIABLE: {problem}')
        return 2

    # ---------------- the new part ----------------
    print(f'\nPhase 3b replay the curve and choose the set to return')
    curve = replay_history(reps, history)
    print(f'  reconstructed {len(curve)} step(s) from the history '
          f'(no extra model fits)')
    if len(curve) < len(history):
        print(f'  !! replay stopped early at {len(curve)}/{len(history)} - '
              f'returning the curve it could verify')
    pick, why = choose(curve, args.select_best, args.knee_tol)
    print_curve(curve, pick_n=pick['n'])
    print(f'  -> {why}')
    chosen = pick['feats']
    chosen_auc = pick['auc']
    if args.select_best != 'last' and len(chosen) != len(final):
        print(f'  NOTE: v19 would have returned {len(final)} features at AUC '
              f'{best_auc:.5f};')
        print(f'        this run returns {len(chosen)} at AUC '
              f'{chosen_auc:.5f}.')

    if args.curve_out:
        os.makedirs(os.path.dirname(args.curve_out) or '.', exist_ok=True)
        pd.DataFrame([{'n': c['n'], 'macro_auc': c['auc'],
                       'macro_gap': c['gap'], 'mode': c['mode']}
                      for c in curve]).to_csv(args.curve_out, index=False)
        print(f'  curve -> {args.curve_out}')

    print(f'\nPhase 3c separability of the RETURNED set ({len(chosen)} feats)')
    after = scorer.per_user(folds, chosen, cand)
    print_per_user(f'{len(chosen)} features:', after, baseline=before)

    print(f'\nPhase 4  per-feature margins ({len(chosen)} refits x 2 metrics)')
    _t = time.time()
    marg, final_gap = margins_ens(folds, chosen, cand, scorer, chosen_auc)
    print(f'  done in {time.time() - _t:.0f}s')
    print(f'  {"dAUC":>9s}  {"dGAP":>9s}  bkt  feature')
    for r in marg[:15]:
        print(f'  {r["margin"]:+9.5f}  {r["margin_gap"]:+9.5f}  '
              f'{r["bucket"]:<3s}  {r["feature"]}')

    macro_gap_after = float(np.mean([r['gap'] for r in after.values()
                                     if np.isfinite(r['gap'])]))

    print('\n' + '=' * 74)
    print(f'  CEILING PROBE v20 RESULT   {len(chosen)} features   '
          f'macro AUC {chosen_auc:.5f}   macro gap {macro_gap_after:+.4f}')
    print(f'  selected by: {args.select_best}   floor: {args.min_features}')
    print('=' * 74)
    print('  buckets  ' + '  '.join(
        f'{k}:{v}' for k, v in sorted(Counter(
            (bucket_of(c)[0] if bucket_of else '?') for c in chosen).items())))
    print()
    print('  NEXT STEP - pick the feature count on DEPLOYED metrics:')
    print(f'    python new_feature_selection_v20.py --sweep-eval \\')
    print(f'        --curve {args.out} --features {args.features} \\')
    print(f'        --sweep-out reports\\v20_deployed_sweep.csv')
    print('  Selection AUC cannot resolve the last few 1e-4; deployed EER can.')

    res = {
        'viable': False,
        'deployable': False,
        'probe': 'ceiling',
        'genuine_contaminated': bool(gen_contaminated),
        'warning': ('CEILING PROBE v20. Every impostor session was visible '
                    'during elimination, and under genuine_scope != enrolment '
                    'so was every testing-CSV genuine session. The returned '
                    'set was chosen as the argmax of a metric measured on '
                    'those same folds, which is a second layer of selection on '
                    'contaminated data: differences of a few 1e-4 in macro AUC '
                    'are below the resolution of this sample. Use the curve '
                    'and --sweep-eval to choose a feature count on deployed '
                    'metrics, and read every number here as resubstitution.'),
        'method': ('prescreen+robust-cluster+backward-elimination past the '
                   '50-feature floor, returning the best set on the curve '
                   '(select_best=' + args.select_best + ')'),
        'base_scripts': ['new_feature_selection_v19.py',
                         'new_feature_selection_v18.py',
                         'new_feature_selection_v6.py'],
        'feature_dir': args.features,
        'impostor_protocol': args.impostor_protocol,
        'n_users': len(folds),
        'min_enrolment_sessions': int(min(len(d) for d in frames.values())),
        'budget': len(chosen),
        'selected': chosen,
        'per_bucket': dict(Counter(
            (bucket_of(c)[0] if bucket_of else '?') for c in chosen)),
        'macro_auc_no_holdout': chosen_auc,
        'macro_gap_no_holdout': macro_gap_after,
        'per_user_before': before,
        'per_user_after': after,
        'margins': marg,
        'elimination_history': history,
        'n_candidates': len(cols),
        'n_after_prescreen': len(cand),
        'n_clusters': len(clusters),
        'selection': {
            'select_best': args.select_best,
            'knee_tol': args.knee_tol,
            'reason': why,
            'min_features_floor': args.min_features,
            'reproduces_v19': bool(args.min_features == 50
                                   and args.select_best == 'last'),
            'last_set_n': len(final),
            'last_set_auc': best_auc,
            'curve_len': len(curve),
        },
        # the whole curve, so --sweep-eval needs no refit of the search
        'curve': [{'n': c['n'], 'auc': c['auc'], 'gap': c['gap'],
                   'mode': c['mode'], 'feats': c['feats']} for c in curve],
        'genuine': {
            'scope': args.genuine_scope,
            'mean_val_g_enrolment': int(np.mean(
                [f['n_val_g_enrolment'] for f in folds.values()])),
            'mean_val_g_testing': int(np.mean(
                [f['n_val_g_testing'] for f in folds.values()])),
        },
        'search': {'stall_metric': args.stall_metric,
                   'lookahead': bool(args.lookahead), 'tol': args.tol,
                   'attribution': attribution, 'stall_events': stall_events},
        'correlation': {'aggregator': args.corr_agg,
                        'quantile': (args.corr_q
                                     if args.corr_agg == 'quantile' else None),
                        'fisher_z': bool(args.corr_fisher_z),
                        'threshold': args.corr,
                        'audit': (audit.reset_index().to_dict('records')
                                  if audit is not None else None)},
        'validation': {'genuine_source': ('enrolment holdout + testing genuine'
                                          if gen_contaminated
                                          else 'enrolment holdout'),
                       'impostor_source': 'ALL attackers, none reserved',
                       'held_out': False,
                       'genuine_held_out': not gen_contaminated},
        'selection_attackers': {k: sorted(v) for k, v in all_att.items()},
        'eval_attackers': {k: [] for k in all_att},
    }
    try:
        import new_feature_registry as _r2
        res['excluded_groups'] = list(_r2.ACTIVE_GROUPS)
        res['excluded_patterns'] = sorted(
            list(_r2.ACTIVE_EXCLUDED_FAMILIES)
            + list(_r2.ACTIVE_EXCLUDED_REGEXES))
    except (ImportError, AttributeError):
        pass

    if args.stall_diag_out and stall_events:
        os.makedirs(os.path.dirname(args.stall_diag_out) or '.', exist_ok=True)
        pd.DataFrame(stall_events).to_csv(args.stall_diag_out, index=False)
    if args.ranking_out:
        write_ranking(args.ranking_out, _all_numeric, cols, fisher, viability,
                      cand, clusters, reps, chosen, history, marg)
        res['ranking_csv'] = args.ranking_out

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    json.dump(res, open(args.out, 'w'), indent=2, default=float)
    print(f'\n  written  {args.out}')
    print(f'  total runtime {(time.time() - t_run) / 60:.1f} min')
    return 0


if __name__ == '__main__':
    sys.exit(main())
