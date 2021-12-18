# Python script to extract emails from an .mbox file.

Python script for extracting emails contained in the 'from' field of your mailbox from an .mbox file. Install the package using `pip install`, run the script, paste the input directory, paste the output directory -> done.

All the emails that contain one of the following are filtered out: noreply, no-reply, do-not-reply, do_not_reply.

# How to use:
To install `csv-from-mbox` using `pip install`:
```
pip install csv-from-mbox
```

To execute the script enter:
```
csv-from-mbox
```
You'll be prompted to specify the `input path`, for example you could paste:
```
./input/mail.mbox
```
You'll then be prompted to specify the `output path`, for example you could paste:
```
./output/emails.csv
```