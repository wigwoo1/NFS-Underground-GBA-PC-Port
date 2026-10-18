"""Resolve relocated replay inputs without modifying historical manifests."""
from pathlib import Path
import hashlib
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_ROOT = 'C:/NFSUG-Workspace/2026-09-13/i-w/'

def load_session(path):
    session = json.loads(Path(path).read_text())
    for key, value in list(session.items()):
        if not isinstance(value, str):
            continue
        normalized = value.replace('\\', '/')
        if not normalized.lower().startswith(PREVIOUS_ROOT.lower()):
            continue
        relative = normalized[len(PREVIOUS_ROOT):]
        target = (PROJECT_ROOT / relative).resolve()
        if not target.is_relative_to(PROJECT_ROOT):
            raise FileNotFoundError(f'Relocated {key}: {target}')
        expected = session.get(key + '_sha256')
        if (expected or key in ('rom', 'state')) and not target.is_file():
            raise FileNotFoundError(f'Relocated {key}: {target}')
        if expected and hashlib.sha256(target.read_bytes()).hexdigest() != expected.lower():
            raise ValueError(f'Relocated {key} hash mismatch')
        session[key] = str(target)
    return session
