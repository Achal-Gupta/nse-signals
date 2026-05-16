# Contributing & Versioning Workflow

## Version Naming

We follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **v0.x.y** — Pre-1.0, breaking changes allowed between minors
- **v1.0.0+** — Production, semver enforced

## Branching Strategy

- `main` — always working, deployable
- `dev/vX.Y.Z` — development branch for the next version
- Feature branches off `dev/vX.Y.Z`: `feature/short-name`

## Release Flow

1. Create `dev/vX.Y.Z` branch from `main`
2. Update `docs/design/vX.Y.Z/` with the new design (copy from previous version + edit)
3. Implement changes
4. Update `CHANGELOG.md` under `[Unreleased]`
5. When stable, merge to `main` and tag the release:
   - Move `[Unreleased]` content to `[X.Y.Z] - DATE`
   - Tag the commit: `vX.Y.Z`

## Adding a New Agent

Every agent follows this package layout:

```
agents/<agent_name>/
├── __init__.py
├── skill.md          # Role definition (system prompt for LLM-based agents)
├── connectors.py     # External data access (APIs, web, etc.)
├── agent.py          # Entry point: returns standardized Signal
├── subagents.py      # Sub-Claude calls (empty placeholder OK)
└── README.md         # One-page reference
```

Every agent's `agent.py` must expose an `analyze()` function returning a `Signal`
(see `lib/contracts.py`).

## Design Docs

Per version, three files in `docs/design/vX.Y.Z/`:

- `architecture.md` — System diagrams (Mermaid) + component list
- `contracts.md` — Data shapes between agents + sheet schemas
- `decisions.md` — Key choices, rationale, roadmap context
