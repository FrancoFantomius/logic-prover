# API Reference: `explorer`

# Module `logic_prover.explorer.filter`

Diversity filter and Bloom-style formula deduplication filter.

---

## Table of Contents
- [Classes](#classes)

---

## Classes

### `class FormulaFilter`

Maintains a set of canonical formula hashes representing already explored, proven, or discarded formulas to prevent duplicate generation. Supports state persistence to disk (JSON formatted hash store).

#### Methods

##### `def __init__(self, storage_path: Optional[str]) -> None`

Initializes the formula deduplication filter and optionally loads state from storage.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `storage_path` | `Optional[str]` | Optional filesystem path to a persisted filter state JSON file. |

**Returns:** `None`

##### `def add(self, formula: Formula) -> None`

Adds formula's canonical hash to the seen filter set.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The Formula whose hash should be marked as seen. |

**Returns:** `None`

##### `def is_seen(self, formula: Formula) -> bool`

Returns True if formula (or an alpha-equivalent variant) has been seen.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `formula` | `Formula` | The Formula to check against the seen set. |

**Returns:** `bool` — True if the formula's canonical hash is already registered.

##### `def save_state(self, filepath: Optional[str]) -> None`

Persists seen hashes and metadata to disk in JSON format.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `filepath` | `Optional[str]` | Target file path. Defaults to self.storage_path if omitted. |

**Returns:** `None`

**Raises:**
- `SolverError`: If no storage path is available.
- `DatabaseError`: If writing the file fails.

##### `def load_state(self, filepath: str) -> None`

Loads seen hashes from a persisted JSON state file.

**Parameters:**
| Name | Type | Description |
| :--- | :--- | :--- |
| `filepath` | `str` | Path to the filter state JSON file to load. |

**Returns:** `None`

**Raises:**
- `DatabaseError`: If the file is missing or cannot be parsed.

##### `def clear(self) -> None`

Clears all stored hashes from the filter.

**Returns:** `None`


---
