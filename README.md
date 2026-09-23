# Synthetic Threat Intelligence Foundation

This project is a local, offline investigator console for evidence-driven
analysis of synthetic threat-intelligence records. It uses only fictional
entities and does not make identity claims about real people.

## Requirements

- Python 3.10 or newer
- No third-party packages
- No network connection, API keys, or external services

## Run

Generate the deterministic dataset and print a summary:

```powershell
python run.py
```

Start the local read-only API:

```powershell
python -m threat_platform.api.server
```

Open `http://127.0.0.1:8765` for the investigator console. The API binds to
loopback only and serves generated local JSON plus local investigator views.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
data/                 Generated synthetic JSON dataset
threat_platform/
  algorithms/         Reserved for future analysis algorithms (empty for now)
  api/                Standard-library local API
  models/             Common schema definitions and validation
  services/           Synthetic generation, storage, and investigator views
  ui/                 Dependency-free console plus InvestigatorConsole.jsx
tests/                Offline foundation tests
run.py                Dataset generation and load smoke test
```

Modules A-D now calculate evidence, attribution, persona, and reliability
outputs that Module E consumes. See
[ARCHITECTURE.md](ARCHITECTURE.md), [DATA_SCHEMA.md](DATA_SCHEMA.md), and
[API_CONTRACT.md](API_CONTRACT.md) for the local contracts and limitations.

`threat_platform/ui/InvestigatorConsole.jsx` is a standalone React + Tailwind
component containing a richer offline judge-demo surface. It embeds its own
synthetic mock state and does not call the Python API, a network, or external
services. It can be imported into any existing React/Tailwind host without
changing the dependency-free Python console.

The generated Python fixture currently contains fifteen fictional actors,
eighteen personas, thirty-six handles, thirty wallets, twenty infrastructure
fingerprints, seventy-two posts, one hundred eight behavior events, one
hundred twenty evidence records, and one hundred twenty relationships.

The project does not import or transform real public records. Public data can
contain personal or operational information, and relabeling it would not make
that information fictional. The local fixture uses public-benchmark-shaped
fields and fully fictional values instead.

