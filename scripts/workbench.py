#!/usr/bin/env python3
import hashlib, json, os, shutil, sys, tarfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from rdflib import Dataset, Graph, Literal, URIRef

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".staging"
RDF_EXTENSIONS = {".ttl", ".trig", ".nt", ".nq", ".rdf", ".xml", ".jsonld"}
CATEGORIES = ("rdf", "vocabs", "model", "data", "annotations", "flattened")
GEO_WKT_LITERAL = URIRef("http://www.opengis.net/ont/geosparql#wktLiteral")

def files_at(path):
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in RDF_EXTENSIONS)

def load_config():
    path = ROOT / "projects.local.yaml"
    if not path.exists():
        raise SystemExit("Missing projects.local.yaml. Run 'task setup', edit its absolute paths, then retry.")
    # Deliberately parse the small documented YAML subset ourselves so the helper
    # can reuse the Prez image without adding a host or container dependency.
    projects, current, category = [], None, None
    for number, original in enumerate(path.read_text().splitlines(), 1):
        line = original.split("#", 1)[0].rstrip()
        if not line.strip() or line.strip() == "projects:": continue
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current = {"id": stripped.split(":", 1)[1].strip()}
            projects.append(current); category = None
        elif stripped.endswith(":") and not stripped.startswith("-"):
            category = stripped[:-1]
            if current is None or category not in CATEGORIES:
                raise SystemExit(f"Unsupported configuration at line {number}: {original}")
            current[category] = []
        elif stripped.startswith("-") and current is not None and category:
            value = stripped[1:].strip().strip('"').strip("'")
            current[category].append(value)
        else:
            raise SystemExit(f"Unsupported configuration at line {number}: {original}")
    if not projects:
        raise SystemExit("projects.local.yaml must contain a non-empty 'projects' list.")
    return projects

def flatten_rdf(source, destination):
    formats = {".ttl":"turtle", ".trig":"trig", ".nt":"nt", ".nq":"nquads", ".rdf":"xml", ".xml":"xml", ".jsonld":"json-ld"}
    dataset = Dataset()
    dataset.parse(source, format=formats.get(source.suffix.lower()))
    graph = Graph()
    omitted_oversized_wkt = 0
    for subject, predicate, obj, _ in dataset.quads((None, None, None, None)):
        # Oxigraph has a 16 MiB RDF token limit. A very small number of source
        # polygons exceed that limit as individual WKT literals. Omit only
        # those literals from the disposable staging copy; the source remains
        # untouched and the UI reports that their geometry is unavailable.
        if isinstance(obj, Literal) and obj.datatype == GEO_WKT_LITERAL and len(str(obj).encode()) >= 16_000_000:
            omitted_oversized_wkt += 1
            continue
        graph.add((subject, predicate, obj))
    graph.serialize(destination, format="turtle")
    return omitted_oversized_wkt

def assemble():
    projects = load_config()
    tmp = ROOT / ".staging.next"
    if tmp.exists(): shutil.rmtree(tmp)
    tmp.mkdir()
    manifest, names = [], defaultdict(list)
    ids = set()
    for project in projects:
        pid = str(project.get("id", "")).strip()
        if not pid or pid in ids or "/" in pid or ".." in pid:
            raise SystemExit(f"Invalid or duplicate project id: {pid!r}")
        ids.add(pid)
        for category in CATEGORIES:
            for raw in project.get(category, []) or []:
                src = Path(raw)
                if not src.is_absolute(): raise SystemExit(f"Configured path must be absolute: {raw}")
                if not src.exists(): raise SystemExit(f"Configured path does not exist: {src}")
                found = files_at(src)
                if not found: raise SystemExit(f"No recognised RDF files at configured path: {src}")
                for f in found:
                    rel = f.name if src.is_file() else f.relative_to(src)
                    if category == "flattened": rel = Path(rel).with_suffix(".ttl")
                    # Prez annotations are reference data rather than repository
                    # data. Stage them flat so the complete directory can be
                    # mounted over the image's custom annotation input directory.
                    staged_category = "rdf" if category == "flattened" else category
                    dest = Path(staged_category) / rel if category == "annotations" else Path(staged_category) / pid / rel
                    names[f.name].append((pid, str(f), str(dest)))
                    out = tmp / dest
                    out.parent.mkdir(parents=True, exist_ok=True)
                    omitted_oversized_wkt = flatten_rdf(f, out) if category == "flattened" else 0
                    if category != "flattened": shutil.copy2(f, out)
                    digest = hashlib.sha256(out.read_bytes()).hexdigest()
                    manifest_item = {"project": pid, "category": category, "source": str(f), "sha256": digest, "staged": str(dest)}
                    if omitted_oversized_wkt: manifest_item["omitted_oversized_wkt"] = omitted_oversized_wkt
                    manifest.append(manifest_item)
    collisions = {n: rows for n, rows in names.items() if len(rows) > 1}
    if collisions:
        shutil.rmtree(tmp)
        lines = ["Duplicate staged filenames detected (rename at source or narrow registration):"]
        for name, rows in sorted(collisions.items()):
            lines.append(f"  {name}")
            lines.extend(f"    [{pid}] {src}" for pid, src, _ in rows)
        raise SystemExit("\n".join(lines))
    (tmp / "manifest.json").write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "files": manifest}, indent=2) + "\n")
    if STAGE.exists(): shutil.rmtree(STAGE)
    tmp.rename(STAGE)
    print(f"Staged {len(manifest)} explicitly registered RDF files from {len(ids)} projects.")

