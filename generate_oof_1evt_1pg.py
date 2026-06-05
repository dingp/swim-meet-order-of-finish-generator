#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from session_report_parser import parse_event_line


SESSION_X = 1.82
SESSION_Y = 6.86
EVENT_NO_X = 6.55
EVENT_NO_Y = 6.86
EVENT_NAME_X = 2.38
EVENT_NAME_Y = 6.405
TOTAL_HEATS_X = 9.95
EVENT_NAME_FONT = (16.5, 19.5)


@dataclass
class Event:
    session_number: int
    event_number: int
    event_name: str
    heats: int


@dataclass
class ParseResult:
    events: list[Event]
    skipped_events: list[Event]


def run_pdftotext(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def ensure_template_image(template_pdf: Path, template_image: Path) -> None:
    if template_image.exists():
        return

    subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-r",
            "300",
            "-singlefile",
            str(template_pdf),
            str(template_image.with_suffix("")),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def clean_event_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    replacements = {
        "Butter ly": "Butterfly",
    }
    for src, dst in replacements.items():
        name = name.replace(src, dst)
    return name


def should_skip_event(event_name: str) -> bool:
    normalized_name = event_name.lower()
    return (
        "freestyle" in normalized_name
        and re.search(r"\b(?:500|800|1000|1500|1650)\b", normalized_name) is not None
    )


def parse_events(report_text: str) -> ParseResult:
    session_number: int | None = None
    events: list[Event] = []
    skipped_events: list[Event] = []

    for raw_line in report_text.splitlines():
        line = raw_line.rstrip()
        session_match = re.search(r"Session:\s*(\d+)\b", line)
        if session_match:
            session_number = int(session_match.group(1))
            continue

        parsed_event = parse_event_line(line)
        if parsed_event is None or session_number is None:
            continue

        event_number, raw_event_name, heats = parsed_event
        event_name = clean_event_name(raw_event_name)
        event = Event(
            session_number=session_number,
            event_number=event_number,
            event_name=event_name,
            heats=heats,
        )
        if should_skip_event(event_name):
            skipped_events.append(event)
            continue
        events.append(event)

    if not events:
        raise RuntimeError("No events found in session report.")

    return ParseResult(events=events, skipped_events=skipped_events)


def tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)




def build_summary_page(events: list[Event], skipped_events: list[Event]) -> str:
    lines = [
        r"\clearpage",
        r"\newgeometry{top=0.8in,bottom=0.8in,left=0.7in,right=0.7in}",
        r"\pagestyle{plain}",
        r"\vspace*{0.3in}",
        r"\section*{Generation Summary}",
        rf"Generated events: {len(events)}\\",
        rf"Skipped long-distance freestyle events: {len(skipped_events)}\\",
        r"\textit{Note: Total heats may not be accurate if the session report is a pre-scratch session report.}\\",
        r"\subsection*{Generated Events}",
        r"\begin{multicols}{2}",
        r"\begin{itemize}",
    ]

    for event in events:
        lines.append(
            rf"  \item S{event.session_number} E{event.event_number}: {tex_escape(event.event_name)} (Heats: {event.heats})"
        )

    lines.extend([
        r"\end{itemize}",
        r"\end{multicols}",
    ])

    if skipped_events:
        lines.extend([
            r"\subsection*{Skipped Long-Distance Freestyle Events}",
            r"\begin{itemize}",
        ])
        for event in skipped_events:
            lines.append(
                rf"  \item S{event.session_number} E{event.event_number}: {tex_escape(event.event_name)} (Heats: {event.heats})"
            )
        lines.append(r"\end{itemize}")
    else:
        lines.append(r"\subsection*{Skipped Long-Distance Freestyle Events}")
        lines.append(r"None.")

    lines.extend([
        r"\vspace*{\fill}",
        r"\restoregeometry",
        r"\pagestyle{empty}",
        r"\clearpage",
    ])

    return "\n".join(lines)

