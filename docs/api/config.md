# API Reference: `config`

# Module `solver.config`

Configuration management module for the solver library.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class SolverConfig`

Central configuration management for solver library settings.

#### Methods

##### `def from_file(cls, path: Union[str, Path]) -> SolverConfig`

Loads configuration settings from a JSON or TOML file.

**Returns:** `SolverConfig`

##### `def to_dict(self) -> Dict[str, Any]`

Converts configuration to a dictionary.

**Returns:** `Dict[str, Any]`

##### `def save(self, path: Union[str, Path]) -> None`

Saves configuration settings to a JSON file.

**Returns:** `None`


---
