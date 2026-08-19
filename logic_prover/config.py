"""Configuration management module for the logic library."""

from __future__ import annotations
import json
import sys
from dataclasses import dataclass, fields, asdict
from pathlib import Path
from typing import Dict, Any, Union

from logic_prover.core.exceptions import SolverError

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


@dataclass
class SolverConfig:
    """Central configuration management for logic library settings."""

    db_path: str = "logic_data.db"
    explorer_max_depth: int = 4
    explorer_batch_size: int = 50
    explorer_top_k: int = 10
    explorer_strategy: str = "mixed"
    prover_max_steps: int = 1000
    prover_timeout_sec: float = 10.0
    log_level: str = "INFO"
    lean_mathlib_version: str = "latest"
    constructive_method: str = "ljt"
    iqc_max_term_depth: int = 2
    iqc_eq_subst_max: int = 5

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> SolverConfig:
        """Loads configuration settings from a JSON or TOML file.

        Unknown keys present in the file are silently ignored.

        Args:
            path: Filesystem path to the .json or .toml configuration file.

        Returns:
            A SolverConfig instance populated from the file contents.

        Raises:
            FileNotFoundError: If the file does not exist.
            SolverError: If TOML is unsupported, the extension is unsupported,
                or the file does not contain a mapping object.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        ext = file_path.suffix.lower()
        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif ext in (".toml", ".tmo"):
            if tomllib is None:
                raise SolverError("TOML parser is not available in this Python environment.")
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        else:
            raise SolverError(f"Unsupported configuration file extension '{ext}'. Expected .json or .toml.")

        if not isinstance(data, dict):
            raise SolverError(f"Configuration file '{path}' must contain a JSON/TOML mapping object.")

        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Converts configuration to a dictionary."""
        return asdict(self)

    def save(self, path: Union[str, Path]) -> None:
        """Saves configuration settings to a JSON file.

        Creates the parent directory if it does not exist.

        Args:
            path: Filesystem path where the JSON configuration should be written.
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
