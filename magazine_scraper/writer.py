from pathlib import Path


def write_epub(data: bytes, output_path: Path) -> Path:
    """Write EPUB bytes to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return output_path
