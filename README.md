# Pitstop 🏁

**Swap Ethereum gas schedules at racing speed; without the pit-crew!**

Prototyping gas schedule is bottlenecked by manual update of 5+ clients in 4+ languages. Pitstop helps automate this.

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
# schedules/fast-storage.yaml
storage:
  SSTORE_SET: 18000    # was 20000
```

```bash
pitstop swap geth fast-storage
# → output/geth/gas.go
```

Researchers iterate faster. Client developers get consistent code. Everyone tests the same values.

## License

MIT
