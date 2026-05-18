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

Build the image from this directory:

```bash
docker build -t oof-generator .
```

Run the one-event-per-page generator:

```bash
docker run --rm \
  -v "$PWD":/work \
  -w /work \
  oof-generator /app/generate_oof_1evt_1pg.py \
  --report /work/example/session_report.pdf \
  --output /work/example/prefilled_order_of_finish_1evt_1pg.pdf
```

Run the two-events-per-page generator:

```bash
docker run --rm \
  -v "$PWD":/work \
  -w /work \
  oof-generator /app/generate_oof_2evt_1pg.py \
  --report /work/example/session_report_2.pdf \
  --output /work/example/prefilled_order_of_finish_2evt_1pg.pdf
```

Notes:

- The image already contains the required command-line tools and the default templates under `/app/templates`.
- Mount your working directory with `-v` so the generated PDFs are written back to the host.
- You can still pass `--template` and `--workdir` explicitly if you want to override the defaults.

## Summary Page

Both scripts append a final summary page to the generated PDF.

The summary page includes:

- a two-column list of generated events and their heats
- a list of skipped long-distance freestyle events
- a note that total heats may not be accurate if the session report is a pre-scratch session report

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
