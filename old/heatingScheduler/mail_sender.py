#!/usr/bin/python
# Import smtplib for the actual sending function
import smtplib
sender = 'smarthome@server'
receivers = ['admin@example.com']


def sendMail(msg): 
	message = """From: SmartHome <smarthome@server>
To: Admin <admin@example.com>
Subject: Thermo status report

%s
""" % msg

   	smtpObj = smtplib.SMTP('mailserver.example.com')
   	smtpObj.sendmail(sender, receivers, message)         
   	print "Successfully sent email"
