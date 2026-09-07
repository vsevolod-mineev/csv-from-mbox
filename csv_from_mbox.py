#!/usr/bin/env python3
"""csv-from-mbox: turn an .mbox export into a CSV you can actually use.

Two modes:
  messages (default)  one row per email: date, from_name, from_email, to, cc,
                      subject, body (text/plain preferred, de-tagged HTML as
                      the fallback)
  --addresses         the classic mode: unique sender addresses, one per row,
                      automated senders (noreply and friends) filtered out

Standard library only. One file. No excuses.
"""

from __future__ import annotations

import argparse
import csv
import html
import mailbox
import re
import sys
from email.header import decode_header, make_header
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Iterator, Optional

__version__ = "0.5.1"

NOREPLY_MARKERS = ("noreply", "no-reply", "do_not_reply", "do-not-reply", "donotreply")

MESSAGE_COLUMNS = ["date", "from_name", "from_email", "to", "cc", "subject", "body"]

_TAG_RE = re.compile(r"<[^>]+>")


def decode_header_value(value: Optional[str]) -> str:
    """Decode RFC 2047 headers ('=?utf-8?q?Pok=C3=A9mon?=') into readable text."""
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value))).strip()
    except Exception:
        return str(value).strip()


def iso_date(value: Optional[str]) -> str:
    """Normalise a Date header to ISO 8601 so spreadsheets sort it properly."""
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        return parsed.isoformat() if parsed else str(value).strip()
    except Exception:
        return str(value).strip()


def _decode_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:  # sender advertised a charset Python has never heard of
        return payload.decode("utf-8", errors="replace")


def extract_body(message: Message) -> str:
    """Prefer text/plain; fall back to de-tagged text/html; skip attachments."""
    plain: Optional[str] = None
    html_part: Optional[str] = None
    for part in message.walk():
        if part.is_multipart() or part.get_content_disposition() == "attachment":
            continue
        content_type = part.get_content_type()
        if content_type == "text/plain" and plain is None:
            plain = _decode_payload(part)
        elif content_type == "text/html" and html_part is None:
            html_part = _decode_payload(part)
    if plain is not None:
        return plain.strip()
    if html_part is not None:
        return html.unescape(_TAG_RE.sub(" ", html_part)).strip()
    return ""


def sender_of(message: Message) -> "tuple[str, str]":
    """Return (display name, address) of the first parseable From address."""
    for name, addr in getaddresses([message.get("From") or ""]):
        if addr:
            return decode_header_value(name), addr.strip()
    return "", ""


def address_list(message: Message, header: str) -> str:
    """All addresses in a header (To, Cc, ...), comma separated."""
    values = message.get_all(header) or []
    return ", ".join(addr for _, addr in getaddresses(values) if addr)


def looks_automated(address: str) -> bool:
    lowered = address.lower()
    return any(marker in lowered for marker in NOREPLY_MARKERS)


def open_mbox(path: Path) -> mailbox.mbox:
    # create=False matters: the default silently creates an empty mailbox for
    # a mistyped path and then cheerfully exports zero rows.
    if not path.is_file():
        raise SystemExit(f"No such mbox file: {path}")
    return mailbox.mbox(path, create=False)


def message_rows(box: mailbox.mbox) -> Iterator["list[str]"]:
    for message in box:
        name, addr = sender_of(message)
        yield [
            iso_date(message.get("Date")),
            name,
            addr,
            address_list(message, "To"),
            address_list(message, "Cc"),
            decode_header_value(message.get("Subject")),
            extract_body(message),
        ]


def unique_senders(box: mailbox.mbox, keep_automated: bool = False) -> "list[str]":
    seen = set()
    for message in box:
        _, addr = sender_of(message)
        if not addr:
            continue
        addr = addr.lower()
        if not keep_automated and looks_automated(addr):
            continue
        seen.add(addr)
    return sorted(seen)


def resolve_output(raw: Optional[str], default_name: str) -> Path:
    path = Path(raw).expanduser() if raw else Path(default_name)
    if path.is_dir():
        path = path / default_name
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write(handle, header: "list[str]", rows: Iterable[Iterable[str]], lineterminator: str) -> int:
    writer = csv.writer(handle, lineterminator=lineterminator)
    writer.writerow(header)
    count = 0
    for row in rows:
        writer.writerow(row)
        count += 1
    return count


def write_csv(path: "Optional[Path]", header: "list[str]", rows: Iterable[Iterable[str]]) -> int:
    """Write rows to a file, or to stdout when path is None (newline-terminated
    for pipe friendliness; files keep the CSV-standard CRLF)."""
    if path is None:
        return _write(sys.stdout, header, rows, "\n")
    with open(path, "w", newline="", encoding="utf-8") as handle:
        return _write(handle, header, rows, "\r\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csv-from-mbox",
        description="Turn an .mbox export (Google Takeout, Thunderbird, mutt...) "
                    "into a CSV of messages, or just the sender addresses.",
    )
    parser.add_argument("mbox", nargs="?", help=".mbox file to read (omit to be prompted)")
    parser.add_argument("-o", "--output",
                        help="output CSV file, a directory to put it in, or - for stdout")
    parser.add_argument("--addresses", action="store_true",
                        help="classic mode: unique sender addresses only")
    parser.add_argument("--no-body", action="store_true",
                        help="messages mode: skip the body column (much smaller file)")
    parser.add_argument("--keep-noreply", action="store_true",
                        help="addresses mode: keep automated senders (noreply and friends)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: "Optional[list[str]]" = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    interactive = args.mbox is None
    if interactive:
        if not sys.stdin.isatty():
            parser.error("no mbox file given")
        # prompts go to stderr so even an interactive run can pipe stdout
        print("\nWelcome to csv from mbox!", file=sys.stderr)
        print("\nPath to the .mbox file:", file=sys.stderr)
        args.mbox = input().strip()
        print("\nWhere to save the CSV (blank for the current directory, - for stdout):",
              file=sys.stderr)
        args.output = input().strip() or None

    to_stdout = args.output == "-"
    box = open_mbox(Path(args.mbox).expanduser())
    try:
        if args.addresses:
            output = None if to_stdout else resolve_output(args.output, "emails.csv")
            senders = unique_senders(box, keep_automated=args.keep_noreply)
            count = write_csv(output, ["email"], ([sender] for sender in senders))
            noun = "address" if count == 1 else "addresses"
        else:
            output = None if to_stdout else resolve_output(args.output, "messages.csv")
            columns = MESSAGE_COLUMNS[:-1] if args.no_body else MESSAGE_COLUMNS
            rows: Iterable["list[str]"] = message_rows(box)
            if args.no_body:
                rows = (row[:-1] for row in rows)
            count = write_csv(output, columns, rows)
            noun = "message" if count == 1 else "messages"
    finally:
        box.close()

    chatter = sys.stderr if to_stdout else sys.stdout
    print(f"Wrote {count} {noun} to {'stdout' if to_stdout else output}", file=chatter)
    if interactive:
        print("\nThank you and happy sorting!\n", file=chatter)


if __name__ == "__main__":
    main()
