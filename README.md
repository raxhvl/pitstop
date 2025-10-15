# Pitstop 🏁

<p align="center">
  <img src="assets/logo.jpg" alt="Pitstop" width="200"/>
</p>

<h3 align="center">
  Swap Ethereum gas schedules at racing speed; without the pit-crew!
</h3>

Prototyping gas schedule is bottlenecked by manual update of 5+ clients in 4+ languages. Pitstop helps automate this.

## Quick Start

Two steps to start using Pitstop:

1. **Install uv** ([docs](https://docs.astral.sh/uv/getting-started/installation/))

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Run Pitstop**

   ```bash
   uvx --from git+https://github.com/raxhvl/pitstop pitstop swap geth prague output.go
   ```

That's it. No cloning, no setup.

## How it works

You want to test new gas costs. You need to:

- Update Geth (Go)
- Update Nethermind (C#)
- Update Reth (Rust)
- Update Besu (Java)
- Update Erigon (Go)
- Update execution-specs (Python)

you run:

```yaml
# schedules/prague.yaml
storage:
  SSTORE_SET: 18000    # was 20000
```

```bash
$ pitstop swap geth fast-storage go-ethereum/core/vm/gas.go
🏁 Config updated!
```

Researchers iterate faster. Client developers get consistent code. Everyone tests the same values.

## License

MIT
