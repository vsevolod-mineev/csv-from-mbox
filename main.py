#usr/bin/python3.9
import re
import csv
import mailbox
from pathlib import Path

class csv_from_mbox(object):

    def __init__(self):
        print("\nWelcome to csv from mbox!")

    def get_from_header(self,path_to_mbox):
        mbox_path=Path(path_to_mbox)
        file_to_store_fields_path='./output/mail_addresses_from_mbox.txt'
        mbox = mailbox.mbox(mbox_path)
        file=open(file_to_store_fields_path,'a')
        for message in mbox:
            # Print the senders for check
            file.write(str(message['from'])+'\n')

    def get_email_from_mbox(self,path_to_mbox):
        self.get_from_header(path_to_mbox)
        #Oper the file with the From Field from the Mailbox
        file_in=open('output/mail_addresses_from_mbox.txt','r')
        #Read the file and store it in a string
        addresses_lines=file_in.read()
        # Find all the email addresses inside and store it into a list
        address_list=re.findall('\S+@\S+',addresses_lines)
        # Create a set for avoid duplicates
        address_set=set()
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
            address_set.add(address_elem)
        return address_set

    def main(self):
        path_to_mbox = input("\nPaste the path to the mbox file:\n")
        address_set = self.get_email_from_mbox(path_to_mbox)
        with open('./output/emails.csv', 'w') as f:
            write = csv.writer(f)
            for address in address_set:
                write.writerow([address])

def entrypoint():
    main = csv_from_mbox()
    main.main()

if __name__ == "__main__":
    entrypoint()