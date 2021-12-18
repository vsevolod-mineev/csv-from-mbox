#usr/bin/python3.9
import re
import csv
import mailbox
from pathlib import Path

class csv_from_mbox(object):

    def __init__(self):
        print("\nWelcome to csv from mbox!")

    def get_from_headers(self,path_to_mbox):
        mbox_path=Path(path_to_mbox)
        mbox = mailbox.mbox(mbox_path)
        from_str = str()
        for message in mbox:
            # Print the senders for check
            from_str = from_str + str(message['from'])+ '\n'
        return from_str

    def get_emails_from_mbox(self,from_fields):
        #Read the file and store it in a string 
        # Find all the email addresses inside and store it into a list
        address_list=re.findall('\S+@\S+',from_fields)
        # Create a set for avoid duplicates
        email_set=set()
        # For every email address
        for address_elem in address_list:
            # Remove no-reply addresses
            if "noreply" in address_elem:
                continue
            if "no-reply" in address_elem:
                continue
            if "do_not_reply" in address_elem:
                continue
            if "do-not-reply" in address_elem:
                continue
            # Remove the angular parenthesis
            address_elem=address_elem[1:-1]
            # Add the address to the set
            email_set.add(address_elem)
        return email_set

    def save_as_csv(self, emails):
        with open('./output/emails.csv', 'w') as f:
            write = csv.writer(f)
            for email in emails:
                write.writerow([email])

def main():
    path_to_mbox = input("\nPaste the path to the mbox file:\n")
    cfm = csv_from_mbox()
    from_fields = cfm.get_from_headers(path_to_mbox)
    emails = cfm.get_emails_from_mbox(from_fields)
    cfm.save_as_csv(emails)

if __name__ == "__main__":
    main()