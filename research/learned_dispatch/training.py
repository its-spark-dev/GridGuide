"""Training-only fits, retained candidate artifacts and development export-parity checks."""
from pathlib import Path
import resource
import sys
import time

import numpy as np

from benchmarks.contracts import BenchmarkProblem
from research.adaptive_dispatch.environment import run_episode
from research.adaptive_dispatch.policies import heuristic
from research.ml_lab.access import isolated
from research.ml_lab.artifacts import (ROOT, digest, environment, file_hash, read_json,
    require_committed, revision, write_json)
from . import VERSION
from .dataset import episode_seed, load, source_hashes
from .features import feature_rows, schema
from .models import CANDIDATES, fit_export, load_model, parse_model
from .teacher import load_shards, training_matrix


def fit(dataset: Path, demonstrations: Path, output: Path):
    if output.exists() or (dataset/"evaluation-receipt.json").exists():
        raise ValueError("Training destination already used or final cohort spent")
    started = time.perf_counter()
    with isolated(dataset/"final_id.jsonl.gz", dataset/"final_shift.jsonl.gz"):
        manifest, _ = load(dataset, "train")
        full = manifest["profile"] == "full"
        if full:
            require_committed([dataset/"manifest.json", *[dataset/f"{p}.jsonl.gz" for p in ("train", "dev")],
                               ROOT/"docs/learned-dispatch/feature-schema.json"])
            if read_json(ROOT/"docs/learned-dispatch/feature-schema.json") != schema():
                raise ValueError("Feature schema not sealed before fitting")
        shards = load_shards(dataset, demonstrations)
        X, y, w, lineage = training_matrix(shards)
        binding = dict(input_identity=manifest["input_identity"], training_matrix_identity=digest([X.tolist(), y.tolist(), w.tolist(), lineage]),
            source_hashes=source_hashes(), teacher_shards={p.name: file_hash(p) for p in sorted(demonstrations.glob("*.jsonl.gz"))})
        # Inference-parity probe from development reactive states; never fitted or used to choose hyperparameters.
        _, dev = load(dataset, "dev")
        probes = []
        for row in dev:
            p = BenchmarkProblem.model_validate(row["problem"])
            def callback(state):
                probes.extend(feature_rows(state)[1])
                return heuristic(state, "downstream")
            run_episode(p, "high", episode_seed(manifest["profile"], "dev", 0), callback, "export-parity-probe")
        Z = np.asarray(probes)
        inventory, timings, scores = {}, {}, {}
        for name in CANDIDATES:
            payload, reference, seconds = fit_export(X, y, w, name, binding)
            repeated, _, repeat_seconds = fit_export(X, y, w, name, binding)
            first, second = parse_model(payload), parse_model(repeated)
            np.testing.assert_allclose(first.predict(X), second.predict(X), rtol=0, atol=1e-10)
            np.testing.assert_allclose(first.predict(Z), reference(Z), rtol=0, atol=1e-10)
            np.testing.assert_allclose(first.predict(Z), second.predict(Z), rtol=0, atol=1e-10)
            path = output/"models"/f"{name}.json"
            write_json(path, payload)
            _, load_ns = load_model(path, file_hash(path))
            inventory[name] = dict(file=f"models/{name}.json", sha256=file_hash(path), bytes=path.stat().st_size,
                                   exact_repeat_export=digest(payload) == digest(repeated))
            timings[name] = dict(fit_seconds=seconds, repeat_fit_seconds=repeat_seconds, load_nanoseconds=load_ns)
            scores[name] = dict(weighted_train_mse=float(np.average((first.predict(X)-y)**2, weights=w)),
                dev_parity_max_absolute_error=float(np.max(np.abs(first.predict(Z)-reference(Z)))))
        write_json(output/"training.json", dict(version=VERSION, revision=revision(), binding=binding, models=inventory,
            rows=len(y), features=X.shape[1], configurations=len(shards), unique_discretionary_states=len(set(lineage)),
            diagnostics={s["group_id"]: s["diagnostics"] for s in shards}, scores=scores,
            dev_export_probe_rows=len(Z), environment=environment()))
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1024**2 if sys.platform == "darwin" else 1024)
        write_json(output/"runtime.json", dict(candidates=timings, elapsed_seconds=time.perf_counter()-started,
                                               peak_rss_mib=peak))
        if peak > 2048 or time.perf_counter()-started > 1800:
            raise RuntimeError("Training resource cap exceeded")
        return read_json(output/"training.json")


def approved_models(training: Path, names=None):
    inventory = read_json(training/"training.json")
    if inventory["version"] != VERSION or inventory["binding"]["source_hashes"] != source_hashes():
        raise ValueError("Trained artifact source identity mismatch")
    result, timing = {}, {}
    for name in names or inventory["models"]:
        row = inventory["models"][name]
        path = (training/row["file"]).resolve()
        if not path.is_relative_to(training.resolve()):
            raise ValueError("Model inventory path escapes approved directory")
        model, elapsed = load_model(path, row["sha256"])
        if model.candidate != name:
            raise ValueError("Model candidate identity mismatch")
        result[name], timing[name] = model, elapsed
    return result, timing
