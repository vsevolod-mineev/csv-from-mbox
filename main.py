#usr/bin/python3.9
import re
import csv
import mailbox
from pathlib import Path

class csv_from_mbox(object):

    def __init__(self, input_path, output_path = "./output/emails.csv" ):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)

    def get_from_headers(self):
        mbox = mailbox.mbox(self.input_path)
        from_str = str()
        for message in mbox:
            from_str = from_str + str(message['from']) + '\n'
        return from_str

    def get_emails_from_mbox(self, from_fields):
        address_list=re.findall('\S+@\S+',from_fields)
        email_set=set()
        for address_elem in address_list:
            if "noreply" in address_elem:
                continue
            if "no-reply" in address_elem:
                continue
            if "do_not_reply" in address_elem:
                continue
            if "do-not-reply" in address_elem:
                continue
            address_elem=address_elem[1:-1]
            email_set.add(address_elem)
        return email_set

    def save_as_csv(self, emails):
        with open(self.output_path, 'w') as f:
            write = csv.writer(f,delimiter=',')
            write.writerow(['email'])
            for email in emails:
                write.writerow([email])

def main():
    print("\nWelcome to csv from mbox!")
    input_path = input("\nPaste the path to the mbox file:\n")
    output_path = input("\nOutput directory for extracted emails:\n")
    cfm = csv_from_mbox(input_path, output_path)
    print("\nLoading the 'from' fields of your emails from mbox...\n")
    from_fields = cfm.get_from_headers()
    print("\nSaving email addresses into csv.\n")
    emails = cfm.get_emails_from_mbox(from_fields)
    cfm.save_as_csv(emails)
    print("\nThank you!\n")

if __name__ == "__main__":
    main()