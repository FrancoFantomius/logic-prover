"""Diversity filter and Bloom-style formula deduplication filter."""

from __future__ import annotations
import json
import hashlib
import os
from typing import Set, Optional, Dict, Any
from logic.core.ast import Formula, canonicalize_bound_variables
from logic.core.exceptions import SolverError, DatabaseError


class FormulaFilter:
    """
    Maintains a set of canonical formula hashes representing already explored,
    proven, or discarded formulas to prevent duplicate generation.
    Supports state persistence to disk (JSON formatted hash store).
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """Initializes the formula deduplication filter and optionally loads state from storage."""
        self.seen_hashes: Set[str] = set()
        self.storage_path: Optional[str] = storage_path
        if self.storage_path and os.path.exists(self.storage_path):
            self.load_state(self.storage_path)

    def _compute_hash(self, formula: Formula) -> str:
        """
        Computes deterministic SHA-256 hash of canonicalized formula.
        Uses canonicalize_bound_variables to ensure alpha-equivalent formulas
        yield identical hashes.
        """
        canonical = canonicalize_bound_variables(formula)
        canonical_repr = repr(canonical)
        return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()

    def add(self, formula: Formula) -> None:
        """Adds formula's canonical hash to the seen filter set."""
        h = self._compute_hash(formula)
        self.seen_hashes.add(h)

    def is_seen(self, formula: Formula) -> bool:
        """Returns True if formula (or an alpha-equivalent variant) has been seen."""
        h = self._compute_hash(formula)
        return h in self.seen_hashes

    def save_state(self, filepath: Optional[str] = None) -> None:
        """
        Persists seen hashes and metadata to disk in JSON format.
        """
        target_path = filepath or self.storage_path
        if not target_path:
            raise SolverError("Cannot save filter state: no storage_path provided.")

        dir_name = os.path.dirname(target_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        data: Dict[str, Any] = {
            "version": "1.0",
            "count": len(self.seen_hashes),
            "hashes": sorted(list(self.seen_hashes))
        }

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise DatabaseError(f"Failed to save filter state to '{target_path}': {e}") from e

    def load_state(self, filepath: str) -> None:
        """
        Loads seen hashes from a persisted JSON state file.
        """
        if not os.path.exists(filepath):
            raise DatabaseError(f"Filter state file not found: '{filepath}'")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            hashes = data.get("hashes", [])
            self.seen_hashes.update(hashes)
            self.storage_path = filepath
        except (json.JSONDecodeError, OSError) as e:
            raise DatabaseError(f"Failed to load filter state from '{filepath}': {e}") from e

    def clear(self) -> None:
        """Clears all stored hashes from the filter."""
        self.seen_hashes.clear()

    def __len__(self) -> int:
        return len(self.seen_hashes)
