"""Genuinely fitted rankers with strict portable JSON inference (never pickle)."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import time

import numpy as np

from research.adaptive_dispatch.environment import Action
from research.adaptive_dispatch.policies import heuristic
from research.ml_lab.artifacts import digest, file_hash, write_json
from . import VERSION, FEATURE_VERSION, SEED
from .features import FEATURE_NAMES, feature_rows, schema
from .public import action_key, validate_state

CANDIDATES = {**{f"ridge-alpha{a:g}": dict(family="ridge", alpha=a) for a in (.1, 1., 10.)},
              **{f"forest-depth{d}": dict(family="forest", max_depth=d) for d in (4, 8)}}
MAX_BYTES = 16 * 1024 * 1024


def fit_export(X, y, weights, candidate, binding):
    """Only training matrices enter preprocessing and fitting."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits
    spec = CANDIDATES[candidate]
    begun = time.perf_counter()
    with threadpool_limits(limits=1):
        if spec["family"] == "ridge":
            scaler = StandardScaler().fit(X, sample_weight=weights)
            model = Ridge(alpha=spec["alpha"], solver="cholesky").fit(scaler.transform(X), y, sample_weight=weights)
            parameters = dict(mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(),
                              coefficients=model.coef_.tolist(), intercept=float(model.intercept_))
            reference = lambda Z: model.predict(scaler.transform(Z))
            importance = dict(zip(FEATURE_NAMES, model.coef_.tolist()))
        else:
            model = RandomForestRegressor(n_estimators=64, max_depth=spec["max_depth"], min_samples_leaf=5,
                max_features=1., bootstrap=True, random_state=SEED, n_jobs=1).fit(X, y, sample_weight=weights)
            parameters = dict(trees=[dict(left=t.tree_.children_left.tolist(), right=t.tree_.children_right.tolist(),
                feature=t.tree_.feature.tolist(), threshold=t.tree_.threshold.tolist(),
                value=t.tree_.value[:, 0, 0].tolist()) for t in model.estimators_])
            reference = model.predict
            importance = dict(zip(FEATURE_NAMES, model.feature_importances_.tolist()))
        fit_seconds = time.perf_counter()-begun
    payload = dict(version=VERSION, format="portable-action-regressor-v1", candidate=candidate,
        feature_version=FEATURE_VERSION, feature_names=list(FEATURE_NAMES), schema_sha256=digest(schema()),
        specification=spec, binding=binding, parameters=parameters, importance=importance,
        objective="dimensionless excess median-teacher rollout cost; minimize")
    portable = parse_model(payload)
    np.testing.assert_allclose(portable.predict(X), reference(X), rtol=0, atol=1e-10)
    return payload, reference, fit_seconds


def _vector(value, size=None, integer=False):
    if type(value) is not list or not value or (size is not None and len(value) != size):
        raise ValueError("Invalid parameter dimensions")
    if any(type(v) not in ((int,) if integer else (int, float)) or not math.isfinite(v) for v in value):
        raise ValueError("Nonfinite/non-numeric parameter")
    result = np.asarray(value, dtype=np.int64 if integer else np.float64)
    result.setflags(write=False)
    return result


def parse_model(payload):
    fields = {"version", "format", "candidate", "feature_version", "feature_names", "schema_sha256",
              "specification", "binding", "parameters", "importance", "objective"}
    if (type(payload) is not dict or set(payload) != fields or payload["version"] != VERSION
            or payload["format"] != "portable-action-regressor-v1" or payload["feature_version"] != FEATURE_VERSION
            or payload["feature_names"] != list(FEATURE_NAMES) or payload["schema_sha256"] != digest(schema())
            or payload["candidate"] not in CANDIDATES or payload["specification"] != CANDIDATES[payload["candidate"]]):
        raise ValueError("Model identity/schema mismatch")
    if (type(payload["binding"]) is not dict or set(payload["importance"]) != set(FEATURE_NAMES)
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in payload["importance"].values())):
        raise ValueError("Invalid model metadata")
    p = payload["parameters"]
    if type(p) is not dict:
        raise ValueError("Invalid parameter object")
    family = payload["specification"]["family"]
    if family == "ridge":
        if set(p) != {"mean", "scale", "coefficients", "intercept"}:
            raise ValueError("Invalid linear parameters")
        mean, scale, coefficients = (_vector(p[k], len(FEATURE_NAMES)) for k in ("mean", "scale", "coefficients"))
        intercept = p["intercept"]
        if np.any(scale <= 0) or type(intercept) not in (int, float) or not math.isfinite(intercept):
            raise ValueError("Invalid linear scale/intercept")
        parameters = (mean, scale, coefficients, intercept)
    else:
        if set(p) != {"trees"} or type(p["trees"]) is not list or len(p["trees"]) != 64:
            raise ValueError("Invalid forest dimensions")
        trees = []
        for tree in p["trees"]:
            if type(tree) is not dict or set(tree) != {"left", "right", "feature", "threshold", "value"}:
                raise ValueError("Invalid tree fields")
            left = _vector(tree["left"], integer=True)
            n = len(left)
            if n > 2**(payload["specification"]["max_depth"]+1)-1:
                raise ValueError("Oversized tree")
            right, feature = (_vector(tree[k], n, integer=True) for k in ("right", "feature"))
            threshold, value = (_vector(tree[k], n) for k in ("threshold", "value"))
            visited, stack = set(), [(0, 0)]
            while stack:
                i, depth = stack.pop()
                if i in visited or not 0 <= i < n or depth > payload["specification"]["max_depth"]:
                    raise ValueError("Cyclic/shared/invalid tree node")
                visited.add(i)
                if left[i] == -1:
                    if right[i] != -1 or feature[i] != -2:
                        raise ValueError("Invalid tree leaf")
                else:
                    if not 0 <= feature[i] < len(FEATURE_NAMES):
                        raise ValueError("Invalid tree feature")
                    stack.extend(((int(left[i]), depth+1), (int(right[i]), depth+1)))
            if len(visited) != n:
                raise ValueError("Unreachable tree nodes")
            trees.append((left, right, feature, threshold, value))
        parameters = tuple(trees)
    return PortableModel(payload["candidate"], family, parameters)


