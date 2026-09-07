# csv-from-mbox

Turn an `.mbox` export into a CSV you can actually open in a spreadsheet.

You know the drill: Google Takeout hands you a two-gigabyte `All mail Including Spam and Trash.mbox`, and every tool that can open it wants to be an email client about it. This one does not. One Python file, standard library only, two modes, done.

## What it does

**Messages mode (default):** one row per email.

| date | from_name | from_email | to | cc | subject | body |
|------|-----------|------------|----|----|---------|------|
| 2026-08-28T10:00:00+01:00 | Ash Ketchum | ash@pallet.town | misty@cerulean.gym | | Gym battle | I choose you! |

Bodies prefer `text/plain`, HTML-only emails get their tags stripped, attachments are ignored, encoded headers (`=?utf-8?q?Pok=C3=A9mon?=`) are decoded, and dates come out ISO 8601 so your spreadsheet sorts them properly.

**Addresses mode (`--addresses`):** the original party trick. Every unique sender address, lowercased, deduplicated and sorted, with automated senders (noreply, no-reply, do-not-reply, do_not_reply, donotreply) filtered out. Great for finding out who actually writes to you.

## Install

Run it straight from GitHub with [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/):

```sh
uvx --from git+https://github.com/vsevolod-mineev/csv-from-mbox csv-from-mbox mail.mbox
pipx run --spec git+https://github.com/vsevolod-mineev/csv-from-mbox csv-from-mbox mail.mbox
```

Or clone it and run the file, there are no dependencies to install:

```sh
python3 csv_from_mbox.py mail.mbox
```

`pip install csv-from-mbox` also exists, but PyPI currently carries the 2021-era 0.4.5; use the GitHub version until 0.5.0 lands there.

## Use

```sh
csv-from-mbox mail.mbox                # messages.csv with everything
csv-from-mbox mail.mbox --no-body      # metadata only, much smaller file
csv-from-mbox mail.mbox --addresses    # emails.csv with unique senders
csv-from-mbox mail.mbox -o ~/Desktop   # choose where it goes
csv-from-mbox                          # no arguments? it will ask nicely
```

## Test

```sh
python3 -m unittest discover tests
```

## Requirements

Python 3.9 or newer. Nothing else. That is the whole point.

## License

[MIT](LICENSE.md).
