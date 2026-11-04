"""Bounded supervised model catalog and validated pre-decision inference."""
from __future__ import annotations
import io
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from benchmarks.policies import POLICIES
from .artifacts import SEED
from .features import FEATURE_NAMES, extract_features, inference_supported


def catalog() -> dict[str, Pipeline]:
    result = {}
    for c in (.1, 1., 10.):
        result[f'logistic-c{c:g}'] = Pipeline([
            ('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
            ('scale', StandardScaler()),
            ('model', LogisticRegression(C=c, solver='lbfgs', max_iter=3000, random_state=SEED))])
    for depth in (4,8,None):
        result[f'forest-depth{depth or "all"}'] = Pipeline([
            ('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
            ('model', RandomForestClassifier(n_estimators=160, max_depth=depth, min_samples_leaf=3,
                                             random_state=SEED, n_jobs=1))])
    for rate in (.03,.1):
        result[f'boosting-rate{rate:g}'] = Pipeline([
            ('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
            ('model', GradientBoostingClassifier(n_estimators=100, learning_rate=rate,
                                                 max_depth=2, random_state=SEED))])
    return result


def matrix(rows: list[dict]) -> np.ndarray:
    for row in rows:
        if set(row['features']) != set(FEATURE_NAMES):
            raise ValueError('Unexpected feature schema; extra outcome/metadata fields forbidden')
    result = np.array([[r['features'][name] for name in FEATURE_NAMES] for r in rows],dtype=float)
    if result.ndim != 2 or not np.isfinite(result).all():
        raise ValueError('Nonfinite or empty feature matrix')
    return result


def predict(model: Pipeline, problem) -> str | None:
    if not inference_supported(problem):
        return None
    values = extract_features(problem)
    result = str(model.predict(matrix([{'features':values}]))[0])
    if result not in POLICIES:
        raise ValueError('Model predicted invalid policy')
    return result


def model_bytes(model: Pipeline) -> bytes:
    stream = io.BytesIO()
    joblib.dump(model,stream,compress=3)
    return stream.getvalue()


def importance(model: Pipeline) -> dict:
    estimator = model.named_steps['model']
    if hasattr(estimator,'coef_'):
        return {'method':'standardized_logistic_coefficients', 'classes':estimator.classes_.tolist(),
                'coefficients':estimator.coef_.tolist(), 'intercepts':estimator.intercept_.tolist(),
                'magnitude_by_feature':dict(zip(FEATURE_NAMES,np.mean(np.abs(estimator.coef_),axis=0).tolist()))}
    return {'method':'training_impurity_importance_not_causal',
            'magnitude_by_feature':dict(zip(FEATURE_NAMES,estimator.feature_importances_.tolist()))}
