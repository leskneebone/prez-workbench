# Prez Workbench

Prez Workbench is an experimental, Docker-based environment for assembling, validating and presenting selected RDF projects with [Prez](https://prez.dev/) and [PrezUI](https://prez.dev/prezui). It is intended for local data review, profile development and demonstrations. It is not a production deployment template.

The workbench combines an explicitly registered set of RDF files into one local Prez API and one PrezUI. It never scans a parent projects directory: only paths listed in the ignored `projects.local.yaml` are copied into the ignored `.staging/` area. Source files are mounted read-only and are never modified.

## Why does this exist?

You can do all of this with Prez and PrezUI directly. If you're comfortable setting up and configuring their development environments, you probably don't need Prez Workbench.

This project is for the rest of us: people who work with RDF, vocabularies, ontologies and linked data, but don't necessarily want to become Prez or frontend developers just to see their data running locally in PrezUI. It packages one opinionated, reproducible route through the setup: point it at some RDF, let it assemble and validate the data, start the containers, and open the result in a browser.

Prez Workbench is not part of Prez or PrezUI, and it isn't an alternative implementation of either. It's a convenience layer built on top of them — a shortcut to a local workbench when the thing you actually want to work on is the data.

## Quick start

Install [Docker Desktop](https://docs.docker.com/desktop/) and [Task](https://taskfile.dev/docs/installation/), then run:

```sh
git clone https://github.com/leskneebone/prez-workbench.git
cd prez-workbench
task setup
task assemble
task validate
task up
```

The initial configuration loads a small catalogue from `examples/`, so a new checkout can be tested before adding external data.

Open:

- PrezUI: <http://localhost:3000/catalogs>
- Prez API: <http://localhost:8000/catalogs>

If either port is occupied, choose alternatives when starting the stack:

```sh
PREZ_PORT=8010 PREZ_UI_PORT=3010 task up
```

## Load your own RDF

Edit `projects.local.yaml`, which `task setup` creates from `projects.example.yaml`. A project may register an RDF file or a directory of RDF files:

```yaml
projects:
  - id: my-project
    rdf:
      - ~/Projects/my-project/outputs
    vocabs:
      - ~/Projects/my-project/vocabs
    model:
      - ~/Projects/my-project/model.ttl
```

Accepted categories are `rdf`, `vocabs`, `model`, `data`, `annotations` and `flattened`. Paths may be relative to the workbench directory or point into `~/Projects`, which the helper container mounts read-only. Directories are searched recursively only after being explicitly registered. Only recognised RDF extensions are copied; XML source exports, databases, documents and other inputs are ignored.

Use `annotations` for Prez ontology-term annotation files. Use `flattened` deliberately when named graphs in TriG or N-Quads must be exposed to local Prez as one default graph. Flattening creates a disposable Turtle copy in staging without modifying the source. WKT literals at or above Oxigraph's 16 MB token limit are omitted from that copy and counted in the staging manifest.

After changing source data or configuration, run:

```sh
task assemble
task validate
task up
```

## Safeguards and outputs

Assembly fails for missing paths, empty registered locations, repeated project IDs, invalid IDs and duplicate source basenames. `.staging/manifest.json` records every source path, staged destination and SHA-256 hash. Validation checks those hashes, parses every RDF file and writes `.staging/duplicate-subjects.json`, distinguishing identical shared descriptions from subjects whose statements differ across projects.

`task up` refuses to start until validation succeeds.

The repository includes IDN-oriented ATNS, ODRL and RiC-O presentation examples. These profiles and UI components demonstrate how a workbench can test project-specific presentation; they are not part of Prez itself and may be replaced for another project.

## Portable client bundle

To package the currently registered RDF and configuration for someone who only needs to view that fixed catalogue, run:

```sh
task export
```

This assembles and validates the data, then writes `dist/prez-workbench-client.tar.gz`. The client needs only Docker and Task. Exported manifests retain source filenames but redact the exporting user's directory paths.

The client bundle is different from this repository: it presents one fixed snapshot, whereas a full checkout can register and rebuild other RDF projects.

## Commands

- `task setup` checks Docker, creates local configuration when absent and builds the helper image.
- `task assemble` copies only explicitly registered RDF and generates the manifest.
- `task validate` verifies hashes and RDF syntax and reports cross-project subject IRIs.
- `task up` validates and starts the Prez API and PrezUI.
- `task down` stops and removes the containers while retaining staged data.
- `task logs` follows API and UI logs.
- `task status` shows container and API health.
- `task export` creates a portable client archive.

## Architecture and maintenance

Docker Compose runs a pinned Prez API image and builds a pinned PrezUI application. Dependency upgrades are deliberate: change the pinned versions on a branch, rebuild the stack and verify both the bundled sample and any project-specific components before merging. This avoids silently adopting an incompatible PrezUI release.

An image is a packaged application template; a container is a running instance of that image. Port 8000 exposes the API and port 3000 exposes the UI. Read-only mounts make staged RDF and configuration visible to the containers without allowing them to edit source projects.

The workbench is development and demonstration tooling. It does not provide production authentication, HTTPS, persistent database administration, backups, monitoring or availability guarantees.

## Licence

Prez Workbench is released under the BSD 3-Clause License. Prez, PrezUI, OpenLayers and container images retain their own licences.