def parse_graph(path):
    formats = {".ttl":"turtle", ".trig":"trig", ".nt":"nt", ".nq":"nquads", ".rdf":"xml", ".xml":"xml", ".jsonld":"json-ld"}
    graph = Graph()
    graph.parse(path, format=formats.get(path.suffix.lower()))
    return graph

def validate():
    manifest_path = STAGE / "manifest.json"
    if not manifest_path.exists(): raise SystemExit("No staging manifest. Run 'task assemble' first.")
    manifest = json.loads(manifest_path.read_text())["files"]
    by_subject = defaultdict(lambda: defaultdict(set))
    errors, triples = [], 0
    for item in manifest:
        path = STAGE / item["staged"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item["sha256"]: errors.append(f"Hash mismatch: {item['staged']}"); continue
        try: graph = parse_graph(path)
        except Exception as exc: errors.append(f"Invalid RDF {item['staged']}: {exc}"); continue
        triples += len(graph)
        for s, p, o in graph:
            if isinstance(s, URIRef): by_subject[str(s)][item["project"]].add((str(p), o.n3()))
    if errors: raise SystemExit("Validation failed:\n  " + "\n  ".join(errors))
    shared = {s:p for s,p in by_subject.items() if len(p) > 1}
    identical = conflicts = 0
    report = []
    for subject, projects in sorted(shared.items()):
        sets = list(projects.values())
        same = all(x == sets[0] for x in sets[1:])
        if same: identical += 1; kind = "identical shared statements"
        else: conflicts += 1; kind = "conflicting/different values"
        report.append({"subject": subject, "projects": sorted(projects), "classification": kind})
    (STAGE / "duplicate-subjects.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Valid RDF: {len(manifest)} files, {triples:,} triples.")
    print(f"Cross-project subject IRIs: {len(shared)} ({identical} identical, {conflicts} conflicting/different).")
    print("Detailed report: .staging/duplicate-subjects.json")

def export_bundle():
    validate()
    dist = ROOT / "dist"; dist.mkdir(exist_ok=True)
    bundle = dist / "prez-workbench-client"
    if bundle.exists(): shutil.rmtree(bundle)
    for source in ["compose.yaml", "Taskfile.client.yml", "CLIENT-README.md", "prezconfig", "ui", ".staging"]:
        src = ROOT / source
        dest_name = "Taskfile.yml" if source == "Taskfile.client.yml" else ("README.md" if source == "CLIENT-README.md" else source)
        dest = bundle / dest_name
        if src.is_dir(): shutil.copytree(src, dest)
        else: dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dest)
    archive = dist / "prez-workbench-client.tar.gz"
    if archive.exists(): archive.unlink()
    with tarfile.open(archive, "w:gz") as tar: tar.add(bundle, arcname=bundle.name)
    print(f"Portable bundle: {archive}")

if __name__ == "__main__":
    commands = {"assemble": assemble, "validate": validate, "export": export_bundle}
    if len(sys.argv) != 2 or sys.argv[1] not in commands: raise SystemExit("Usage: workbench.py assemble|validate|export")
    commands[sys.argv[1]]()
