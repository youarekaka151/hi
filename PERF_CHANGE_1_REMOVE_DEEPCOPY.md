# Change 1 — Stop deep-copying the session on the predict path

| | |
|---|---|
| **What** | `feature_extraction.extract_session` deep-copies the whole incoming session before processing it. The predict path will skip that copy. |
| **Why** | The copy protects a caller that reuses the session object after extraction. The predict path never does, so the copy is pure cost. |
| **Measured gain** | `copy.deepcopy` alone takes a median of **140 ms** per session (mean 161 ms, max 496 ms). Whole extraction is **0.17 s faster** (median, −5.9%), 3.14 s → 3.00 s. 43 real sessions, laptop. |
| **Effect on results** | None. All **5,483** extracted columns were identical with and without the copy, on **43/43** sessions. |
| **Files changed** | `mobile_navigation_core/feature_extraction.py`, `mobile_navigation_core/prediction_service.py`, `.env` |
| **Files added** | `tests/conftest.py`, `tests/test_change1_no_deepcopy.py` |
| **Not touched** | Everything in `mobile_navigation_core/vendor/`, training (`enrollment_service.py`), bundles, the backend, the SDK |
| **Rollback** | Set `ML_EXTRACT_COPY=1` in `.env` and restart. No redeploy. |
| **Effort** | About 2 hours including tests |

---

## 1. Where the copy is today

`mobile_navigation_core/feature_extraction.py`, inside `extract_session` (lines 171–276):

```python
171  def extract_session(raw_session, user_id, templates,
172                      census=None, needs_census=False):
...
179      IT IS DEEP-COPIED FIRST, and a shallow copy is not enough. Both
180      behavior_cleaner.clean_session and new_sensor_sanitizer.sanitize_view repair
181      IN PLACE, reaching into the nested key_events / touch_events lists and the
182      per-sensor sample arrays. A `dict(raw_session)` shares all of those, so the
183      caller's payload comes back mutated and a second extraction of the same
184      object silently runs on already-repaired data. The first parity test hit
185      exactly that and produced a double-sanitised second reading. 167 ms on a 3.5 MB session, against 9-17 s of extraction.
...
210      raw = copy.deepcopy(raw_session)             # see the docstring
211      normalize_upload_shape(raw)
```

Line 210 copies everything in the session: about 8,000 sensor-sample dicts, every touch with its path points, every key event and all metadata. Every later step then works on `raw`:

| Line | Step | Mutates `raw`? |
|---|---|---|
| 211 | `normalize_upload_shape(raw)` | **yes**: regroups `sensor_samples`, fills `down_size` / `point_size` / `seq`, sorts touches |
| 227 | `BC.clean_session(raw, census)` | **yes**: repairs key and touch events, adds `raw['_clean']` |
| 232 | `SCH.SessionView(raw, ...)` | reads |
| 239 | `SAN.sanitize_view(view)` | repairs the per-sensor arrays it reads from `raw` |
| 246 | `_EXTRACTOR.extract(view, ...)` | reads |

The copy exists so the **caller's** object comes back unchanged. The docstring names why: an earlier parity test ran extraction twice on the same object and got a double-repaired second result.

## 2. Why the copy is not needed on the predict path

Here is the full life of the session object for one predict request, traced in the current code:

| Step | File:line | What happens to the object |
|---|---|---|
| 1 | `mobile_navigation_model_predict/mobile_navigation_predict.py:52` | `payload = _extract_payload()` builds a **brand-new** dict from this request's bytes (`json.loads` at :33, or `request.get_json` at :38). Nothing else holds it. |
| 2 | same file :54 | `prediction_service.predict(payload)` |
| 3 | `prediction_service.py:185` | `session, user_id = self._unwrap(payload)` returns the same object, or `payload['sessions'][0]`, which is part of the same fresh object |
| 4 | `prediction_service.py:193` | `session_id = session.get('session_id')`. The only field needed later, read **before** extraction |
| 5 | `prediction_service.py:207` | `extract_session(session, ...)`. **The only use of the object** |
| 6 | `prediction_service.py:220–274` | the response is built from `row`, `diagnostics`, `bundle`, `user_id` and `session_id`. **`session` is never read again** |
| 7 | `mobile_navigation_predict.py:62` | `jsonify(result)`; the request ends and the object is garbage |

