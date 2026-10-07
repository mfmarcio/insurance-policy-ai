from __future__ import annotations

import hashlib
from pathlib import Path


class IntakeAgent:
    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

    def validate_and_register(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Formato não suportado: {suffix}")
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError("Arquivo vazio ou inexistente.")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        return f"doc-{digest}"
