
import re
import csv

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

# IF YOU WANT TO STORE ALL THE ADDRESSES IN COLUMN UNCOMMENT THIS PART
# clean_addresses=open('final_addresses.txt','a')

# for elem in address_set:
#     clean_addresses.write(elem+'\n')

# clean_addresses.close()

# Open a file in the .vcf standard


#v_card=open('contacts.vcf','a')

# Store every address in a vCard Standard file with all the addresses
#for address in address_set:
#    v_card.write("BEGIN:VCARD\nVERSION:3.0\nN:;;;;\nFN:\nEMAIL;TYPE=INTERNET;TYPE=WORK:"+address+"\n"+"END:VCARD\n") 
#v_card.close()
with open('./output/emails', 'w') as f:
    write = csv.writer(f)
    for address in address_set:
        write.writerow([address])
    
