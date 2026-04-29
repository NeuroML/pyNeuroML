# AGENTS.md - pyNeuroML

Single Python package for reading, writing, simulating and analysing NeuroML2/LEMS models.

## Architecture

- **Single package** — all code under `pyneuroml/`, tests under `tests/`, examples under `examples/`
- **Bundled jNeuroML** — `pyneuroml/lib/*.jar` provides Java simulation backend
- **CLI entry points** — `pynml` (main), `jnml`, `pynml-channelanalysis`, `pynml-povray`, `pynml-tune`, `pynml-swc2nml`, `pynml-xpp`, and others (see `setup.cfg` `[options.entry_points]`)
- **Core modules**: `pynml.py` (main CLI), `io.py`, `runners.py`, `lems/`, `analysis/`, `neuron/`, `channelml/`, `plot/`, `tune/`, `swc/`, `xppaut/`

## Developer Commands

```bash
# Install for development (from repo root)
pip install .[dev]

# Run lint + format (ruff)
ruff check . --fix
ruff format .

# Run full test suite (installs deps, runs CLI tests + pytest + examples)
./test.sh             # or ./test-ghactions.sh
./test-ghactions.sh -neuron   # includes NEURON examples

# Run pytest only (skips tests marked localonly — they segfault on CI)
pytest -m "not localonly"

# Run a single test file
pytest tests/test_pynml.py

# Run pre-commit hooks manually
pre-commit run --all-files
```

## Testing Quirks

- `pyproject.toml` defines a `localonly` marker — tests with it are skipped on GitHub Actions because they segfault
- `test-ghactions.sh` is the authoritative test script; it installs the package, verifies all CLI tools, runs pytest, and executes examples
- Some tests require a display (matplotlib); they're guarded by `if [[ "$CI" != "true" ]]`
- NEURON examples require the `-neuron` flag and `nrniv` on PATH

## CI

- **ci.yml** — matrix build on Python 3.9–3.13, runs `./test-ghactions.sh -neuron`
- **ruff.yml** — ruff check on PRs (changed files only)
- **python-publish.yml** — PyPI publishing

## Conventions

- **No unicode characters in code**: use ASCII only in comments and strings.
- **Branch**: development is the working branch; master is stable
- **Ruff config**: ignores `F403`, `F405` (wildcard imports); excludes `examples/`
- **mypy**: `ignore_missing_imports = True` (minimal type checking)
- **Pre-commit**: trailing whitespace, EOF fixer, large file check (<5MB), ruff import sort + format
- **Python support**: 3.9–3.13

## Session Continuity

- Check `.agents/` for prior session logs (`YYYY-MM-DD.md`) at session start
- Use the template in `.agents/Readme.md` for new session summaries

## Dependencies

- **External**: Java (JRE) for jNeuroML, Graphviz (`dot`) for diagrams
- **Optional backends**: NEURON, Brian2, NetPyNE, Tellurium (installed via extras like `[neuron]`, `[brian]`, etc.)

## References

- `setup.cfg` — authoritative source for entry points, extras, and dependencies
- `pyproject.toml` — pytest, ruff, and coverage config
- `test-ghactions.sh` — full integration test flow
