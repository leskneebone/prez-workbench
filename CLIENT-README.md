# Prez Workbench client bundle

This bundle presents a fixed RDF catalogue snapshot using a local Prez API and PrezUI. It does not modify source data and is intended for review and demonstration, not production hosting.

Install [Docker Desktop](https://docs.docker.com/desktop/) and [Task](https://taskfile.dev/docs/installation/), extract the archive, open a terminal in this directory and run:

```sh
task up
```

Then open <http://localhost:3000/catalogs>. The API is available at <http://localhost:8000/catalogs>.

The first start requires internet access while Docker downloads and builds the application images. No local Python, Node.js, private source data or source repository is required.

Useful commands:

- `task status` shows whether the containers are running.
- `task logs` follows diagnostic output; press Control-C to stop watching.
- `task down` stops the catalogue without deleting the bundle.
- `task up` starts it again.

If startup fails, confirm that Docker Desktop is running and that ports 3000 and 8000 are available. Send the output of `task status` and the relevant part of `task logs` when asking for help.

To load different RDF rather than view this fixed snapshot, use the full Prez Workbench repository: <https://github.com/leskneebone/prez-workbench>.
