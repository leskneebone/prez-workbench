# Prez Workbench

Prez Workbench combines explicitly registered RDF from independent projects into one local Prez 4.23.7 API and one PrezUI. It never scans `~/Projects`: only paths listed in the ignored `projects.local.yaml` are copied into the ignored `.staging/` area. Source files are read-only from the workbench's point of view and are never modified.

## Quick start

Requirements: Docker Desktop and [Task](https://taskfile.dev/). You do not need a local Python or Node installation. Registered source projects must be beneath your `~/Projects` directory, which the helper container mounts read-only.

```sh
task setup
# Edit projects.local.yaml if the suggested paths are not correct.
task assemble
task validate
task up
```

Open `http://localhost:3000/catalogs`. The API is at `http://localhost:8000/catalogs`.

If ports 8000 or 3000 are occupied, stop the conflicting service or set alternatives before starting, for example `PREZ_PORT=8010 PREZ_UI_PORT=3010 task up`.

## What Docker is doing

An **image** is a packaged application template. A **container** is a running instance of an image. This project runs two containers: Prez (the API) and PrezUI (the browser interface). The UI image is built using PrezUI's upstream Docker recipe, entirely inside Docker. A **port** maps a container service to your computer: port 8000 is the API and port 3000 is the UI. A **mount** makes local files visible inside a container; the staged RDF and configuration are mounted read-only, so the services cannot edit them.

`task down` removes the running containers but keeps `.staging/`. `task logs` follows their logs and `task status` shows whether they are healthy.

## Registration and safeguards

Copy `projects.example.yaml` to `projects.local.yaml` (normally done by `task setup`) and use absolute paths. Accepted keys are `rdf`, `vocabs`, `model`, and `data`. Directories are searched recursively only after being explicitly registered. Only recognised RDF extensions are copied; private XML, databases, documents, and other raw inputs are ignored.

Assembly fails for missing paths, empty registered locations, repeated project IDs, invalid IDs, and duplicate basenames. `.staging/manifest.json` records every source path, SHA-256 hash, project, category, and destination. Validation checks hashes, parses every RDF file, and writes `.staging/duplicate-subjects.json`, distinguishing graph-identical shared descriptions from subjects whose statements differ across projects.

`task up` refuses to start until validation succeeds. Run `task assemble` whenever source outputs change.

## Portable delivery

`task export` assembles and validates, then writes `dist/prez-workbench-client.tar.gz`. The bundle contains staged RDF, profiles, endpoints, Compose, and client commands. It contains no machine-specific source paths in its runtime configuration and needs only Docker and Task. Review `.staging/manifest.json` before sending because it intentionally preserves provenance paths; remove or redact that manifest if path disclosure is undesirable.

## Commands

- `task setup`: check Docker, create the local config when absent, and build the helper image.
- `task assemble`: copy only registered RDF and generate the manifest.
- `task validate`: verify hashes/RDF syntax and report cross-project subject IRIs.
- `task up`: validate and start both services.
- `task down`: stop both services.
- `task logs`: follow logs.
- `task status`: show container and API health.
- `task export`: build the portable client archive.
