import mailbox

#WARNING:Check the right path for your .mbox file, in Mac OS Environment the .mbox is a directory so you can navigate it
# the .box files could be very heavy also!

mbox_path='mail.mbox' 
file_to_store_fields_path='mail_addresses_from_mbox.txt'

mbox = mailbox.mbox(mbox_path)

file=open(file_to_store_fields_path,'a')
 

for message in mbox:
    # Print the senders for check
    print (message['from']+'\n')
    file.write(message['from']+'\n')