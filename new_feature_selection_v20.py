#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Raw docstring: the run commands below contain Windows paths, so backslashes
# must survive verbatim rather than being read as escapes.
r"""
new_feature_selection_v20_stand_alone.py
========================================
new_feature_selection_v20.py and everything it runs, merged into ONE file, so
the v20 feature selection can be moved to another machine with just two files:

    new_feature_selection_v20_stand_alone.py    (this file)
    prescreen_v3_device.py                      (unchanged, same folder)

plus the data folder (--features, default features\v3_v2) holding
<user>_training_sessions.csv and <user>_testing_sessions.csv for every user.
Nothing else is read, apart from files you name yourself (--users, --curve).

SAME CODE, NOT A REWRITE
------------------------
Built mechanically from the original files. Every function, class and
constant that new_feature_selection_v20.main can reach - for ANY of its
command-line options, not only the ones used in the V20 runs - was copied
verbatim, in original order, module by module in import order. Code that v20
can never reach (the other scripts' main() functions, unused helpers) was
left out. The only edits are mechanical, and every one is listed below:
qualified references such as v4.NU become NU, imports of the merged modules
are removed, and one name is renamed to avoid a clash. The command-line
interface, the printed output and the written JSON/CSV files are those of
new_feature_selection_v20.py.

Not needed any more. new_feature_selection_v20.py stops with ImportError
unless all of these are present (it also loads derived_features.py and
keystroke_fields.py when they exist, but those two are optional):
    new_feature_selection_v4.py, new_feature_selection_v4_v3.py,
    new_feature_selection_v6.py, new_feature_selection_v8.py,
    new_feature_selection_v9.py, new_feature_selection_v10.py,
    new_feature_selection_v11.py, new_feature_selection_v18.py,
    new_feature_selection_v19.py, new_feature_selection_v20.py,
    prescreen_v2.py, new_feature_registry.py,
    new_feature_creation_session.py, new_adapid_schema.py,
    new_build_dtw_templates.py
(new_feature_creation_session.py was imported only for the 9-item ID_COLUMNS
list, which pulled in the DTW/schema modules as well. v8 and v10 contribute
no code that runs; v9 and v11 contribute only default constants.)

RUN COMMANDS (PowerShell, from the folder holding features\v3_v2)
--------------------------------------------------------------------
Identical to new_feature_selection_v20.py; only the script name changes.

  # 1) selection: eliminate down to 10, keep the whole curve
  python new_feature_selection_v20_stand_alone.py ^
      --ranking consensus --corr-agg quantile --corr-q 0.25 ^
      --ens-m 1 --stall-metric none --no-lookahead --tol 0.005 ^
      --genuine-scope enrolment+testing ^
      --min-features 10 --select-best auc ^
      --out features\v3_v2\selected_V20_BEST_AUC_CEILING_PROBE.json ^
      --curve-out reports\v20_auc_curve.csv

  # 2) deployed sweep: TAR/FAR/FRR/EER for every feature count on the curve
  python new_feature_selection_v20_stand_alone.py --sweep-eval ^
      --curve features\v3_v2\selected_V20_BEST_AUC_CEILING_PROBE.json ^
      --features features\v3_v2 ^
      --sweep-out reports\v20_deployed_sweep.csv

Note: the run's closing "NEXT STEP" hint and the --help text still name
new_feature_selection_v20.py, because main() is copied verbatim. Use this
file's name instead.

The 46-feature list (selected_V20_N46_TAR95_CEILING_PROBE.json) was NOT
written by v20. It was cut from the step-1 curve by a one-off snippet after
n=46 was chosen by hand from the step-2 table under macro TAR >= 0.95. To
redo it with only these two files, take curve entry n == 46 from the step-1
JSON (its 'feats' list, in order) and import bucket_of from this file.

WHAT "SAME RESULT" REQUIRES
---------------------------
  * the same data files (the CSVs are the only input)
  * prescreen_v3_device.py byte-identical in content (line endings may
    differ). This file checks its sha256 at start-up and warns if it differs.
  * the same library versions. OneClassSVM scores decide every elimination
    step, so a different scikit-learn/numpy can change the path. Verified with
    python 3.13.9, numpy 2.5.3, pandas 3.0.2, scipy 1.18.1, scikit-learn 1.5.2
    and a warning is printed at start-up if any of these differ.
  * the environment variables new_feature_registry honours, unset as in the
    V20 runs: FEATURE_EXCLUDE_GROUPS, FEATURE_EXCLUDE_FAMILIES,
    FEATURE_KEEP_FAMILIES.

KNOWN ISSUE, KEPT AS-IS (it is in new_feature_selection_v18.py as well)
----------------------------------------------------------------------
With --ens-m 2 or more, draw_subspaces() seeds its random generator from
Python's hash() of a tuple holding the user name. Python randomises string
hashing in every new process, so the sub-models, and with them the selected
features, are not repeatable from one run to the next - with the original
v18/v20 exactly as with this file. Setting $env:PYTHONHASHSEED = "0" before
such a run makes it repeatable from then on (it cannot recreate an earlier
run made without it). --ens-m 1, used by every V20 run, never reaches that
code and is fully deterministic.

prescreen_v3_device.py imports prescreen_v2 when it loads. The prescreen_v2
functions copied below are registered as sys.modules['prescreen_v2'], so
that import is satisfied by this file and prescreen_v2.py is not needed. If a
prescreen_v2.py happens to be present it is NOT used.

The original import chain also ran, at import time,
    warnings.filterwarnings('ignore', category=RuntimeWarning)
(new_feature_creation_session.py:113). It is repeated below so the console
output matches. It hides warnings only and changes no number.

PROVENANCE (sha256 of the source files, line endings normalised to LF)
----------------------------------------------------------------------
    file                            names lines edits  sha256 (first 12)
    new_feature_registry.py            28   545     0  6e765717bdfa
    new_feature_creation_session.py     1     7     1  01e8b390cc07
    prescreen_v2.py                    14   235     0  c8d7ca5503de
    new_feature_selection_v4.py        24   267     1  d56bba8a1e51
    new_feature_selection_v4_v3.py      3    54     0  f1cff8a7537a
    new_feature_selection_v6.py        11   343     1  64af792fed69
    new_feature_selection_v9.py         3    12     0  2ec63a428e7c
    new_feature_selection_v11.py        3    13     0  b94dadc9f264
    new_feature_selection_v18.py       18   695    15  2786a9495b07
    new_feature_selection_v19.py        4   125     0  1d31e8f282bc
    new_feature_selection_v20.py        8   659    21  93c83fd6b9ed
    prescreen_v3_device.py          (external, unchanged)  64bff73fb31b

MECHANICAL EDITS (line numbers refer to the ORIGINAL source file)
-----------------------------------------------------------------
  new_feature_creation_session.py
     3694  ID_COLUMNS -> FCS_ID_COLUMNS
  new_feature_selection_v4.py
      441  ID_COLUMNS -> FCS_ID_COLUMNS
  new_feature_selection_v6.py
      356  v4.CORR_THRESHOLD -> CORR_THRESHOLD
  new_feature_selection_v18.py
      439  v4.RANDOM_SEED -> RANDOM_SEED
      468  v4.StandardScaler -> StandardScaler
      470  v4.OneClassSVM -> OneClassSVM
      470  v4.KERNEL -> KERNEL
      470  v4.NU -> NU
      471  v4.resolve_gamma -> resolve_gamma
      471  v4.GAMMA -> GAMMA
      490  v4.roc_auc -> roc_auc
      522  v4.roc_auc -> roc_auc
      726  v4.SATURATION_AUC -> SATURATION_AUC
      728  v4.SATURATION_AUC -> SATURATION_AUC
      769  v11.DEFAULT_FLOAT_CAP -> DEFAULT_FLOAT_CAP
      780  v11.DEFAULT_FLOAT_MIN_GAIN -> DEFAULT_FLOAT_MIN_GAIN
      785  v11.DEFAULT_FLOAT_MAX_READMIT -> DEFAULT_FLOAT_MAX_READMIT
      800  v11.DEFAULT_FLOAT_MIN_GAIN -> DEFAULT_FLOAT_MIN_GAIN
  new_feature_selection_v20.py
      336  removed `from new_feature_selection_v4 import normalise_label`
      464  inserted `global _ACTIVE_RX` at top of main()
      473  v4.PRESCREEN_KEEP -> PRESCREEN_KEEP
      474  v4.CORR_THRESHOLD -> CORR_THRESHOLD
      475  v4.SBS_TOL -> SBS_TOL
      481  v4.SBS_CANDIDATE_CAP -> SBS_CANDIDATE_CAP
      482  v4.SBS_MAX_STEPS -> SBS_MAX_STEPS
      486  v4.RANDOM_SEED -> RANDOM_SEED
      592  removed `import new_feature_registry as _reg`
      597  _reg.GROUP_DEFINITIONS -> GROUP_DEFINITIONS
      601  _reg.EXCLUDE_GROUPS -> EXCLUDE_GROUPS
      604  _reg.EXTRA_EXCLUDED_FAMILIES -> EXTRA_EXCLUDED_FAMILIES
      605  _reg.refresh_exclusions -> refresh_exclusions
      608  _reg.ACTIVE_EXCLUDED_FAMILIES -> ACTIVE_EXCLUDED_FAMILIES
      609  _reg.ACTIVE_EXCLUDED_REGEXES -> ACTIVE_EXCLUDED_REGEXES
      610  _reg._ACTIVE_RX -> _ACTIVE_RX
      610  _reg._ACTIVE_RX -> _ACTIVE_RX
      864  removed `import new_feature_registry as _r2`
      865  _r2.ACTIVE_GROUPS -> ACTIVE_GROUPS
      867  _r2.ACTIVE_EXCLUDED_FAMILIES -> ACTIVE_EXCLUDED_FAMILIES
      868  _r2.ACTIVE_EXCLUDED_REGEXES -> ACTIVE_EXCLUDED_REGEXES
  Whitespace only: new_feature_creation_session.py:3695,
  new_feature_creation_session.py:3696, new_feature_selection_v18.py:471,
  new_feature_selection_v20.py:611 are continuation lines re-indented to
  stay aligned with their bracket after a name on the line above changed
  length.

THE ORIGINAL new_feature_selection_v20.py DOCSTRING, VERBATIM
-------------------------------------------------------------

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
import hashlib as _hashlib
import importlib.util as _ilu
import itertools
import json
import os
import platform as _platform
import re
import sys
import time
import types as _types
import warnings
from collections import Counter, OrderedDict

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

# Executed by the original import chain (new_feature_creation_session.py:113,
# imported by new_feature_selection_v4.py after its sklearn imports).
warnings.filterwarnings('ignore', category=RuntimeWarning)


# ##########################################################################
#  from new_feature_registry.py
#  bucket rules, exclusion groups, bucket_of / model_columns
#  28 name(s), 545 source lines copied verbatim, 0 edit(s) (see header)
# ##########################################################################


EXCLUDE_GROUPS = [
    'magnetometer',        # 395 cols: mag_ rv_ orient_ dtw_mag_ dtw_rv_ + corr_ pairs
    'protocol',            # 305 cols: scr_ nav_ cog_ -- rehearsal, not identity
    'capability',          # path_ pooled + tap micro-jitter -- handset step
    'sampler',             # adaptive-sampler duty cycle - partly protocol
    'ambient_absolute',    # light level = where you are sitting
    # 'ambient_dynamic',   # occlusion dynamics = hand position. ELIGIBLE.
    # 'platform_fused',    # 822 cols: grav_ lin_ grv_ tilt_ motion_ + their DTW
    # 'placement',         # 113 cols: place_ -- screen geometry
    # 'device_frame',      # 1520 cols. DO NOT ACTIVATE until bucket W exists.
]

# Ad-hoc prefixes on top of the groups, for a quick one-off.
EXTRA_EXCLUDED_FAMILIES = {
    # 'kg_':  'keystroke x sensor, only 46 cols and thin on this data',
}

GROUP_DEFINITIONS = {

    # -----------------------------------------------------------------------
    'magnetometer': {
        'why': 'magnetic field = where the phone is and what metal is near it, '
               'not who is holding it',
        'prefixes': {
            'mag_':      'raw magnetometer  (212)',
            'dtw_mag_':  'DTW template on a magnetometer channel  (32)',
            'rv_':       'rotation_vector is acc+gyro+MAG fused, so rv_yaw is '
                         'magnetic heading  (111)',
            'dtw_rv_':   'DTW on that mag-contaminated orientation channel  (24)',
            'orient_':   'orient_rv_grv_*_diff IS a magnetic-distortion measure '
                         '(2)',
        },
        # corr_ names are POSITIONAL: corr_<s1>_<s2>_<axis>, and the axis slot
        # can itself be the word "mag" meaning MAGNITUDE. So corr_acc_mag_z is
        # accelerometer x MAGNETOMETER (exclude) while corr_acc_gyro_mag is
        # acc x gyro on the MAGNITUDE axis (keep). No prefix separates those.
        'regexes': {
            r'^corr_mag_[xyz]{2}':                'magnetometer axis pairs  (6)',
            r'^corr_(acc|gyro)_mag_(mag|[xyz])$': 'acc/gyro x magnetometer  (8)',
        },
    },

    # -----------------------------------------------------------------------
    'platform_fused': {
        'why': "Android computes these from acc+gyro(+mag); they are the OS "
               "fusion filter's output, not hardware, and inherit its group "
               "delay",
        'prefixes': {
            'grav_':       'gravity vector  (165)',
            'dtw_grav_':   'DTW on gravity  (24)',
            'lin_':        'linear_acceleration = acc minus gravity  (220)',
            'dtw_lin_':    'DTW on linear_acceleration  (32)',
            'grv_':        'game_rotation_vector - magnetometer-FREE rotation '
                           'vector  (111)',
            'dtw_grv_':    'DTW on game_rotation_vector  (24)',
            'tilt_':       'pitch/roll from the gravity stream  (147)',
            'dtw_tilt_':   'DTW on tilt  (16)',
            'motion_':     'derived from linear_acceleration  (75)',
            'dtw_motion_': 'DTW on motion  (8)',
        },
        # NEW in rev 4. acc and grv share 78.4% of their timestamps because grv
        # is computed FROM acc, so acc<->grv coupling partly measures Android's
        # fusion scheduler rather than the hand. Positional naming, so regexes.
        'regexes': {
            r'^corr_(acc|gyro)_(grv|grav|lin)_(mag|[xyz])$':
                'acc/gyro x a platform-fused stream',
            r'^(lag|xcorr|mi)_(acc|gyro)_(grv|grav|lin)_':
                'lag / cross-correlation / MI against a fused stream',
        },
    },

    # -----------------------------------------------------------------------
    'protocol': {
        'why': 'encodes WHICH screens were visited and how deep navigation '
               'went. Across 50 genuine enrolment sessions nav_flow_complete, '
               'nav_seq_len, nav_back_count and nav_unique_screens each take '
               'ONE value; across 70 test sessions they take 2-5. That is '
               'rehearsal, not identity',
        'prefixes': {
            'scr_': 'per-screen behavioural profile  (171)',
            'nav_': 'navigation events  (55)',
            'cog_': 'cognitive, touch+navigation, inherits nav protocol  (79)',
        },
        'regexes': {},
    },

    # -----------------------------------------------------------------------
    # NEW in rev 4.
    'capability': {
        'why': 'the handset decides whether these exist at all. Thin-path rate '
               'runs 7.9% (realme) to 94.8% (reddy), so path_n_gestures counts '
               'a different POPULATION of gestures per device: scrolls only on '
               'reddy/srikanth, taps+scrolls on realme/surya. path_len_mean '
               'medians 0.019/0.027 vs 0.491/0.499 - an 18-25x handset step, '
               'and the largest Fisher score in the pool',
        'prefixes': {
            # The POOLED path family only. path_scroll_* is deliberately NOT
            # here: scroll capture is 0.0% thin on every device measured, and
            # path_scroll_straightness_* survives into all four v4 selections
            # on merit. See the regex below, which re-admits it.
            'path_':      'pooled intra-gesture path - tap-vs-scroll mix is a '
                          'handset property  (117, minus the scroll re-admits)',
            'dtw_path_':  'DTW on a path channel built from that mixed pool  (8)',
        },
        'regexes': {},
        # Patterns re-admitted despite matching a prefix above. Longest-prefix
        # resolution cannot express "everything under path_ EXCEPT path_scroll_",
        # so keep_regexes is checked first and wins.
        'keep_regexes': {
            r'^path_scroll_': 'scroll paths are 0.0% thin on every device '
                              'measured; this is the portable part of the family',
        },
    },

    # -----------------------------------------------------------------------
    'placement': {
        'why': 'tap position against the enrolment layout - partly screen '
               'geometry and app version rather than the person',
        'prefixes': {'place_': 'per-element tap placement  (113)'},
        'regexes': {},
    },

    # -----------------------------------------------------------------------
    # REWRITTEN in rev 4. The revision-3 note claimed this group was a no-op
    # and that a "0 col(s)" print was your confirmation. Both were wrong once
    # light turned out to be a 24.4 Hz stream. Split in two.
    'ambient_absolute': {
        'why': 'absolute light level is where you are sitting and what time of '
               'day it is. Identical failure mode to mag_z, which drove surya '
               'FRR to 0.760',
        'prefixes': {
            'light_abs_': 'absolute lux level statistics',
            'prox_':      'proximity (constant 5.0 on every device measured)',
            'step_':      'step_counter (constant within a session)',
            'pressure_':  'barometric pressure  (0 in v3)',
            'baro_':      'barometer, alternative naming  (0)',
        },
        'regexes': {},
    },

    'ambient_dynamic': {
        'why': 'ELIGIBLE BY DEFAULT. Occlusion dynamics - the hand shadows the '
               'sensor, so lux MODULATION is hand position. Defined here only '
               'so you can withhold it if it misbehaves',
        'prefixes': {
            'light_mod_': 'level-normalised lux variability',
            'ltc_':       'light x touch coupling, the tmc_ analogue',
        },
        'regexes': {},
    },

    # -----------------------------------------------------------------------
    # NEW in rev 4.1. Built and withheld, exactly as intended for magnetometer.
    'sampler': {
        'why': 'the adaptive sampler switches to its active rate on detected '
               'motion, so samp_active_frac is a motion duty cycle derived '
               'from Android\'s own detector - genuinely behavioural, but also '
               'partly a property of the capture protocol and of which handset '
               'honours which requested rate. Built so a future experiment is '
               'one uncommented line, withheld so it cannot quietly carry a '
               'result',
        'prefixes': {'samp_': 'adaptive-sampler duty cycle  (~5)'},
        'regexes': {},
    },

    # -----------------------------------------------------------------------
    # DEFINED BUT NOT ACTIVE. Activating this today leaves the model with
    # almost nothing; it exists so that the day bucket W is populated,
    # "orientation-invariant features only" is one uncommented line.
    'device_frame': {
        'why': 'every inertial feature expressed in the PHONE\'s axes, so its '
               'value depends on how the phone is rotated in the hand. Withhold '
               'this ONLY once bucket W (world-frame) exists to replace it',
        'prefixes': {
            'acc_':      'raw accelerometer, device axes  (436)',
            'gyro_':     'raw gyroscope, device axes  (392)',
            'dtw_acc_':  'DTW on device-frame acc  (40)',
            'dtw_gyro_': 'DTW on device-frame gyro  (32)',
        },
        'regexes': {},
    },
}


def _resolve_exclusions():
    groups = list(EXCLUDE_GROUPS)
    env_g = os.environ.get('FEATURE_EXCLUDE_GROUPS')
    if env_g is not None:
        groups = [g.strip() for g in env_g.split(',') if g.strip()]

    unknown = [g for g in groups if g not in GROUP_DEFINITIONS]
    if unknown:
        raise ValueError(
            f'unknown group(s) {unknown}. Known: {sorted(GROUP_DEFINITIONS)}. '
            f'Fix EXCLUDE_GROUPS in new_feature_registry.py or '
            f'FEATURE_EXCLUDE_GROUPS.')

    prefixes, regexes, keeps, owner = {}, {}, {}, {}
    for g in groups:
        d = GROUP_DEFINITIONS[g]
        for pat, why in d.get('prefixes', {}).items():
            prefixes[pat] = why
            owner[pat] = g
        for pat, why in d.get('regexes', {}).items():
            regexes[pat] = why
            owner[pat] = g
        for pat, why in d.get('keep_regexes', {}).items():
            keeps[pat] = why
    for pat, why in EXTRA_EXCLUDED_FAMILIES.items():
        prefixes[pat] = why
        owner[pat] = 'extra'

    env_f = os.environ.get('FEATURE_EXCLUDE_FAMILIES')
    if env_f is not None:
        prefixes = {pat.strip(): 'set via FEATURE_EXCLUDE_FAMILIES'
                    for pat in env_f.split(',') if pat.strip()}
        owner = {pat: 'env' for pat in prefixes}
        regexes, keeps = {}, {}

    for pat in (x.strip() for x in
                os.environ.get('FEATURE_KEEP_FAMILIES', '').split(',')):
        if pat:
            prefixes.pop(pat, None)
            regexes.pop(pat, None)
            owner.pop(pat, None)

    return groups, prefixes, regexes, keeps, owner


(ACTIVE_GROUPS, ACTIVE_EXCLUDED_FAMILIES, ACTIVE_EXCLUDED_REGEXES,
 ACTIVE_KEEP_REGEXES, PATTERN_OWNER) = _resolve_exclusions()

_ACTIVE_RX = [(re.compile(r), r) for r in ACTIVE_EXCLUDED_REGEXES]
_KEEP_RX = [(re.compile(r), r) for r in ACTIVE_KEEP_REGEXES]

# Bucket code for an excluded pattern. Deliberately NOT 'X': "withheld because
# you asked" and "withheld because it is bookkeeping" are different claims and
# belong in different rows of the report.
FAMILY_BUCKET = 'XF'


def refresh_exclusions():
    """Re-resolve after mutating EXCLUDE_GROUPS / EXTRA_EXCLUDED_FAMILIES.

    Needed because --drop-families mutates the module at run time and the
    compiled regex lists have to be rebuilt to match.
    """
    global ACTIVE_GROUPS, ACTIVE_EXCLUDED_FAMILIES, ACTIVE_EXCLUDED_REGEXES
    global ACTIVE_KEEP_REGEXES, PATTERN_OWNER, _ACTIVE_RX, _KEEP_RX
    (ACTIVE_GROUPS, ACTIVE_EXCLUDED_FAMILIES, ACTIVE_EXCLUDED_REGEXES,
     ACTIVE_KEEP_REGEXES, PATTERN_OWNER) = _resolve_exclusions()
    _ACTIVE_RX = [(re.compile(r), r) for r in ACTIVE_EXCLUDED_REGEXES]
    _KEEP_RX = [(re.compile(r), r) for r in ACTIVE_KEEP_REGEXES]


def excluded_family_of(column):
    """The pattern excluding this column, or None. Longest prefix wins.

    keep_regexes are checked FIRST and win outright, because longest-prefix
    resolution cannot express "everything under path_ except path_scroll_".

    Prefixes use startswith, regexes use re.match. Both are anchored at the
    start of the name; nothing here does a substring match. That is
    load-bearing: touch_flight_* contains "light", touch_press_* contains
    "press" and touch_step_* contains "step", so a substring match against the
    ambient patterns would silently delete 137 of the strongest behavioural
    features.
    """
    for rx, _src in _KEEP_RX:
        if rx.match(column):
            return None
    hit = None
    for prefix in ACTIVE_EXCLUDED_FAMILIES:
        if column.startswith(prefix) and (hit is None or len(prefix) > len(hit)):
            hit = prefix
    if hit is not None:
        return hit
    for rx, src in _ACTIVE_RX:
        if rx.match(column):
            return src
    return None


def exclusion_reason(column):
    """Human-readable reason this column is withheld, or None."""
    pat = excluded_family_of(column)
    if pat is None:
        return None
    grp = PATTERN_OWNER.get(pat, 'extra')
    why = (ACTIVE_EXCLUDED_FAMILIES.get(pat)
           or ACTIVE_EXCLUDED_REGEXES.get(pat) or '')
    return f'group {grp!r}, pattern {pat!r}: {why}'


BUCKETS = OrderedDict([
    ('A',  'Touch-only'),
    ('B',  'Navigation-only'),
    ('C',  'Touch + Navigation'),
    ('D',  'Sensor - single raw stream'),
    ('E',  'Sensor - per-sensor independent'),
    ('F',  'Sensor - true multi-sensor fusion'),
    ('G',  'Touch x Sensor'),
    ('H',  'Session metadata (excluded by default)'),
    ('P',  'Platform-fused sensor'),
    ('K',  'Keystroke-only'),
    ('KG', 'Keystroke x Sensor'),
    ('V',  'View / element placement'),
    # ---- reserved in rev 4, populated as the families are built -------------
    ('W',  'World-frame / orientation-invariant inertial'),
    ('T',  'Touch contact geometry'),
    ('KB', 'Keyboard-geometry keystroke'),
    ('L',  'Ambient / environmental'),
    # ---- withheld ----------------------------------------------------------
    ('N',  'Extensive count (excluded by default)'),
    ('X',  'Diagnostic - exclude from model'),
    ('XF', 'Excluded GROUP (see EXCLUDE_GROUPS at top)'),
    ('?',  'UNCLASSIFIED'),
])

VALID_BUCKETS = frozenset(BUCKETS) | {'ID'}

SUFFIX_QUARANTINE = [
    (r'_n$',            'raw sample/event count ~ fs x duration'),
    (r'_count$',        'raw event count ~ duration'),
    (r'_total$',        'cumulative total ~ duration'),
    (r'_n_gestures$',   'gesture count ~ duration'),
    (r'_n_elements$',   'element count ~ how much the user typed'),
    (r'_n_points$',     'point count ~ duration'),
    (r'_n_keys$',       'keystroke count ~ duration'),
    (r'_n_windowed$',   'window count ~ duration'),
    (r'_visits$',       'visit count ~ protocol'),
    (r'_n_codes$',      'distinct-keycode count ~ how much was typed'),
    (r'_n_fields$',     'field count ~ protocol'),
    (r'_seq_len$',      'sequence length ~ protocol'),
    (r'_n_events$',     'event count ~ duration'),
    (r'_n_transitions$', 'transition count ~ protocol'),
    (r'_unique_screens$', 'screen count ~ protocol'),
    (r'_span_s$',       'elapsed span in seconds - a duration by another name'),
]
_SUFFIX_RX = [(re.compile(p), w) for p, w in SUFFIX_QUARANTINE]

# Counts deliberately re-admitted, by exact name, with a reason. Empty by
# design: nothing has earned it yet. Populate this AFTER segment-level features
# land, when a count over a fixed-length segment is a rate.
COUNT_READMIT = {
    # 'touch_iv_n': 'over a fixed 15 s segment this is a tap RATE',
}


def _suffix_quarantined(column):
    """(True, why) if an extensive-count suffix quarantines this column."""
    if column in COUNT_READMIT:
        return False, None
    for rx, why in _SUFFIX_RX:
        if rx.search(column):
            return True, why
    return False, None


# Order matters: the first matching rule wins, so specific patterns precede
# general ones. Each rule is (regex, bucket, why).
_RULES = [
    # ---- X: diagnostics. Must come first, since san_/ctx_/q_ would otherwise
    # be caught by the sensor rules below.
    (r'^feat_(errors|n_errors)$',        'X', 'extractor error reporting'),
    (r'^san_',                           'X', 'sanitizer counters'),
    (r'^hold_',                          'X', 'hold detector output'),
    (r'^cap_',                           'X', 'device capability flags'),
    (r'^bc_',                            'X', 'behaviour_cleaner counters'),
    (r'^ctx_fs_',                        'X', 'sampling-rate bookkeeping'),
    (r'^q_',                             'X', 'per-stream quality metrics'),
    (r'_fs_used$',                       'X', 'which fs a spectrum used'),
    (r'_n_used$',                        'X', 'how many samples were usable'),
    (r'_available$',                     'X', 'family availability flag'),
    (r'^touch_cap_',                     'X', 'touch capability flag'),
    (r'_measurable$',                    'X', 'sub-feature availability flag'),
    (r'_valid$',                         'X', 'validity flag'),

    # ---- X: collection conditions and anything proportional to duration.
    (r'^ctx_duration_s$',                'X', 'session duration - protocol confound'),
    (r'^ctx_n_',                         'X', 'raw count ~ fs x duration'),
    (r'^ctx_(thermal|power_save|dropped_samples)$',
                                         'X', 'collection condition'),
    (r'^ctx_rate_switch',                'X', 'sampling stability bookkeeping'),
    (r'^ctx_idle_after_ms$',             'X', 'collection condition'),
    (r'^ctx_start_rotation$',            'X', 'device orientation at start'),
    (r'^ctx_has_',                       'X', 'stream availability flag'),
    (r'^ctx_dev_',                       'X', 'hardware descriptor'),
    (r'^ctx_schema_version$',            'X', 'schema bookkeeping'),

    # rev 4.1: segment metadata from session_segmenter. seg_dur_s and the raw
    # seg_n_* counts are EXTENSIVE - segments run 4.3-55.5 s here, so a count
    # over one carries the same length confound bucket N exists for. The
    # seg_*_rate_hz columns are the per-second form and are the ones to use.
    (r'^seg_(t0|t1|index)$',             'X', 'segment bookkeeping'),
    (r'^seg_dur_s$',                     'X', 'segment length - the confound itself'),
    (r'^seg_screen$',                    'X', 'segment identity'),
    # The per-second form. Bucket H, matching ctx_touch_rate_hz, which is the
    # same quantity over the whole session: excluded by DEFAULT_EXCLUDE but
    # present and auditable, so re-admitting it is a deliberate act rather than
    # something that happens because a prefix went unnoticed.
    (r'^seg_.*_rate_hz$',                'H', 'segment event rate'),
    (r'^seg_',                           'X', 'segment bookkeeping, unrecognised'),

    # ---- H: what remains of session context is duration-normalised rates only.
    (r'^session_',                       'H', 'session identity/timing'),
    (r'^ctx_',                           'H', 'session context rate'),

    # ---- L: ambient (rev 4)
    (r'^(light|prox|step|baro|pressure)_', 'L', 'ambient / environmental'),
    (r'^ltc_',                           'L', 'light x touch coupling'),

    # ---- V: placement, keyed on view_id
    (r'^place_layout_n_',                'X', 'layout comparison coverage'),
    (r'^place_layout_',                  'V', 'drift against enrolment layout'),
    (r'^place_',                         'V', 'per-element tap placement'),

    # ---- KB: keyboard-geometry keystroke (rev 4, needs the touch<->key join)
    # kbres_ before kb_: it is a longer prefix and the rules are first-match.
    # rev 4.1: consumes behavior_cleaner's resolved_field / key_role /
    # view_resolved, so it is only ever computable on CLEANED input - a
    # measurable flag of 0 here means the cleaner did not run, not that the
    # user typed nothing.
    (r'^kbres_',                        'KB', 'features from the cleaner\'s '
                                              'touch<->key join'),
    (r'^kb_',                           'KB', 'keyboard-geometry keystroke'),

    # ---- K / KG: keystrokes
    (r'^kg_n_',                          'X', 'keystroke window counts'),
    (r'^kg_.*_measurable$',              'X', 'keystroke sub-family flag'),
    (r'^kg_settle_n$',                   'X', 'settle sample count'),
    (r'^kg_',                           'KG', 'sensor conditioned on key label'),
    (r'^key_',                           'K', 'keystroke dynamics'),

    # ---- T: touch contact geometry (rev 4)
    (r'^tgeo_',                          'T', 'contact ellipse geometry'),

    # ---- G: touch-gated sensor windows
    (r'^tap_',                           'G', 'sensor window around each touch'),
    (r'^tmc_',                           'G', 'touch/motion energy coupling'),
    # rev 4.1: the tap ringdown. Bucket G, not D, because the window is defined
    # by a touch - it is the phone-in-hand system's impulse response, so it is
    # meaningless without the touch that excited it.
    (r'^tapdamp_',                       'G', 'damped natural frequency and log '
                                              'decrement of the post-tap ringdown'),

    # ---- W: world-frame (rev 4). Before F, since wf_ pairs two streams.
    (r'^wf_',                            'W', 'world-frame / gravity-projected'),
    (r'^dtw_wf_',                        'W', 'DTW on a world-frame channel'),

    # ---- F: genuine cross-sensor coupling
    # rev 4.1: coherence is frequency-resolved coupling between two DIFFERENT
    # sensors, which is what bucket F means. Ahead of the corr_ rules because
    # coh_acc_gyro_* would otherwise fall through to E.
    (r'^coh_',                           'F', 'magnitude-squared coherence and '
                                              'coupling stability across sensors'),
    (r'^mi_',                            'F', 'mutual information across sensors'),
    (r'^lag_',                           'F', 'cross-sensor lag structure'),
    (r'^xcorr_',                         'F', 'cross-correlation'),
    (r'^corr_(acc|gyro|mag|grav|lin|grv)_(acc|gyro|mag|grav|lin|grv)_',
                                         'F', 'between-sensor correlation'),
    (r'^tilt_',                          'F', 'acc/gyro fused tilt'),

    # ---- E: within one sensor, axes compared
    (r'^corr_(acc|gyro|mag)_[xyz]{2}',   'E', 'axis pairs within one sensor'),
    (r'^corr_',                          'E', 'correlation, single sensor'),

    # ---- P: platform-fused streams
    (r'^(grav|lin|rv|grv)_',             'P', 'platform sensor-fusion output'),
    (r'^orient_',                        'P', 'quaternion orientation'),
    (r'^motion_',                        'P', 'derived from linear_acceleration'),

    # ---- D: raw single IMU stream
    (r'^(acc|gyro|mag)_',                'D', 'single raw stream'),

    # ---- C / B / A: behavioural
    (r'^scr_',                           'C', 'per-screen behavioural profile'),
    (r'^cog_',                           'C', 'cognitive, touch + navigation'),
    (r'^nav_',                           'B', 'navigation events'),
    (r'^(touch|path)_',                  'A', 'touch events only'),

    # ---- DTW: bucket depends on the channel it templates
    (r'^dtw_(grav|lin|rv|grv|tilt|motion)_',
                                         'P', 'DTW on a fused channel'),
    (r'^dtw_(acc|gyro|mag)_',            'D', 'DTW on a raw stream'),
    (r'^dtw_(touch|path)_',              'A', 'DTW on a touch channel'),
    (r'^dtw_key_',                       'K', 'DTW on a keystroke channel'),
    (r'^dtw_',                           '?', 'DTW, channel unrecognised'),
]

_COMPILED = [(re.compile(p), b, w) for p, b, w in _RULES]

# Columns that are identifiers, not features.
#
# session_start_ts is HERE, not in bucket H. It is raw wall-clock epoch time.
# Every enrolment session predates every test session, so after StandardScaler
# it is always a large z-score at scoring time -- and where genuine and impostor
# collection happened in different time blocks it is a perfect label. Measured
# single-feature AUC from session_start_ts alone: reddy 0.580, srikanth 1.000,
# test 0.506.
ID_COLUMNS = {'session_id', 'session_label', 'label', 'test_type',
              'impostor_user_id', 'user_id', 'device_id', 'operator_id',
              'install_id', 'session_type', 'profile_type',
              'session_start_ts'}

# Bucket H and bucket N are excluded by default. See the module docstring.
DEFAULT_EXCLUDE = ('X', 'XF', 'ID', '?', 'H', 'N')


def bucket_of(column):
    """
    (bucket, reason) for one column name.

    Returns ('?', ...) rather than guessing when nothing matches. An
    unclassified column is a real signal - either a new family was added without
    updating this file, or the column is misnamed.

    Order of adjudication, rev 4:
      1. identifier
      2. excluded GROUP            -> XF
      3. extensive-count SUFFIX    -> N     <-- NEW, and it is deliberately
                                               ahead of the family rules, since
                                               that is exactly the precedence
                                               that was missing
      4. family rules              -> A..V, W/T/KB/L, X, H
      5. nothing matched           -> ?
    """
    if column in ID_COLUMNS:
        return 'ID', 'identifier, not a feature'
    if excluded_family_of(column) is not None:
        return FAMILY_BUCKET, exclusion_reason(column)
    quarantined, why = _suffix_quarantined(column)
    if quarantined:
        return 'N', f'extensive count: {why}'
    for rx, b, why in _COMPILED:
        if rx.search(column):
            return b, why
    return '?', 'no rule matched'


def model_columns(columns, exclude=DEFAULT_EXCLUDE):
    """
    The columns that should actually be fed to the model.

    Excludes diagnostics, session metadata, withheld groups AND extensive counts
    by default. To run a single-bucket experiment, add bucket codes:

        model_columns(cols, exclude=('X','XF','ID','?','H','N','D','E','P','G'))

    leaves the behavioural buckets only.

        model_columns(cols, exclude=[b for b in BUCKETS if b != 'A'] + ['ID'])

    leaves touch only.
    """
    exclude = tuple(exclude)
    assert_known_buckets(exclude)
    return [c for c in columns if bucket_of(c)[0] not in exclude]


def assert_known_buckets(codes):
    """
    Fail loudly on an unrecognised bucket code.

    new_feature_selection_v4.numeric_universe() hard-codes
    keep_buckets = set('ABCDEFGKPV') | {'KG'}. Adding a bucket without editing
    that line drops every column in it SILENTLY - the features are computed,
    written, and never seen again, and nothing prints. Both directions of that
    mistake now raise.
    """
    unknown = sorted(set(codes) - VALID_BUCKETS)
    if unknown:
        raise ValueError(
            f'unknown bucket code(s) {unknown}. Known: {sorted(VALID_BUCKETS)}. '
            f'If you added a family, add its bucket to BUCKETS in '
            f'new_feature_registry.py AND to keep_buckets in '
            f'new_feature_selection_v4.numeric_universe().')


# ##########################################################################
#  from new_feature_creation_session.py
#  ID_COLUMNS only
#  1 name(s), 7 source lines copied verbatim, 1 edit(s) (see header)
# ##########################################################################


# Columns that identify a session rather than describe behaviour. They are
# written to the CSV because they are needed for auditing and error analysis,
# and they are listed here so the training script can drop exactly these and
# nothing else.
FCS_ID_COLUMNS = ['session_id', 'session_type', 'operator_id', 'device_id',
                  'session_start_ts', 'label', 'test_type', 'san_verdict',
                  'feat_errors']


# ##########################################################################
#  from prescreen_v2.py
#  viability gates + robust Fisher (also served to prescreen_v3_device.py)
#  14 name(s), 235 source lines copied verbatim, 0 edit(s) (see header)
# ##########################################################################


MIN_DISTINCT_FRAC = 0.20
MIN_PRESENCE = 0.60
MIN_WITHIN_VAR = 1e-6
PERM_N = 200
PERM_Q = 0.95
WINSOR = 10.0   # clip standardised values to +/- this many robust SDs


def _winsor(Z, lim=WINSOR):
    """Clip standardised values.

    A feature whose MAD is tiny but non-zero (a near-quantised channel) produces
    z-scores in the thousands, a between-variance in the billions, and a Fisher
    ratio of 1e23. That is not a discriminative feature, it is a division. On
    your data touch_press_slope did exactly this. Clipping at +/-10 robust SDs
    keeps genuine outliers visible while removing the numerical blow-ups, and it
    is applied identically to observed and permuted data so the null stays
    comparable.
    """
    return np.clip(Z, -lim, lim)


def _num(df, cols):
    return df[cols].apply(pd.to_numeric, errors='coerce')


def viability_mask(frames, cols, min_presence=MIN_PRESENCE,
                   min_distinct=MIN_DISTINCT_FRAC, verbose=True):
    """Per-(user, feature) usability. Rows = users, cols = features, bool.

    Three independent reasons a feature can be unusable for one user: it is
    mostly absent, it is too coarsely quantised to carry information, or it is
    frozen. Each is decided for that user alone.
    """
    users = list(frames)
    pres, res, var = {}, {}, {}
    for u in users:
        d = _num(frames[u], cols)
        v = d.to_numpy(float)
        pres[u] = pd.Series((np.isfinite(v) & (v != 0.0)).mean(axis=0), index=cols)
        res[u] = d.nunique(dropna=False) / max(len(d), 1)
        med = d.median()
        mad = (d - med).abs().median() * 1.4826
        scale = mad.where(mad > 1e-12,
                          (d.quantile(0.75) - d.quantile(0.25)) / 1.349)
        z = (d - med) / scale.replace(0.0, np.nan)
        var[u] = z.var(ddof=1)
    P = pd.DataFrame(pres).T.reindex(index=users, columns=cols)
    R = pd.DataFrame(res).T.reindex(index=users, columns=cols)
    V = pd.DataFrame(var).T.reindex(index=users, columns=cols)

    ok_p = P >= min_presence
    ok_r = R >= min_distinct
    ok_v = V.fillna(0.0) >= MIN_WITHIN_VAR
    mask = ok_p & ok_r & ok_v

    if verbose:
        print('  [prescreen_v2] per-user viability')
        for u in users:
            print(f'    {u:12s} presence {int(ok_p.loc[u].sum()):5d} | '
                  f'resolution {int(ok_r.loc[u].sum()):5d} | '
                  f'live variance {int(ok_v.loc[u].sum()):5d} | '
                  f'ALL THREE {int(mask.loc[u].sum()):5d} of {len(cols)}')
        n_all = int(mask.all(axis=0).sum())
        n_any = int(mask.any(axis=0).sum())
        print(f'    viable for EVERY user: {n_all}   for at least one: {n_any}')
        if n_any > n_all * 1.2:
            weakest = mask.sum(axis=1).idxmin()
            print(f'    -> {n_any - n_all} features are usable by some users but not all. '
                  f'{weakest} is the limiting user.')
            print(f'       A shared feature list throws those away. Prefer per-user lists.')
    return mask, P, R, V


def robust_fisher(frames, cols, mask=None, verbose=True):
    """Fisher ratio on median/MAD-standardised features, within = median across
    users, between corrected for the noise each per-user mean carries.

    Cells that are not viable for a user are excluded from that user's
    contribution rather than imputed, so a dead channel neither inflates nor
    deflates the score.
    """
    users = list(frames)
    pooled = pd.concat([_num(frames[u], cols) for u in users], ignore_index=True)
    med = pooled.median()
    mad = (pooled - med).abs().median() * 1.4826
    scale = mad.where(mad > 1e-12, (pooled.quantile(0.75) - pooled.quantile(0.25)) / 1.349)
    scale = scale.replace(0.0, np.nan)

    Vs, Ms, Ns = [], [], []
    for u in users:
        d = _num(frames[u], cols)
        z = (d - med) / scale
        z = z.fillna(z.median())          # user's OWN median, not the pooled mean
        z = z.clip(-WINSOR, WINSOR)
        if mask is not None:
            m = mask.loc[u].reindex(z.columns).fillna(False).to_numpy(bool)
            z = z.mask(~np.broadcast_to(m, z.shape))
        Vs.append(z.var(ddof=1).to_numpy())
        Ms.append(z.mean().to_numpy())
        Ns.append(len(z))
    V, M = np.vstack(Vs), np.vstack(Ms)
    with np.errstate(all='ignore'):
        within = np.nanmedian(V, axis=0)
        kbar = float(np.mean(Ns))
        between = np.maximum(np.nanvar(M, axis=0, ddof=1) - within / max(kbar, 1.0), 0.0)
        fl = _within_floor(within)
        F = np.where(np.isfinite(within) & (within >= fl), between / within, np.nan)
    out = pd.Series(F, index=cols)
    health = pd.Series(within + between, index=cols)
    if verbose:
        v = health[out.notna()]
        n_bad = int((v < 0.1).sum())
        print(f'  [prescreen_v2] robust Fisher on {int(out.notna().sum())} features')
        print(f'    variance-health (within+between, should be ~1.0): '
              f'median {v.median():.3f}, {n_bad} feature(s) below 0.1')
        if n_bad:
            print(f'    -> {n_bad} feature(s) have outlier-dominated pooled scale. '
                  f'Run outlier_audit.py before trusting their Fisher values.')
    return out, health


def _within_floor(V):
    """Data-driven floor for the Fisher denominator.

    MIN_WITHIN_VAR=1e-6 is far below anything real, so a feature that happens to
    have a near-zero within-variance divides by it and scores 1e23. Those are
    numerical artefacts, not discoveries, and with `max` as the null statistic a
    single one of them makes the whole permutation test meaningless. Floor at the
    5th percentile of observed within-variance instead, and treat anything under
    it as unusable rather than infinitely good.
    """
    w = V[np.isfinite(V) & (V > 0)]
    return float(np.percentile(w, 5)) if w.size else MIN_WITHIN_VAR


def _fisher_np(blocks, floor=None):
    """Fisher vector from a list of per-user 2-D arrays, already standardised.
    Pure numpy so the permutation loop is not pandas-bound."""
    V = np.vstack([np.nanvar(b, axis=0, ddof=1) for b in blocks])
    M = np.vstack([np.nanmean(b, axis=0) for b in blocks])
    with np.errstate(all='ignore'):
        within = np.nanmedian(V, axis=0)
        fl = _within_floor(within) if floor is None else floor
        kbar = float(np.mean([len(b) for b in blocks]))
        between = np.maximum(np.nanvar(M, axis=0, ddof=1) - within / max(kbar, 1.0), 0.0)
        return np.where(np.isfinite(within) & (within >= fl), between / within, np.nan), fl


def permutation_cut(frames, cols, observed, mask=None, n_perm=PERM_N, q=PERM_Q,
                    budget=200, seed=0, fdr=0.10, verbose=True):
    """How many features actually beat chance?

    Shuffle which user each session belongs to, recompute Fisher, and record the
    q-quantile of the null. Any observed Fisher above that is a candidate; the
    count is the honest keep_n. Sessions are shuffled as whole sessions across
    users, which preserves each feature's marginal distribution and destroys only
    the user structure - that is exactly the null we want.
    """
    rng = np.random.default_rng(seed)
    users = list(frames)
    sizes = [len(frames[u]) for u in users]
    big = pd.concat([_num(frames[u], cols) for u in users], ignore_index=True)
    med = big.median()
    mad = (big - med).abs().median() * 1.4826
    scale = mad.where(mad > 1e-12,
                      (big.quantile(0.75) - big.quantile(0.25)) / 1.349).replace(0.0, np.nan)
    Zall = _winsor(((big - med) / scale).to_numpy(float))
    Vobs = np.vstack([np.nanvar(Zall[sum(sizes[:i]):sum(sizes[:i + 1])], axis=0, ddof=1)
                      for i in range(len(sizes))])
    obs_floor = _within_floor(np.nanmedian(Vobs, axis=0))
    nulls = []
    for _ in range(n_perm):
        perm = rng.permutation(len(Zall))
        blocks, i = [], 0
        for n in sizes:
            blocks.append(Zall[perm[i:i + n]])
            i += n
        f, _fl = _fisher_np(blocks, floor=obs_floor)
        nulls.append(f)
    nulls = np.concatenate([n[np.isfinite(n)] for n in nulls])
    obs = observed.dropna()
    n_feat = len(obs)

    # FDR cut: at threshold t, expected false positives = n_feat * P(null > t).
    # Take the largest candidate set whose expected false-positive fraction stays
    # under `fdr`. This replaces the hardcoded 200 with a number that answers
    # 'how many of these would shuffled labels have produced anyway'.
    order = np.sort(obs.to_numpy())[::-1]
    keep_n, thresh = 0, float('inf')
    for k in range(1, n_feat + 1):
        t = order[k - 1]
        exp_fp = n_feat * float((nulls > t).mean())
        if exp_fp / k > fdr:
            break                      # step-down: stop at the first violation
        keep_n, thresh = k, float(t)
    keep_n = int(min(budget, keep_n))
    n_beat = keep_n
    if verbose:
        print(f'  [prescreen_v2] permutation null over {n_perm} label shuffles '
              f'({len(nulls)} null Fisher values)')
        print(f'    within-variance floor (5th pct): {obs_floor:.4g}')
        print(f'    null Fisher: median {np.median(nulls):.3f}  q95 '
              f'{np.quantile(nulls, 0.95):.3f}  q99.9 {np.quantile(nulls, 0.999):.3f}')
        print(f'    FDR<={fdr:.2f} threshold: Fisher > {thresh:.3f} -> {n_beat} feature(s)')
        print(f'    observed max {obs.max():.3f} at {obs.idxmax()}')
        if n_beat == 0:
            print(f'    !! NOTHING beats a shuffled-label null. With {len(users)} users '
                  f'the between-user variance has {len(users) - 1} df and cannot')
            print(f'       support screening {len(cols)} candidates. More users is the '
                  f'only fix; downstream elimination cannot recover this.')
        elif n_beat < budget:
            print(f'    -> keep_n reduced from {budget} to {keep_n}. The other '
                  f'{budget - n_beat} would be noise you then spend wrapper time on.')
    return keep_n, thresh, nulls


def prescreen_v2(frames, cols, keep_n=200, per_user=True, calibrate=True,
                 verbose=True):
    """Returns (candidates, fisher_series, viability_mask).

    `candidates` is a dict of user -> list when per_user=True, else a single list.
    Pass the dict straight into your fold builder and fit each user's model on
    that user's own columns; nothing downstream requires a shared feature space
    except the correlation clustering, which should also be run per user.
    """
    mask, P, R, V = viability_mask(frames, cols, verbose=verbose)
    viable_any = [c for c in cols if bool(mask[c].any())]
    F, health = robust_fisher(frames, viable_any, mask=mask, verbose=verbose)

    if calibrate:
        keep_n, thresh, _ = permutation_cut(frames, viable_any, F, mask=mask,
                                            budget=keep_n, verbose=verbose)
        keep_n = max(keep_n, 20)   # floor so the wrapper still has something to chew

    ranked = F.dropna().sort_values(ascending=False)
    if per_user:
        out = {}
        for u in frames:
            ok = [c for c in ranked.index if bool(mask.loc[u, c])]
            out[u] = ok[:keep_n]
            if verbose:
                print(f'    {u:12s} -> {len(out[u])} candidates')
    else:
        shared = [c for c in ranked.index if bool(mask[c].all())]
        out = shared[:keep_n]
        if verbose:
            print(f'    shared -> {len(out)} candidates '
                  f'(costs you {len(ranked) - len(shared)} features that only some '
                  f'users can measure)')
    return out, F, mask


# ##########################################################################
#  prescreen_v3_device.py (kept as a separate, unmodified file) runs
#      from prescreen_v2 import prescreen_v2, viability_mask, robust_fisher
#  when it is imported. Serve that import from the copies above, so
#  prescreen_v2.py is not needed and a stray copy of it cannot be picked up.
# ##########################################################################

_prescreen_v2_module = _types.ModuleType('prescreen_v2')
_prescreen_v2_module.MIN_DISTINCT_FRAC = MIN_DISTINCT_FRAC
_prescreen_v2_module.MIN_PRESENCE = MIN_PRESENCE
_prescreen_v2_module.MIN_WITHIN_VAR = MIN_WITHIN_VAR
_prescreen_v2_module.PERM_N = PERM_N
_prescreen_v2_module.PERM_Q = PERM_Q
_prescreen_v2_module.WINSOR = WINSOR
_prescreen_v2_module._fisher_np = _fisher_np
_prescreen_v2_module._num = _num
_prescreen_v2_module._winsor = _winsor
_prescreen_v2_module._within_floor = _within_floor
_prescreen_v2_module.permutation_cut = permutation_cut
_prescreen_v2_module.prescreen_v2 = prescreen_v2
_prescreen_v2_module.robust_fisher = robust_fisher
_prescreen_v2_module.viability_mask = viability_mask
sys.modules['prescreen_v2'] = _prescreen_v2_module


# ##########################################################################
#  from new_feature_selection_v4.py
#  config, loaders, numeric universe, gamma, AUC, representatives
#  24 name(s), 267 source lines copied verbatim, 1 edit(s) (see header)
# ##########################################################################


EXTRA_NON_FEATURES = {'user_id', 'impostor_user_id', 'session_label',
                      'install_id', 'profile_type', '__label__'}

NU = 0.05
KERNEL = 'rbf'
# 'median' resolves per fit. A float re-introduces the confound described above.
GAMMA = 'median'

# --- validation construction ------------------------------------------------
# Fraction of each user's TRAINING sessions held back as validation genuine. A
# temporal split (the last VAL_FRAC), not random: sessions minutes apart are
# near-duplicates, and a random split would put twins on both sides and report an
# AUC that measures nothing.
VAL_FRAC = 0.30

# A user needs this many training sessions to be usable: enough to fit on after
# giving up VAL_FRAC.
MIN_TRAIN_SESSIONS = 12
# Between-user structure is the whole signal. Below this many users there is
# nothing to select on.
MIN_USERS = 2

# --- Phase 1 pre-screen -----------------------------------------------------
VAR_EPS = 1e-9              # std below this for ANY user = unusable feature

# Wrapper elimination costs O(candidates^2 x users) model fits, so the candidate
# set has to be pre-screened to something tractable. This is what the filter
# method is genuinely good for.
PRESCREEN_KEEP = 400

# --- Phase 2 clustering -----------------------------------------------------
CORR_THRESHOLD = 0.90

# --- Phase 3 backward elimination -------------------------------------------
SBS_TOL = 0.001             # accept a removal if macro val AUC drops <= this

SBS_CANDIDATE_CAP = 60      # per step, only try removing this many weakest
SBS_MAX_STEPS = 400         # hard stop, so a pathological run cannot hang

# Above this starting AUC the validation set is SATURATED: the users are trivially
# separable on the pre-screened features, so removing any one of them costs nothing
# and the elimination has no gradient to follow. It will then run to the feature
# floor and return whichever features happen to survive, with every margin at
# exactly 0.00000 - an answer that looks confident and is arbitrary.
#
# Observed on the reference data with 2 users: starting AUC 1.00000, seven removals
# at 1.00000, all margins 0.00000. The cause is the impostor pool - with one other
# user it holds 8 sessions from a single person, and any reasonable feature set
# separates two people perfectly. Wrapper selection needs enough users that the
# validation problem is actually hard.
SATURATION_AUC = 0.995

SAME_DEVICE_EXCLUDE_BUCKETS = ('H',)
RANDOM_SEED = 42


def normalise_label(x):
    """
    'genuine' / 'impostor' / 'unknown'.

    Explicit membership. The original used a substring test that silently mapped
    every unrecognised value to impostor, which deflates FAR - failure in the
    flattering direction.
    """
    s = str(x).strip().lower()
    if s in ('genuine', 'owner', 'legitimate', 'enrollment', 'enrolment'):
        return 'genuine'
    if s in ('impostor', 'imposter', 'attack', 'attacker', 'spoof'):
        return 'impostor'
    return 'unknown'


def discover_users(feature_dir):
    suf = '_training_sessions.csv'
    if not os.path.isdir(feature_dir):
        raise FileNotFoundError(feature_dir)
    return sorted(f[:-len(suf)] for f in os.listdir(feature_dir)
                  if f.endswith(suf))


def load_enrolment(feature_dir, users, verbose=True):
    """
    Per-user enrolment matrices. Reads *_training_sessions.csv ONLY.

    Rows are assumed chronological, which the feature pipeline guarantees
    (split_by_type time-sorts and _frame preserves order). Verified rather than
    assumed, because the temporal validation split depends on it.
    """
    frames = {}
    for u in users:
        p = os.path.join(feature_dir, f'{u}_training_sessions.csv')
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p, low_memory=False)
        if len(df) < MIN_TRAIN_SESSIONS:
            if verbose:
                print(f'  [skip] {u}: {len(df)} training session(s), '
                      f'need >= {MIN_TRAIN_SESSIONS}')
            continue
        if 'session_start_ts' in df.columns:
            t = pd.to_numeric(df['session_start_ts'], errors='coerce')
            if len(t.dropna()) > 1 and not (t.diff().dropna() >= 0).all():
                print(f'  ! {u}: training rows are NOT chronological; the '
                      f'temporal validation split will behave like a random one')
        frames[u] = df
    return frames


def write_ranking(path, all_numeric, universe, fisher, viability, cand,
                  clusters, reps, final, history, marg, verbose=True):
    """One row per numeric column, with the stage that decided its fate.

    Answers "why is feature X not in my model?" without rerunning anything.
    Every column gets a row, including ones the registry withheld before any
    scoring happened, because "withheld by provenance" and "scored badly" are
    different answers and you need to tell them apart.
    """
    import csv as _csv

    ranked = list(fisher.dropna().sort_values(ascending=False).index)
    frank = {c: i + 1 for i, c in enumerate(ranked)}

    cid, isrep = {}, set(reps or [])
    for i, grp in enumerate(clusters or []):
        for c in grp:
            cid[c] = i

    elim = {}
    for i, h in enumerate(history or []):
        if h.get('removed'):
            elim[h['removed']] = i + 1

    mg = {r['feature']: r['margin'] for r in (marg or [])}
    uni, cnd, fin = set(universe), set(cand or []), set(final or [])

    def stage(c):
        if c in fin:
            return 'SELECTED'
        if c in elim:
            return 'eliminated'
        if c in isrep:
            return 'rep_not_selected'
        if c in cnd:
            return 'cluster_absorbed'
        if c in uni:
            return ('prescreen_rank_cut' if c in frank
                    else 'prescreen_unviable')
        return f'registry_{(bucket_of(c)[0] if bucket_of else "?")}'

    rows = []
    for c in all_numeric:
        rows.append({
            'feature': c,
            'stage_out': stage(c),
            'selected': int(c in fin),
            'bucket': bucket_of(c)[0] if bucket_of else '?',
            'excluded_pattern': (excluded_family_of(c) or ''
                                 if excluded_family_of else ''),
            'in_universe': int(c in uni),
            'fisher': ('' if c not in fisher.index or pd.isna(fisher[c])
                       else round(float(fisher[c]), 6)),
            'fisher_rank': frank.get(c, ''),
            'passed_prescreen': int(c in cnd),
            'cluster_id': cid.get(c, -1),
            'is_cluster_rep': int(c in isrep),
            'elim_step': elim.get(c, ''),
            'margin': ('' if c not in mg else round(mg[c], 6)),
        })

    order = {'SELECTED': 0, 'eliminated': 1, 'rep_not_selected': 2,
             'cluster_absorbed': 3, 'prescreen_rank_cut': 4,
             'prescreen_unviable': 5}
    rows.sort(key=lambda r: (order.get(r['stage_out'], 9),
                             r['fisher_rank'] if r['fisher_rank'] else 10 ** 9))

    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = _csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    if verbose:
        c = Counter(r['stage_out'] for r in rows)
        print(f'\n  ranking -> {path}   ({len(rows)} column(s))')
        for k in sorted(c, key=lambda x: order.get(x, 9)):
            print(f'      {c[k]:6d}  {k}')
    return rows


def numeric_universe(frames, same_device_impostors=True, verbose=True):
    """
    Candidate columns common to every user, before any statistical screening.

    Built from the CSV columns rather than an external features.txt. The original
    read a separate text file, which can silently drift out of step with the data
    it names - and when it does, the mismatch surfaces as features quietly missing
    from a user's universe rather than as an error.
    """
    common = None
    for df in frames.values():
        s = set(df.columns)
        common = s if common is None else (common & s)
    common = sorted(common or [])

    ids = set(FCS_ID_COLUMNS) | EXTRA_NON_FEATURES
    cols = [c for c in common if c not in ids]

    cols = [c for c in cols
            if all(pd.api.types.is_numeric_dtype(df[c]) for df in frames.values())]

    if model_columns is not None:
        keep = set(model_columns(cols))
        n0 = len(cols)
        cols = [c for c in cols if c in keep]
        if verbose:
            print(f'  -{n0 - len(cols):<5d} diagnostic (bucket X)')

    if same_device_impostors and bucket_of is not None:
        bad = set(SAME_DEVICE_EXCLUDE_BUCKETS)
        n0 = len(cols)
        cols = [c for c in cols if bucket_of(c)[0] not in bad]
        if verbose:
            print(f'  -{n0 - len(cols):<5d} device / session metadata '
                  f'(same-device impostors)')
    return cols


def resolve_gamma(gamma, Z):
    """
    Median heuristic, resolved per fit.

    This is the fix that makes backward elimination measure feature quality rather
    than dimensionality. See the module docstring.
    """
    if gamma != 'median':
        return gamma
    if len(Z) < 3:
        return 'scale'
    idx = np.arange(len(Z))
    if len(Z) > 300:
        idx = np.random.default_rng(0).choice(len(Z), 300, replace=False)
    d2 = pdist(Z[idx], 'sqeuclidean')
    d2 = d2[d2 > 0]
    return float(1.0 / np.median(d2)) if d2.size else 'scale'


def roc_auc(pos, neg):
    """
    AUC via rank statistic. Ties get 0.5 credit.

    Implemented directly rather than through sklearn so ties are handled explicitly
    - with quantised features, tied scores are common, and silently breaking ties
    in the positive class's favour would inflate the metric everywhere.
    """
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    if pos.size == 0 or neg.size == 0:
        return float('nan')
    allv = np.concatenate([pos, neg])
    order = allv.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, allv.size + 1)
    # average ranks within tie groups
    s = pd.Series(allv)
    ranks = s.rank(method='average').values
    r_pos = ranks[:pos.size].sum()
    return float((r_pos - pos.size * (pos.size + 1) / 2.0) /
                 (pos.size * neg.size))


def pick_representatives(folds, clusters, fisher, verbose=True):
    """
    One feature per cluster: the highest Fisher ratio within it.

    The original used permutation importance here. Fisher is used instead because
    at this point the members of a cluster are correlated above 0.90 - they are
    near-substitutes, so the choice among them barely affects the wrapper stage,
    and permutation importance would cost a model fit per member per repeat for a
    decision that is close to arbitrary. The expensive, careful comparison is
    Phase 3's job.
    """
    reps = []
    for g in clusters:
        reps.append(max(g, key=lambda c: fisher.get(c, 0.0)))
    if verbose:
        multi = sum(1 for g in clusters if len(g) > 1)
        big = sorted(clusters, key=len, reverse=True)[:3]
        print(f'  {len(clusters)} cluster(s) from {sum(len(g) for g in clusters)} '
              f'features; {multi} had >1 member')
        for g in big:
            if len(g) > 1:
                print(f'    {len(g):3d} members, rep = '
                      f'{max(g, key=lambda c: fisher.get(c, 0.0))}')
    return reps


# ##########################################################################
#  from new_feature_selection_v4_v3.py
#  load ALL attackers
#  3 name(s), 54 source lines copied verbatim, 0 edit(s) (see header)
# ##########################################################################


# Minimum impostor sessions a user needs before their fold is usable. Lower than
# v4's effective floor because no sessions are being reserved here - every
# impostor session the user has is in play.
MIN_IMPOSTORS = 4

# Filenames this script refuses to overwrite without an explicit override,
# because they are what new_train_session.py gets pointed at in practice.
PROTECTED_OUT = ('selected_rev', 'selected_features')


def load_all_attackers(feature_dir, users, cols, verbose=True):
    """
    EVERY impostor session from EVERY attacker, per user.

    This is the whole point of the experiment and the whole reason the output is
    not deployable. v4's load_selection_attackers() splits attackers into a
    selection fold and a reserved fold and returns only the former; this returns
    all of them.

    Genuine rows in the testing CSVs are still never read. That restraint is
    kept deliberately: it costs nothing here, and it means a later honest
    evaluation of the genuine side is still possible even after this probe has
    been run.
    """
    per_user, all_att = {}, {}
    for u in users:
        p = os.path.join(feature_dir, f'{u}_testing_sessions.csv')
        if not os.path.exists(p):
            if verbose:
                print(f'  [no testing CSV] {u}')
            continue
        df = pd.read_csv(p, low_memory=False)
        if df.empty:
            continue
        lc = next((c for c in ('test_type', 'session_label', 'label')
                   if c in df.columns), None)
        if lc is None or 'operator_id' not in df.columns:
            if verbose:
                print(f'  [no label/operator column] {u}')
            continue

        imp = df[df[lc].map(normalise_label) == 'impostor']
        if len(imp) < MIN_IMPOSTORS:
            if verbose:
                print(f'  [too few impostors] {u}: {len(imp)} '
                      f'(need >= {MIN_IMPOSTORS})')
            continue

        att = sorted(set(imp['operator_id'].astype(str)))
        X = imp[cols].apply(pd.to_numeric, errors='coerce').fillna(0.0).values
        per_user[u] = X
        all_att[u] = att
        if verbose:
            print(f'  {u:14s} ALL {len(att):2d} attacker(s), '
                  f'{len(X):3d} impostor session(s)   '
                  f'[v4 would have reserved ~{max(0, len(att) - int(round(len(att) * 0.45)))}]')
    return per_user, all_att


# ##########################################################################
#  from new_feature_selection_v6.py
#  robust correlation clustering + audit
#  11 name(s), 343 source lines copied verbatim, 1 edit(s) (see header)
# ##########################################################################


# Aggregators available for combining per-user correlation matrices.
CORR_AGGREGATORS = ('mean', 'median', 'trimmed', 'quantile')

# Default across-user spread above which a pair is refused a merge regardless of
# its central value. 0.15 is chosen to be permissive: with ~33 fit rows per user
# the standard error on a single r near 0.9 is roughly 0.03-0.05, so genuine
# agreement should sit well inside 0.15 and only real disagreement trips it.
DEFAULT_DISPERSION_MAX = 0.15

# Quantile used by --corr-agg quantile. 0.25 means "at least 75% of users must
# report this pair above threshold".
DEFAULT_CORR_Q = 0.25

# Clamp before the Fisher-z transform. arctanh(1.0) is infinite, and a feature
# pair that is numerically identical for one user would otherwise poison the
# aggregate with an inf. 0.999999 keeps z finite at ~7.25.
FISHER_CLAMP = 0.999999


def per_user_corr_stack(folds, feats, verbose=True):
    """
    The per-user |r| matrices, stacked rather than accumulated.

    v4 accumulates into a running sum and divides at the end, which is what
    forces the mean and makes any other estimator impossible. Keeping the stack
    costs n_users * n_feats^2 floats - at 8 users and 400 features that is about
    10 MB, which is nothing - and it is what lets every aggregator below, and
    the audit, work from the same numbers.

    Standardisation before np.corrcoef is kept from v4 even though correlation
    is scale-invariant, so that the degenerate-column handling (std < VAR_EPS
    mapped to divisor 1.0) matches v4's behaviour exactly on constant columns.

    Computed on the FIT blocks only - never on validation - so the clustering
    cannot be shaped by the data the wrapper is scored against. Unchanged from
    v4 and load-bearing.

    Returns (stack, users_used) where stack has shape (n_users, n_feats, n_feats).
    """
    n = len(feats)
    mats, used_users = [], []

    for u, f in folds.items():
        X = f['fit']
        if X.shape[1] != n:
            # v4 skipped this silently via `if C.shape == (n, n)`. A silent skip
            # means `used` quietly disagrees with the user count and the average
            # is over a different denominator than anyone reading the code
            # expects. Say it out loud instead.
            print(f'  !! {u}: fit block has {X.shape[1]} columns, expected {n}'
                  f' - EXCLUDED from correlation')
            continue

        sd = X.std(0)
        Z = (X - X.mean(0)) / np.where(sd < VAR_EPS, 1.0, sd)
        C = np.abs(np.nan_to_num(np.corrcoef(Z, rowvar=False)))

        if C.shape != (n, n):
            print(f'  !! {u}: correlation matrix came back {C.shape}, '
                  f'expected {(n, n)} - EXCLUDED from correlation')
            continue

        # A column that is constant for this user has undefined correlation with
        # everything. np.nan_to_num already turned those into 0.0, which reads as
        # "uncorrelated" and is the safe direction: it can only prevent a merge,
        # never force one.
        mats.append(C)
        used_users.append(u)

    if not mats:
        return None, []

    stack = np.stack(mats, axis=0)
    if verbose:
        print(f'  per-user correlation matrices: {len(used_users)} user(s) '
              f'x {n} x {n} features')
        if len(used_users) < len(folds):
            missing = sorted(set(folds) - set(used_users))
            print(f'  !! {len(missing)} user(s) excluded: {missing}')
    return stack, used_users


def _fisher_z(r):
    """r -> z. Clamped so an exactly-1.0 pair cannot produce an infinity."""
    return np.arctanh(np.clip(r, -FISHER_CLAMP, FISHER_CLAMP))


def _fisher_z_inv(z):
    """z -> r."""
    return np.tanh(z)


def aggregate_corr(stack, agg='median', use_fisher_z=True, q=DEFAULT_CORR_Q,
                   verbose=True):
    """
    Collapse the per-user stack to one consensus matrix.

    Aggregating in z space and transforming back is the standard treatment for
    averaging correlations and matters most near |r| = 0.9, which is precisely
    where the threshold sits. It is skipped for agg='mean' so that arm reproduces
    v4's arithmetic exactly rather than approximately.

    The median is order-preserving, so median-in-z and median-in-r give the same
    answer; the transform is applied anyway for uniformity and costs nothing.
    """
    k = stack.shape[0]

    if agg == 'mean' and not use_fisher_z:
        # The v4 path, reproduced rather than re-implemented.
        C = stack.mean(axis=0)
    else:
        W = _fisher_z(stack) if use_fisher_z else stack
        if agg == 'mean':
            A = W.mean(axis=0)
        elif agg == 'median':
            A = np.median(W, axis=0)
        elif agg == 'trimmed':
            if k <= 2:
                # Trimming both tails of 2 users leaves nothing. Degrade to the
                # median and say so rather than returning an empty slice.
                if verbose:
                    print(f'  !! only {k} user(s): trimmed mean falls back to '
                          f'median')
                A = np.median(W, axis=0)
            else:
                S = np.sort(W, axis=0)
                A = S[1:-1].mean(axis=0)
        elif agg == 'quantile':
            A = np.quantile(W, q, axis=0)
        else:
            raise ValueError(f'unknown aggregator {agg!r}')
        C = _fisher_z_inv(A) if use_fisher_z else A

    # The diagonal must be exactly 1 and the matrix exactly symmetric; quantile
    # and median can leave both slightly off through floating point.
    C = np.clip(C, 0.0, 1.0)
    C = (C + C.T) / 2.0
    np.fill_diagonal(C, 1.0)
    return C


def dispersion_matrix(stack):
    """
    Across-user spread of |r| for every pair.

    Interquartile range rather than standard deviation, deliberately: the whole
    reason this matrix exists is to detect a single deviant user, and the sd is
    itself inflated by exactly the outlier it is meant to catch. The IQR is not.
    """
    if stack.shape[0] < 4:
        # IQR over fewer than 4 users is not meaningful; fall back to range.
        return stack.max(axis=0) - stack.min(axis=0)
    return (np.quantile(stack, 0.75, axis=0) - np.quantile(stack, 0.25, axis=0))


def correlation_clusters_robust(folds, feats, threshold=None, agg='median',
                                use_fisher_z=True, q=DEFAULT_CORR_Q,
                                dispersion_max=DEFAULT_DISPERSION_MAX,
                                verbose=True, return_detail=False):
    """
    v4's union-find clustering with a robust aggregator and a dispersion veto.

    The union-find half is unchanged from v4 and is still better than greedy
    pruning, for v4's original reason: greedy walks a ranking and discards
    anything correlated with a survivor, so the survivor is whichever happened to
    rank first, whereas clustering groups first and chooses a representative on
    merit.

    What changes is which pairs get unioned:

      * the consensus |r| comes from `agg`, not necessarily the mean, so one
        user cannot carry a merge on their own;
      * a pair whose across-user IQR exceeds `dispersion_max` is REFUSED even
        when its consensus clears the threshold, because users disagreeing about
        whether two features move together is evidence that they are not one
        underlying quantity.

    Computed on the FIT blocks only, exactly as in v4.
    """
    if threshold is None:
        threshold = CORR_THRESHOLD

    n = len(feats)
    t0 = time.time()

    if verbose:
        print(f'  aggregator: {agg}'
              + (f' (q={q})' if agg == 'quantile' else '')
              + f' | Fisher-z: {"on" if use_fisher_z else "off"}'
              + f' | dispersion veto: '
              + (f'IQR > {dispersion_max}' if dispersion_max > 0 else 'off'))

    stack, used_users = per_user_corr_stack(folds, feats, verbose=verbose)
    if stack is None:
        if verbose:
            print('  !! no usable per-user correlation matrix; '
                  'every feature becomes its own cluster')
        empty = {'users': [], 'n_pairs_above': 0, 'n_vetoed': 0,
                 'consensus': None, 'dispersion': None, 'stack': None}
        return ([[c] for c in feats], empty) if return_detail \
            else [[c] for c in feats]

    C = aggregate_corr(stack, agg=agg, use_fisher_z=use_fisher_z, q=q,
                       verbose=verbose)
    D = dispersion_matrix(stack)

    # Upper triangle only - the matrix is symmetric and the diagonal is 1.
    iu = np.triu_indices(n, k=1)
    above = C[iu] >= threshold
    vetoed = above & (D[iu] > dispersion_max) if dispersion_max > 0 \
        else np.zeros_like(above)
    merge = above & ~vetoed

    if verbose:
        print(f'  pairs: {above.sum()} above |r| >= {threshold}, '
              f'{vetoed.sum()} vetoed for disagreement, '
              f'{merge.sum()} merged')
        if vetoed.sum():
            # These are the pairs the mean would have merged and this run did
            # not. They are the concrete difference between the two arms.
            vi, vj = iu[0][vetoed], iu[1][vetoed]
            order = np.argsort(-D[vi, vj])
            print(f'  most-disputed vetoed pairs (consensus |r| / IQR):')
            for t in order[:5]:
                i_, j_ = int(vi[t]), int(vj[t])
                per_u = ', '.join(f'{u}={stack[m, i_, j_]:.2f}'
                                  for m, u in enumerate(used_users))
                print(f'    {C[i_, j_]:.3f} / {D[i_, j_]:.3f}  '
                      f'{feats[i_]}  ~  {feats[j_]}')
                print(f'              [{per_u}]')

    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for t in np.nonzero(merge)[0]:
        union(int(iu[0][t]), int(iu[1][t]))

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(feats[i])
    clusters = list(groups.values())

    if verbose:
        sizes = sorted((len(g) for g in clusters), reverse=True)
        multi = sum(1 for s in sizes if s > 1)
        print(f'  -> {len(clusters)} cluster(s), {multi} with >1 member, '
              f'largest {sizes[0] if sizes else 0}  ({time.time() - t0:.0f}s)')

    if return_detail:
        detail = {
            'users': used_users,
            'n_pairs_above': int(above.sum()),
            'n_vetoed': int(vetoed.sum()),
            'consensus': C,
            'dispersion': D,
            'stack': stack,
        }
        return clusters, detail
    return clusters


def correlation_audit(stack, users, C, D, feats, threshold, path=None,
                      verbose=True):
    """
    Per-user deviation from consensus - the answer to "is one user damaging it?"

    For each user this reports, over all feature pairs:

      mean_abs_dev    mean |r_user - r_consensus|. A user whose correlation
                      structure simply differs from everyone else's.
      p95_abs_dev     the tail of that deviation. Catches a user who agrees on
                      most pairs but is wildly off on a few - the damaged-channel
                      signature, which the mean deviation can hide.
      frac_above      share of pairs this user puts above threshold. A rail-
                      clipped or stuck sensor inflates this hard; if one user
                      reports 60% of pairs correlated while everyone else reports
                      8%, that user is measuring their hardware, not behaviour.
      n_sole_driver   pairs where this user is above threshold and the consensus
                      (computed WITHOUT them) is not. This is the direct count of
                      merges this user would force single-handedly under a mean.

    n_sole_driver is the number to read first. Under v4's mean a user with a high
    count here is reshaping the feature space on their own.
    """
    k = stack.shape[0]
    rows = []
    iu = np.triu_indices(stack.shape[1], k=1)

    for m, u in enumerate(users):
        R = stack[m][iu]
        dev = np.abs(R - C[iu])

        if k > 1:
            # Leave-one-out consensus, so "sole driver" means the pair would not
            # have merged without this user rather than merely that they agreed
            # with a consensus they themselves helped set.
            others = np.delete(stack, m, axis=0)
            C_loo = np.median(others, axis=0)[iu]
            sole = int(((R >= threshold) & (C_loo < threshold)).sum())
        else:
            sole = 0

        rows.append({
            'user': u,
            'mean_abs_dev': float(dev.mean()),
            'p95_abs_dev': float(np.quantile(dev, 0.95)),
            'max_abs_dev': float(dev.max()),
            'frac_above_threshold': float((R >= threshold).mean()),
            'n_sole_driver': sole,
            'mean_abs_r': float(R.mean()),
        })

    audit = pd.DataFrame(rows).set_index('user').sort_values(
        'n_sole_driver', ascending=False)

    if verbose:
        print('\n  PER-USER CORRELATION AUDIT')
        print(f'    {"user":<12s} {"meanDev":>8s} {"p95Dev":>8s} '
              f'{"fracAbove":>10s} {"soleDrv":>8s} {"meanR":>7s}')
        for u, r in audit.iterrows():
            print(f'    {u:<12s} {r["mean_abs_dev"]:8.4f} '
                  f'{r["p95_abs_dev"]:8.4f} {r["frac_above_threshold"]:10.4f} '
                  f'{int(r["n_sole_driver"]):8d} {r["mean_abs_r"]:7.4f}')

        # Flag anyone whose behaviour is far enough from the group to be worth
        # a look. These are heuristics for directing attention, not verdicts.
        fa = audit['frac_above_threshold']
        if len(fa) >= 3:
            med, iqr = fa.median(), fa.quantile(.75) - fa.quantile(.25)
            hi = fa[fa > med + 3 * max(iqr, 0.01)]
            for u in hi.index:
                print(f'    !! {u}: reports {fa[u]:.1%} of pairs correlated vs '
                      f'group median {med:.1%}.')
                print(f'       Check this user for a stuck, clipped or '
                      f'low-resolution sensor channel.')
        drv = audit['n_sole_driver']
        tot = len(iu[0])
        for u in drv[drv > 0.02 * tot].index:
            print(f'    !! {u}: alone forces {int(drv[u])} merges '
                  f'({drv[u] / tot:.1%} of all pairs).')
            print(f'       Under v4\'s mean this user reshapes the feature '
                  f'space by themselves.')

    if path:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        audit.to_csv(path)
        if verbose:
            print(f'  correlation audit -> {path}')

    return audit


# ##########################################################################
#  from new_feature_selection_v9.py
#  lookahead defaults
#  3 name(s), 12 source lines copied verbatim, 0 edit(s) (see header)
# ##########################################################################


# How many of the weakest survivors (by solo AUC) enter the pair sweep.
# C(24,2) = 276 macro_auc calls per stall, which is ~4.6 single-steps of work at
# cap=60. Large enough to contain a real redundant pair, small enough that
# hitting several stalls in one run is still affordable.
DEFAULT_LOOKAHEAD_CAP = 24

# Combination size for the lookahead sweep. 2 is the recommended value; see the
# docstring's note on why triples are available but not default.
DEFAULT_LOOKAHEAD_K = 2

# Hard ceiling on macro_auc calls in a single lookahead sweep, as a guard against
# a large --lookahead-cap and --lookahead-k 3 combining into an overnight run by
# accident. The sweep is truncated (weakest-first) and says so.
LOOKAHEAD_CALL_BUDGET = 3000


# ##########################################################################
#  from new_feature_selection_v11.py
#  floating-search defaults
#  3 name(s), 13 source lines copied verbatim, 0 edit(s) (see header)
# ##########################################################################


# How many recently-removed features are offered back at each forward step. The
# most recent are used because they were removed under conditions closest to the
# current set, so they are the most likely to have become useful again. 12 keeps
# the per-step overhead at ~20% of the single sweep.
DEFAULT_FLOAT_CAP = 12

# A re-admission must beat best_seen by MORE than this to be accepted. A strict
# improvement requirement is what makes oscillation impossible: a neutral swap
# (drop A, add A back at the same AUC) is refused, so the search cannot cycle.
# 1e-5 is well below SBS_TOL (1e-3) so genuine improvements are not missed.
DEFAULT_FLOAT_MIN_GAIN = 1e-5

# A feature re-admitted this many times is locked out permanently. Belt and
# braces alongside the min-gain rule.
DEFAULT_FLOAT_MAX_READMIT = 2


# ##########################################################################
#  from new_feature_selection_v18.py
#  EnsembleScorer + stall-gated elimination
#  18 name(s), 695 source lines copied verbatim, 15 edit(s) (see header)
# ##########################################################################


ENS_MODES = ('overlap', 'disjoint')
ENS_RULES = ('min', 'mean', 'median', 'trimmed')
STALL_METRICS = ('gap', 'auc', 'none')

# Number of sub-models. 7 is odd so the 'median' rule is unambiguous, and it is
# small enough that the per-step cost stays near the single-model cost: measured
# 0.068 s per macro call at M=1 versus 0.103 s at M=7, because each sub-model is
# cheaper than the full model it replaces.
DEFAULT_ENS_M = 7

# Fraction of the current feature set each sub-model sees under 'overlap'.
DEFAULT_ENS_FRAC = 0.70

# Accepted steps over which the stall metric must improve by more than
# DEFAULT_STALL_TOL, or the search floats.
DEFAULT_STALL_WINDOW = 5

# 1e-4 on the gap, not on AUC. The gap is an O(0.1) quantity on this data
# (0.025 to 0.368 across users), so 1e-4 is genuinely "no movement" rather than
# a tolerance that swallows real gains.
DEFAULT_STALL_TOL = 1e-4

# Hard cap on float events, so a pathological run cannot thrash between the two
# directions forever.
DEFAULT_MAX_FLOATS = 12

# Trimmed rule drops this many sub-models from each end before averaging.
TRIM_EACH_END = 1


def draw_subspaces(n_feats, m, frac, mode, user, seed):
    """
    The M column-index subsets for one user, as positions into the CURRENT
    feature list.

    Seeded from (seed, user, mode, m, n_feats) so a rerun reproduces exactly and
    two different users get different subspaces. Deriving the seed from the user
    NAME rather than from a running counter matters: the subsets must not depend
    on the order users happen to be iterated in, or the result would change when
    the cohort file is reordered.

    The draw uses only n_feats - a COUNT. No feature values, no validation data
    and no impostor data enter here, so the subspacing cannot be shaped by what
    the models are scored against.

    Note that the subsets are redrawn whenever n_feats changes, i.e. at every
    elimination step. That is deliberate: a fixed subset of POSITIONS would mean
    something different after a removal shifted the positions, and a fixed
    subset of FEATURE NAMES would shrink unevenly as elimination progressed,
    leaving some sub-models with almost nothing. Redrawing keeps every sub-model
    at ens_frac of the current set, which is the invariant the design wants.
    """
    if m <= 1:
        return [np.arange(n_feats, dtype=int)]

    rng = np.random.default_rng(
        abs(hash((int(seed), str(user), str(mode), int(m), int(n_feats))))
        % (2 ** 32))

    if mode == 'disjoint':
        # One permutation cut into M contiguous blocks. np.array_split handles a
        # non-divisible count by making the first blocks one larger, which keeps
        # every feature in exactly one sub-model.
        perm = rng.permutation(n_feats)
        return [np.sort(b) for b in np.array_split(perm, m) if b.size > 0]

    # overlap: each sub-model draws its own subset without replacement.
    # The floor of 2 is clamped by n_feats AFTER it is applied, not before: a
    # one-feature set would otherwise ask for 2 columns out of 1 and numpy
    # raises. min() last is what keeps k <= n_feats unconditionally.
    k = min(max(2, int(np.ceil(frac * n_feats))), n_feats)
    subs = [np.sort(rng.choice(n_feats, k, replace=False)) for _ in range(m)]

    # A feature present in NO subset is invisible to the whole ensemble, which
    # would silently turn the search's feature set into a smaller one and make
    # every removal decision about a set that is not the set being reported.
    # Force each orphan into one randomly chosen sub-model.
    covered = np.zeros(n_feats, dtype=bool)
    for s in subs:
        covered[s] = True
    for o in np.flatnonzero(~covered):
        j = int(rng.integers(len(subs)))
        subs[j] = np.sort(np.unique(np.append(subs[j], o)))
    return subs


def _combine(scores, rule):
    """
    Combine an (M, n_sessions) score matrix down to (n_sessions,).

    At M == 1 every rule collapses to the identity, which is what makes
    --ens-m 1 the single-model path rather than an approximation of it.
    """
    if scores.shape[0] == 1:
        return scores[0]
    if rule == 'min':
        return scores.min(axis=0)
    if rule == 'mean':
        return scores.mean(axis=0)
    if rule == 'median':
        return np.median(scores, axis=0)
    if rule == 'trimmed':
        s = np.sort(scores, axis=0)
        t = TRIM_EACH_END
        if s.shape[0] > 2 * t:
            s = s[t:s.shape[0] - t]
        return s.mean(axis=0)
    raise ValueError(f'unknown ensemble rule {rule!r}')


class EnsembleScorer:
    """
    The one genuinely new mechanism, and the thing the search is scored by.

    Exposes macro_auc(folds, idx) with the same call signature as v4.macro_auc,
    so the search below can be written against either without a special case,
    and so --ens-m 1 is literally v4's computation rather than a copy of it.

    Scaling is fitted PER SUB-MODEL on that sub-model's own columns, not once
    globally. A StandardScaler fitted on all columns and then subset would give
    each sub-model the full set's scaling, which is not the same thing and would
    quietly couple the sub-models through a shared fit.
    """

    def __init__(self, m=DEFAULT_ENS_M, frac=DEFAULT_ENS_FRAC, mode='overlap',
                 rule='min', seed=RANDOM_SEED):
        self.m = max(1, int(m))
        self.frac = float(frac)
        self.mode = mode
        self.rule = rule
        self.seed = int(seed)
        self.n_calls = 0
        self.n_fits = 0

    # ---- the single-fold primitive everything else is built on ----
    def fold_scores(self, fold, idx, user):
        """
        (genuine, impostor, submodel_genuine, submodel_impostor) for one user on
        feature positions `idx`.

        The per-sub-model matrices come back too because the diversity audit
        needs them, and recomputing them later would be both wasteful and a
        second code path that could disagree with this one.
        """
        Xf = fold['fit'][:, idx]
        Xg = fold['val_g'][:, idx]
        Xi = fold['val_i'][:, idx]

        subs = draw_subspaces(len(idx), self.m, self.frac, self.mode,
                              user, self.seed)

        sg_all, si_all = [], []
        for s in subs:
            f, g, i = Xf[:, s], Xg[:, s], Xi[:, s]
            sc = StandardScaler().fit(f)
            Zf = sc.transform(f)
            mdl = OneClassSVM(kernel=KERNEL, nu=NU,
                              gamma=resolve_gamma(GAMMA, Zf)).fit(Zf)
            self.n_fits += 1
            sg_all.append(mdl.decision_function(sc.transform(g)))
            si_all.append(mdl.decision_function(sc.transform(i))
                          if i.size else np.empty(0))

        SG = np.vstack(sg_all)
        SI = (np.vstack(si_all) if si_all and si_all[0].size
              else np.empty((len(subs), 0)))
        sg = _combine(SG, self.rule)
        si = _combine(SI, self.rule) if SI.shape[1] else np.empty(0)
        return sg, si, SG, SI

    # ---- drop-in replacement for v4.macro_auc(folds, idx) ----
    def macro_auc(self, folds, idx):
        self.n_calls += 1
        vals = []
        for u, f in folds.items():
            sg, si, _, _ = self.fold_scores(f, idx, u)
            a = roc_auc(sg, si)
            if np.isfinite(a):
                vals.append(a)
        return float(np.mean(vals)) if vals else float('nan')

    # ---- the stall signal: what AUC cannot see ----
    def macro_gap(self, folds, idx):
        """
        Mean over users of median(genuine) - max(impostor).

        This is v4_v3's per-user 'gap' aggregated. It is the quantity the min
        rule is supposed to widen and the quantity AUC is blind to, so it serves
        as both the stall trigger and the primary reported effect.
        """
        vals = []
        for u, f in folds.items():
            sg, si, _, _ = self.fold_scores(f, idx, u)
            if sg.size and si.size:
                vals.append(float(np.median(sg) - np.max(si)))
        return float(np.mean(vals)) if vals else float('nan')

    def per_user(self, folds, feats, all_cols, verbose=True):
        """AUC, gap and the operating-point detail for every user."""
        pos = {c: i for i, c in enumerate(all_cols)}
        idx = np.array([pos[c] for c in feats], dtype=int)
        out = {}
        for j, (u, fold) in enumerate(folds.items(), 1):
            if verbose:
                print(f'    scoring {u} ({j}/{len(folds)})...',
                      end='\r', flush=True)
            sg, si, SG, SI = self.fold_scores(fold, idx, u)
            out[u] = {
                'auc': roc_auc(sg, si),
                'gap': (float(np.median(sg) - np.max(si))
                        if si.size else float('nan')),
                'gen_median': float(np.median(sg)),
                'imp_max': float(np.max(si)) if si.size else float('nan'),
                'n_imp': int(si.size),
                'n_submodels': int(SG.shape[0]),
            }
        if verbose:
            print(' ' * 46, end='\r')
        return out

    # ---- the audit that decides whether the ensemble is real ----
    def diversity_audit(self, folds, feats, all_cols, path=None, verbose=True):
        """
        Per user: how much do the M sub-models actually disagree?

        Reports the mean pairwise Pearson correlation of the sub-model score
        vectors, separately on the impostor side (the side FAR is decided on)
        and the genuine side. Also reports the gap the SAME sub-models would
        give under the plain mean rule, and the best gap any SINGLE sub-model
        achieves alone.

        Those two comparisons are the point. If the combined gap barely beats
        the best single sub-model, M-1 of the models are overhead. If the min
        and mean rules give nearly the same gap, the rule is not doing what the
        idea claims. And if mean pairwise correlation is high, the sub-models
        are near-copies and min over them is close to a constant downward shift,
        which a calibrated threshold absorbs - the null result this experiment
        most plausibly has, demonstrated with a number rather than left as a
        caveat in prose.
        """
        if self.m <= 1:
            if verbose:
                print('  ensemble audit: M=1, no sub-model diversity to report '
                      '(this IS the baseline arm)')
            return None

        pos = {c: i for i, c in enumerate(all_cols)}
        idx = np.array([pos[c] for c in feats], dtype=int)
        rows = []
        for u, fold in folds.items():
            sg, si, SG, SI = self.fold_scores(fold, idx, u)
            subs = draw_subspaces(len(idx), self.m, self.frac, self.mode,
                                  u, self.seed)
            rows.append({
                'user': u,
                'n_submodels': int(SG.shape[0]),
                'feats_per_submodel': float(np.mean([len(s) for s in subs])),
                'mean_pairwise_r_impostor': _mean_pairwise_r(SI),
                'mean_pairwise_r_genuine': _mean_pairwise_r(SG),
                'gap_rule': (float(np.median(sg) - np.max(si))
                             if si.size else float('nan')),
                'gap_mean_rule': _gap_under(SG, SI, 'mean'),
                'gap_single_best': _gap_best_submodel(SG, SI),
                'imp_max_rule': float(np.max(si)) if si.size else float('nan'),
                'imp_max_mean_rule': (float(np.max(_combine(SI, 'mean')))
                                      if SI.shape[1] else float('nan')),
                'gen_median_rule': float(np.median(sg)),
                'gen_median_mean_rule': float(np.median(_combine(SG, 'mean'))),
            })

        df = pd.DataFrame(rows).set_index('user').sort_index()
        if verbose:
            print(f'  ENSEMBLE DIVERSITY AUDIT   rule={self.rule}  '
                  f'M={self.m}  mode={self.mode}')
            print(f'    {"user":<12s} {"r_imp":>7s} {"r_gen":>7s} '
                  f'{"gap":>8s} {"gapMEAN":>8s} {"gapBEST1":>9s} {"f/sub":>6s}')
            for u, r in df.iterrows():
                print(f'    {u:<12s} {r["mean_pairwise_r_impostor"]:7.3f} '
                      f'{r["mean_pairwise_r_genuine"]:7.3f} '
                      f'{r["gap_rule"]:+8.3f} {r["gap_mean_rule"]:+8.3f} '
                      f'{r["gap_single_best"]:+9.3f} '
                      f'{r["feats_per_submodel"]:6.1f}')
            rbar = float(df['mean_pairwise_r_impostor'].mean())
            print(f'    mean impostor-side sub-model correlation: {rbar:.3f}')
            if rbar > 0.90:
                print('    !! ABOVE 0.90. The sub-models are near-copies, so '
                      'the combine rule is')
                print('       close to a constant score shift, which a '
                      'calibrated threshold absorbs.')
                print('       Read any gap change as a SHIFT, not as added '
                      'separation.')
            elif rbar > 0.75:
                print('    ~  0.75-0.90. Partial diversity. The rule is doing '
                      'something, but the')
                print('       sub-models share most of their evidence. Compare '
                      'gap against gapMEAN.')
            else:
                print('    OK below 0.75. The sub-models carry genuinely '
                      'different evidence, so')
                print('       min over them is a real conjunction rather than '
                      'a shift.')
            n_beat = int((df['gap_rule'] > df['gap_single_best']).sum())
            print(f'    users where the ensemble beats its best single '
                  f'sub-model: {n_beat}/{len(df)}')
            if n_beat == 0:
                print('    !! NO user beats its own best sub-model. On this '
                      'evidence the ensemble')
                print('       is not earning its cost and a single OCSVM on '
                      'the right subspace')
                print('       would do as well.')

        if path:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            df.to_csv(path)
            print(f'  ensemble audit -> {path}')
        return df


def _mean_pairwise_r(S):
    """Mean off-diagonal Pearson r between sub-model score vectors."""
    if S.ndim != 2 or S.shape[0] < 2 or S.shape[1] < 3:
        return float('nan')
    C = np.nan_to_num(np.corrcoef(S))
    iu = np.triu_indices(S.shape[0], k=1)
    return float(np.mean(C[iu]))


def _gap_under(SG, SI, rule):
    if SI.shape[1] == 0:
        return float('nan')
    return float(np.median(_combine(SG, rule)) - np.max(_combine(SI, rule)))


def _gap_best_submodel(SG, SI):
    """
    The best gap any SINGLE sub-model achieves on its own.

    This is the number the ensemble has to beat to have earned its cost. If the
    best single sub-model already matches the combined gap, M-1 of the models
    are overhead.
    """
    if SI.shape[1] == 0:
        return float('nan')
    gaps = [float(np.median(SG[j]) - np.max(SI[j])) for j in range(SG.shape[0])]
    return float(np.max(gaps)) if gaps else float('nan')


def stall_gated_eliminate(folds, feats, all_cols, scorer, tol, min_features,
                          cap, max_steps, stall_metric='gap',
                          stall_window=DEFAULT_STALL_WINDOW,
                          stall_tol=DEFAULT_STALL_TOL,
                          max_floats=DEFAULT_MAX_FLOATS,
                          lookahead=True,
                          lookahead_k=DEFAULT_LOOKAHEAD_K,
                          lookahead_cap=DEFAULT_LOOKAHEAD_CAP,
                          verbose=True):
    """
    Backward elimination as the main engine, floating only when it goes stale.

    The mechanism, in the order it runs:

      1. Plain backward elimination, scored by macro AUC through `scorer`. The
         acceptance test is v4_v3's unchanged: take the removal that costs least
         if that cost is within `tol` of the best AUC ever seen.
      2. After each accepted removal, append the current value of the STALL
         METRIC to a rolling window.
      3. When the window is full and the metric's improvement across it is
         <= stall_tol, the search is stale: run ONE conditional re-admission
         pass (the forward half), then clear the window and return to backward.
      4. When no single removal is affordable at all, fall back to a k-feature
         lookahead.
      5. If the lookahead also fails, float ONE more time before confirming the
         stop. This is the case the idea exists for - the search is maximally
         stuck - and a gate that only fired after an accepted removal would skip
         it entirely. A stop is final only once a float has also failed.

    Why re-admission is conditional on a stall rather than run every step: v11
    already measured the unconditional version and reported macro AUC 0.9998708.
    Gating it is the only thing this search does that v11 does not, so any
    difference between the two is attributable to the gate.

    Re-admission requires STRICT improvement in macro AUC, inherited from v11's
    anti-oscillation rule, and a re-admitted feature is locked out after being
    taken back DEFAULT_FLOAT_MAX_READMIT times so the two directions cannot
    thrash. The window is cleared after every float event for the same reason:
    leaving it full would re-fire the gate on the very next step and turn the
    conditional float back into an unconditional one.

    Returns (features, best_auc, history, problem, stall_events, attribution).
    """
    pos = {c: i for i, c in enumerate(all_cols)}
    cur = list(feats)
    idx = lambda cs: np.array([pos[c] for c in cs], dtype=int)

    sc_auc = lambda cs: scorer.macro_auc(folds, idx(cs))
    if stall_metric == 'none':
        sc_stall = None
    elif stall_metric == 'gap':
        sc_stall = lambda cs: scorer.macro_gap(folds, idx(cs))
    else:
        sc_stall = sc_auc

    base = sc_auc(cur)
    base_gap = scorer.macro_gap(folds, idx(cur))
    if verbose:
        print(f'  start: {len(cur)} features, macro AUC {base:.5f}, '
              f'macro gap {base_gap:+.4f}  (on FULL impostor pool)')
    if not np.isfinite(base):
        return cur, base, [], 'AUC is not computable', [], {}

    if base >= SATURATION_AUC and verbose:
        print(f'  !! starting AUC {base:.5f} is at/above saturation '
              f'({SATURATION_AUC}). Read as "separable on this sample".')
        if stall_metric == 'auc':
            print('  !! --stall-metric auc on a SATURATED metric will report a '
                  'stall almost every')
            print('     step, collapsing this into v11\'s unconditional float. '
                  'That is the expected')
            print('     degenerate behaviour, not a failure. Prefer '
                  '--stall-metric gap.')

    history = [{'n': len(cur), 'auc': base, 'stall_metric_value': base_gap,
                'removed': None, 'mode': 'start'}]
    stall_events = []
    removed_order = []
    readmit_count = Counter()
    locked_out = set()
    att = Counter()
    window = []
    t0 = time.time()
    best_seen = base
    n_floats = 0

    def try_float(reason, improvement=float('nan')):
        """
        One conditional re-admission pass: the forward half of the search.

        Offers recently-removed features back and takes the single best one only
        if it STRICTLY improves macro AUC by more than v11's min-gain. Returns
        True if something was re-admitted.

        Shared by the two places a float can be triggered - the stall window and
        the hard stop - because a float that only ran on one of them would miss
        the case the idea exists to handle. See the call sites.

        `nonlocal` rather than passing state around: this is one search with one
        set of bookkeeping, and copying it in and out would create two places
        where best_seen could disagree with history.
        """
        nonlocal n_floats, best_seen, window
        n_floats += 1
        pool_back = [c for c in reversed(removed_order)
                     if c not in locked_out and c not in cur]
        pool_back = pool_back[:DEFAULT_FLOAT_CAP]
        took = None
        best_r, best_r_auc = None, -np.inf
        for c in pool_back:
            a = sc_auc(cur + [c])
            if a > best_r_auc:
                best_r, best_r_auc = c, a
        # STRICT improvement, inherited from v11. A neutral re-admission is
        # refused, which is what stops the gate from oscillating with the
        # backward step it just undid.
        if (best_r is not None
                and best_r_auc > best_seen + DEFAULT_FLOAT_MIN_GAIN):
            cur.append(best_r)
            removed_order.remove(best_r)
            readmit_count[best_r] += 1
            att['readmit'] += 1
            if readmit_count[best_r] >= DEFAULT_FLOAT_MAX_READMIT:
                locked_out.add(best_r)
            took = best_r
            m_now = (sc_stall(cur) if sc_stall is not None else float('nan'))
            history.append({'n': len(cur), 'auc': best_r_auc,
                            'stall_metric_value': m_now,
                            'removed': None, 'readmitted': best_r,
                            'mode': 'readmit'})
            best_seen = max(best_seen, best_r_auc)
            if verbose:
                print(f'     ++ RE-ADMIT {best_r}: AUC {best_r_auc:.5f}, '
                      f'{len(cur)} features'
                      + ('  [locked out]' if best_r in locked_out else ''))
        elif verbose:
            print(f'     no re-admission improved AUC by more than '
                  f'{DEFAULT_FLOAT_MIN_GAIN} -> back to backward\n')

        stall_events.append({
            'event': n_floats,
            'trigger': reason,
            'n_features': len(cur),
            'stall_metric': stall_metric,
            'window': stall_window,
            'improvement_over_window': float(improvement),
            'candidates_offered': len(pool_back),
            'best_candidate': best_r or '',
            'best_candidate_auc': (float(best_r_auc)
                                   if np.isfinite(best_r_auc)
                                   else float('nan')),
            'readmitted': took or '',
            'accepted': bool(took),
        })
        # Clear the window either way. The gate has fired for this stall;
        # leaving it full would re-fire on the very next step and turn the
        # conditional float back into an unconditional one.
        window = []
        return bool(took)

    step = 0
    while step < max_steps:
        if len(cur) <= min_features:
            if verbose:
                print(f'  stop: floor of {min_features} features reached')
            break

        solo = None
        trial = cur
        if len(cur) > cap:
            solo = {c: sc_auc([c]) for c in cur}
            trial = sorted(cur, key=lambda c: solo.get(c, 0.0))[:cap]

        best_c, best_auc = None, -np.inf
        for c in trial:
            a = sc_auc([x for x in cur if x != c])
            if a > best_auc:
                best_c, best_auc = c, a

        accepted = False

        if best_auc >= best_seen - tol:
            cur.remove(best_c)
            removed_order.append(best_c)
            att['single'] += 1
            m_now = (sc_stall(cur) if sc_stall is not None else float('nan'))
            history.append({'n': len(cur), 'auc': best_auc,
                            'stall_metric_value': m_now,
                            'removed': best_c, 'mode': 'single'})
            best_seen = max(best_seen, best_auc)
            accepted = True
            if sc_stall is not None and np.isfinite(m_now):
                window.append(m_now)
            if verbose and (step % 5 == 0 or len(cur) <= min_features + 5):
                el = time.time() - t0
                done = step + 1
                left = max(0, len(cur) - min_features)
                eta = (el / done) * left
                sm = (f', {stall_metric} {m_now:+.4f}'
                      if sc_stall is not None and np.isfinite(m_now) else '')
                print(f'  step {done:3d}: -{best_c:38s} '
                      f'{len(cur):3d} left, AUC {best_auc:.5f}{sm} '
                      f'({el:.0f}s elapsed, ~{eta / 60:.0f}m left)')
        elif not lookahead:
            # ---- v4_v3's stop, exactly: no lookahead, no combination sweep ----
            # This is what makes --no-lookahead + M=1 + --stall-metric none a
            # BIT-IDENTICAL reproduction of v4_v3.backward_eliminate_probe, and
            # therefore of v6. The acceptance test above is already v4_v3's; the
            # STOP has to match too, and v4_v3 stops here rather than trying
            # combinations. Verified by comparing removal order, step count and
            # final AUC against backward_eliminate_probe directly.
            if verbose:
                print(f'  stop: best removal ({best_c}) would cost '
                      f'{best_seen - best_auc:.5f} AUC, over tolerance {tol}')
        else:
            # ---- no affordable single removal: lookahead, then stop ----
            if verbose:
                print(f'\n  ** SINGLE REMOVAL STALLED at {len(cur)} features **')
                print(f'     best single: -{best_c} costs '
                      f'{best_seen - best_auc:.5f} (tolerance {tol})')
                print(f'     trying {lookahead_k}-feature combinations...')
            if solo is None:
                solo = {c: sc_auc([c]) for c in cur}
            shortlist = sorted(cur,
                               key=lambda c: solo.get(c, 0.0))[:lookahead_cap]
            combos = list(itertools.combinations(shortlist, lookahead_k))
            if len(combos) > LOOKAHEAD_CALL_BUDGET:
                combos = combos[:LOOKAHEAD_CALL_BUDGET]
                if verbose:
                    print(f'     ! sweep truncated to '
                          f'{LOOKAHEAD_CALL_BUDGET} combination(s)')
            t_look = time.time()
            best_combo, best_combo_auc = None, -np.inf
            for g in combos:
                drop = set(g)
                a = sc_auc([x for x in cur if x not in drop])
                if a > best_combo_auc:
                    best_combo, best_combo_auc = g, a
            if best_combo is not None and best_combo_auc >= best_seen - tol:
                for c in best_combo:
                    cur.remove(c)
                    removed_order.append(c)
                att[f'lookahead-{lookahead_k}'] += 1
                m_now = (sc_stall(cur) if sc_stall is not None
                         else float('nan'))
                history.append({'n': len(cur), 'auc': best_combo_auc,
                                'stall_metric_value': m_now,
                                'removed': '|'.join(best_combo),
                                'mode': f'lookahead-{lookahead_k}'})
                best_seen = max(best_seen, best_combo_auc)
                accepted = True
                if sc_stall is not None and np.isfinite(m_now):
                    window.append(m_now)
                if verbose:
                    print(f'     FOUND a jointly-affordable combination: '
                          f'{"|".join(best_combo)}')
                    print(f'     AUC {best_combo_auc:.5f} '
                          f'(cost {best_seen - best_combo_auc:+.5f}), '
                          f'{time.time() - t_look:.0f}s\n')
            elif verbose:
                print(f'     no affordable {lookahead_k}-combination either '
                      f'-> STOP CONFIRMED')
                print(f'     ({time.time() - t_look:.0f}s for '
                      f'{len(combos)} combination(s))')

        if not accepted:
            # ---- LAST-RESORT FLOAT, before the stop is final ----
            # This is the case the whole idea exists for, and gating the float on
            # "after an accepted removal" alone would skip it: backward
            # elimination has run out of affordable removals AND the lookahead
            # found no affordable combination, so the search is maximally stuck.
            # Offering features back here can change which removals are
            # affordable next, so a stop is only confirmed once a float has also
            # failed. Without this the search could never float at precisely the
            # moment it is most stale, which was the point of the gate.
            if sc_stall is not None and n_floats < max_floats:
                if verbose:
                    print(f'     before confirming the stop: one last float '
                          f'(event {n_floats + 1}/{max_floats})')
                if try_float('hard-stop'):
                    step += 1
                    continue        # a re-admission changed the set: resume
            break

        # ---------------- the gate: float only when stale ----------------
        if (sc_stall is not None and len(window) >= stall_window
                and n_floats < max_floats):
            recent = window[-stall_window:]
            improvement = max(recent) - recent[0]
            if improvement <= stall_tol:
                if verbose:
                    print(f'\n  ** {stall_metric.upper()} STALE over last '
                          f'{stall_window} steps: improvement '
                          f'{improvement:+.6f} <= {stall_tol} **')
                    print(f'     floating: offering removed features back '
                          f'(event {n_floats + 1}/{max_floats})')
                try_float('stall-window', improvement)

        step += 1

    if verbose:
        print(f'  eliminated to {len(cur)} features in {time.time() - t0:.0f}s')
        print(f'  single {att["single"]}, '
              f'lookahead {att[f"lookahead-{lookahead_k}"]}, '
              f'float events {n_floats}, re-admitted {att["readmit"]}')
        print(f'  scorer: {scorer.n_calls} macro calls, '
              f'{scorer.n_fits} OCSVM fits')

    attribution = {
        'single_removals': int(att['single']),
        'lookahead_removals': int(att[f'lookahead-{lookahead_k}']),
        'float_events': int(n_floats),
        'readmissions': int(att['readmit']),
        'locked_out': sorted(locked_out),
        'readmit_counts': dict(readmit_count),
        'macro_calls': int(scorer.n_calls),
        'ocsvm_fits': int(scorer.n_fits),
    }
    return cur, best_seen, history, None, stall_events, attribution


def print_per_user(title, table, baseline=None):
    print(f'  {title}')
    hdr = (f'    {"user":<12s} {"AUC":>7s} {"gap":>8s} {"genMED":>8s} '
           f'{"impMAX":>8s} {"nImp":>5s}')
    if baseline:
        hdr += f'  {"dAUC":>8s}  {"dGAP":>8s}'
    print(hdr)
    for u in sorted(table):
        r = table[u]
        line = (f'    {u:<12s} {r["auc"]:7.4f} {r["gap"]:+8.3f} '
                f'{r["gen_median"]:+8.3f} {r["imp_max"]:+8.3f} {r["n_imp"]:5d}')
        if baseline and u in baseline:
            line += (f'  {r["auc"] - baseline[u]["auc"]:+8.4f}'
                     f'  {r["gap"] - baseline[u]["gap"]:+8.3f}')
        print(line)


def margins_ens(folds, feats, all_cols, scorer, base_auc, verbose=True):
    """
    Leave-one-out margin per surviving feature, measured through the ensemble.

    v4's margins() is defined against v4.macro_auc and would therefore report
    the single-model margin of a set that was chosen by the ensemble - the wrong
    quantity, and the same mistake v17's docstring flags about measuring an
    AUC margin on a TAR-chosen set. Both the AUC margin and the GAP margin are
    reported, because the gap is where the ensemble is expected to act.
    """
    pos = {c: i for i, c in enumerate(all_cols)}
    idx = lambda cs: np.array([pos[c] for c in cs], dtype=int)
    base_gap = scorer.macro_gap(folds, idx(feats))
    out = []
    t0 = time.time()
    for j, c in enumerate(feats, 1):
        rest = [x for x in feats if x != c]
        a = scorer.macro_auc(folds, idx(rest))
        g = scorer.macro_gap(folds, idx(rest))
        out.append({
            'feature': c,
            'bucket': (bucket_of(c)[0] if bucket_of else '?'),
            'margin': float(base_auc - a),
            'margin_gap': float(base_gap - g),
        })
        if verbose and (j % 10 == 0 or j == len(feats)):
            el = time.time() - t0
            eta = (el / j) * (len(feats) - j)
            print(f'    margin {j}/{len(feats)}  ({el:.0f}s elapsed, '
                  f'~{eta / 60:.1f}m left)', end='\r', flush=True)
    if verbose:
        print(' ' * 60, end='\r')
    out.sort(key=lambda r: -r['margin'])
    return out, base_gap


# ##########################################################################
#  from new_feature_selection_v19.py
#  test-genuine loading + genuine-scope folds
#  4 name(s), 125 source lines copied verbatim, 0 edit(s) (see header)
# ##########################################################################


GENUINE_SCOPES = ('enrolment', 'enrolment+testing', 'testing')

# A user needs at least this many test genuine sessions to be worth splicing.
# Below it the addition is noise and the fold is left as v18 built it.
MIN_TEST_GENUINE = 5


def load_test_genuine(feature_dir, users, cols, verbose=True):
    """
    Genuine rows from the TESTING CSVs - the data every earlier file refused.

    This is the mirror image of v4_v3.load_all_attackers: same files, same label
    column resolution, same normalise_label, but it keeps 'genuine' where that
    function keeps 'impostor'. Written as a parallel function rather than a flag
    on that one so load_all_attackers stays byte-identical for the impostor side.

    The label columns are self-reported (a checkbox in the collection app), so a
    mislabelled impostor session now lands in the GENUINE side of a fold instead
    of being dropped. That is a real new failure mode; it is called out in the
    module docstring and the count is printed per user so an implausible number
    is visible rather than silent.
    """
    per_user = {}
    for u in users:
        p = os.path.join(feature_dir, f'{u}_testing_sessions.csv')
        if not os.path.exists(p):
            if verbose:
                print(f'  [no testing CSV] {u}')
            continue
        df = pd.read_csv(p, low_memory=False)
        if df.empty:
            continue
        lc = next((c for c in ('test_type', 'session_label', 'label')
                   if c in df.columns), None)
        if lc is None:
            if verbose:
                print(f'  [no label column] {u}')
            continue

        gen = df[df[lc].map(normalise_label) == 'genuine']
        if len(gen) < MIN_TEST_GENUINE:
            if verbose:
                print(f'  {u:14s} only {len(gen)} test genuine session(s) '
                      f'(need >= {MIN_TEST_GENUINE}) - NOT spliced')
            continue

        missing = [c for c in cols if c not in gen.columns]
        if missing:
            if verbose:
                print(f'  {u:14s} testing CSV lacks {len(missing)} selected '
                      f'column(s) - NOT spliced')
            continue

        X = gen[cols].apply(pd.to_numeric, errors='coerce').fillna(0.0).values
        per_user[u] = X
        if verbose:
            print(f'  {u:14s} {len(X):3d} test genuine session(s) spliced into '
                  f'val_g')
    return per_user


def build_folds_genuine(frames, cols, attacker_imp, test_gen, scope,
                        verbose=True):
    """
    v4's fold construction with the genuine side widened.

    The fit block and the impostor side are built exactly as
    v4_v3.build_folds_no_holdout does - same k, same temporal split, same
    MIN_TRAIN_SESSIONS/VAL_FRAC arithmetic, same full impostor pool. Only val_g
    changes, and only when scope says so.

    The fit block is NEVER touched. Test genuine sessions go to the scored side,
    never to the side the model is trained on: moving them into fit would be a
    different experiment (more enrolment data) and would confound this one.
    """
    folds = {}
    for u, df in frames.items():
        n = len(df)
        k = max(MIN_TRAIN_SESSIONS - 4, int(round(n * (1.0 - VAL_FRAC))))
        k = min(k, n - 3)
        if k < 6 or n - k < 3:
            continue
        X = df[cols].apply(pd.to_numeric, errors='coerce').fillna(0.0).values
        folds[u] = {'fit': X[:k], 'val_g': X[k:],
                    'n_val_g_enrolment': int(len(X) - k),
                    'n_val_g_testing': 0}

    # ---- the splice ----
    for u in list(folds):
        if scope == 'enrolment':
            continue
        Xt = test_gen.get(u)
        if Xt is None or len(Xt) == 0:
            continue
        if scope == 'testing':
            # The extreme arm: enrolment holdout dropped entirely. Guard against
            # leaving a fold with too few genuine rows to compute a median on.
            if len(Xt) < 3:
                continue
            folds[u]['val_g'] = Xt
            folds[u]['n_val_g_enrolment'] = 0
        else:
            folds[u]['val_g'] = np.vstack([folds[u]['val_g'], Xt])
        folds[u]['n_val_g_testing'] = int(len(Xt))

    # ---- impostor side, unchanged from v4_v3 ----
    for u in list(folds):
        if attacker_imp and u in attacker_imp:
            folds[u]['val_i'] = attacker_imp[u]
            folds[u]['val_i_kind'] = 'ALL same-device attackers'
        else:
            del folds[u]

    if verbose and folds:
        ge = int(np.mean([f['n_val_g_enrolment'] for f in folds.values()]))
        gt = int(np.mean([f['n_val_g_testing'] for f in folds.values()]))
        gi = int(np.mean([len(f['val_i']) for f in folds.values()]))
        print(f'  folds: {len(folds)} user(s) | mean val genuine '
              f'{ge + gt} (enrolment {ge} + testing {gt}) | '
              f'mean val impostor {gi}')
        print(f'         genuine scope: {scope}')
        if gt > 0:
            print('         ! TEST GENUINE SESSIONS ARE NOW VISIBLE TO THE '
                  'SEARCH.')
            print('           The genuine side is no longer a holdout. Any FRR '
                  'measured later')
            print('           on these sessions is RESUBSTITUTION, not a '
                  'measurement.')
        print('         impostor source: EVERY attacker, nothing reserved')
    return folds


# ##########################################################################
#  from new_feature_selection_v20.py
#  curve replay, best-set choice, deployed sweep, main
#  8 name(s), 659 source lines copied verbatim, 21 edit(s) (see header)
# ##########################################################################


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


def main(argv=None):
    # stand-alone: the original wrote new_feature_registry._ACTIVE_RX through
    # its module alias (_reg._ACTIVE_RX = ...); here that registry global lives in
    # this file, so it is declared global to keep the same rebinding.
    global _ACTIVE_RX
    ap = argparse.ArgumentParser(
        description='CEILING PROBE v20. v19 with the 50-feature floor removed '
                    'and best-set selection over the elimination curve. '
                    'Output is NOT deployable.')

    ap.add_argument('--features', default=os.path.join('features', 'v3_v2'))
    ap.add_argument('--out', default=os.path.join(
        'features', 'v3_v2', 'selected_V20_BEST_CEILING_PROBE.json'))
    ap.add_argument('--users', default=None)
    ap.add_argument('--prescreen', type=int, default=PRESCREEN_KEEP)
    ap.add_argument('--corr', type=float, default=CORR_THRESHOLD)
    ap.add_argument('--tol', type=float, default=SBS_TOL)
    ap.add_argument('--min-features', type=int, default=DEFAULT_MIN_FEATURES,
                    help=f'floor for elimination. Default '
                         f'{DEFAULT_MIN_FEATURES}, NOT v4\'s 50 - the point of '
                         f'this file is that 50 was a budget, not a stopping '
                         f'criterion. Pass 50 to reproduce v19.')
    ap.add_argument('--sbs-cap', type=int, default=SBS_CANDIDATE_CAP)
    ap.add_argument('--max-steps', type=int, default=SBS_MAX_STEPS)
    ap.add_argument('--impostor-protocol',
                    choices=('same-device', 'cross-device'),
                    default='same-device')
    ap.add_argument('--seed', type=int, default=RANDOM_SEED)
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
        if args.exclude_groups:
            grp = ([] if args.exclude_groups.strip().lower() in ('none', 'null')
                   else [x.strip() for x in args.exclude_groups.split(',')
                         if x.strip()])
            unknown = [x for x in grp if x not in GROUP_DEFINITIONS]
            if unknown:
                print(f'  unknown group(s) {unknown}')
                return 2
            EXCLUDE_GROUPS[:] = grp
        for p_ in (x.strip() for x in args.drop_families.split(',')):
            if p_:
                EXTRA_EXCLUDED_FAMILIES[p_] = 'set via --drop-families'
        refresh_exclusions()
        for p_ in (x.strip() for x in args.keep_families.split(',')):
            if p_:
                ACTIVE_EXCLUDED_FAMILIES.pop(p_, None)
                ACTIVE_EXCLUDED_REGEXES.pop(p_, None)
                _ACTIVE_RX = [(rx, src) for rx, src in _ACTIVE_RX
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
        res['excluded_groups'] = list(ACTIVE_GROUPS)
        res['excluded_patterns'] = sorted(
            list(ACTIVE_EXCLUDED_FAMILIES)
            + list(ACTIVE_EXCLUDED_REGEXES))
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


# ##########################################################################
#  Transfer guards. Silent when everything matches the verified setup; they
#  print a warning, and change nothing, when it does not.
# ##########################################################################

_VERIFIED_PRESCREEN_V3_DEVICE_SHA256 = (
    '64bff73fb31b7f346c3a7d239f071289149930f1b7f1bec756d7ee1761e7fe1e')
_VERIFIED_VERSIONS = {"python": "3.13.9", "numpy": "2.5.3", "pandas": "3.0.2", "scipy": "1.18.1", "scikit-learn": "1.5.2"}


def _transfer_guards():
    notes = []
    try:
        spec = _ilu.find_spec('prescreen_v3_device')
    except (ImportError, ValueError):
        spec = None
    if spec is not None and spec.origin and os.path.isfile(spec.origin):
        with open(spec.origin, 'rb') as fh:
            h = _hashlib.sha256(fh.read().replace(b'\r\n', b'\n')).hexdigest()
        if h != _VERIFIED_PRESCREEN_V3_DEVICE_SHA256:
            notes.append(f'prescreen_v3_device.py ({spec.origin}) is not the '
                         f'copy this file was verified with (sha256 '
                         f'{h[:16]}..., expected '
                         f'{_VERIFIED_PRESCREEN_V3_DEVICE_SHA256[:16]}...). '
                         f'Results can differ.')
    try:
        import scipy as _scipy
        import sklearn as _sklearn
        have = {'python': _platform.python_version(),
                'numpy': np.__version__, 'pandas': pd.__version__,
                'scipy': _scipy.__version__,
                'scikit-learn': _sklearn.__version__}
        diff = [f'{k} {have[k]} (verified {v})'
                for k, v in _VERIFIED_VERSIONS.items() if have.get(k) != v]
        if diff:
            notes.append('library versions differ from the verified run: '
                         + ', '.join(diff) + '. OneClassSVM scores decide '
                         'every elimination step, so the selected features '
                         'can differ.')
    except Exception:                                    # noqa: BLE001
        pass
    for n in notes:
        print('  !! STAND-ALONE CHECK: ' + n, flush=True)


_transfer_guards()


if __name__ == '__main__':
    sys.exit(main())
