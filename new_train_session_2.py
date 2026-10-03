#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
new_train_session_2.py
======================
CEILING-PROBE EVALUATOR. The matching second half of new_feature_selection_v4_v3.py.

This trains and evaluates on ALL test data - every genuine session and every
impostor session, with NO attacker exclusion - using a feature list that was
itself chosen while looking at those same impostor sessions.

    THE NUMBER THIS PRODUCES IS NOT A PERFORMANCE ESTIMATE.

It is a RESUBSTITUTION score: features were selected on these exact sessions, so
evaluating on them measures how well the selection fitted its own sample. It is
the upper bound of the upper bound. Read it as "the best this feature space
could possibly look", never as "this is how the system performs".

WHY RUN IT ANYWAY
-----------------
The ceiling probe (new_feature_selection_v4_v3.py) reported macro AUC 0.9995 on
its own folds and showed Parthish lifting 0.796 -> 0.998. That was measured
inside the selection loop, on a temporal enrolment holdout for genuine. This
script closes the loop differently: it fits the real per-user OCSVM the way
new_train_session.py does - full enrolment, real calibration, real threshold -
and scores the real test CSVs. So it answers:

    "With the probe's 50 features, does the ACTUAL pipeline separate these
     users, at a real calibrated threshold, on all the real test data?"

If the answer is no even here, the features are worthless and no amount of
honest evaluation will rescue them. If the answer is yes, you have learned only
that the ceiling is high - and the next step is the held-out validation, not a
report.

WHAT THIS SCRIPT CHANGES vs new_train_session.py
------------------------------------------------
Exactly three things. Everything else is imported, so any difference in results
is attributable to these and nothing else:

 1. ACCEPTS A NON-VIABLE FEATURE LIST. new_train_session.py refuses a JSON with
    "viable": false, which is correct there - selection saying "I could not
    choose" must not silently degrade into training on 4,000 columns. Here the
    non-viable flag means "deliberately not honest", and reading it is the
    entire point. The refusal is replaced by a loud banner.

 2. IGNORES selection_attackers. new_train_session.py excludes selection-fold
    attackers from FAR so the reported FAR comes only from attackers the search
    never saw. The probe JSON lists EVERY attacker there, so that exclusion
    would leave zero impostors and FAR would be undefined - which is why the
    plain script produced nothing. This one evaluates on all of them and labels
    the result accordingly.

 3. REPORTS CONTAMINATION EXPLICITLY. Every per-user line and the summary state
    how many impostor sessions were seen during selection (here: all of them).
    A summary.csv from this script carries a `contaminated` column so a later
    reader cannot mistake it for models/summary.csv.

SAFETY
------
Defaults to --models models_ceiling and --plot-dir plots_ceiling so it cannot
overwrite the honest artefacts in models/ and plots/. It refuses to write into
a directory whose summary.csv came from an honest run unless --force-overwrite
is passed. That check is cheap and the alternative - silently replacing the
numbers you intend to report with resubstitution numbers - is expensive.

USAGE
-----
    python new_train_session_2.py --features features\\v3_v2 \\
        --feature-list features\\v3_v2\\selected_CEILING_PROBE.json \\
        --calibrate-frr 0.05 --calibrate-method temporal

Compare against the honest baseline in models/summary.csv (macro EER 0.0834,
macro AUC 0.9610) and against the probe's own internal numbers. The gap between
this and the honest run is the size of the optimism.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

# Import the real pipeline rather than reimplementing it. Scoring, calibration,
# gamma resolution, plotting and the OCSVM wrapper stay bit-identical to the
# honest script so the comparison is meaningful.
import new_train_session as nts
from new_train_session import (
    GAMMA,
    NU,
    SessionOCSVM,
    discover_users,
    plot_global,
    plot_user,
    read_users,
    _HAVE_PLT,
)


BANNER = '#' * 72


