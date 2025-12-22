# Pitstop Design Rationale

## 1. Overview

Pitstop is a flexible, composable way to describe gas schedules across Ethereum forks. 

**Core idea:**

* **Everything is a “change” driven by an EIP**:
  * A special "base eip" that defines the complete Frontier schedule.
  * Research/prototype can create their own experimental eips.
* **Fork = ordered list of change IDs**, with optional inheritance (`extends`).
* **Conflict resolution is purely by order**: later changes override earlier ones.

This gives:

* Clean evolution across forks.
* Easy “what if” experiments (add/remove changes).
* No ever-growing “schema union” problem for new categories.
* A single, composable source of truth.

---

## 2. Concepts

### 2.1 Change driven by an EIP

A change to the schedule is driven by an EIP located at `schedules/eips/*.yaml`:

```yaml
name: "<human description>"

categories:
  <category-name>:
    <constant-name>: <int>
    ...
  ...
```

**Fields:**
- `name` (required): Human-readable description
- `categories` (required): Gas cost changes grouped by category

**Filename conventions:**
- Official EIPs: `{number}.yaml` (e.g., `150.yaml`, `1884.yaml`)
- Research/experimental: `research.{name}.yaml` (e.g., `research.sload_100.yaml`)
- Base schedule: `base.yaml` (special case - complete Frontier schedule)

### 2.2 Fork

A **Fork** a collection of (`eips`). Optionally a fork can `extends` to another fork.

The **effective list of changes** for a fork is:

> all changes from ancestor forks (via `extends`)
> **+** this fork’s own change IDs (in order)

```yaml
forks:
  frontier:
    # root fork, no extends
    eips: ["base"]

  homestead:
    extends: frontier
    eips: ["150"]

  istanbul:
    extends: homestead
    eips: ["1884"]

  shanghai:
    extends: istanbul
    eips: ["3860"]

  cancun:
    extends: shanghai
    eips: ["4844"]

  prague:
    extends: cancun
    eips: ["7002", "7685"]

  osaka:
    extends: prague
    eips: ["XXXX"]

  # Example research fork extending prague
  prague_sload_100:
    extends: prague
    eips: ["research.sload_100"]
```
Rules:

* `extends` is optional (root fork like `frontier` has no parent).
* `eips` is an ordered list of change IDs.
* The total ordered change list for a fork is:

```
 all ancestor eips (via extends chain, in order)
  + this fork’s eips, in listed order
```

### 2.3 Categories

A **Category** groups related constants:

`categories: { category_name → { symbol → cost } }`

Initial categories (extensible):

* `operations` – opcode / opcode-group gas costs (e.g. `SLOAD`, `BALANCE`, `BLOBBASEFEE`).
* `storage` – storage & state transition costs (e.g. `SSTORE_SET`, warm/cold costs).
* `memory` – memory expansion/initcode costs (e.g. `MEMORY`, `INITCODE_WORD`).
* `precompiles` – per-precompile costs (e.g. `ECRECOVER`, `SHA256`).
* `tx` – transaction-level constants (e.g. `TX_BASE`, `TX_DATA_ZERO`).
* `blobs` – blob-related constants (e.g. `BLOB_BASE`, `BLOB_WORD`).
* Optional: `refunds`, `fee_market`, `misc`.

New categories can be added later by just using a new key under `categories`; no schema change required.

### 2.4 Resolved Schedule

A **ResolvedSchedule** is the final, flattened gas schedule for a fork after we apply base + all relevant changes in order.

This is what code generators and validators consume.

---

## 3. File Layout

Everything lives under `schedules/`:

```text
schedules/
  eips/
    base.yaml                   # complete Frontier schedule
    150.yaml
    1884.yaml
    3860.yaml
    4844.yaml
    7002.yaml
    7685.yaml
    research.sload_100.yaml     # example research change
    ...
  forks.yaml                    # fork definitions
```

---

## 4. Resolution Semantics

### 4.1 Algorithm

Given `fork_name`, we want a `ResolvedSchedule`:

1. **Compute ordered change list**

   * Follow `extends` chain from the root (`frontier`) to `fork_name`.
   * For each fork in the chain, append its `eips` in order.
   * Result: `change_ids: List[str]` (e.g. `["base", "150", "1884", ..., "research.sload_100"]`).

2. **Apply changes in order**

   * Start with empty `categories = {}`.
   * For each change in `change_ids`:

     * For each `category` in `change.categories`:

       * Ensure `categories[category]` exists (dict).
       * For each `name, value` in that category: overwrite (`categories[category][name] = value`).

3. **Conflict resolution**

   * If multiple changes touch the same `(category, name)`, the **last change in the list wins**.

4. **Return ResolvedSchedule**

   * `fork = fork_name`
   * `eips = change_ids`
   * `categories = categories`

### 4.2 Example: `prague_sload_100`

With the fork definition above:

* `frontier` → `["base"]`
* `prague` extends `cancun`, and adds `["7002", "7685"]`.
* `prague_sload_100`:

  * inherits all changes from `prague` (i.e. `base, 150, 1884, 3860, 4844, 7002, 7685`)
  * adds `["research.sload_100"]`.

So `pitstop resolve prague_sload_100` will:

* Apply `base` → Frontier schedule.
* Apply EIPs (150, 1884, 3860, 4844, 7002, 7685) in order.
* Apply `research.sload_100` last, overriding `SLOAD` to `100`.

Result: a full schedule identical to Prague except `SLOAD` is 100.

---

## 5. CLI Behavior

### 5.1 `pitstop resolve <fork>`

**Purpose:** resolve a fork into its full gas schedule.

* Input: `fork` name, e.g. `prague`, `osaka`, `prague_sload_100`.
* This will:

  1. Load `forks.yaml` and `eips/*.yaml`.
  2. Compute ordered change IDs for `fork`.
  3. Apply resolution algorithm.
  4. Output the final schedule (e.g. as YAML/JSON).

Example:

```bash
pitstop resolve prague_sload_100 > prague_sload_100.resolved.yaml
```

You can then:

* Diff it vs `pitstop resolve prague`.
* Feed it into generators or analysis tools.

### 5.2 `pitstop swap geth <fork>`

**Purpose:** generate client code from a resolved schedule.

Implementation detail:

* Internally: `resolve(fork)` → `ResolvedSchedule` → template → `output.go`.

Example:

```bash
pitstop swap geth prague_sload_100 output.go
```

### 5.3 `pitstop compare <forkA> <forkB>`

**Purpose:** show differences between two forks.

* Resolve both.
* Diff by `(category, name)` and show changed values and the change IDs that caused them.

Example:

```bash
pitstop compare prague osaka
```

### 5.4 (Optional) `pitstop explain <fork> <category.name>`

**Purpose:** explain why a specific constant has its final value.

* Track a small “trace” during resolution: for each `(category, name)`, which change IDs set it and in what order.
* `pitstop explain prague operations.SLOAD` might output:

  ```text
  base: operations.SLOAD = 50
  150:  operations.SLOAD = 200
  1884: operations.SLOAD = 800   (final)
  ```

This is extremely useful for debugging and research.

---

## 6. Data Model (Python-level Sketch)

```python
from typing import Dict, List, Optional
from pydantic import BaseModel

CategoryMap = Dict[str, Dict[str, int]]  # e.g. {"operations": {"SLOAD": 800, ...}}

class EIP(BaseModel):
    name: str
    categories: CategoryMap

class Fork(BaseModel):
    name: str
    extends: Optional[str] = None
    eips: List[str]   # change IDs, in order

class ResolvedSchedule(BaseModel):
    fork: str
    eips: List[str]   # final ordered list of change IDs
    categories: CategoryMap

    @property
    def operations(self) -> Dict[str, int]:
        return self.categories.get("operations", {})

    @property
    def storage(self) -> Dict[str, int]:
        return self.categories.get("storage", {})

    @property
    def memory(self) -> Dict[str, int]:
        return self.categories.get("memory", {})

    @property
    def precompiles(self) -> Dict[str, int]:
        return self.categories.get("precompiles", {})

    @property
    def blobs(self) -> Dict[str, int]:
        return self.categories.get("blobs", {})
```