def build_tex(events: list[Event], skipped_events: list[Event], template_image: Path) -> str:
    pages: list[str] = []
    image_path = template_image.as_posix()

    for event in events:
        pages.append(
            "\n".join(
                [
                    r"\null",
                    r"\begin{tikzpicture}[remember picture,overlay]",
                    rf"  \node[anchor=south west,inner sep=0] at (current page.south west) {{\includegraphics[width=\paperwidth,height=\paperheight]{{{image_path}}}}};",
                    rf"    \node[anchor=west,font=\bfseries\fontsize{{16}}{{18}}\selectfont] at ([xshift={SESSION_X}in,yshift={SESSION_Y}in]current page.south west) {{{event.session_number}}};",
                    rf"    \node[anchor=west,font=\bfseries\fontsize{{16}}{{18}}\selectfont] at ([xshift={EVENT_NO_X}in,yshift={EVENT_NO_Y}in]current page.south west) {{{event.event_number}}};",
                    rf"    \node[anchor=west,text width=5.6in,align=left,font=\bfseries\fontsize{{{EVENT_NAME_FONT[0]}}}{{{EVENT_NAME_FONT[1]}}}\selectfont] at ([xshift={EVENT_NAME_X}in,yshift={EVENT_NAME_Y}in]current page.south west) {{{tex_escape(event.event_name)}}};",
                    rf"    \node[anchor=east,font=\bfseries\fontsize{{{EVENT_NAME_FONT[0]}}}{{{EVENT_NAME_FONT[1]}}}\selectfont] at ([xshift={TOTAL_HEATS_X}in,yshift={EVENT_NAME_Y}in]current page.south west) {{Total Heats: {event.heats}}};",
                    r"\end{tikzpicture}",
                    r"\newpage",
                ]
            )
        )

    return "\n".join(
        [
            r"\documentclass[letterpaper,landscape]{article}",
            r"\usepackage[margin=0in,landscape]{geometry}",
            r"\usepackage{graphicx}",
            r"\usepackage{tikz}",
            r"\usepackage{grffile}",
            r"\usepackage{multicol}",
            r"\pagestyle{empty}",
            r"\begin{document}",
            build_summary_page(events, skipped_events),
            *pages,
            r"\end{document}",
        ]
    )


def compile_pdf(tex_path: Path) -> None:
    command = [
        "pdflatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        tex_path.name,
    ]
    for _ in range(2):
        subprocess.run(
            command,
            check=True,
            cwd=tex_path.parent,
            capture_output=True,
            text=True,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate prefilled order-of-finish forms from a meet session report."
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("session_report.pdf"),
        help="Path to the meet session report PDF.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent / "templates" / "OOF_template_one_event_per_page.pdf",
        help="Path to the order-of-finish template PDF.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("prefilled_order_of_finish.pdf"),
        help="Output PDF path.",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=None,
        help="Directory for intermediate TeX and template image files. Defaults to a temporary directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_pdf = args.report.resolve()
    template_pdf = args.template.resolve()
    output_pdf = args.output.resolve()
    temp_workdir: tempfile.TemporaryDirectory[str] | None = None
    if args.workdir is None:
        temp_workdir = tempfile.TemporaryDirectory(prefix=f"{output_pdf.stem}_")
        workdir = Path(temp_workdir.name)
    else:
        workdir = args.workdir.resolve()

    if not report_pdf.exists():
        raise FileNotFoundError(f"Session report not found: {report_pdf}")
    if not template_pdf.exists():
        raise FileNotFoundError(f"Template PDF not found: {template_pdf}")
    try:
        workdir.mkdir(parents=True, exist_ok=True)

        output_tex = workdir / f"{output_pdf.stem}.tex"
        template_image = workdir / f"{template_pdf.stem}_template.png"

        report_text = run_pdftotext(report_pdf)
        parse_result = parse_events(report_text)
        ensure_template_image(template_pdf, template_image)
        tex_source = build_tex(parse_result.events, parse_result.skipped_events, template_image)
        output_tex.write_text(tex_source, encoding="utf-8")
        compile_pdf(output_tex)

        compiled_pdf = output_tex.with_suffix(".pdf")
        if not compiled_pdf.exists():
            raise RuntimeError("Expected output PDF was not created.")

        if compiled_pdf != output_pdf:
            output_pdf.write_bytes(compiled_pdf.read_bytes())

        print(f"Generated {output_pdf} with {len(parse_result.events)} event pages plus 1 summary page.")
    finally:
        if temp_workdir is not None:
            temp_workdir.cleanup()


if __name__ == "__main__":
    main()
