# Source, provenance and dependency licensing

ML Lab contains independently authored fictional configurations and generated cases.
It does not import AEP/GIS/customer records, historical G2 examples, NOAA observations,
EAGLE-I data or real utility outcomes. The original project MIT grant applies to its
contributor-owned code, documentation and authored synthetic evidence. It grants no
new rights to AEP or other external materials. Original contributors and notices remain
unchanged.

`requirements-ml.txt` records direct dependencies; `requirements-ml.lock` pins every
installed transitive dependency with release hashes for compatible platform wheels.
The lock is isolated from `deploy/requirements.lock` and from frozen release assets.
Python 3.12.14, scikit-learn 1.7.2, NumPy 2.3.5 and SciPy 1.15.3 define the recorded
training/replay environment. Matplotlib 3.10.7 renders the research figures.

Installed distribution metadata identifies the following license families. Full wheel
license texts and bundled-library notices remain in each installed `.dist-info`
directory; this summary does not replace those texts or extend the project MIT grant
to third-party software. No dependency wheel or native library is redistributed in
ML Lab evidence.

| Distribution | Pinned version | License metadata / family |
|---|---|---|
| annotated-types | 0.8.0 | MIT |
| cloudpickle | 3.1.2 | BSD-3-Clause |
| contourpy | 1.4.0 | BSD-3-Clause |
| cycler | 0.12.1 | BSD license classifier; see installed license |
| fonttools | 4.68.0 | MIT |
| joblib | 1.6.0 | BSD-3-Clause |
| kiwisolver | 1.5.1 | BSD license classifier; see installed license |
| matplotlib | 3.10.7 | Matplotlib license agreement / PSF license classifier |
| numpy | 2.3.5 | BSD license classifier; bundled components retain separate notices |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pillow | 13.0.0 | MIT-CMU |
| pydantic | 2.12.3 | MIT |
| pydantic_core | 2.41.4 | MIT |
| pyparsing | 3.3.3 | MIT |
| python-dateutil | 4.0.0 | BSD-3-Clause |
| scikit-learn | 1.7.2 | BSD-3-Clause |
| scipy | 1.15.3 | BSD license classifier; bundled components retain separate notices |
| threadpoolctl | 3.7.0 | BSD-3-Clause |
| typing-inspection | 0.4.4 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.6 | Apache-2.0 metadata; see included data notices |

Technical references: [scikit-learn pipelines and persistence](https://scikit-learn.org/1.7/model_persistence.html),
[logistic regression](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.LogisticRegression.html),
[grouped cross-validation](https://scikit-learn.org/1.7/modules/generated/sklearn.model_selection.GroupKFold.html).
Joblib files can execute code when loaded. Only the locally trusted, hash-bound artifacts
in this repository are used; checksums do not authenticate unknown third-party models.
