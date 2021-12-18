
import re
import csv

class csv_from_mbox(object):

    def __init__(self):
        print("\nWelcome to csv from mbox!")

    def get_email_from_mbox(self):
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
        address_set = self.get_email_from_mbox()
        with open('./output/emails', 'w') as f:
            write = csv.writer(f)
            for address in address_set:
                write.writerow([address])
    
if __name__ == "__main__":
    main = csv_from_mbox()
    main.main()