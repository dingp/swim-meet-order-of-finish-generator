#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from session_report_parser import parse_event_line


PAGE_LAYOUTS = {
    "front": {
        "template_page": 1,
        "slots": [
            {
                "session_x": 1.28,
                "session_y": 9.87,
                "event_no_x": 2.78,
                "event_no_y": 9.87,
                "event_name_x": 4.88,
                "event_name_y": 9.84,
                "event_name_width": None,
                "total_heats_x": 7.18,
                "total_heats_y": 6.31,
            },
            {
                "session_x": 1.28,
                "session_y": 4.56,
                "event_no_x": 2.78,
                "event_no_y": 4.56,
                "event_name_x": 4.88,
                "event_name_y": 4.51,
                "event_name_width": None,
                "total_heats_x": 7.18,
                "total_heats_y": 1.00,
            },
        ],
    },
    "continuation": {
        "template_page": 2,
        "slots": [
            {
                "session_x": 1.28,
                "session_y": 9.87,
                "event_no_x": 2.64,
                "event_no_y": 9.87,
                "event_name_x": 4.75,
                "event_name_y": 9.84,
                "event_name_width": 2.00,
                "total_heats_x": None,
                "total_heats_y": None,
            },
            {
                "session_x": 1.28,
                "session_y": 4.56,
                "event_no_x": 2.64,
                "event_no_y": 4.44,
                "event_name_x": 4.75,
                "event_name_y": 4.44,
                "event_name_width": 2.00,
                "total_heats_x": None,
                "total_heats_y": None,
            },
        ],
    },
}

HEADER_FONT = (16, 18)
EVENT_NAME_FONT = (16, 19)
TOTAL_HEATS_FONT = (16, 19)


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


def ensure_template_images(template_pdf: Path, workdir: Path) -> dict[int, Path]:
    required_pages = sorted({layout["template_page"] for layout in PAGE_LAYOUTS.values()})
    pdfinfo = subprocess.run(
        ["pdfinfo", str(template_pdf)],
        check=True,
        capture_output=True,
        text=True,
    )
    page_count_match = re.search(r"^Pages:\s+(\d+)\s*$", pdfinfo.stdout, re.MULTILINE)
    if page_count_match is None:
        raise RuntimeError(f"Could not determine page count for template: {template_pdf}")
    available_pages = int(page_count_match.group(1))
    if available_pages < 1:
        raise RuntimeError(f"Template has no pages: {template_pdf}")

    images: dict[int, Path] = {}

    for page_number in required_pages:
        source_page = min(page_number, available_pages)
        image_path = workdir / f"{template_pdf.stem}_template_page_{page_number}.png"
        images[page_number] = image_path
        if image_path.exists():
            continue
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-r",
                "300",
                "-f",
                str(source_page),
                "-l",
                str(source_page),
                "-singlefile",
                str(template_pdf),
                str(image_path.with_suffix("")),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    return images


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


def build_slot_nodes(event: Event | None, slot: dict[str, float | None]) -> list[str]:
    if event is None:
        return []

    nodes = [
        rf"    \node[anchor=west,font=\sffamily\fontsize{{{HEADER_FONT[0]}}}{{{HEADER_FONT[1]}}}\selectfont] at ([xshift={slot['session_x']}in,yshift={slot['session_y']}in]current page.south west) {{{event.session_number}}};",
        rf"    \node[anchor=west,font=\sffamily\fontsize{{{HEADER_FONT[0]}}}{{{HEADER_FONT[1]}}}\selectfont] at ([xshift={slot['event_no_x']}in,yshift={slot['event_no_y']}in]current page.south west) {{{event.event_number}}};",
        (
            rf"    \node[anchor=west,font=\sffamily\fontsize{{{EVENT_NAME_FONT[0]}}}{{{EVENT_NAME_FONT[1]}}}\selectfont] at ([xshift={slot['event_name_x']}in,yshift={slot['event_name_y']}in]current page.south west) {{{tex_escape(event.event_name)}}};"
            if slot['event_name_width'] is None
            else rf"    \node[anchor=west,text width={slot['event_name_width']}in,align=left,font=\sffamily\fontsize{{{EVENT_NAME_FONT[0]}}}{{{EVENT_NAME_FONT[1]}}}\selectfont] at ([xshift={slot['event_name_x']}in,yshift={slot['event_name_y']}in]current page.south west) {{{tex_escape(event.event_name)}}};"
        ),
    ]

    total_heats_x = slot.get("total_heats_x")
    total_heats_y = slot.get("total_heats_y")
    if total_heats_x is not None and total_heats_y is not None:
        nodes.append(
            rf"    \node[anchor=center,font=\sffamily\fontsize{{{TOTAL_HEATS_FONT[0]}}}{{{TOTAL_HEATS_FONT[1]}}}\selectfont] at ([xshift={total_heats_x}in,yshift={total_heats_y}in]current page.south west) {{Total Heats: {event.heats}}};"
        )

    return nodes


