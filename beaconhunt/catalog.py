"""Load and index the artifact catalog from YAML on disk."""

from __future__ import annotations

from pathlib import Path

from .schema import Artifact, SchemaError, load_artifact_file

# Repo-root/catalog by default.
DEFAULT_CATALOG_DIR = Path(__file__).resolve().parent.parent / "catalog"


class Catalog:
    def __init__(self, artifacts: list[Artifact]):
        by_id: dict[str, Artifact] = {}
        for art in artifacts:
            if art.id in by_id:
                raise SchemaError(f"duplicate artifact id: {art.id!r}")
            by_id[art.id] = art
        self._by_id = by_id

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self):
        return iter(self._by_id.values())

    def get(self, artifact_id: str) -> Artifact:
        return self._by_id[artifact_id]

    def all(self) -> list[Artifact]:
        return list(self._by_id.values())

    def filter(
        self,
        service: str | None = None,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[Artifact]:
        out = []
        for art in self._by_id.values():
            if service and art.service != service:
                continue
            if category and art.category != category:
                continue
            if difficulty and art.difficulty != difficulty:
                continue
            out.append(art)
        return out

    @property
    def services(self) -> set[str]:
        return {a.service for a in self._by_id.values()}


def load_catalog(catalog_dir: Path | None = None) -> Catalog:
    catalog_dir = Path(catalog_dir) if catalog_dir else DEFAULT_CATALOG_DIR
    if not catalog_dir.is_dir():
        raise FileNotFoundError(f"catalog dir not found: {catalog_dir}")
    artifacts: list[Artifact] = []
    for path in sorted(catalog_dir.rglob("*.yaml")):
        artifacts.append(load_artifact_file(path))
    for path in sorted(catalog_dir.rglob("*.yml")):
        artifacts.append(load_artifact_file(path))
    return Catalog(artifacts)
