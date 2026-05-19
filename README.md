# Order Of Finish Generator

This directory contains two PDF generator entrypoints:

- `generate_oof_1evt_1pg.py`: the original one-event-per-page generator
- `generate_oof_2evt_1pg.py`: the two-tables-per-page generator tuned for `templates/OOF_template_two_events_per_page.pdf`

## Requirements

Python:

- `python3`
- No third-party Python modules are required. Both scripts use only the Python standard library.

Command-line tools:

- `pdftotext`
- `pdftoppm`
- `pdflatex`
- `pdfinfo`

## Install Tools

macOS with Homebrew:

```bash
brew install poppler
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install collection-latexrecommended pgf grffile multicol
```

If `tlmgr` is not on your `PATH`, use:

```bash
sudo /Library/TeX/texbin/tlmgr update --self
sudo /Library/TeX/texbin/tlmgr install collection-latexrecommended pgf grffile multicol
```

Verify the tools are available:

```bash
python3 --version
pdftotext -v
pdftoppm -v
pdfinfo -v
pdflatex --version
```

## One Event Per Page

Use `generate_oof_1evt_1pg.py` when the template is a single full-page PDF form for each event.

Defaults:

- `--template` defaults to `templates/OOF_template_one_event_per_page.pdf`
- `--workdir` defaults to a temporary directory that is deleted automatically when the script finishes

Example using defaults:

```bash
python3 generate_oof_1evt_1pg.py \
  --report example/session_report.pdf \
  --output example/prefilled_order_of_finish_1evt_1pg.pdf
```

Example with explicit paths:

```bash
python3 generate_oof_1evt_1pg.py \
  --report /path/to/session_report.pdf \
  --template /path/to/OOF_template_one_event_per_page.pdf \
  --output /path/to/prefilled_order_of_finish_1evt_1pg.pdf \
  --workdir /path/to/tmp-build-dir
```

## Two Tables Per Page

Use `generate_oof_2evt_1pg.py` when the template has two event tables per page.
It fills:

- session number
- event number
- event name
- total heats

When an event has more than 20 heats, the script uses the continuation template page when available for heats 21 to 40. If the template PDF has only one page, page 1 is reused for the continuation layout.

Defaults:

- `--template` defaults to `templates/OOF_template_two_events_per_page.pdf`
- `--workdir` defaults to a temporary directory that is deleted automatically when the script finishes

Example using defaults:

```bash
python3 generate_oof_2evt_1pg.py \
  --report example/session_report_2.pdf \
  --output example/prefilled_order_of_finish_2evt_1pg.pdf
```

Example with explicit paths:

```bash
python3 generate_oof_2evt_1pg.py \
  --report /path/to/session_report.pdf \
  --template /path/to/OOF_template_two_events_per_page.pdf \
  --output /path/to/prefilled_order_of_finish_2evt_1pg.pdf \
  --workdir /path/to/tmp-build-dir
```

## Docker

Use the published multi-arch image:

```bash
docker pull ghcr.io/dingp/swim-meet-order-of-finish-generator:latest
```

Run the web app container:

```bash
docker run --rm -p 8000:8000 ghcr.io/dingp/swim-meet-order-of-finish-generator:latest
```

Then open `http://localhost:8000`.

The `latest` tag is a multi-arch image and should work on both:

- `linux/arm64` hosts, including Apple Silicon Macs running Docker Desktop
- `linux/amd64` / x86-64 hosts

Use Docker Compose:

```bash
docker compose pull
docker compose up
```

Then open `http://localhost:8000`.

Stop it with:

```bash
docker compose down
```

You can still use the container to run the CLI scripts directly:

```bash
docker run --rm \
  -v "$PWD":/work \
  -w /work \
  ghcr.io/dingp/swim-meet-order-of-finish-generator:latest python3 /app/generate_oof_1evt_1pg.py \
  --report /work/example/session_report.pdf \
  --output /work/example/prefilled_order_of_finish_1evt_1pg.pdf
```

```bash
docker run --rm \
  -v "$PWD":/work \
  -w /work \
  ghcr.io/dingp/swim-meet-order-of-finish-generator:latest python3 /app/generate_oof_2evt_1pg.py \
  --report /work/example/session_report_2.pdf \
  --output /work/example/prefilled_order_of_finish_2evt_1pg.pdf
```

Notes:

- The image starts the Flask app with Gunicorn on port `8000`.
- If you want to rebuild from source locally instead, run `docker build -t oof-generator .` from this directory and substitute `oof-generator` in the commands above.
- Mount your working directory with `-v` only if you want to run the CLI scripts inside the container.
- The web app itself returns the generated PDF directly in the browser and does not need a mounted output directory.

## Helm

A Helm chart is included at `charts/swim-meet-order-of-finish-generator`.

It deploys:

- the web app `Deployment` and `Service`
- an `Ingress`
- the ACME helper PVC, web server, placeholder TLS secret, and renewal `CronJob` used to obtain and refresh the ingress TLS certificate

For the development cluster deployment in namespace `oof`, use `charts/swim-meet-order-of-finish-generator/values-development.yaml`.

See `charts/swim-meet-order-of-finish-generator/README.md` for the install command and the remaining values you need to set before installing it.

## Web App

A minimal Flask web app is included for browser-based use and container deployment.

Endpoints:

- `GET /`: upload form
- `POST /generate`: generate and download the PDF
- `GET /healthz`: health check

Run locally after installing Python dependencies:

```bash
pip install -r requirements.txt
python3 app.py
```

Then open `http://localhost:8000`.

The web interface lets users:

- upload a session report PDF
- choose one-event-per-page or two-events-per-page output
- download the generated order-of-finish PDF

The web app uses the bundled templates and writes each request to a temporary working directory that is deleted after the response is created.

## Summary Page

Both scripts place the summary before the order-of-finish pages in the generated PDF.

The summary page includes:

- a two-column list of generated events and their heats
- a list of skipped long-distance freestyle events
- a note that total heats may not be accurate if the session report is a pre-scratch session report
- automatic overflow onto additional summary pages when needed

Long-distance freestyle events currently skipped are:

- `500 Freestyle`
- `800 Freestyle`
- `1000 Freestyle`
- `1500 Freestyle`
- `1650 Freestyle`

## Notes

- Both scripts extract each event's session number, event number, event name, and heat count.
- If you pass `--workdir`, intermediate files such as the generated `.tex` file and rendered template images are written there and left in place.
- If you omit `--workdir`, a temporary directory is created and deleted automatically.
