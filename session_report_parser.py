from __future__ import annotations

import re


EVENT_PREFIX = re.compile(r"^(?P<round>\S+)\s+(?P<event_number>\d+)\s+(?P<remainder>.+?)\s*$")
TIME_COLUMN = re.compile(r"^\d{1,2}:\d{2}\s+[AP]M$")
NUMERIC_COLUMN = re.compile(r"^(?P<value>\d+)(?:\s+u)?$")
UNDERSCORE_COLUMN = re.compile(r"^_+$")


def parse_event_line(line: str) -> tuple[int, str, int] | None:
    match = EVENT_PREFIX.match(line.strip())
    if match is None:
        return None

    columns = [column.strip() for column in re.split(r"\s{2,}", match.group("remainder")) if column.strip()]
    if not columns:
        return None

    event_name = columns[0]
    heats = extract_heats(columns[1:])
    if heats is None:
        return None

    return int(match.group("event_number")), event_name, heats


def extract_heats(columns: list[str]) -> int | None:
    if not columns:
        return None

    time_index = next((index for index, column in enumerate(columns) if TIME_COLUMN.match(column)), None)
    if time_index is None:
        candidate_columns = columns
    else:
        candidate_columns = columns[:time_index]

    heats = extract_heats_from_columns(candidate_columns)
    if heats is not None:
        return heats

    if time_index is None:
        return None

    # Some exports move the standalone "u" after the start time or reorder filler columns.
    fallback_columns = [
        column
        for column in columns
        if not TIME_COLUMN.match(column) and not UNDERSCORE_COLUMN.match(column) and column.lower() != "u"
    ]
    return extract_heats_from_columns(fallback_columns)


def extract_heats_from_columns(columns: list[str]) -> int | None:
    numeric_values: list[int] = []

    for column in columns:
        if UNDERSCORE_COLUMN.match(column) or column.lower() == "u":
            continue

        match = NUMERIC_COLUMN.match(column)
        if match is not None:
            numeric_values.append(int(match.group("value")))

    if len(numeric_values) >= 2:
        return numeric_values[1]
    if len(numeric_values) == 1:
        return numeric_values[0]
    return None
