import imaplib
import email
import database_methods
import re

#Credentials - INSERT YOUR OWN HERE!!!
email_address = ''
password = ''
#The email address to check for to generate tickets from
target_email = ''

#Takes a string, checks if for VALID email addresses, then returns a list of them should it find any. Otherwise it returns an empty list
def EmailRegex(testcase):
    return re.findall(r'[A-z0-9!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&\'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?',testcase)

def IPRegex(testcase):
    #Takes a string, checks if for IP addresses, then returns a list of them should it find any. Otherwise it returns an empty list
    results = re.findall(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',testcase)
    for index,result in enumerate(results):
        #Split each of the results of the regex at the . to get the seperate octets of the IP addresses
        octets = result.split('.')
        #Perform a check to see if each octet is valid, if it isn't remove the result from the results list
        for value in octets:
            if(int(value) > 255):
                results.pop(index)
                break
    
    #return all valid IP addresses 
    if(results):
        return results
    else:
        return []

#Takes a string, checks if for VALID mac addresses, then returns a list of them should it find any. Otherwise it returns an empty list
def MACRegex(testcase):
    return re.findall(r'((?:[\da-fA-F]{2}[:\-]){5}[\da-fA-F]{2})',testcase)

def CheckForKeyinfo(title,body):
    #Create an empty list, ready to hold any key information values
    results = []
        #Each of the pieces of information in the email should be comma seperated. This helps to break down the information line by line but the code would work either way
    lines = body.split(",")
    #adds the title to the lines list, so that it can be checked for key information. Inserted in position 0 (start).
    lines.insert(0,title)
    for line in lines:
        #This line runs each of the regexes created above, unpacks (*) any results and generates a list of all of the results.
        matches = *EmailRegex(line),*IPRegex(line),*MACRegex(line)

        #Checks if any matches were found at all, if none then return False
        if(matches):
            for match in matches:
                #Checks that match is not blank, regexes that find nothing return blank lists. Also checks for duplicates and stops them being added again.
                if(match and match not in results):
                    results.append(match)
    if not(results):
        return False
    
    return results

#Takes a integer, checks if a ticket queue exists
def check_queue_exists(queueid):
    db,cur = database_methods.db_connection()
    #if a queue is found with the id, return true else false
    if(cur.execute(f'SELECT 1 FROM queue WHERE id = {queueid}').fetchone()):
        return True
    
    return False

def MailRead(Mail):
    #For each email in the list that has been passed in
    for id in Mail[0].split():
        #Fetch mail, using RFC822 format for emails
        result,data = mail.fetch(id,"(RFC822)")
        #fetch the email body from the data returned by the fetch, ignoring uneccessary metadata
        message = email.message_from_bytes(data[0][1])
        
        #Get the email Subject
        title = message.get("Subject")

        #Fetch the body/message of the email and decode it into UTF-8
        body = message.get_payload(decode=True).decode('utf-8')

        #Generate the ticket, get the new tickets id as a return value
        ticket_id = GenerateTicket(title,body)

        #Search for key information, add any key information found to the database
        database_methods.auto_key_info(ticket_id,CheckForKeyinfo(title,body))


def GenerateTicket(title,body):
    queue = 1
    #Take the number from before the first hyphen, this is used to indicate the queue id, remove wany whitespace
    if("-" in title):
        queue = title.split("-")[0].strip()
        #Generate the true title, removing the queue ID as that has no value once the ticket is made
        title = "".join(title.split("-")[1:]).strip()
    
    #if a queue is specified but doesn't exist, set to default as 1, as one always exists
    if not(check_queue_exists(queue)):
        queue = 1
    
    #Generate a ticket based on the information of the email, with the name of ticket being the title of email, the content of the ticket being the email body, the status as new and the owner as Nobody, a predefined user in the database.
    database_methods.generate_email_ticket(title,queue,body,1,"New")
    #return the id of the ticket so it can be used to find any key info contained inside of it.
    return database_methods.find_email_ticket(title,body)



#Connects to gmail's IMAP server with SSL Encryption
mail = imaplib.IMAP4_SSL('imap.gmail.com')
#Login to account using supplied credentials
mail.login(email_address,password)

#Select mail only from the Inbox
mail.select('inbox')

#Search for mail from the target email address, that hasn't been seen yet.
result,data=mail.search(None,f'(FROM "{target_email}" UNSEEN)')

#Try to read emails from the target email address, if it fails generate a log file (if it doesn't exist) and write the error to it.
    #Process all emails that were found that were unread
MailRead(data)