@dataclass(frozen=True)
class PortableModel:
    candidate: str
    family: str
    parameters: tuple

    def predict(self, X):
        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 2 or X.shape[1] != len(FEATURE_NAMES) or not np.isfinite(X).all():
            raise ValueError("Invalid model input")
        if self.family == "ridge":
            mean, scale, coefficients, intercept = self.parameters
            result = ((X-mean)/scale) @ coefficients + intercept
        else:
            X = X.astype(np.float32)  # sklearn tree comparisons use DTYPE=float32
            if not np.isfinite(X).all():
                raise ValueError("Float32 feature overflow")
            result = np.zeros(len(X))
            for left, right, feature, threshold, value in self.parameters:
                nodes = np.zeros(len(X), dtype=np.int64)
                for _ in range(9):
                    rows = np.flatnonzero(left[nodes] != -1)
                    if not len(rows):
                        break
                    current = nodes[rows]
                    nodes[rows] = np.where(X[rows, feature[current]] <= threshold[current], left[current], right[current])
                if np.any(left[nodes] != -1):
                    raise ValueError("Incomplete tree traversal")
                result += value[nodes]
            result /= len(self.parameters)
        if not np.isfinite(result).all():
            raise ValueError("Nonfinite model scores")
        return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def load_model(path: Path, expected_sha256: str):
    begun = time.perf_counter_ns()
    if type(expected_sha256) is not str or len(expected_sha256) != 64 or path.stat().st_size > MAX_BYTES:
        raise ValueError("Invalid artifact approval or size")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Model SHA-256 mismatch")
    try:
        payload = json.loads(raw, object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
        model = parse_model(payload)
    except (TypeError, KeyError, IndexError, OverflowError, RecursionError) as error:
        raise ValueError("Malformed model") from error
    return model, time.perf_counter_ns()-begun


class LearnedPolicy:
    def __init__(self, model: PortableModel | None, allow_no_model=False):
        if model is None and not allow_no_model:
            raise ValueError("A loaded learned model is required")
        self.model = model
        self.fallbacks = []
        self.calls = 0

    def __call__(self, state):
        view = validate_state(state)  # malformed observations never reach fallback
        if not view.actions:
            raise ValueError("No legal decision")
        self.calls += 1
        reason = None
        if not view.supported:
            reason = "unsupported-public-scope"
        elif self.model is None:
            reason = "explicit-no-model"
        else:
            try:
                actions, X = feature_rows(state, validated=view)
                predicted = self.model.predict(X)
                if predicted.shape != (len(actions),) or not np.isfinite(predicted).all():
                    raise ValueError("Invalid prediction")
                chosen = min(range(len(actions)), key=lambda i: (predicted[i], action_key(actions[i])))
                return actions[chosen]
            except (ValueError, ArithmeticError, RuntimeError):
                reason = "inference-failure"
        action = heuristic(state, "downstream")
        if action not in view.actions:
            raise ValueError("Fallback did not produce a certified legal action")
        self.fallbacks.append(dict(call=self.calls, reason=reason))
        return action

    def score(self, state, candidate: Action) -> float:
        if self.model is None:
            raise ValueError("Non-learning fallback has no learned score")
        actions, X = feature_rows(state)
        if type(candidate) is not Action or candidate not in actions:
            raise ValueError("Invalid candidate action")
        # Interface is priority: higher is better; regression predicts cost (lower is better).
        return -float(self.model.predict(X)[actions.index(candidate)])
