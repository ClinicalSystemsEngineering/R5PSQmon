# -*- coding: utf-8 -*-
"""
04/24/17
Version 3 change notes:
Removed emailer for monitoring team and opted to use the webpage ERROR text as the trigger for the monitoring team
Updated error text for idsmailer messages to reflect BIG IP failover active or queue not processing

11/15/16
Version 2 change notes:
original version was run from a "watcher" machine
this version is meant to be run from the actual paging server
it will check the q value of the local service and update the r5pagemonitor website that is monitored by the load balancer
If the q reaches an unacceptable limit, currently 60, the load balancer should sever the connection and bounce
the connection to the next available server.  The script will also send an email when this happens to groupidsnursecall@cshs.org
In the event that the queue is not processing since the last check an email will be sent to the monitoring to to open a ticket for idsnursecall.
The q value is written to a database for historical record. 

Created on Mon Dec 21 16:17:52 2015

@author: clinicalsystemsengineering@gmail.com
"""


import pycurl
import pymysql
import socket
import smtplib
from io import BytesIO
from email.mime.text import MIMEText

#parses the q value from the given server address and returns the value of the q or -1 if connection issue
def serverchecker(serveraddress):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, serveraddress)
    c.setopt(c.WRITEDATA, buffer)
    #c.setopt(c.VERBOSE, True)
    try: c.perform() 
    except:
        c.close()
        #print("connection issue on " + serveraddress)
        return(-1)
        pass
   
    c.close() 
    body = buffer.getvalue()
# Body is a byte string.
# We have to know the encoding in order to print it to a text file
# such as standard output.
    pageserverhtml = body.decode('iso-8859-1')
#print(pageserverhtml)
    lhs,rhs = pageserverhtml.split("Pages in queue:",1)
    queuecount,leftover = rhs.split("<br",1)
    return(int(queuecount))

def monitoremailer(message):
    pageservername = socket.gethostname()
    msg = MIMEText(message)
    msg['Subject'] = message
    msg['From'] = pageservername + "@yoursite.org"#address of the from server
    msg['To'] = "monitoredmailbox@yoursite.org"#address of the monitoring service
    s= smtplib.SMTP('emailgateway.yoursite.org')#email gateway
    s.send_message(msg)
    s.quit()
    return(1)
    
def supportteamemailer(message):
    pageservername = socket.gethostname()
    msg = MIMEText(message)
    msg['Subject'] = message
    msg['From'] = pageservername + "@yoursite.org"#address of the from server
    msg['To'] = "supportteammailbox@yoursite.org"#address of the support team
    s= smtplib.SMTP('emailgateway.yoursite.org')#email gateway
    s.send_message(msg)
    s.quit()
    return(1)    

#gets the page server hostname for database recording
pageservername = socket.gethostname()
#the page server address
pageserver = "http://"+pageservername+".yoursite.org:5051/"#address of the local paging server

#set the acceptable limit for the queue.  Note: Currently r5 processes msgs at approx 38msgs/min
acceptablelimit = 60

#get the q value using the serverchecker function
q = serverchecker(pageserver)

#open the default page of the website r5pagemonitor for editing
monitorpage = open("C:/inetpub/wwwroot/r5pagemonitor/Default.htm","w")#the monitoring page

#read the last q value from file and write the current q value back to file
lastqvalfile = open("lastqval.txt","r")
lastqvalfile.seek(0)
lastqvalstr = lastqvalfile.readline()
lastqvalfile.close()
lastqvalfile = open("lastqval.txt","w")
lastqvalfile.seek(0)
lastqvalfile.write(str(q))
lastqvalfile.truncate()
lastqvalfile.close()

#last q value for comparison
lastqval = int(lastqvalstr.strip())

   
if q < 0:
    #case where the paging service is down
    print(pageserver + " connection issue" )
    #write webpage serice unavailable
    monitorpage.seek(0)
    monitorpage.write("<html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Service is Down</body></html>")
    monitorpage.truncate()
    monitorpage.close()
    
elif q >= acceptablelimit:
    #case where the queue is above acceptable value
    if((q >= lastqval) and (lastqval >= acceptablelimit)):
        #if the queue is above acceptable value and it has not reduced since last check then open a ticket to resolve
        print(pageserver + " over maximum queue allowed, and queue is not processing correctly. Emailing monitoring team to open ticket with Q value: " + str(q))
    #write webpage q overload    
        monitorpage.seek(0)
        monitorpage.write("<html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Q hung with value: " + str(q) + "</body></html>")
        monitorpage.truncate()
        monitorpage.close()
    #email the ids team about the Q overload and not processing
        supporteamemailer("ERROR: Paging Q hung with value: " + str(q) + " on server " + pageservername+".   This node does not seem to be processing the Queue. Please investigate the digi connections.")
    else:
    #the queue was above acceptable value, but is still being processed correctly notify idsnursecall because the network will be switching automatically
        print(pageserver + " over maximum queue allowed. Emailing ids team and failing over with q value: " + str(q))
    #write webpage q overload    
        monitorpage.seek(0)
        monitorpage.write("<html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Q overloaded with value: " + str(q) + "</body></html>")
        monitorpage.truncate()
        monitorpage.close()
    #email the idsnursecall team about the Q overload       
        supportteamemailer("ERROR: Paging Q overloaded with value: " + str(q) + " on server " + pageservername+". BIG IP automatic failover active.")
	
else:
    print(pageserver + " OK current Q value: "+str(q))
     #write the current q value webpage
    monitorpage.seek(0)
    monitorpage.write("<html><header><title>R5 Page Q Monitor</title></header><body>OK: Paging Q value: " + str(q) + "</body></html>")
    monitorpage.truncate()
    monitorpage.close()


#write current q value to mysql db for historical record
#db will need the following:
#tablename = r5psq
#Column definitions:
#ID int(11)
#ServerName varchar(45)
#QValue int(11)
#timestamp datetime default value of CURRENT_TIMESTAMP

conn = pymysql.connect(host='mysqlserver.yoursite.org',port=3306,user='username',passwd='password',db='dbname')#databse connection for logging historical values
cur = conn.cursor()
insertstring = "INSERT INTO r5psq (ServerName,Qvalue) VALUES (\""+pageservername+"\","+str(q)+")"
cur.execute(insertstring)
conn.commit()
conn.close()