def load_feature_list_permissive(path):
    """
    Read a selection JSON or text list, ALLOWING a non-viable / probe selection.

    This is new_train_session.load_feature_list() with the viability refusal
    replaced by a warning. Returns (columns, meta) where meta carries the flags
    that make the output honest about itself.
    """
    meta = {'probe': None, 'viable': True, 'deployable': True, 'warning': None,
            'n_selection_attackers': 0, 'macro_auc_no_holdout': None}
    with open(path) as fh:
        head = fh.read(1)
        fh.seek(0)
        if head == '{':
            obj = json.load(fh)
            cols = obj.get('selected') or []
            meta['probe'] = obj.get('probe')
            meta['viable'] = obj.get('viable', True)
            meta['deployable'] = obj.get('deployable', True)
            meta['warning'] = obj.get('warning')
            meta['macro_auc_no_holdout'] = obj.get('macro_auc_no_holdout')
            sa = obj.get('selection_attackers') or {}
            ea = obj.get('eval_attackers') or {}
            meta['n_selection_attackers'] = sum(len(v) for v in sa.values())
            meta['selection_attackers'] = {u: sorted(map(str, v))
                                           for u, v in sa.items()}
            meta['eval_attackers'] = {u: sorted(map(str, v))
                                      for u, v in ea.items()}
        else:
            cols = [l.split('#')[0].strip() for l in fh
                    if l.split('#')[0].strip()]
            meta['selection_attackers'] = {}
            meta['eval_attackers'] = {}
    if not cols:
        raise ValueError(f'{path} contains no feature names')
    return cols, meta