This confirms:
- `extract_session` has exactly **one** caller in the service: `prediction_service.py:207`. Training uses `SessionPipelineV2`, which never calls `extract_session`.
- The object is never shared between requests and never read after extraction, so the double-repair problem cannot happen here.

So the copy protects nothing on this path. It only costs time and a second full set of objects in memory.

## 3. The design: make the copy optional, keep it on by default

The copy is **not deleted**. Two changes:

1. `extract_session` gets a new keyword argument `copy_input=True`.
   - The default keeps today's behaviour for any other caller, such as a test, a notebook, or a future batch job that might reuse its object.
2. Only `PredictionService.predict` passes `copy_input=False`, controlled by the environment variable `ML_EXTRACT_COPY`:
   - `0` (default) skips the copy;
   - `1` restores it.

This keeps the documented protection for everyone who might need it and removes the cost from the one path that doesn't.

## 4. Code changes, line by line

### 4.1 `mobile_navigation_core/feature_extraction.py`

**(a) Signature, lines 171–172**

Before:
```python
def extract_session(raw_session, user_id, templates,
                    census=None, needs_census=False):
```

After:
```python
def extract_session(raw_session, user_id, templates,
                    census=None, needs_census=False, copy_input=True):
```

**(b) Docstring, lines 179–185:** replace the paragraph so it tells the truth about the new argument.

Before:
```python
    IT IS DEEP-COPIED FIRST, and a shallow copy is not enough. Both
    behavior_cleaner.clean_session and new_sensor_sanitizer.sanitize_view repair
    IN PLACE, reaching into the nested key_events / touch_events lists and the
    per-sensor sample arrays. A `dict(raw_session)` shares all of those, so the
    caller's payload comes back mutated and a second extraction of the same
    object silently runs on already-repaired data. The first parity test hit
    exactly that and produced a double-sanitised second reading. 167 ms on a 3.5 MB session, against 9-17 s of extraction.
```

After:
```python
    BY DEFAULT IT IS DEEP-COPIED FIRST, and a shallow copy is not enough. Both
    behavior_cleaner.clean_session and new_sensor_sanitizer.sanitize_view repair
    IN PLACE, reaching into the nested key_events / touch_events lists and the
    per-sensor sample arrays. A `dict(raw_session)` shares all of those, so the
    caller's payload comes back mutated and a second extraction of the same
    object silently runs on already-repaired data. The first parity test hit
    exactly that and produced a double-sanitised second reading.

    copy_input=False skips the copy (measured: 140 ms median per session) and
    lets the steps below repair `raw_session` itself. Pass it ONLY when the
    caller owns the object and never reads it again - PredictionService.predict
    does exactly that: its session is the request's own freshly parsed body.
    After a copy_input=False call the object is in the repaired, regrouped
    state (sensor_samples keyed by sensor, touches sorted, `_clean` added) and
    must not be extracted a second time.
```

**(c) The copy itself, line 210**

Before:
```python
    raw = copy.deepcopy(raw_session)             # see the docstring
```

After:
```python
    # see the docstring: the copy protects a caller that reuses its object
    raw = copy.deepcopy(raw_session) if copy_input else raw_session
```

`import copy` (line 60) stays, because the default path still uses it.

**(d) Diagnostics, lines 213–217:** record which path ran, so it's visible in logs and in the response.

Before:
```python
    diagnostics = {
        'used_census': False,
        'needs_census': bool(needs_census),
        'census_available': census is not None,
    }
```

After:
```python
    diagnostics = {
        'used_census': False,
        'needs_census': bool(needs_census),
        'census_available': census is not None,
        'copied_input': bool(copy_input),
    }
```

No other line in this file changes.

### 4.2 `mobile_navigation_core/prediction_service.py`

**(a) Read the switch once, at import.** Insert after line 55 (`logger = logging.getLogger(__name__)`). `os` is already imported at line 39.

Before (lines 55–58):
```python
logger = logging.getLogger(__name__)


class PredictionService:
```

After:
```python
logger = logging.getLogger(__name__)

# Change 1. 0 (default): predict hands extract_session its own request object
# and skips the defensive deepcopy (140 ms median per session). 1: copy as before.
COPY_INPUT = (os.getenv('ML_EXTRACT_COPY') or '0').strip() == '1'


class PredictionService:
```

