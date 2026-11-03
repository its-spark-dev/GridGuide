"""Mode-selected entrypoint; the public artifact defaults to fictional data only."""
import os


def create_runtime_app(mode: str | None = None):
    selected = os.environ.get("GRIDGUIDE_MODE", "synthetic-demo") if mode is None else mode
    if selected == "synthetic-demo":
        from .synthetic_api import create_synthetic_app
        return create_synthetic_app()
    if selected == "challenge-local":
        # This branch is deliberately absent from the synthetic artifact's modules.
        from .api import create_app
        return create_app()
    raise ValueError("GRIDGUIDE_MODE must be synthetic-demo or challenge-local")


app = create_runtime_app()
