import hashlib
from typing import Tuple


def compute_file_hash(file_path: str) -> str:
    """Calculates SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_text_hash(text: str) -> str:
    """Calculates SHA-256 hash of normalized text."""
    normalized = " ".join(text.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