**(b) The extraction call, lines 205–209**

Before:
```python
        # ---- features -----------------------------------------------------
        try:
            row, diagnostics = extract_session(
                session, user_id, templates,
                census=bundle.census, needs_census=bundle.needs_census)
```

After:
```python
        # ---- features -----------------------------------------------------
        # `session` is this request's own freshly parsed body (see
        # mobile_navigation_predict._extract_payload) and nothing below reads it
        # again - session_id was taken at the top of this method - so the
        # deepcopy inside extract_session protects nothing here (Change 1).
        try:
            row, diagnostics = extract_session(
                session, user_id, templates,
                census=bundle.census, needs_census=bundle.needs_census,
                copy_input=COPY_INPUT)
```

**(c) Response, line 271:** add one field after `'extract_ms'`.

Before:
```python
            'extract_ms': diagnostics.get('extract_ms'),
            'score_ms': score_ms,
```

After:
```python
            'extract_ms': diagnostics.get('extract_ms'),
            'copied_input': diagnostics.get('copied_input'),
            'score_ms': score_ms,
```

The backend's `call_predict_api` only requires `is_genuine` and `risk_score`. It stores the whole response in `NAV_SESSION_SCORES.DETAILS_JSON`, so a new scalar field is harmless.

**(d) Startup log:** one line so operators can see the mode. In `__init__`, after the existing `logger.info('extractor %s (align_hz=%s) ...` call at lines 86–88, add:

```python
        logger.info('predict extraction copies its input: %s (ML_EXTRACT_COPY)',
                    COPY_INPUT)
```

### 4.3 `.env`

Add next to the other `ML_` settings:

```dotenv
# Change 1: 0 = predict skips the defensive deepcopy of the session (faster), 1 = copy as before
ML_EXTRACT_COPY=0
```

`docker-compose.yml` already loads `.env` through `env_file`, so nothing else is needed.

## 5. What happens before and after

| | Before | After (`ML_EXTRACT_COPY=0`) |
|---|---|---|
| Objects created per request | the parsed body **plus a full second copy** | the parsed body only |
| Time in `copy.deepcopy` | 140 ms median, up to ~0.5 s on large sessions | 0 |
| Whole extraction (laptop, 43 sessions) | 3.14 s median | 3.00 s median (−0.17 s, −5.9%; garbage collection also has less to do) |
| Extracted features | 5,483 columns | the same 5,483 columns, **identical values** (43/43) |
| Score, threshold, `is_genuine`, `risk_score` | — | unchanged, since the features are identical |
| State of the request object after extraction | untouched | repaired and regrouped. Harmless, because nothing reads it |
| Other callers of `extract_session` | copy | still copy (default `copy_input=True`) |
| Response | — | one extra field `copied_input: false` |

## 6. Tests

There is no `tests/` folder in the repo yet, so these files are new. They need real sessions, so they read a small corpus from a folder given by the environment variable `ADAPID_PARITY_CORPUS` and **skip** when it isn't set.

### 6.1 Building the parity corpus

The corpus layout is one folder per user:

```
<corpus>/<user>/sessions.json                     # a staging envelope (EnvelopeWriter format)
<corpus>/<user>/templates/<user>_dtw_templates.pkl
```

The 43-session corpus used for every measurement in this document was built this way:
- the backend's own `payload_from_request_session` turned each captured upload into the exact body predict receives;
- `new_build_dtw_templates.build_for_user` built the templates.

The two scripts that do it, `prepare_sessions.py` and `time_extraction.py`, are in the scratchpad folder `extract_timing`. Copy them into `tools/` if the team wants to rebuild the corpus.

### 6.2 `tests/conftest.py` (new, shared by changes 1–3)

