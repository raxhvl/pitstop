# Pitstop API Reference

**Status:** 🚧 Pending verification after EIP-centric migration

---

## Commands

### `pitstop swap <client> <fork> <output>`

Generate client code from a fork.

**Arguments:**
- `client`: Client name (`geth`, `nethermind`, `reth`, `besu`, `erigon`)
- `fork`: Fork name from `forks.yaml`
- `output`: Output file path

**Example:**
```bash
pitstop swap geth prague gas.go
pitstop swap nethermind osaka GasCostOf.cs
pitstop swap geth prague_cheap_sload gas.go  # Research fork
```

---

### `pitstop check <client> <fork> <file>`

Verify a file matches the fork's generated code.

**Arguments:**
- `client`: Client name
- `fork`: Fork name from `forks.yaml`
- `file`: File path to verify

**Example:**
```bash
pitstop check geth prague go-ethereum/core/vm/gas.go
```

**Exit codes:**
- `0` - File matches
- `1` - File differs or error

---

### `pitstop compare <fork1> <fork2>`

Compare two forks and show differences.

**Arguments:**
- `fork1`: First fork name
- `fork2`: Second fork name

**Example:**
```bash
pitstop compare prague osaka
```

**Output:**
```
Comparing prague vs osaka

Operations:
  SLOAD: 800 → 100

✓ 1 changed
```

**Exit codes:**
- `0` - Forks are identical
- `1` - Forks differ

---

### `pitstop resolve <fork>`

Resolve a fork into its full gas schedule.

**Arguments:**
- `fork`: Fork name from `forks.yaml`

**Output:** YAML with resolved schedule

**Example:**
```bash
pitstop resolve prague
pitstop resolve prague > prague.resolved.yaml
```

**Output:**
```yaml
fork: prague
eips: ["base", "150", "1884", "3860", "4844", "7002", "7685"]
categories:
  operations:
    SLOAD: 800
    BALANCE: 700
    # ...
  storage:
    SLOAD: 2100
    # ...
```

---

### `pitstop explain <fork> <category.name>`

Explain why a constant has its final value.

**Arguments:**
- `fork`: Fork name
- `category.name`: Category and constant name (e.g., `operations.SLOAD`)

**Example:**
```bash
pitstop explain prague operations.SLOAD
```

**Output:**
```
base:  operations.SLOAD = 50
150:   operations.SLOAD = 200
1884:  operations.SLOAD = 800  (final)
```

---

## Template API

Templates receive `ResolvedSchedule`:

```jinja2
// {{ pitstop_header }}
// Fork: {{ schedule.fork }}
// EIPs: {{ schedule.eips|join(', ') }}

package vm

const (
    GasSLoad uint64 = {{ schedule.operations.SLOAD }}
    GasBalance uint64 = {{ schedule.operations.BALANCE }}

    {% if schedule.since('cancun') %}
    // Blob gas costs (EIP-4844)
    GasBlobBase uint64 = {{ schedule.blobs.BLOB_BASE }}
    GasBlobWord uint64 = {{ schedule.blobs.BLOB_WORD }}
    {% endif %}
)
```

**Available methods:**
- `schedule.since(fork_name)` - Check if fork is in ancestry chain
- `schedule.operations` - Get operations category
- `schedule.storage` - Get storage category
- `schedule.precompiles` - Get precompiles category
- `schedule.memory` - Get memory category
- `schedule.blobs` - Get blobs category (if exists)
- `schedule.categories` - Access all categories dynamically

**Error handling:**
- Missing constants: **THROW** (no silent fallbacks)
- Use `since()` to guard fork-specific features

---

## Error Messages

### Error: Fork not found: osaka
  Available forks: frontier, homestead, ..., prague

### Error: EIP not found: 9999
  Referenced by fork: osaka
  Expected file: schedules/eips/9999.yaml

### Error: Cycle detected in fork chain:
  osaka → prague → cancun → osaka

### Error: Template error generating geth code for fork 'homestead':
  Line 42: {{ schedule.blobs.BLOB_BASE }}
  Category 'blobs' doesn't exist in homestead
  Fix: Add conditional check:
    {% if schedule.since('cancun') %}

### Error: Missing required constant:
  Fork: prague
  Category: operations
  Constant: SLOAD
  This constant is required by the geth template

---

## Exit Codes

- `0` - Success
- `1` - Error or differences found

---

## Notes

- No configuration files (`.pitstoprc`) - all behavior via CLI args and YAML
- Templates must fail loud on missing constants (no `.get()` with defaults)
- Fork names must match exactly (case-sensitive)
- EIP files use filename as ID (no `id` field in YAML)