Resolution and CLI use these types; no additional versioning layer is needed because **forks themselves are the “versions”**.

---

## 7. Validation & Invariants

To keep things sane:

* **Change-level validation**

  * `categories` must not have duplicate keys (YAML loader should error on duplicate keys).
  * Optional checks like “no empty categories”.

* **Fork-level validation**

  * `name` must be unique.
  * `extends`, if present, must refer to an existing fork.
  * All `eips` must refer a valid eip.
  * No cycles in `extends` chain.

* **Resolved schedule validation**

  * Required opcodes exist for a given fork, etc.
  * If a required value for a category is not found, it MUST throw instead of silently failing.

* **Template-level validation**

  * If a template references a constant that doesn't exist in the resolved schedule, generation should fail with a clear error.
  * Use `since(fork)` checks to guard fork-specific constants.

  Example error:
  ```
  Error generating geth code for fork 'homestead':
    Template references 'schedule.blobs.BLOB_BASE' but 'blobs' category doesn't exist.
    Fix: Add conditional check in template:
      {% if schedule.since('cancun') %}
  ```

---

## 8. Template Directives

Templates may need conditional logic when constants are introduced in different forks.

### 8.1 `since(fork_name)`

Check if the current fork includes a specific fork in its ancestry chain.

**Usage:**
```jinja2
{% if schedule.since('cancun') %}
  // Cancun or later - blobs available
  public const long BlobBase = {{ schedule.blobs.BLOB_BASE }};
  public const long BlobWord = {{ schedule.blobs.BLOB_WORD }};
{% endif %}
```

**When to use:**
- Templates shared across multiple forks
- Features introduced in specific fork (e.g., blobs in Cancun)
- Client-specific versioned constants

**Implementation:**
```python
class ResolvedSchedule(BaseModel):
    fork: str
    eips: list[str]
    categories: CategoryMap

    def since(self, name: str) -> bool:
        """Check if fork 'name' is in this schedule's ancestry."""
        if name in get_all_forks():
            return name in get_fork_ancestry(self.fork)
        return False
```

**Error handling:**
- If constant is missing and not guarded: **THROW** (loud failure)
- No silent fallbacks allowed

**Example:**
```go
// Geth template
const (
    GasSLoad uint64 = {{ schedule.operations.SLOAD }}

    {% if schedule.since('cancun') %}
    // Blob gas costs (EIP-4844, introduced in Cancun)
    GasBlobBase uint64 = {{ schedule.blobs.BLOB_BASE }}
    GasBlobWord uint64 = {{ schedule.blobs.BLOB_WORD }}
    {% endif %}
)
```

This allows templates to evolve with the protocol without breaking older forks.

---

## 9. Template Authoring Guide

### 9.1 Basic Template Structure

```go
// {{ pitstop_header }}
// Fork: {{ schedule.fork }}

package vm

// Operations gas costs
const (
{%- for name, cost in schedule.operations.items() %}
    Gas{{ name }} uint64 = {{ cost }}
{%- endfor %}
)
```

### 9.2 Handling Optional Categories

```csharp
// Nethermind example - blobs introduced in Cancun
{% if schedule.since('cancun') %}
// Blob gas costs (EIP-4844)
public const long BlobBase = {{ schedule.blobs.BLOB_BASE }};
public const long BlobWord = {{ schedule.blobs.BLOB_WORD }};
{% endif %}
```

### 9.3 Fork-Specific Constants

Some clients have fork-specific variations of the same constant:

```csharp
// Base value
public const long Balance = {{ schedule.operations.BALANCE }};

// EIP-150 override (if applicable)
{% if schedule.since('homestead') %}
public const long BalanceEip150 = 400;
{% endif %}

// EIP-1884 override (if applicable)
{% if schedule.since('istanbul') %}
public const long BalanceEip1884 = 700;
{% endif %}
```