def build_page(events: list[Event | None], layout_name: str, template_images: dict[int, Path]) -> str:
    layout = PAGE_LAYOUTS[layout_name]
    image_path = template_images[layout["template_page"]].as_posix()
    nodes = [
        r"\null",
        r"\begin{tikzpicture}[remember picture,overlay]",
        rf"  \node[anchor=south west,inner sep=0] at (current page.south west) {{\includegraphics[width=\paperwidth,height=\paperheight]{{{image_path}}}}};",
        r"  \draw[dash pattern=on 6pt off 4pt,line width=0.6pt,gray] ([xshift=0.25in,yshift=5.5in]current page.south west) -- ([xshift=-0.25in,yshift=5.5in]current page.south east);",
    ]

    for event, slot in zip(events, layout["slots"]):
        nodes.extend(build_slot_nodes(event, slot))

    nodes.extend(
        [
            r"\end{tikzpicture}",
            r"\newpage",
        ]
    )
    return "\n".join(nodes)




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

def build_tex(events: list[Event], skipped_events: list[Event], template_images: dict[int, Path]) -> str:
    pages: list[str] = []

    for index in range(0, len(events), 2):
        pair = events[index:index + 2]
        page_events: list[Event | None] = [pair[0], pair[1] if len(pair) > 1 else None]
        pages.append(build_page(page_events, "front", template_images))

        if any(event is not None and event.heats > 20 for event in page_events):
            continuation_events = [
                event if event is not None and event.heats > 20 else None
                for event in page_events
            ]
            pages.append(build_page(continuation_events, "continuation", template_images))

    return "\n".join(
        [
            r"\documentclass[letterpaper]{article}",
            r"\usepackage[margin=0in]{geometry}",
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
        default=Path(__file__).resolve().parent / "templates" / "OOF_template_two_events_per_page.pdf",
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
    if template_pdf.suffix.lower() != ".pdf":
        raise ValueError("This generator currently supports PDF templates only.")
    if output_pdf.suffix.lower() != ".pdf":
        raise ValueError("Output path must be a .pdf file.")
    try:
        workdir.mkdir(parents=True, exist_ok=True)

        output_tex = workdir / f"{output_pdf.stem}.tex"
        report_text = run_pdftotext(report_pdf)
        parse_result = parse_events(report_text)
        template_images = ensure_template_images(template_pdf, workdir)
        tex_source = build_tex(parse_result.events, parse_result.skipped_events, template_images)
        output_tex.write_text(tex_source, encoding="utf-8")
        compile_pdf(output_tex)

        compiled_pdf = output_tex.with_suffix(".pdf")
        if not compiled_pdf.exists():
            raise RuntimeError("Expected output PDF was not created.")

        if compiled_pdf != output_pdf:
            shutil.copyfile(compiled_pdf, output_pdf)

        print(f"Generated {output_pdf} with {len(parse_result.events)} events plus 1 summary page.")
    finally:
        if temp_workdir is not None:
            temp_workdir.cleanup()


if __name__ == "__main__":
    main()
