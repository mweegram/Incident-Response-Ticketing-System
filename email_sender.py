import smtplib
from email.message import EmailMessage
import random

addr = '' #Your email address to monitor - CHANGE ME
password = '' #Mail account password - Change ME


emails = (
    ("1 - INC1 - Multiple SSH Failures at 192.167.1.12","Host:192.167.1.12,Account:root"),
    ("1 - INC2 - Password Brute Force Attempts at 192.10.1.101","Host:192.10.101,Account:admin"),
    ("1 - INC3 - Impossible Travel Activity","Account:Michael,IP:176.10.1.13,Country:Nigeria")
)

def SendEmail(subject,body):
    message = EmailMessage()
    message.set_content(body)
    message['From'] = addr
    message['To'] = addr
    message['Subject'] = subject

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(addr,password)


    server.send_message(message)

selection = random.choice(emails)
SendEmail(selection[0],selection[1])