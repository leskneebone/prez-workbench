# Prez Workbench client bundle

Install Docker Desktop and Task, extract this archive, and run `task up`. Then open `http://localhost:3000/catalogs`.

Docker downloads two application images the first time. It starts an API container on port 8000 and a UI container on port 3000. The packaged RDF is mounted read-only. No Node, Python, private source data, or source repository is required.

Use `task status`, `task logs`, and `task down` to inspect, troubleshoot, and stop the environment.

