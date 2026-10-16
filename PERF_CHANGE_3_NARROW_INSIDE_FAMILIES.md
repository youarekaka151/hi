# Change 3 — Inside the kept families, compute only what the 50 columns read

| | |
|---|---|
| **What** | After Change 2, the 15 kept families still compute **4,260 columns to deliver 50**. Every family loops over every channel and calls a generic helper that returns dozens of statistics. This change adds two things. **(A) Helper gating:** a helper call runs only if one of its output keys is read by the model; otherwise it returns the same zero-filled result the code already uses for a missing channel. **(B) A narrowed `tap_locked` loop:** the per-touch window loop runs only the channels and metrics the model reads. |
| **Why** | The kept families are now ~90% of extraction time. The model reads 1–12 of their columns each, e.g. 1 of 665 from `sensor_stats` and 10 of 641 from `tap_locked`. |
| **Measured gain** | One run, paired, 43 sessions, no deepcopy in any arm. Extraction median: Change 2 alone **527 ms** → with (A) **277 ms** → with (A)+(B) **236 ms**, which is −55%. Feature-family time 476 → 221 → 181 ms. |
| **Effect on results** | None. All 50 selected values were identical on **43/43** sessions for (A) and for (A)+(B). |
| **Files changed** | `mobile_navigation_core/feature_extraction.py`, `mobile_navigation_core/extraction_plan.py`, `mobile_navigation_core/selected_extractor.py`, `.env` |
| **Files added** | `mobile_navigation_core/narrowing.py`, `tests/test_change3_narrow.py` |
| **Not touched** | Everything in `vendor/` (byte-identical), training and enrolment output, bundles, the backend, the SDK |
| **Switch** | `ML_EXTRACT_MODE=narrow` (needs Change 2's plan and map) |
| **Rollback** | `ML_EXTRACT_MODE=needed` (Change 2 only) or `full`, then restart |
| **Effort** | 2–3 days including tests |
| **Depends on** | **Change 2** (`extraction_plan.py`, `selected_extractor.py`, `column_families.json`). Change 1 is independent. |

Absolute milliseconds on the test laptop drift between runs: the same Change-2 arm measured 294–970 ms in different runs. The ratios within one run are stable, so judge this change by its ratio: about 0.45–0.5× of Change 2 alone.

---

## 1. Why the kept families are still slow

**Example 1: `extract_sensor_stats`** (`vendor/new_feature_creation_session.py:2111-2126`):

```python
for short, axis in ALL_STAT_CHANNELS:                 # 19 channels (:193 = INERTIAL + FUSED + FIELD)
    _, vals, _ = self._channel_values(view, short, axis)
    f.update(stat_block(vals, f'{short}_{axis}'))     # ~40 statistics each (:442-510)
```

- `stat_block` computes mean, std, min, max, range, median, iqr, mad, rms, energy, abs_mean, cv, zcr, entropy and slope; scipy skew and kurtosis; 5 percentiles; 9 first- and second-difference statistics; and 3 autocorrelations.
- That is 665 columns. v8 reads **one**, `lin_mag_zcr`.

**Example 2: `extract_tap_locked`** (`:2509-2598`):
- For every touch (median 47 per session) and **8 channels**, it cuts a −150 ms…+400 ms window and computes **8 metrics**.
- It then summarises each of the 64 lists with `_agg_block`, which v2 replaces with the 10-key `_wide_agg_block` (`_v2.py:881-912`) that includes a scipy skew.
- v8 reads 10 numbers from **5 channels × 5 metrics**.

**Every kept family, for v8:**

| Family | Columns computed | Read by v8 | Time with Change 2 only (ms) | With (A) | With (A)+(B) |
|---|---|---|---|---|---|
| `extract_tap_locked` | 641 | 10 | 127.8 | 80.9 | **29.7** |
| `extract_stage2` | 198 | 1 | 80.8 | **18.6** | 18.6 |
| `extract_sensor_stats` | 665 | 1 | 59.8 | **6.7** | 6.5 |
| `extract_sensor_spectral` | 749 | 5 | 41.0 | **11.1** | 11.1 |
| `extract_touch` | 423 | 10 | 35.9 | **12.2** | 12.9 |
| `extract_orientation` | 371 | 1 | 30.4 | **4.4** | 4.2 |
| `extract_tap_spectral` | 20 | 1 | 22.7 | 25.3 | 22.7 |
| `extract_keystrokes` | 421 | 12 | 19.2 | 19.4 | 20.8 |
| `extract_correlations` | 59 | 1 | 18.5 | 16.8 | 17.7 |
| `extract_key_locked` | 52 | 1 | 14.8 | 13.4 | 13.6 |
| `extract_derived_motion` | 123 | 2 | 11.9 | **6.8** | 6.8 |
| `extract_touch_paths` | 165 | 1 | 7.5 | **1.4** | 1.4 |
| `extract_field_segments` | 196 | 2 | 2.3 | 2.3 | 2.3 |
| `extract_field_contrasts` | 50 | 1 | 2.2 | 2.4 | 2.4 |
| `extract_nonkbd` | 13 | 1 | 0.9 | 1.1 | 1.0 |

Mean ms per session, exclusive, round 4. Bold marks where each part of this change helps.

## 2. Part A: helper gating

### 2.1 The convention it relies on
Every one of these helpers already returns its **complete key set, zero-filled**, when given empty input. The families depend on that whenever a channel is missing.
- For example, `_channel_values` returns `np.array([])` for an absent stream (`:2086-2091`), and `stat_block` then returns zeros for every key (`:453-465`).
- The pipeline is built so a column's presence never depends on the data ("Every sub-family emits its full key set even when it cannot be computed", `:1228-1232`).

### 2.2 The rule
For each helper call:
1. Work out the helper's **output keys**. Call it once with the data arguments emptied, and cache the key set by the non-data arguments (prefix, percentiles, bands and so on).
2. If any output key is **read**, call the real helper exactly as the family asked.
3. Otherwise return the zero-filled result from step 1.

A key counts as **read** if it equals one of the bundle's 50 columns **or** is a `_`-suffix of one. The suffix rule is required:
- `extract_touch` calls `interval_block(t_down, 'iv')` and renames each key to `touch_<key>` (`:1582`);
- so the helper produces `iv_median`, which the model reads as `touch_iv_median`.

The first prototype matched exact names only and broke `touch_iv_median` and `touch_iv_log_std` on every session. The suffix rule fixed that: 43/43.

When a helper does run, it runs the real code on the real inputs, so the value is identical. When it is skipped, nothing reads its output.

### 2.3 The helpers gated

| Helper | Module (file:line) | Data arguments emptied |
|---|---|---|
| `stat_block` | `new_feature_creation_session.py:442` | `values` |
| `spectral_block` | `:513` | `values` |
| `wavelet_block` | `:667` | `values` |
| `complexity_block` | `:907` | `values` |
| `shape_block` | `:953` | `xs`, `ys` |
| `interval_block` | `:1030` | `times` |
| `_agg_block` (the installed 10-key version, `_v2.py:881`) | `:3561` | `values` |
| `_lag_features` | `:3666` | `a`, `b` |
| `contact_geometry` | `derived_features.py:108` | `touches` |
| `world_frame` | `derived_features.py:157` | `lin_xyz`, `grav_xyz`, `quat` |
| `interval_dynamics` | `derived_features.py:212` | `intervals` |
| `spectral_entropy_block` | `derived_features.py:276` | `values`, `fs` |

### 2.4 Why a context variable rather than patching per request
- The service runs gunicorn **gevent** workers (`nginx/gunicorn.config.py:8`), so many requests share one process. Swapping module functions around each request is unsafe.
- Instead, the gated wrappers are installed **once at import**. They do **nothing** unless the current request has set `READ_KEYS` (a `contextvars.ContextVar`).
  - Only `extract_session` sets it, and only in `narrow` mode, around the single extraction call.
  - Context variables are per-greenlet under gevent (gevent ≥ 20.12 with greenlet ≥ 0.4.17) and per-thread under threads.
  - Training, the research CLIs, `full` and `needed` modes and the shadow comparison never set it, so the original helpers run unchanged.
- There is a precedent: v2 already wraps a v1 helper the same way at import (`install_wide_agg`, `_v2.py:915-938`).

## 3. Part B: the narrowed `tap_locked` loop

Helper gating alone takes `tap_locked` from 128 to 81 ms. The rest is its inline window loop, which slices 8 channels and computes 8 metrics per touch.

The narrowed version is a **line-for-line copy** of `extract_tap_locked` (`:2509-2598`) with two filters:
1. only channels with a selected `tap_<channel>_<metric>_<agg>` column;
2. only those metrics.

The windows, baselines and formulas are untouched, so every kept list gets the same values in the same order. The result is 81 → 30 ms.

Because it is a copy, it must not drift from vendor:
- The class stores the sha256 of `inspect.getsource(V1.SessionFeatureExtractor.extract_tap_locked)`.
- If vendor changes, the narrowed method switches itself off (logging an error) and the original runs.
- A test fails as well, so the copy gets reviewed.

## 4. New file: `mobile_navigation_core/narrowing.py`

```python
"""Change 3 (ML_EXTRACT_MODE=narrow): skip helper work whose outputs no model column reads.

install() wraps twelve prefix-based helpers once, at import. A wrapper does
NOTHING unless the current request has set READ_KEYS - feature_extraction does so
only in narrow mode, around one extraction - so training, the research CLIs and
the full / needed modes run the original helpers.

When active, a helper call runs for real only if one of its output keys is read.
Otherwise it returns the helper's own empty-input result: the same zero-filled key
set the families already produce for a missing channel.
"""
from __future__ import annotations

import contextvars
import inspect
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import vendor                                   # noqa: E402,F401  puts vendor/ on sys.path
import new_feature_creation_session as V1      # noqa: E402
import new_feature_creation_session_v2 as V2   # noqa: E402,F401  must be imported FIRST: it installs
                                                #   the 10-key _agg_block that is wrapped below
import derived_features as DF                   # noqa: E402

# The request's read keys: the bundle's columns plus every '_'-suffix of them.
READ_KEYS = contextvars.ContextVar('adapid_read_keys', default=None)

_EMPTY = np.array([])
GATED = {
    'stat_block':             (V1, {'values': _EMPTY}),
    'spectral_block':         (V1, {'values': _EMPTY}),
    'wavelet_block':          (V1, {'values': _EMPTY}),
    'complexity_block':       (V1, {'values': _EMPTY}),
    'shape_block':            (V1, {'xs': _EMPTY, 'ys': _EMPTY}),
    'interval_block':         (V1, {'times': _EMPTY}),
    '_agg_block':             (V1, {'values': []}),
    '_lag_features':          (V1, {'a': _EMPTY, 'b': _EMPTY}),
    'contact_geometry':       (DF, {'touches': []}),
    'world_frame':            (DF, {'lin_xyz': [], 'grav_xyz': [], 'quat': None}),
    'interval_dynamics':      (DF, {'intervals': []}),
    'spectral_entropy_block': (DF, {'values': [], 'fs': None}),
}
_NOT_KEY = ('fs', 'hz')            # data-dependent arguments that never change the key set
_KEYS = {}                         # (helper, non-data arguments) -> frozenset of output keys
_INSTALLED = False


def _gate(name, real, empty):
    sig = inspect.signature(real)

    def gated(*args, **kwargs):
        read = READ_KEYS.get()
        if read is None:                               # not in a narrow extraction
            return real(*args, **kwargs)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        a = bound.arguments
        ck = (name,) + tuple((k, repr(v)) for k, v in sorted(a.items())
                             if k not in empty and k not in _NOT_KEY)
        keys = _KEYS.get(ck)
        zero = None
        if keys is None:
            try:
                zero = real(**{**a, **empty})
            except Exception:                           # noqa: BLE001  cannot tell: compute
                return real(*args, **kwargs)
            keys = _KEYS.setdefault(ck, frozenset(zero))
        if keys & read:
            return real(*args, **kwargs)               # read: the real computation
        return zero if zero is not None else real(**{**a, **empty})

    gated.__wrapped__ = real
    gated.__name__ = name
    return gated


def install():
    """Wrap the helpers once. Idempotent."""
    global _INSTALLED
    if _INSTALLED:
        return
    for name, (module, empty) in GATED.items():
        setattr(module, name, _gate(name, getattr(module, name), empty))
    _INSTALLED = True


def read_keys_for(columns):
    """The columns plus every '_'-suffix of each (catches families that rename keys)."""
    read = set(columns)
    for c in columns:
        read.update(c[i + 1:] for i, ch in enumerate(c) if ch == '_')
    return frozenset(read)
```

Why the gates are reached:
- v1 code calls these helpers as **module globals at call time**, and v2 calls `V1._agg_block` at call time.
- `stage2` and `stage3` reach `derived_features` through the module aliases `S2` and `S3`, which are the same module object.
- Replacing the module attributes is therefore enough. That is exactly the mechanism `install_wide_agg` relies on (`_v2.py:926-931`).

Cost when active: about 200 gate checks per session, each a signature bind plus a set intersection. That's a few milliseconds and is included in the measured numbers.

## 5. Changed files, line by line

### 5.1 `mobile_navigation_core/extraction_plan.py` (from Change 2)

**(a) Two new fields on `ExtractionPlan`**

Before:
```python
@dataclass(frozen=True)
class ExtractionPlan:
    families: frozenset        # family methods that must run
    skip: frozenset            # family methods that are not run
    need_templates: bool       # any dtw_ / place_layout_ column selected
    columns: tuple             # the bundle's feature columns, in bundle order
```

After:
```python
@dataclass(frozen=True)
class ExtractionPlan:
    families: frozenset        # family methods that must run
    skip: frozenset            # family methods that are not run
    need_templates: bool       # any dtw_ / place_layout_ column selected
    columns: tuple             # the bundle's feature columns, in bundle order
    read_keys: frozenset = frozenset()   # Change 3: columns + every '_'-suffix
    tap_need: tuple = None               # Change 3: ((channel, (metric, ...)), ...) or None
```

**(b) Parse the `tap_locked` columns.** Add above `plan_for`. The lists are copied from `extract_tap_locked` (`:2531-2535`, `:2595-2596`).

```python
TAP_CHANNELS = ('acc_mag', 'gyro_mag', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z')
TAP_METRICS = ('peak', 'ttp_ms', 'energy', 'rms', 'settle_ms', 'recovery', 'post_var', 'pre_var')


def _tap_need(columns, fmap):
    """{channel: metrics} the tap_locked columns read, or None to run the original loop."""
    need = {}
    for c in columns:
        if 'extract_tap_locked' not in fmap.get(c, ()):
            continue
        hit = [(ch, m) for ch in TAP_CHANNELS for m in TAP_METRICS
               if c.startswith(f'tap_{ch}_{m}_')]
        if len(hit) != 1:
            return None                 # e.g. tap_n_used: not a channel/metric column
        ch, m = hit[0]
        need.setdefault(ch, set()).add(m)
    return tuple(sorted((ch, tuple(sorted(ms))) for ch, ms in need.items())) or None
```

**(c) Fill the fields in `plan_for`**

Before:
```python
    families = frozenset(families)
    return ExtractionPlan(
        families=families,
        skip=frozenset(ALL_FAMILIES) - families,
        need_templates=any(c.startswith(TEMPLATE_PREFIXES) for c in columns),
        columns=tuple(columns),
    )
```

After:
```python
    families = frozenset(families)
    read = set(columns)
    for c in columns:
        read.update(c[i + 1:] for i, ch in enumerate(c) if ch == '_')
    return ExtractionPlan(
        families=families,
        skip=frozenset(ALL_FAMILIES) - families,
        need_templates=any(c.startswith(TEMPLATE_PREFIXES) for c in columns),
        columns=tuple(columns),
        read_keys=frozenset(read),
        tap_need=_tap_need(columns, fmap),
    )
```

### 5.2 `mobile_navigation_core/selected_extractor.py` (from Change 2)

**(a) Imports:** add after `import new_feature_creation_session_v2 as V2`.

```python
import hashlib                                  # noqa: E402
import inspect                                  # noqa: E402
import logging                                  # noqa: E402
from collections import defaultdict             # noqa: E402

import numpy as np                              # noqa: E402

import narrowing as NARROW                      # noqa: E402
import new_feature_creation_session as V1      # noqa: E402

logger = logging.getLogger(__name__)

# sha256 of inspect.getsource(V1.SessionFeatureExtractor.extract_tap_locked) that the
# narrowed copy below was taken from. Fill in at implementation time with:
#   python -c "import sys,inspect,hashlib; sys.path[:0]=['mobile_navigation_core',
#   'mobile_navigation_core/vendor']; import new_feature_creation_session as V1;
#   print(hashlib.sha256(inspect.getsource(V1.SessionFeatureExtractor.extract_tap_locked)
#   .encode()).hexdigest())"
TAP_LOCKED_SOURCE_SHA256 = '<fill in>'


def _tap_source_unchanged():
    src = inspect.getsource(V1.SessionFeatureExtractor.extract_tap_locked)
    return hashlib.sha256(src.encode()).hexdigest() == TAP_LOCKED_SOURCE_SHA256
```

**(b) The class gains `tap_need` and the narrowed method**

Before:
```python
class SelectiveExtractorV2(V2.SessionFeatureExtractorV2):

    def __init__(self, skip=(), **kw):
        super().__init__(**kw)                  # same constructor as feature_extraction._EXTRACTOR
        self.skip = frozenset(skip)
        for name in self.skip:
            if not hasattr(V2.SessionFeatureExtractorV2, name):
                raise ValueError('unknown feature family %r' % name)
            setattr(self, name, _skipped_family)
```

After:
```python
class SelectiveExtractorV2(V2.SessionFeatureExtractorV2):

    def __init__(self, skip=(), tap_need=None, **kw):
        super().__init__(**kw)                  # same constructor as feature_extraction._EXTRACTOR
        self.skip = frozenset(skip)
        for name in self.skip:
            if not hasattr(V2.SessionFeatureExtractorV2, name):
                raise ValueError('unknown feature family %r' % name)
            setattr(self, name, _skipped_family)
        self.tap_need = ({ch: frozenset(ms) for ch, ms in tap_need} if tap_need else None)
        if self.tap_need is not None and not _tap_source_unchanged():
            logger.error('vendor extract_tap_locked changed since the narrowed copy was '
                         'taken: running the original. Review selected_extractor.py.')
            self.tap_need = None

    def extract_tap_locked(self, view):
        """Change 3 (B). Outside a narrow extraction, or without a plan: the original."""
        if self.tap_need is None or NARROW.READ_KEYS.get() is None:
            return super().extract_tap_locked(view)
        return _tap_locked_narrow(self, view, self.tap_need)
```

**(c) The narrowed loop:** add as a module function. Lines marked `NARROWED` are the only differences from `vendor/new_feature_creation_session.py:2523-2598`.

```python
def _tap_locked_narrow(self, view, need):
    f = {}
    shorts = [s for s in ('acc', 'gyro') if view.has(s)]
    if not shorts or not view.touches:
        f.update(V1._zero_like(self._tap_keys()))
        f['tap_n_used'] = 0.0
        return f

    pre_ms, post_ms = 150.0, 400.0
    channels = [('acc', 'mag'), ('gyro', 'mag')]
    if view.has('acc'):
        channels += [('acc', 'x'), ('acc', 'y'), ('acc', 'z')]
    if view.has('gyro'):
        channels += [('gyro', 'x'), ('gyro', 'y'), ('gyro', 'z')]
    channels = [(s, ax) for s, ax in channels if f'{s}_{ax}' in need]          # NARROWED

    per_channel = {f'{s}_{ax}': defaultdict(list) for s, ax in channels}
    for touch in view.touches:
        t0 = touch.t_down
        if not np.isfinite(t0):
            continue
        for s, ax in channels:
            st = view.streams.get(s)
            if st is None:
                continue
            idx = st.slice_time(t0 - pre_ms, t0 + post_ms)
            if idx.size < 6:
                continue
            vals = (st.mag[idx] if ax == 'mag' else st.xyz[idx, 'xyz'.index(ax)])
            times = st.t[idx]
            m = np.isfinite(vals)
            if m.sum() < 6:
                continue
            vals, times = vals[m], times[m]
            pre = vals[times < t0]
            post = vals[times >= t0]
            if post.size < 3:
                continue
            want = need[f'{s}_{ax}']                                            # NARROWED
            base = float(np.median(pre)) if pre.size >= 2 else float(post[0])
            dev = post - base
            adev = np.abs(dev)
            peak_i = int(np.argmax(adev))
            peak = float(adev[peak_i])
            d = per_channel[f'{s}_{ax}']
            if 'peak' in want:                                                  # NARROWED
                d['peak'].append(peak)
            if 'ttp_ms' in want:                                                # NARROWED
                d['ttp_ms'].append(float(times[times >= t0][peak_i] - t0))
            if 'energy' in want:                                                # NARROWED
                d['energy'].append(float(np.sum(dev ** 2)))
            if 'rms' in want:                                                   # NARROWED
                d['rms'].append(V1.rms(dev))
            if 'settle_ms' in want:                                             # NARROWED
                d['settle_ms'].append(V1._settle_time(times[times >= t0] - t0, adev, peak))
            if 'recovery' in want:                                              # NARROWED
                tail = adev[max(1, int(0.7 * adev.size)):]
                d['recovery'].append(V1.safe_ratio(peak - V1.safe_mean(tail), peak)
                                     if peak > 1e-9 else 0.0)
            if 'post_var' in want:                                              # NARROWED
                d['post_var'].append(V1.safe_std(post))
            if 'pre_var' in want:                                               # NARROWED
                d['pre_var'].append(V1.safe_std(pre) if pre.size >= 2 else 0.0)

    for name, d in per_channel.items():
        for metric in need[name]:                                               # NARROWED
            f.update(V1._agg_block(d.get(metric, []), f'tap_{name}_{metric}'))  # called at call time:
    return f                                                                    # the 10-key, gated one
```

Columns this version leaves out:
- `tap_n_used`;
- the unread channels and metrics.

None of them is read. `_tap_need` returns `None` (use the original) if `tap_n_used` or any column it can't parse is selected.

**(d) The cache key includes `tap_need`**

Before:
```python
@functools.lru_cache(maxsize=16)
def extractor_for(skip):
    """One shared instance per frozenset of skipped families."""
    return SelectiveExtractorV2(skip=skip)
```

After:
```python
@functools.lru_cache(maxsize=16)
def extractor_for(skip, tap_need=None):
    """One shared instance per (skipped families, narrowed tap_locked need)."""
    return SelectiveExtractorV2(skip=skip, tap_need=tap_need)
```

### 5.3 `mobile_navigation_core/feature_extraction.py` (on top of Change 2)

**(a) Imports and install, after the Change-2 imports**

Before (Change 2 state):
```python
import extraction_plan as PLAN                  # noqa: E402  Change 2
import selected_extractor as SX                 # noqa: E402  Change 2
```

After:
```python
import extraction_plan as PLAN                  # noqa: E402  Change 2
import selected_extractor as SX                 # noqa: E402  Change 2
import narrowing as NARROW                      # noqa: E402  Change 3
```

After the `EXTRACT_MODE` block from Change 2 (§4.1b of that plan), add:

```python
if EXTRACT_MODE == 'narrow':
    # Once, after V2 is imported (it installs the 10-key _agg_block that gets wrapped).
    # The wrappers stay inert until extract_session sets NARROW.READ_KEYS.
    NARROW.install()
```

**(b) Step 5: the `else:` branch Change 2 added**

Before (Change 2 state):
```python
    else:
        extractor = SX.extractor_for(plan.skip)
        # templates only when a dtw_ / place_layout_ column is selected:
        # V1.extract skips DTW and zero-fills place_layout_* when it gets None
        row = extractor.extract(view, templates if plan.need_templates else None, None)
        diagnostics['extract_mode'] = 'needed'
        diagnostics['n_families'] = len(plan.families)
```

After:
```python
    else:
        narrow = EXTRACT_MODE == 'narrow'
        extractor = SX.extractor_for(plan.skip, plan.tap_need if narrow else None)
        # Change 3: in narrow mode the gated helpers and the narrowed tap_locked are
        # active for THIS extraction only (a context variable, so per request / greenlet)
        token = NARROW.READ_KEYS.set(plan.read_keys) if narrow else None
        try:
            # templates only when a dtw_ / place_layout_ column is selected:
            # V1.extract skips DTW and zero-fills place_layout_* when it gets None
            row = extractor.extract(view, templates if plan.need_templates else None, None)
        finally:
            if token is not None:
                NARROW.READ_KEYS.reset(token)
        diagnostics['extract_mode'] = EXTRACT_MODE
        diagnostics['n_families'] = len(plan.families)
```

The `if EXTRACT_SHADOW:` block from Change 2 follows unchanged. Because it runs **after** the `finally`, its full extraction runs with the gates inactive: a true reference.

### 5.4 `.env`

```dotenv
ML_EXTRACT_MODE=narrow
```

### 5.5 Not changed
`prediction_service.py` already passes `feature_columns` (Change 2). There is nothing new to pass.

## 6. What happens before and after

| | Change 2 only (`needed`) | Change 3 (`narrow`) |
|---|---|---|
| Families run | 15 | the same 15 |
| Helper calls per session that compute | all (~200) | ~30–60; the rest return zero-filled results |
| `tap_locked` window loop | 8 channels × 8 metrics | 5 channels × 5 metrics (v8) |
| Columns in the row | 4,260 | 4,260. Same keys, unread ones are zeros (`tap_locked`'s unread columns are absent) |
| Extraction median (one paired run, laptop) | 527 ms | **236 ms** |
| Feature-family time | 476 ms | **181 ms** |
| The 50 selected values | — | **identical** (43/43) |
| Score, `is_genuine`, `risk_score` | — | unchanged |
| Training, enrolment, research CLIs | — | unchanged; the gates are installed but inactive there |
| `full` / `needed` modes, shadow comparison | — | original helpers (no context set) |

**Cumulative with Changes 1 and 2:** about 3.1 s → about 0.45 s per extraction on the laptop, roughly 7× faster. The last two steps were measured in a different run, so the combined figure is approximate.

## 7. Tests: `tests/test_change3_narrow.py` (new)

Uses `tests/conftest.py` from Change 1 (`PERF_CHANGE_1_REMOVE_DEEPCOPY.md` §6.2).

```python
import json

from conftest import same


def _v8_columns():
    import enrollment_service as ES
    return tuple(ES.check_selection(ES.active_profile())[0])


def _extract(FE, monkeypatch, mode, user, raw, census, templates, cols):
    monkeypatch.setattr(FE, 'EXTRACT_MODE', mode)
    return FE.extract_session(json.loads(raw), user, templates, census=census,
                              feature_columns=cols)


def test_narrow_gives_identical_selected_values(corpus, monkeypatch):
    import feature_extraction as FE
    import narrowing as NARROW
    NARROW.install()
    cols = _v8_columns()
    for user, raw, census, templates in corpus:
        full, _ = _extract(FE, monkeypatch, 'full', user, raw, census, templates, cols)
        narrow, diag = _extract(FE, monkeypatch, 'narrow', user, raw, census, templates, cols)
        assert diag['extract_mode'] == 'narrow'
        bad = [c for c in cols if c not in narrow or not same(narrow[c], full[c])]
        assert not bad, (user, bad[:5])


def test_renamed_keys_are_kept():
    """Regression: interval_block(t, 'iv') -> 'touch_iv_median' must count as read."""
    import narrowing as NARROW
    read = NARROW.read_keys_for(('touch_iv_median',))
    assert 'iv_median' in read


def test_gates_inactive_outside_narrow_extraction(corpus):
    """With the gates installed but no context, every helper behaves as the original."""
    import new_feature_creation_session as V1
    import narrowing as NARROW
    NARROW.install()
    assert NARROW.READ_KEYS.get() is None
    vals = [0.1, 0.4, 0.2, 0.9, 0.3, 0.8]
    assert V1.stat_block(vals, 'x') == V1.stat_block.__wrapped__(vals, 'x')


def test_tap_locked_copy_matches_vendor():
    """Fails when vendor extract_tap_locked changes: review the narrowed copy."""
    import selected_extractor as SX
    assert SX._tap_source_unchanged()


def test_training_output_unchanged_with_gates_installed(corpus):
    """The training pipeline never sets the context: its rows must not change."""
    import new_feature_creation_session_v2 as V2
    import narrowing as NARROW
    import feature_extraction as FE
    user, raw, census, templates = corpus[0]
    before, _ = FE.extract_session(json.loads(raw), user, templates, census=census)
    NARROW.install()
    after, _ = FE.extract_session(json.loads(raw), user, templates, census=census)
    assert before.keys() == after.keys()
    assert all(same(before[k], after[k]) for k in before)
```

Two more checks to run by hand before switching production to `narrow`:
- **Greenlet isolation:** start two gevent greenlets in one process, one extracting in `narrow` mode and one in `full`, and confirm the `full` result equals a sequential full run.
- **Shadow in production:** `ML_EXTRACT_MODE=narrow` with `ML_EXTRACT_SHADOW=1` for a day or two, and confirm there are no `SHADOW:` lines in `app.log`.

## 8. Rollout

1. Changes 1 and 2 must be live, with `needed` mode stable.
2. Fill in `TAP_LOCKED_SOURCE_SHA256` (§5.2a) and merge.
   - Behaviour doesn't change until the mode changes.
   - The gates aren't installed unless the mode is `narrow`.
3. Tests in §7 must be green on the corpus.
4. One instance: `ML_EXTRACT_MODE=narrow`, `ML_EXTRACT_SHADOW=1`. Watch for `SHADOW:` warnings and `shadow_differ` in responses; both must be zero.
5. `ML_EXTRACT_SHADOW=0` everywhere. Watch `extract=...ms[narrow]` in `app.log`.

**Rollback:** `ML_EXTRACT_MODE=needed` (keeps Change 2) or `full`, then restart.

## 9. Risks and how they are covered

| Risk | Covered by |
|---|---|
| A skipped helper's zeros feed a selected column through a rename or a derived formula | suffix rule (§2.2); exact parity test over the corpus; shadow mode |
| A helper's key set depends on the data | the pipeline guarantees data-independent key sets; a violation shows up as a parity failure |
| Vendor changes `extract_tap_locked` | source-hash check switches the copy off automatically; `test_tap_locked_copy_matches_vendor` fails |
| Concurrent requests under gevent | the gates read a context variable (per greenlet); no per-request patching |
| Training or research affected | the gates are inert without the context; `test_training_output_unchanged_with_gates_installed` |
| Gate overhead | measured inside the 236 ms; a few ms per session |

## 10. Further work (not part of this change)

These families still cost 13–23 ms each because their time is in **inline loops, not helpers**:

| Family | Time |
|---|---|
| `tap_spectral` | 23 ms |
| `keystrokes` | 21 ms |
| `stage2` | 19 ms |
| `correlations` | 18 ms |
| `key_locked` | 14 ms |
| `touch` | 13 ms |

Narrowing each the way §3 narrows `tap_locked` is projected, not measured, to bring family time to about 80–110 ms. The hard floor is the cleaning, parsing and sanitising that every feature depends on, about 56–78 ms.

## 11. Checklist

- [ ] `mobile_navigation_core/narrowing.py` (§4)
- [ ] `extraction_plan.py`: `read_keys`, `tap_need`, `_tap_need` (§5.1)
- [ ] `selected_extractor.py`: imports, source hash, `tap_need`, narrowed method, cache key (§5.2)
- [ ] `feature_extraction.py`: import, `install()`, context around the extraction (§5.3)
- [ ] `.env`: `ML_EXTRACT_MODE=narrow` (§5.4)
- [ ] `tests/test_change3_narrow.py` green; greenlet check by hand (§7)
- [ ] Shadow, then live (§8)
