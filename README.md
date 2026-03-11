# Order Of Finish Generator

This directory contains a reusable script for generating prefilled order-of-finish forms from:

- a meet session report PDF
- an order-of-finish template PDF

As of March 11, 2026, the order-of-finish form is the USA Swimming Event Order of Finish form:

- `USA Swimming Event Order of Finish`
  Source: `https://www.usaswimming.org/docs/default-source/officialsdocuments/officiating-forms/admin-forms/event-order-of-finish.pdf`

It is kept in this repo as:

- `example/order-of-finish.pdf`

The expected session report format is like the GoMotion-generated HY-TEK Meet Manager Session Report for the 2026 ISI Winter 11-14 Age Group Championships:

- `GoMotion HY-TEK Meet Manager Session Report example`
  Source: `https://www.gomotionapp.com/ilslsc/__eventform__/1535236_cf0e7abb-27a9-4ce3-ba35-2c005bfd7f5a.pdf`

It is copied in this repo as:

- `example/session_report.pdf`

## Files

- `generate_oof.py`: parses the session report and creates one prefilled form page per event

## Requirements

The script uses command-line tools that should already be available on this machine:

- `python3`
- `pdftotext`
- `pdftoppm`
- `pdflatex`

## Default Usage

Run this from the meet directory that contains:

- `session_report.pdf`
- `order_of_finish.pdf`

Command:

```bash
python3 oof_generator/generate_oof.py
```

That writes:

- `prefilled_order_of_finish.pdf`

## Explicit Paths

You can also pass file paths directly:

```bash
python3 oof_generator/generate_oof.py \
  --report /path/to/session_report.pdf \
  --template /path/to/order_of_finish.pdf \
  --output /path/to/prefilled_order_of_finish.pdf \
  --workdir /path/to/tmp-build-dir
```

## Notes

- The script extracts each event's session number, event number, event name, and heat count.
- It places `Total Heats: N` on the same line as the event name, aligned to the right.
- Intermediate files such as the generated `.tex` file and rendered template image are written to `--workdir`.
