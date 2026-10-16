# Change 2 — Run only the feature families the user's model reads

| | |
|---|---|
| **What** | Today every predict request runs **all 29 feature families plus the DTW distances**, producing 5,483 columns. The model then reads its 50. After this change only the families that produce at least one of the bundle's 50 columns run. DTW and layout run only if a `dtw_` or `place_layout_` column is among the 50. |
| **Why** | For the active selection (v8), 14 of the 29 families produce none of the 50 columns. DTW alone takes **52% of extraction time**, and v8 uses no DTW column. |
| **Measured gain** | Extraction median **3.14 s → 1.09 s** on its own (−2.03 s, −64.4%); **0.97 s** together with Change 1 (−69.0%). 43 real sessions, laptop; production should see a similar percentage. |
| **Effect on results** | None. All 50 selected values were identical on **43/43** sessions. |
| **Files changed** | `mobile_navigation_core/feature_extraction.py`, `mobile_navigation_core/prediction_service.py`, `.env` |
| **Files added** | `tools/build_column_family_map.py`, `mobile_navigation_core/features/column_families.json` (generated), `mobile_navigation_core/extraction_plan.py`, `mobile_navigation_core/selected_extractor.py`, `tests/test_change2_needed_families.py` |
| **Not touched** | Everything in `mobile_navigation_core/vendor/` (byte-identical), training and enrolment, bundles, the backend, the SDK |
| **Switch** | `ML_EXTRACT_MODE=full` (today's behaviour, default) or `needed` (this change). `narrow` is Change 3. |
| **Rollback** | `ML_EXTRACT_MODE=full`, then restart |
| **Effort** | 1.5–2 days including the map generator and tests |
| **Depends on** | Nothing. It works with or without Change 1. |

---

## 1. How extraction works today

`extract_session` (`feature_extraction.py:171`) runs, for every request:

```
clean_session -> SessionView -> recompute_caps -> sanitize_view          (≈ 80 ms, all needed)
-> _EXTRACTOR.extract(view, templates, None)                             (feature_extraction.py:246)
     V2.extract (vendor/new_feature_creation_session_v2.py:3004)
       cview = CleanView(view)
       row = super().extract(cview, templates, None)  -> V1.extract (vendor/new_feature_creation_session.py:3384)
            19 v3 families, each:  f.update(self.extract_<name>(view))   (:3397-3430)
            if templates: compare_layout(...)      -> place_layout_* (:3437-3446)
            if templates: compute_dtw_features(...) -> dtw_*          (:3453-3458)
            quality + sanitizer + identity columns                     (:3461-3478)
       10 v2 families:  new.update(getattr(self, f'extract_{name}')(cview))   (:3036-3042)
       corrections, dead/leak column drops, tail ordering                  (:3045-3053)
-> row with 5,483 columns
```

Then `bundle.score(row)` → `Bundle.vectorise` (`bundle_loader.py:200-236`) reads **only** `bundle.feature_columns`, which is 50 names for v8. The other 5,433 columns are computed and thrown away.

**Where the time goes today** (round 1, 43 sessions, mean ms per session). "Needed by v8" means the family produces at least one of the 50 columns.

| Stage | ms | Share | Needed by v8 |
|---|---|---|---|
| `compute_dtw_features` (DTW) | 1,630.7 | 52.4% | **no** |
| `extract_tap_locked` | 241.0 | 7.8% | yes (10 columns) |
| `extract_sensor_complexity` | 229.4 | 7.4% | **no** |
| `copy.deepcopy` | 160.9 | 5.2% | Change 1 |
| `extract_stage2` | 148.5 | 4.8% | yes (1) |
| `extract_sensor_stats` | 102.7 | 3.3% | yes (1) |
| `extract_sensor_spectral` | 70.5 | 2.3% | yes (5) |
| `extract_touch` | 62.2 | 2.0% | yes (10) |
| `extract_stage3` | 52.9 | 1.7% | **no** |
| `extract_orientation` | 51.4 | 1.7% | yes (1) |
| parse, caps, sanitise, clean | ~95 | 3% | always |
| `extract_tap_spectral` | 43.9 | 1.4% | yes (1) |
| `extract_keystrokes` | 35.0 | 1.1% | yes (12) |
| `extract_correlations` | 30.7 | 1.0% | yes (1) |
| `extract_key_locked` | 29.0 | 0.9% | yes (1) |
| `extract_derived_motion` | 20.4 | 0.7% | yes (2) |
| `extract_placement` | 16.3 | 0.5% | **no** |
| `extract_posture_digraph` | 14.3 | 0.5% | **no** |
| `extract_touch_paths` | 14.2 | 0.5% | yes (1) |
| `extract_per_screen` | 12.0 | 0.4% | **no** |
| `extract_cross_event` | 10.8 | 0.3% | **no** |
| `extract_cross_window`, `cognitive`, `context`, `touch_motion_coupling`, `states`, `adev`, `navigation`, `screen_deep`, layout | ~22 | 0.7% | **no** |
| `extract_field_contrasts`, `field_segments`, `nonkbd` | ~10 | 0.3% | yes (1, 2, 1) |

**Totals:** 15 families are needed and 14 aren't, plus DTW and layout. The needed families still produce 4,260 columns, and the 50 come from them. Change 3 addresses that part.

## 2. The design

```
bundle.feature_columns (50 names)
        |
        v
extraction_plan.plan_for(columns)  -- uses features/column_families.json (column -> family)
        |      returns None (= run FULL, today's path) if: map missing, map built for other
        |      vendor files, or any column not in the map
        v
ExtractionPlan(families to run, families to skip, need_templates)
        |
        v
selected_extractor.extractor_for(plan.skip)  -- one cached SelectiveExtractorV2 per skip set
        |      skipped families are replaced ON THE INSTANCE by a function returning {}
        v
extractor.extract(view, templates if plan.need_templates else None, None)
```

### 2.1 Why skipping works without touching `vendor/`
Both orchestrators call each family through `self`:
- V1: `('context', self.extract_context), ...` (`:3397-3424`);
- V2: `getattr(self, f'extract_{name}')` (`:3037`).

An attribute set on the instance shadows the class method, so `SelectiveExtractorV2` sets the skipped families on itself to a function returning `{}`. Every other line of both orchestrators runs unchanged: `CleanView`, the corrections, the quality and sanitizer columns, the error accounting. The skipped families' columns are simply absent from the row, and `vectorise` never asks for them.

### 2.2 Why DTW and layout are skipped by passing `templates=None`
`V1.extract` guards both with `if templates:` (`:3437` and `:3453`). With `templates=None`:
- DTW isn't computed;
- the seven `place_layout_*` columns are written as `0.0` (`:3444-3446`), exactly as for a session without templates.

This needs **no monkeypatching**, which matters because the service runs gunicorn **gevent** workers (`nginx/gunicorn.config.py:8`). Many requests share one process, so patching module functions per request would be unsafe.

### 2.3 Why a committed column-to-family map
Column names don't say reliably which family produced them. For example, `touch_iv_median` comes from `extract_touch` calling `interval_block(t, 'iv')` and renaming the keys. The only reliable source is running the families and recording what each returns.

`tools/build_column_family_map.py` does that offline over real sessions and writes `features/column_families.json`. The file records the sha256 of the two vendored extractor files it was built from. At load time the service compares them; if either file has changed, it ignores the map and extracts in full until the map is rebuilt. It logs an error saying so.

### 2.4 Why the switch defaults to `full`
With `ML_EXTRACT_MODE=full`, the code path is today's: `_EXTRACTOR.extract(view, templates, None)`. Any doubt in production is one environment change and a restart away from today's behaviour.

## 3. New files

### 3.1 `mobile_navigation_core/extraction_plan.py` (new)

```python
"""Which feature families a bundle's columns need (ML_EXTRACT_MODE=needed|narrow).

features/column_families.json maps every extracted column to the family (or
families) that produce it. It is generated offline by
tools/build_column_family_map.py from real sessions and is trusted only while the
two vendored extractor files are byte-identical to the ones it was built from.

plan_for() returns None - meaning "extract in full, exactly as before" - whenever
it cannot be sure: no map, a stale map, or a column the map does not know.
"""
from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(HERE, 'features', 'column_families.json')
VENDOR_FILES = ('new_feature_creation_session.py', 'new_feature_creation_session_v2.py')

# The family methods both orchestrators call, in their own order
# (vendor/new_feature_creation_session.py:3397-3424, _v2.py:3000-3002).
V1_FAMILIES = (
    'extract_context', 'extract_navigation', 'extract_touch', 'extract_touch_paths',
    'extract_keystrokes', 'extract_sensor_stats', 'extract_sensor_spectral',
    'extract_sensor_complexity', 'extract_derived_motion', 'extract_orientation',
    'extract_correlations', 'extract_tap_locked', 'extract_touch_motion_coupling',
    'extract_per_screen', 'extract_cognitive', 'extract_placement', 'extract_key_locked',
    'extract_stage2', 'extract_stage3')
V2_FAMILIES = (
    'extract_field_segments', 'extract_field_contrasts', 'extract_posture_digraph',
    'extract_cross_window', 'extract_adev', 'extract_states', 'extract_cross_event',
    'extract_nonkbd', 'extract_tap_spectral', 'extract_screen_deep')
ALL_FAMILIES = V1_FAMILIES + V2_FAMILIES
TEMPLATE_PREFIXES = ('dtw_', 'place_layout_')       # columns that need the DTW templates

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExtractionPlan:
    families: frozenset        # family methods that must run
    skip: frozenset            # family methods that are not run
    need_templates: bool       # any dtw_ / place_layout_ column selected
    columns: tuple             # the bundle's feature columns, in bundle order


def vendor_sha256():
    out = {}
    for name in VENDOR_FILES:
        with open(os.path.join(HERE, 'vendor', name), 'rb') as fh:
            out[name] = hashlib.sha256(fh.read()).hexdigest()
    return out


@functools.lru_cache(maxsize=1)
def load_map():
    """{column: (family, ...)} or None when the map is missing or stale."""
    try:
        with open(MAP_PATH, encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as error:
        logger.error('column family map unavailable (%s): extraction stays FULL', error)
        return None
    if doc.get('vendor_sha256') != vendor_sha256():
        logger.error('column family map was built for different vendor files: '
                     'extraction stays FULL until tools/build_column_family_map.py is re-run')
        return None
    return {col: tuple(fams) for col, fams in doc['columns'].items()}


@functools.lru_cache(maxsize=64)
def plan_for(columns):
    """ExtractionPlan for a tuple of feature columns, or None (= extract in full)."""
    fmap = load_map()
    if fmap is None:
        return None
    families = set()
    for col in columns:
        if col.startswith(TEMPLATE_PREFIXES):
            continue                                 # produced by DTW / layout, not a family
        fams = fmap.get(col)
        if fams is None:
            logger.warning('column %r is not in the family map: this bundle extracts FULL', col)
            return None
        families.update(f for f in fams if f in ALL_FAMILIES)   # 'orchestration' always runs
    families = frozenset(families)
    return ExtractionPlan(
        families=families,
        skip=frozenset(ALL_FAMILIES) - families,
        need_templates=any(c.startswith(TEMPLATE_PREFIXES) for c in columns),
        columns=tuple(columns),
    )
```

### 3.2 `mobile_navigation_core/selected_extractor.py` (new)

```python
"""SessionFeatureExtractorV2 that runs only some families (ML_EXTRACT_MODE=needed|narrow).

Nothing in vendor/ is changed and nothing is patched at module level. A skipped
family is replaced on the INSTANCE by a function that returns {}: both
orchestrators call families through `self` (V1.extract builds its list from
self.extract_*, V2.extract uses getattr(self, ...)), so they pick up the stub and
every other line of them - CleanView, corrections, quality and sanitizer columns,
feat_errors - runs exactly as before.

Instances are built once per skip set and shared across requests; they are never
modified after __init__, so sharing is safe under gevent / threads.
"""
from __future__ import annotations

import functools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import vendor                                   # noqa: E402,F401  puts vendor/ on sys.path
import new_feature_creation_session_v2 as V2    # noqa: E402


def _skipped_family(view):
    return {}


class SelectiveExtractorV2(V2.SessionFeatureExtractorV2):

    def __init__(self, skip=(), **kw):
        super().__init__(**kw)                  # same constructor as feature_extraction._EXTRACTOR
        self.skip = frozenset(skip)
        for name in self.skip:
            if not hasattr(V2.SessionFeatureExtractorV2, name):
                raise ValueError('unknown feature family %r' % name)
            setattr(self, name, _skipped_family)


@functools.lru_cache(maxsize=16)
def extractor_for(skip):
    """One shared instance per frozenset of skipped families."""
    return SelectiveExtractorV2(skip=skip)
```

### 3.3 `tools/build_column_family_map.py` (new)

```python
"""Build mobile_navigation_core/features/column_families.json.

Runs the FULL v2 extractor over real sessions with every family wrapped, records
which family returned which column, and writes the map with the sha256 of the two
vendored extractor files. Re-run it whenever either vendored file changes: the
service ignores a stale map and extracts in full until then.

usage: python tools/build_column_family_map.py <staging envelope> [<envelope> ...]
       An envelope is any file EnvelopeWriter wrote (an enrolment's stage/sessions.json,
       or <corpus>/<user>/sessions.json). Use several users for full coverage.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'mobile_navigation_core')
sys.path[:0] = [CORE, ROOT]

import behavior_cleaner as BC                   # noqa: E402
import extraction_plan as PLAN                  # noqa: E402
import feature_extraction as FE                 # noqa: E402
import new_feature_creation_session_v2 as V2    # noqa: E402


def main(paths):
    extractor = V2.SessionFeatureExtractorV2()
    produced = {}
    for name in PLAN.ALL_FAMILIES:
        real = getattr(extractor, name)

        def recording(view, _real=real, _name=name):
            out = _real(view)
            for key in out:
                produced.setdefault(key, set()).add(_name)
            return out
        setattr(extractor, name, recording)

    FE._EXTRACTOR = extractor                   # this tool's own process only
    columns, n = set(), 0
    for path in paths:
        with open(path, encoding='utf-8') as fh:
            blob = json.load(fh)
        user = blob['data'].get('user_id') or os.path.basename(os.path.dirname(path))
        census = BC.build_census(BC.iter_raw_sessions(path), user)
        for s in blob['data']['sessions']:
            # templates=None: dtw_ / place_layout_ columns are recognised by prefix
            row, _ = FE.extract_session(json.loads(json.dumps(s)), user, None, census=census)
            columns.update(row)
            n += 1
            print(f'{n} sessions, {len(columns)} columns', flush=True)

    doc = {
        'built_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'n_sessions': n,
        'vendor_sha256': PLAN.vendor_sha256(),
        'columns': {c: sorted(produced.get(c, {'orchestration'})) for c in sorted(columns)},
    }
    with open(PLAN.MAP_PATH, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
    print(f'wrote {PLAN.MAP_PATH}: {len(columns)} columns from {n} sessions')

    # every column of every selection profile must be known (or be DTW/layout)
    with open(os.path.join(CORE, 'features', 'selections.json'), encoding='utf-8') as fh:
        profiles = json.load(fh)['profiles']
    for name, prof in profiles.items():
        with open(os.path.join(CORE, prof['file']), encoding='utf-8') as fh:
            cols = json.load(fh).get('selected') or []
        missing = [c for c in cols if c not in doc['columns'] and not c.startswith(PLAN.TEMPLATE_PREFIXES)]
        print(f'profile {name}: {len(cols)} columns, {len(missing)} unmapped {missing[:5]}')


if __name__ == '__main__':
    main(sys.argv[1:])
```

### 3.4 `mobile_navigation_core/features/column_families.json` (generated, committed)

This file is produced by the tool above; never edit it by hand. Its shape:

```json
{
 "built_at": "2026-10-20T10:00:00",
 "n_sessions": 43,
 "vendor_sha256": {
  "new_feature_creation_session.py": "<sha256>",
  "new_feature_creation_session_v2.py": "<sha256>"
 },
 "columns": {
  "acc_x_centroid": ["extract_sensor_spectral"],
  "lin_mag_zcr": ["extract_sensor_stats"],
  "san_verdict": ["orchestration"],
  "tap_acc_x_energy_idr": ["extract_tap_locked"],
  "touch_iv_median": ["extract_touch"]
 }
}
```

Generate it with:

```bash
python tools/build_column_family_map.py <corpus>/*/sessions.json
```

## 4. Changed files, line by line

### 4.1 `mobile_navigation_core/feature_extraction.py`

**(a) Imports, after line 75** (`import new_feature_creation_session_v2 as V2`)

Before:
```python
import new_feature_creation_session_v2 as V2    # noqa: E402

logger = logging.getLogger(__name__)
```

After:
```python
import new_feature_creation_session_v2 as V2    # noqa: E402

import extraction_plan as PLAN                  # noqa: E402  Change 2
import selected_extractor as SX                 # noqa: E402  Change 2

logger = logging.getLogger(__name__)
```

**(b) The mode switch, after line 81** (`_EXTRACTOR = V2.SessionFeatureExtractorV2()`)

Before:
```python
_EXTRACTOR = V2.SessionFeatureExtractorV2()

ALIGN_HZ = SCH.ALIGN_HZ_DEFAULT                 # 50.0
```

After:
```python
_EXTRACTOR = V2.SessionFeatureExtractorV2()

# ML_EXTRACT_MODE
#   full    every family + DTW, exactly as before (default)
#   needed  only the families the bundle's columns come from; DTW/layout only if
#           a dtw_ / place_layout_ column is selected (Change 2)
#   narrow  needed + skip unread work inside those families (Change 3)
# Any mode falls back to `full` for a bundle the column map cannot fully explain.
EXTRACT_MODE = (os.getenv('ML_EXTRACT_MODE') or 'full').strip().lower()
if EXTRACT_MODE not in ('full', 'needed', 'narrow'):
    logger.error('ML_EXTRACT_MODE=%r is not full|needed|narrow; using full', EXTRACT_MODE)
    EXTRACT_MODE = 'full'
# ML_EXTRACT_SHADOW=1: also run the full extractor and log any selected value that
# differs. For the first days after switching mode only - it doubles the time.
EXTRACT_SHADOW = (os.getenv('ML_EXTRACT_SHADOW') or '0').strip() == '1'

ALIGN_HZ = SCH.ALIGN_HZ_DEFAULT                 # 50.0
```

**(c) `extractor_identity`, lines 162–168:** report the mode at boot and in `/nav/ai/info`.

Before:
```python
def extractor_identity():
    """What this module will run, for the startup log and /nav/ai/info."""
    return {
        'extractor': 'v2',
        'extractor_class': 'SessionFeatureExtractorV2',
        'align_hz': float(ALIGN_HZ),
    }
```

After:
```python
def extractor_identity():
    """What this module will run, for the startup log and /nav/ai/info."""
    return {
        'extractor': 'v2',
        'extractor_class': 'SessionFeatureExtractorV2',
        'align_hz': float(ALIGN_HZ),
        'extract_mode': EXTRACT_MODE,
        'extract_shadow': EXTRACT_SHADOW,
        'column_map_loaded': EXTRACT_MODE == 'full' or PLAN.load_map() is not None,
    }
```

**(d) Signature, lines 171–172.** If Change 1 is already in, keep its `copy_input` argument as well.

Before:
```python
def extract_session(raw_session, user_id, templates,
                    census=None, needs_census=False):
```

After:
```python
def extract_session(raw_session, user_id, templates,
                    census=None, needs_census=False, feature_columns=None):
```

Add one sentence to the docstring:

```python
    `feature_columns` (the bundle's column list) lets ML_EXTRACT_MODE=needed|narrow
    run only the families those columns come from. None = every family.
```

**(e) Step 5, lines 245–246: the actual change**

Before:
```python
    # ---- 5. features -------------------------------------------------------
    row = _EXTRACTOR.extract(view, templates, None)
```

After:
```python
    # ---- 5. features -------------------------------------------------------
    plan = (PLAN.plan_for(tuple(feature_columns))
            if EXTRACT_MODE != 'full' and feature_columns else None)
    if plan is None:
        # today's path: every family, DTW and layout
        row = _EXTRACTOR.extract(view, templates, None)
        diagnostics['extract_mode'] = 'full'
        diagnostics['n_families'] = len(PLAN.ALL_FAMILIES)
    else:
        extractor = SX.extractor_for(plan.skip)
        # templates only when a dtw_ / place_layout_ column is selected:
        # V1.extract skips DTW and zero-fills place_layout_* when it gets None
        row = extractor.extract(view, templates if plan.need_templates else None, None)
        diagnostics['extract_mode'] = 'needed'
        diagnostics['n_families'] = len(plan.families)
        if EXTRACT_SHADOW:
            full = _EXTRACTOR.extract(view, templates, None)
            differ = [c for c in plan.columns
                      if c not in row or not _same(row[c], full.get(c))]
            diagnostics['shadow_differ'] = len(differ)
            if differ:
                logger.warning('SHADOW: %d selected column(s) differ from full '
                               'extraction for session %s: %s', len(differ),
                               raw.get('session_id'), differ[:5])
```

**(f) A helper for the shadow comparison.** Add next to `_first` (after line 106):

```python
def _same(a, b):
    """Exact equality with NaN == NaN (shadow comparison)."""
    if isinstance(a, float) and isinstance(b, float) and a != a and b != b:
        return True
    return a == b
```

**(g)** `diagnostics['n_columns'] = len(row)` (line 248) stays. It now reports the smaller column count in `needed` mode, which is expected.

### 4.2 `mobile_navigation_core/prediction_service.py`

**(a) Lines 206–209:** pass the bundle's own column list.

Before:
```python
            row, diagnostics = extract_session(
                session, user_id, templates,
                census=bundle.census, needs_census=bundle.needs_census)
```

After:
```python
            row, diagnostics = extract_session(
                session, user_id, templates,
                census=bundle.census, needs_census=bundle.needs_census,
                feature_columns=bundle.feature_columns)       # Change 2
```

With Change 1 also in, the call has both `copy_input=COPY_INPUT` and `feature_columns=bundle.feature_columns`.

**(b) Response, line 271:** add after `'extract_ms'`.

```python
            'extract_mode': diagnostics.get('extract_mode'),
            'n_families': diagnostics.get('n_families'),
```

**(c) The per-request log line, lines 280–288:** add the mode, so `app.log` shows which path ran.

Before:
```python
        logger.info(
            '%s/%s -> %s score=%+.6f thr=%+.6f margin=%+.6f k=%d %s '
            '(load=%.0fms extract=%.0fms score=%.0fms total=%.0fms)',
            user_id, session_id, 'GENUINE' if is_genuine else 'IMPOSTER',
            score, bundle.threshold, score - bundle.threshold,
            described['n_features'],
            'UNCERTIFIED' if described['model_uncertified'] else 'deployable',
            load_ms, diagnostics.get('extract_ms') or 0, score_ms,
            response['total_ms'])
```

After:
```python
        logger.info(
            '%s/%s -> %s score=%+.6f thr=%+.6f margin=%+.6f k=%d %s '
            '(load=%.0fms extract=%.0fms[%s] score=%.0fms total=%.0fms)',
            user_id, session_id, 'GENUINE' if is_genuine else 'IMPOSTER',
            score, bundle.threshold, score - bundle.threshold,
            described['n_features'],
            'UNCERTIFIED' if described['model_uncertified'] else 'deployable',
            load_ms, diagnostics.get('extract_ms') or 0,
            diagnostics.get('extract_mode'), score_ms,
            response['total_ms'])
```

### 4.3 `.env`

```dotenv
# Change 2/3: full = every feature family (as before) | needed = only families the model reads | narrow = Change 3
ML_EXTRACT_MODE=full
# 1 = also run full extraction and log differences (validation only; doubles extraction time)
ML_EXTRACT_SHADOW=0
```

### 4.4 Not changed
- **`bundle_loader.py`**: `BundleStore.get` still loads the DTW templates for every user.
  - Skipping that load when `need_templates` is false is a possible later saving, but templates are loaded once per user and then cached (`bundle_loader.py:347-351`), so the per-request cost is zero.
- **`enrollment_service.py`, `train_jobs.py`**: training still builds every column with `SessionPipelineV2`. The training CSVs, census, templates and bundles are byte-identical.
- **`vendor/`**: no byte changes.

## 5. What happens before and after (v8 selection)

| | Before (`full`) | After (`needed`) |
|---|---|---|
| Families run | 29 | 15 |
| DTW distances | computed (1.63 s mean on the laptop) | not computed |
| Layout comparison | computed | skipped; 7 `place_layout_*` columns written as 0.0 |
| Columns in the row | 5,483 | 4,260 |
| Extraction median (laptop, 43 sessions) | 3.14 s | **1.09 s** (0.97 s with Change 1) |
| The 50 selected values | — | **identical** (43/43) |
| Score, `is_genuine`, `risk_score` | — | unchanged |
| Response | — | adds `extract_mode`, `n_families`; `n_columns` drops |
| A user whose bundle uses `dtw_` columns (another selection) | — | DTW still runs (`need_templates=True`) |
| A bundle with a column the map doesn't know | — | full extraction, plus a warning in the log |
| Map missing, or vendor files changed | — | full extraction, plus an error in the log |
| Training and enrolment | — | unchanged |

## 6. Tests: `tests/test_change2_needed_families.py` (new)

Uses `tests/conftest.py` from Change 1 (copy it from `PERF_CHANGE_1_REMOVE_DEEPCOPY.md` §6.2 if Change 1 isn't in yet).

```python
import json

from conftest import same


def _v8_columns():
    import enrollment_service as ES
    return tuple(ES.check_selection(ES.active_profile())[0])


def test_map_is_current():
    """The committed map must match the vendored files, or the service runs FULL."""
    import extraction_plan as PLAN
    assert PLAN.load_map() is not None, 're-run tools/build_column_family_map.py'


def test_every_profile_is_fully_mapped():
    import os
    import extraction_plan as PLAN
    feats = os.path.join(PLAN.HERE, 'features')
    with open(os.path.join(feats, 'selections.json'), encoding='utf-8') as fh:
        profiles = json.load(fh)['profiles']
    for name, prof in profiles.items():
        with open(os.path.join(PLAN.HERE, prof['file']), encoding='utf-8') as fh:
            cols = json.load(fh).get('selected') or []
        assert PLAN.plan_for(tuple(cols)) is not None, f'profile {name} would extract FULL'


def test_needed_mode_gives_identical_selected_values(corpus, monkeypatch):
    import feature_extraction as FE
    cols = _v8_columns()
    for user, raw, census, templates in corpus:
        monkeypatch.setattr(FE, 'EXTRACT_MODE', 'full')
        full, _ = FE.extract_session(json.loads(raw), user, templates, census=census,
                                     feature_columns=cols)
        monkeypatch.setattr(FE, 'EXTRACT_MODE', 'needed')
        part, diag = FE.extract_session(json.loads(raw), user, templates, census=census,
                                        feature_columns=cols)
        assert diag['extract_mode'] == 'needed'
        bad = [c for c in cols if c not in part or not same(part[c], full[c])]
        assert not bad, (user, bad[:5])


def test_unknown_column_falls_back_to_full():
    import extraction_plan as PLAN
    assert PLAN.plan_for(('no_such_feature_column',)) is None


def test_no_module_globals_are_patched(corpus, monkeypatch):
    """Needed mode must not swap any module-level function (gevent safety)."""
    import feature_extraction as FE
    import new_feature_creation_session as V1
    before = (V1.compute_dtw_features, V1.compare_layout, V1._agg_block)
    monkeypatch.setattr(FE, 'EXTRACT_MODE', 'needed')
    user, raw, census, templates = corpus[0]
    FE.extract_session(json.loads(raw), user, templates, census=census,
                       feature_columns=_v8_columns())
    assert (V1.compute_dtw_features, V1.compare_layout, V1._agg_block) == before
```

Run:

```bash
ADAPID_PARITY_CORPUS=/path/to/corpus python -m pytest tests/test_change2_needed_families.py -q
```

## 7. Rollout

1. Build the map from as many real sessions as available, at least the 43-session corpus plus a few enrolment staging files from production, and commit `column_families.json`.
2. Merge with `ML_EXTRACT_MODE=full`. No behaviour change; the boot log and `/nav/ai/info` show `extract_mode: full`.
3. Run the tests in §6. All must pass.
4. Set `ML_EXTRACT_MODE=needed` and `ML_EXTRACT_SHADOW=1` on one instance for a day or two.
   - Every request then also runs the full extractor and compares.
   - `grep SHADOW app.log` must show nothing.
   - `shadow_differ` in the response must be 0.
5. Set `ML_EXTRACT_SHADOW=0`, then watch `extract_ms` and `extract=...ms[needed]` in `app.log`.
6. Whenever a vendored extractor file changes, re-run `tools/build_column_family_map.py` and commit the new map. Until then the service runs `full` on its own.

**Rollback:** `ML_EXTRACT_MODE=full`, then restart.

## 8. Risks and how they are covered

| Risk | Covered by |
|---|---|
| A skipped family's work was secretly needed by a kept family (shared state) | parity test (43/43 for v8); shadow mode in production |
| A different selection (rev4, v6) uses DTW or other families | the plan is built per bundle from its own `feature_columns`; DTW runs whenever a `dtw_` column is selected |
| Vendored code is updated and the map goes stale | sha256 check means automatic fallback to `full`, plus a log error; `test_map_is_current` fails in CI |
| A new column appears that the map doesn't know | that bundle falls back to `full`, with a log warning |
| Shared extractor instances under gevent | instances are never modified after `__init__`; no module-level patching (`test_no_module_globals_are_patched`) |
| Training drifts from serving | training is untouched and still uses the full extractor |

## 9. Checklist

- [ ] `mobile_navigation_core/extraction_plan.py` (§3.1)
- [ ] `mobile_navigation_core/selected_extractor.py` (§3.2)
- [ ] `tools/build_column_family_map.py` (§3.3); generate and commit `features/column_families.json` (§3.4)
- [ ] `feature_extraction.py`: imports, mode switch, identity, signature, step 5, `_same` (§4.1)
- [ ] `prediction_service.py`: call, response fields, log line (§4.2)
- [ ] `.env`: `ML_EXTRACT_MODE`, `ML_EXTRACT_SHADOW` (§4.3)
- [ ] `tests/test_change2_needed_families.py` green on the corpus (§6)
- [ ] Deploy `full`, then `needed` + shadow, then `needed` (§7)