```python
"""Shared fixtures for the extraction-mode tests. Skipped unless
ADAPID_PARITY_CORPUS points at <dir>/<user>/sessions.json (+ templates/)."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, 'mobile_navigation_core')
for p in (CORE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

CORPUS = os.getenv('ADAPID_PARITY_CORPUS')


def _load_corpus():
    import behavior_cleaner as BC
    import feature_extraction as FE
    out = []
    for user in sorted(os.listdir(CORPUS)):
        env = os.path.join(CORPUS, user, 'sessions.json')
        if not os.path.isfile(env):
            continue
        census = BC.build_census(BC.iter_raw_sessions(env), user)
        templates = FE.load_templates(
            os.path.join(CORPUS, user, 'templates', f'{user}_dtw_templates.pkl'))
        with open(env, encoding='utf-8') as fh:
            for s in json.load(fh)['data']['sessions']:
                out.append((user, json.dumps(s).encode('utf-8'), census, templates))
    return out


@pytest.fixture(scope='session')
def corpus():
    if not CORPUS:
        pytest.skip('ADAPID_PARITY_CORPUS not set')
    return _load_corpus()


def same(a, b):
    """Exact equality, with NaN == NaN."""
    if isinstance(a, float) and isinstance(b, float) and a != a and b != b:
        return True
    return a == b
```

### 6.3 `tests/test_change1_no_deepcopy.py` (new)

```python
import json

from conftest import same


def test_features_identical_without_copy(corpus):
    """copy_input=False must not change a single extracted value."""
    import feature_extraction as FE
    for user, raw, census, templates in corpus:
        row_copy, _ = FE.extract_session(json.loads(raw), user, templates,
                                         census=census, copy_input=True)
        row_nocopy, diag = FE.extract_session(json.loads(raw), user, templates,
                                              census=census, copy_input=False)
        assert diag['copied_input'] is False
        assert row_copy.keys() == row_nocopy.keys()
        bad = [k for k in row_copy if not same(row_copy[k], row_nocopy[k])]
        assert not bad, bad[:5]


def test_default_still_protects_the_caller(corpus):
    """Default behaviour is unchanged: the caller's object comes back untouched."""
    import feature_extraction as FE
    user, raw, census, templates = corpus[0]
    session = json.loads(raw)
    before = json.dumps(session, sort_keys=True)
    FE.extract_session(session, user, templates, census=census)
    assert json.dumps(session, sort_keys=True) == before


def test_no_copy_does_mutate(corpus):
    """Documents the contract: with copy_input=False the object is repaired in place."""
    import feature_extraction as FE
    user, raw, census, templates = corpus[0]
    session = json.loads(raw)
    FE.extract_session(session, user, templates, census=census, copy_input=False)
    assert '_clean' in session


def test_predict_never_reads_session_after_extraction():
    """Guard against a future edit that reuses `session` after extract_session."""
    import inspect
    import prediction_service as PS
    src = inspect.getsource(PS.PredictionService.predict)
    after = src.split('extract_session(', 1)[1].split(')', 1)[1]
    assert 'session[' not in after and 'session.get(' not in after, \
        'predict() reads `session` after extraction; copy_input=False is no longer safe'
```

Run:

```bash
ADAPID_PARITY_CORPUS=/path/to/corpus python -m pytest tests/test_change1_no_deepcopy.py -q
```

## 7. Rollout

1. Merge the code with `ML_EXTRACT_COPY=1` in `.env`. This is exactly today's behaviour; the only visible difference is the new `copied_input: true` field.
2. Run the tests in §6 against the corpus. All must pass.
3. Set `ML_EXTRACT_COPY=0` and restart the service.
4. Watch `extract_ms` in the response and in `app.log` (`extract=...ms`). The median should drop by roughly the copy time; on the server that is about 100–170 ms, since it was 167 ms on a 3.5 MB session per the original docstring.

**Rollback:** `ML_EXTRACT_COPY=1`, then restart.

## 8. Risks and how they are covered

| Risk | Covered by |
|---|---|
| A future edit makes `predict()` read `session` after extraction | `test_predict_never_reads_session_after_extraction` fails; the docstring states the rule |
| A new caller of `extract_session` reuses its object | default `copy_input=True` keeps that caller safe |
| Features change | `test_features_identical_without_copy` checks all 5,483 columns exactly |

## 9. Checklist

- [ ] `feature_extraction.py`: signature, docstring, line 210, diagnostics (§4.1)
- [ ] `prediction_service.py`: `COPY_INPUT`, call, response field, boot log (§4.2)
- [ ] `.env`: `ML_EXTRACT_COPY` (§4.3)
- [ ] `tests/conftest.py`, `tests/test_change1_no_deepcopy.py` (§6)
- [ ] Tests green on the corpus
- [ ] Deploy with `=1`, then switch to `=0`, then watch `extract_ms`
