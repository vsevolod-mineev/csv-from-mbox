"""Tests for csv_from_mbox. Run from the repo root:

    python3 -m unittest discover tests
"""

from __future__ import annotations

import contextlib
import csv
import io
import mailbox
import sys
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import csv_from_mbox as cfm  # noqa: E402


def build_sample_mbox(path: Path) -> None:
    box = mailbox.mbox(path)

    m1 = EmailMessage()
    m1["From"] = '"Ash Ketchum" <Ash@pallet.town>'
    m1["To"] = "misty@cerulean.gym"
    m1["Cc"] = "brock@pewter.gym"
    m1["Subject"] = "Gym battle"
    m1["Date"] = "Thu, 28 Aug 2026 10:00:00 +0100"
    m1.set_content("I choose you!")
    box.add(m1)

    m2 = EmailMessage()  # bare address, base64 body, RFC 2047 subject
    m2["From"] = "bare@example.com"
    m2["Subject"] = "=?utf-8?q?Pok=C3=A9mon_cards?="
    m2["Date"] = "Thu, 28 Aug 2026 11:00:00 +0100"
    m2.set_content("Bare from header, no angle brackets.", cte="base64")
    box.add(m2)

    m3 = EmailMessage()  # automated sender
    m3["From"] = "Shop <noreply@shop.example>"
    m3["Subject"] = "Your order"
    m3.set_content("Automated mail.")
    box.add(m3)

    m4 = EmailMessage()  # duplicate sender in a different case, HTML-only body
    m4["From"] = "ASH@PALLET.TOWN"
    m4["Subject"] = "duplicate, different case"
    m4.set_content("<p>HTML only body &amp; stuff</p>", subtype="html")
    box.add(m4)

    m5 = EmailMessage()  # multipart with an attachment that must not become the body
    m5["From"] = "=?utf-8?q?Bj=C3=B6rn?= <bjorn@example.se>"
    m5["Subject"] = "With attachment"
    m5.set_content("The real body.")
    m5.add_attachment(b"a,b\n1,2\n", maintype="text", subtype="csv", filename="data.csv")
    box.add(m5)

    box.flush()
    box.close()


def read_csv(path: Path) -> "list[dict]":
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class CsvFromMboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.mbox = self.tmp / "sample.mbox"
        build_sample_mbox(self.mbox)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_main(self, *extra: str) -> Path:
        out = self.tmp / "out.csv"
        cfm.main([str(self.mbox), "-o", str(out), *extra])
        return out

    def test_addresses_mode_dedupes_filters_and_keeps_bare_addresses_intact(self):
        rows = read_csv(self.run_main("--addresses"))
        emails = [row["email"] for row in rows]
        self.assertEqual(emails, ["ash@pallet.town", "bare@example.com", "bjorn@example.se"])

    def test_addresses_mode_keep_noreply(self):
        rows = read_csv(self.run_main("--addresses", "--keep-noreply"))
        self.assertIn("noreply@shop.example", [row["email"] for row in rows])

    def test_messages_mode_exports_every_message(self):
        rows = read_csv(self.run_main())
        self.assertEqual(len(rows), 5)

    def test_messages_mode_decodes_headers_and_dates(self):
        rows = read_csv(self.run_main())
        self.assertEqual(rows[1]["subject"], "Pokémon cards")
        self.assertEqual(rows[1]["from_email"], "bare@example.com")
        self.assertEqual(rows[0]["from_name"], "Ash Ketchum")
        self.assertTrue(rows[0]["date"].startswith("2026-08-28T10:00:00"))
        self.assertEqual(rows[0]["to"], "misty@cerulean.gym")
        self.assertEqual(rows[0]["cc"], "brock@pewter.gym")

    def test_messages_mode_decodes_base64_body(self):
        rows = read_csv(self.run_main())
        self.assertEqual(rows[1]["body"], "Bare from header, no angle brackets.")

    def test_messages_mode_strips_html_fallback(self):
        rows = read_csv(self.run_main())
        self.assertEqual(rows[3]["body"], "HTML only body & stuff")

    def test_messages_mode_ignores_attachments(self):
        rows = read_csv(self.run_main())
        self.assertEqual(rows[4]["body"], "The real body.")
        self.assertEqual(rows[4]["from_name"], "Björn")

    def test_no_body_flag_drops_the_column(self):
        rows = read_csv(self.run_main("--no-body"))
        self.assertNotIn("body", rows[0])
        self.assertEqual(len(rows), 5)

    def test_output_can_be_a_directory(self):
        target = self.tmp / "somewhere"
        target.mkdir()
        cfm.main([str(self.mbox), "-o", str(target)])
        self.assertTrue((target / "messages.csv").is_file())

    def run_main_stdout(self, *extra: str) -> "tuple[str, str]":
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            cfm.main([str(self.mbox), "-o", "-", *extra])
        return out.getvalue(), err.getvalue()

    def test_stdout_mode_streams_clean_csv(self):
        out, err = self.run_main_stdout()
        rows = list(csv.DictReader(io.StringIO(out)))
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["from_email"], "Ash@pallet.town")
        self.assertNotIn("Wrote", out, "chatter must not pollute piped CSV")
        self.assertIn("Wrote 5 messages to stdout", err)
        self.assertNotIn("\r\n", out, "stdout stream should be newline-terminated")

    def test_stdout_mode_addresses(self):
        out, _ = self.run_main_stdout("--addresses")
        rows = list(csv.DictReader(io.StringIO(out)))
        self.assertEqual([row["email"] for row in rows],
                         ["ash@pallet.town", "bare@example.com", "bjorn@example.se"])

    def test_missing_mbox_fails_loudly_instead_of_creating_one(self):
        missing = self.tmp / "nope.mbox"
        with self.assertRaises(SystemExit):
            cfm.main([str(missing), "-o", str(self.tmp / "x.csv")])
        self.assertFalse(missing.exists(), "must not silently create the mailbox")


if __name__ == "__main__":
    unittest.main()