def guard_output_dir(models_dir, force):
    """
    Refuse to overwrite an honest run's artefacts.

    models/summary.csv from new_train_session.py has no `contaminated` column.
    If we find one like that and we were not told to force, stop - those are the
    numbers the user intends to report, and replacing them with resubstitution
    numbers is the single most damaging thing this script could do.
    """
    p = os.path.join(models_dir, 'summary.csv')
    if not os.path.exists(p) or force:
        return True
    try:
        cols = pd.read_csv(p, nrows=1).columns
    except (OSError, pd.errors.ParserError):
        return True
    if 'contaminated' not in cols:
        print(f'REFUSING to write into {models_dir}/')
        print(f'  {p} looks like output from an HONEST run (no `contaminated`')
        print('  column). This script produces resubstitution numbers, and')
        print('  overwriting an honest summary with them is how a contaminated')
        print('  figure ends up in a report.')
        print('  Use --models models_ceiling (the default), or pass')
        print('  --force-overwrite if you really mean it.')
        return False
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='CEILING-PROBE evaluator: train and evaluate on ALL test '
                    'data with no attacker exclusion. Produces resubstitution '
                    'numbers, NOT a performance estimate.')
    ap.add_argument('--features', default=os.path.join('features', 'v3_v2'))
    ap.add_argument('--models', default='models_ceiling',
                    help='default is models_ceiling so the honest models/ '
                         'directory is never clobbered')
    ap.add_argument('--plot-dir', default='plots_ceiling')
    ap.add_argument('--users', default=None)
    ap.add_argument('--nu', type=float, default=NU)
    ap.add_argument('--gamma', default=GAMMA)
    ap.add_argument('--no-registry', action='store_true')
    ap.add_argument('--no-plots', action='store_true')
    ap.add_argument('--calibrate-method', choices=('temporal', 'loo'),
                    default='temporal')
    ap.add_argument('--calibrate-frr', type=float, default=None)
    ap.add_argument('--feature-list', required=True,
                    help='the CEILING PROBE JSON. Required - this script has no '
                         'meaning without one.')
    ap.add_argument('--exclude-selection-attackers', action='store_true',
                    help='honour selection_attackers after all. With a ceiling '
                         'probe JSON this excludes every attacker and leaves no '
                         'impostors, so it exists only for A/B runs against a '
                         'normal selection JSON.')
    ap.add_argument('--force-overwrite', action='store_true',
                    help='allow writing into a directory holding an honest run')
    args = ap.parse_args(argv)

    try:
        gamma = float(args.gamma)
    except ValueError:
        gamma = args.gamma

    try:
        feature_list, meta = load_feature_list_permissive(args.feature_list)
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f'! {e}')
        return 2

    # Contamination is detected STRUCTURALLY, not from the viability flags.
    # Those flags are one line in a JSON and are easy to flip to get past a
    # guard; the structure is not. A selection that reserved nothing has an
    # empty eval_attackers for every user while selection_attackers is
    # populated - that is the signature of a ceiling probe regardless of what
    # the flags claim, and it is what actually makes the FAR below optimistic.
    _sa = meta.get('selection_attackers', {})
    _ea = meta.get('eval_attackers', {})
    nothing_reserved = bool(_sa) and not any(_ea.get(u) for u in _sa)
    contaminated = (meta['probe'] == 'ceiling' or not meta['viable']
                    or not meta['deployable'] or nothing_reserved)

    print(BANNER)
    print('#  CEILING-PROBE EVALUATION - RESUBSTITUTION, NOT PERFORMANCE')
    print(BANNER)
    print(f'#  feature list : {args.feature_list}')
    print(f'#  features     : {len(feature_list)}')
    if meta['probe']:
        print(f'#  probe type   : {meta["probe"]}')
    if meta['macro_auc_no_holdout'] is not None:
        print(f'#  probe AUC    : {meta["macro_auc_no_holdout"]:.5f} '
              f'(measured inside the selection loop)')
    if contaminated:
        print('#')
        print('#  THIS FEATURE SET WAS CHOSEN WHILE LOOKING AT THE IMPOSTOR')
        print('#  SESSIONS IT IS ABOUT TO BE SCORED ON.')
        print(f'#  {meta["n_selection_attackers"]} attacker-user pairing(s) were '
              f'visible during selection.')
        if not args.exclude_selection_attackers:
            print('#  Every one of them is included in the FAR below, on purpose.')
        print('#  Every FAR / EER / AUC printed below is optimistically biased.')
        print('#  Do not put these numbers in a report.')
    print(BANNER)

    if not guard_output_dir(args.models, args.force_overwrite):
        return 2

    # THE KEY DIFFERENCE: no attacker exclusion. new_train_session.py builds this
    # from the JSON and drops those impostors before scoring; here it stays empty
    # unless explicitly asked for.
    excl = {}
    if args.exclude_selection_attackers:
        excl = {u: set(v) for u, v in meta.get('selection_attackers', {}).items()}
        print(f'  --exclude-selection-attackers: honouring exclusions for '
              f'{len(excl)} user(s)')
        print('  ! with a ceiling-probe JSON this removes every attacker and '
              'FAR will be undefined')
    else:
        print('  attacker exclusion: OFF - ALL impostor sessions are scored')

    users = read_users(args.users) if args.users else discover_users(args.features)
    if not users:
        print(f'no users found in {args.features}')
        return 1

    print('=' * 70)
    print(f'  {len(users)} user(s) | nu={args.nu} gamma={gamma} '
          f'| registry={"off" if args.no_registry else "on"}')
    print('=' * 70)

    rows = []
    pooled_scores, pooled_labels = [], []
    reference_columns = None

    for u in users:
        tr = os.path.join(args.features, f'{u}_training_sessions.csv')
        te = os.path.join(args.features, f'{u}_testing_sessions.csv')
        print(f'\n[{u}]')

        if not os.path.exists(tr):
            print('    ! no training CSV, skipped')
            continue

        m = SessionOCSVM(u, nu=args.nu, gamma=gamma)
        try:
            X_tr, X_te, y_te, tr_df, te_df = m.load(
                tr, te, use_registry=not args.no_registry,
                feature_list=feature_list,
                exclude_attackers=excl.get(u))
        except (ValueError, KeyError) as e:
            print(f'    ! {e}')
            continue

        d = m.drop_report
        print(f'    train {X_tr.shape[0]} x {X_tr.shape[1]} features '
              f'(dropped {d["identifier"]} id, {d["diagnostic"]} diagnostic, '
              f'{d["constant"]} constant)')

        current_cols = sorted(m.feature_columns)
        if reference_columns is None:
            reference_columns = current_cols
        elif current_cols != reference_columns:
            missing = set(reference_columns) - set(current_cols)
            extra = set(current_cols) - set(reference_columns)
            print(f'    ! schema mismatch: {len(missing)} missing, '
                  f'{len(extra)} extra vs first user - skipped')
            continue

        if X_tr.shape[0] < 2:
            print('    ! fewer than 2 enrolment sessions, cannot fit')
            continue
        if X_tr.shape[0] < X_tr.shape[1] / 10:
            print(f'    ! {X_tr.shape[0]} sessions against {X_tr.shape[1]} '
                  f'features - heavily underdetermined')

        m.verbose = True
        m.fit(X_tr, calibrate_frr=args.calibrate_frr,
              calibrate_method=args.calibrate_method)
        gu = m.gamma_used
        gs = gu if isinstance(gu, str) else f'{gu:.5f}'
        print(f'    gamma {gs}'
              + (f'  threshold {m.threshold:+.5f} '
                 f'({args.calibrate_method}, target FRR '
                 f'{args.calibrate_frr:.2f})'
                 if args.calibrate_frr is not None else
                 '  threshold +0.00000 (uncalibrated)'))
        path = m.save(args.models)

        if X_te is None or len(X_te) == 0:
            print(f'    no test sessions - model saved to {path}, not evaluated')
            rows.append({'user': u, 'n_train': X_tr.shape[0],
                         'n_features': X_tr.shape[1],
                         'contaminated': int(contaminated)})
            continue

        r = m.evaluate(X_te, y_te)
        pooled_scores.extend(np.asarray(r['scores']) - r['threshold'])
        pooled_labels.extend(y_te)

        # How many of the scored impostors were visible during selection. With a
        # ceiling probe this is all of them, and saying so on every line is the
        # point - a reader skimming the output cannot miss it.
        seen = set(meta.get('selection_attackers', {}).get(u, []))
        n_seen = 0
        if seen and 'operator_id' in te_df.columns:
            op = te_df['operator_id'].astype(str)
            n_seen = int(((te_df['__label__'] == 'impostor')
                          & op.isin(seen)).sum())

        far_s = 'n/a ' if r['n_impostor'] == 0 else f'{r["far"]:.4f}'
        frr_s = 'n/a ' if r['n_genuine'] == 0 else f'{r["frr"]:.4f}'
        extra = ''
        if np.isfinite(r['eer']):
            extra = f'  EER={r["eer"]:.4f}  AUC={r["auc"]:.4f}'
        print(f'    test  {r["n_genuine"]} genuine / {r["n_impostor"]} impostor'
              f'  FRR={frr_s} ({r["n_false_reject"]})'
              f'  FAR={far_s} ({r["n_false_accept"]}){extra}')
        if n_seen:
            pct = 100.0 * n_seen / max(r['n_impostor'], 1)
            print(f'    CONTAMINATED: {n_seen}/{r["n_impostor"]} '
                  f'({pct:.0f}%) of these impostor sessions were visible '
                  f'during feature selection')

        if args.calibrate_frr is not None and r['n_genuine']:
            gap = r['frr'] - args.calibrate_frr
            note = ''
            if abs(gap) > 0.15:
                note = ('   <- calibration MISSED badly; check whether enrolment '
                        'spans more than one sitting')
            print(f'    calibration: predicted FRR {args.calibrate_frr:.2f}, '
                  f'achieved {r["frr"]:.2f}{note}')

        rows.append({'user': u, 'n_train': X_tr.shape[0],
                     'n_features': X_tr.shape[1],
                     'n_genuine': r['n_genuine'], 'n_impostor': r['n_impostor'],
                     'n_impostor_seen_in_selection': n_seen,
                     'frr': r['frr'], 'far': r['far'], 'tar': r['tar'],
                     'eer': r['eer'], 'auc': r['auc'],
                     'threshold': r['threshold'],
                     'n_false_reject': r['n_false_reject'],
                     'n_false_accept': r['n_false_accept'],
                     'contaminated': int(contaminated)})

        if args.plot_dir and not args.no_plots and _HAVE_PLT:
            p = plot_user(u, np.asarray(r['scores']), y_te, r['threshold'],
                          m.loo_scores, args.plot_dir,
                          target_frr=args.calibrate_frr,
                          eer=r['eer'], auc=r['auc'])
            if p:
                print(f'    plot  {p}')

    # ------------------------------------------------------------- summary
    print('\n' + '=' * 70)
    df = pd.DataFrame(rows)
    if df.empty:
        print('  nothing trained')
        return 1

    evaluated = df.dropna(subset=['far', 'frr'], how='all') \
        if 'far' in df.columns else pd.DataFrame()

    print(f'  trained          {len(df)}')
    print(f'  evaluated        {len(evaluated)}')

    if not evaluated.empty:
        ps, pl = np.asarray(pooled_scores), np.asarray(pooled_labels)
        ng, ni = int((pl == 1).sum()), int((pl == -1).sum())
        if ng:
            print(f'  pooled FRR       {np.mean(ps[pl == 1] < 0):.4f}  (n={ng})')
        if ni:
            print(f'  pooled FAR       {np.mean(ps[pl == -1] >= 0):.4f}  (n={ni})')
        mf, ma = evaluated['frr'].dropna(), evaluated['far'].dropna()
        if len(mf):
            print(f'  macro FRR        {mf.mean():.4f}  (over {len(mf)} user(s))')
        if len(ma):
            print(f'  macro FAR        {ma.mean():.4f}  (over {len(ma)} user(s))')
        me = evaluated['eer'].dropna()
        mu_ = evaluated['auc'].dropna()
        if len(me):
            print(f'  macro EER        {me.mean():.4f}')
        if len(mu_):
            print(f'  macro AUC        {mu_.mean():.4f}')

        tot_seen = int(evaluated.get('n_impostor_seen_in_selection',
                                     pd.Series(dtype=int)).sum())
        tot_imp = int(evaluated['n_impostor'].sum())
        if tot_imp:
            print(f'  CONTAMINATION    {tot_seen}/{tot_imp} '
                  f'({100.0 * tot_seen / tot_imp:.0f}%) of scored impostor '
                  f'sessions were seen during selection')

    if args.plot_dir and not args.no_plots and _HAVE_PLT and pooled_scores:
        p = plot_global(rows, pooled_scores, pooled_labels, args.plot_dir,
                        target_frr=args.calibrate_frr)
        if p:
            print(f'  plot             {p}')

    os.makedirs(args.models, exist_ok=True)
    out = os.path.join(args.models, 'summary.csv')
    df.to_csv(out, index=False)
    print(f'  per-user results {out}')
    print('=' * 70)

    if contaminated:
        print(BANNER)
        print('#  REMINDER: the numbers above are RESUBSTITUTION.')
        print('#  The features were selected on these impostor sessions, so')
        print('#  this is the ceiling, not the performance. The honest')
        print('#  comparison is models/summary.csv from new_train_session.py')
        print('#  with selected_rev4.json (macro EER 0.0834, macro AUC 0.9610).')
        print('#')
        print('#  If these numbers are much better than the honest ones, that')
        print('#  gap IS the optimism, and it is what a held-out run has to')
        print('#  close before any of this can be reported.')
        print(BANNER)
    return 0


if __name__ == '__main__':
    sys.exit(main())
