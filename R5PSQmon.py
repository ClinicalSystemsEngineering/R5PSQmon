# -*- coding: utf-8 -*-


import requests
import pymysql
import socket
import smtplib
from io import BytesIO
from email.mime.text import MIMEText

#parses the q value from the given server address and returns the value of the q or -1 if connection issue
def serverchecker(serveraddress):
    buffer = BytesIO()
    try: r = requests.get(serveraddress)
    except:
        r.close()
        return(-1)
        pass
   
    r.close() 
#body = r.text
# Body is a byte string.
# We have to know the encoding in order to print it to a text file
# such as standard output.
    pageserverhtml = r.text
#print(pageserverhtml)
   
    lhs,rhs = pageserverhtml.split("Pages in queue:",1)
    queuecount,leftover = rhs.split("<br",1)
    return(int(queuecount))

def monitoremailer(message):
    pageservername = socket.gethostname()
    msg = MIMEText(message)
    msg['Subject'] = message
    msg['From'] = pageservername + "@your domain"
    msg['To'] = "your monitoring mailbox address"
    s= smtplib.SMTP('your smtp server address')
    s.send_message(msg)
    s.quit()
    return(1)
    

def diemailer(message):
    pageservername = socket.gethostname()
    msg = MIMEText(message)
    msg['Subject'] = message
    msg['From'] = pageservername + "@your domain"
    msg['To'] = "your support team email address"
    s= smtplib.SMTP('your smpt server address')
    s.send_message(msg)
    s.quit()
    return(1) 

#gets the page server hostname for database recording
pageservername = socket.gethostname()
#the page server address for r5 standard
#pageserver = "http://"+pageservername+".your domain:5051/"
#for xml2tap
pageserver = "http://"+pageservername+".your domain:8080/status"


#set the acceptable limit for the queue.  Note: Currently r5 processes msgs at approx 38msgs/min
acceptablelimit = 100
#acceptable limit for xml2tap is 100

#get the q value using the serverchecker function
q = serverchecker(pageserver)



#open the default page of the website r5pagemonitor for editing
monitorpage = open("C:/inetpub/wwwroot/r5pagemonitor/Default.htm","w")
hungqpage = open("C:/inetpub/wwwroot/r5pagemonitor/hungqstate.htm","w")

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
    monitorpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Service is Down</body></html>")
    monitorpage.truncate()
    monitorpage.close()
      
    
elif q >= acceptablelimit:
    #case where the queue is above acceptable value
    if((q >= lastqval) and (lastqval >= acceptablelimit)):
        #if the queue is above acceptable value and it has not reduced since last check then open a ticket to resolve
        print(pageserver + " over maximum queue allowed, and queue is not processing correctly. Emailing monitoring team to open ticket with Q value: " + str(q))
    
    #write webpage q overload    
        monitorpage.seek(0)
        monitorpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Q hung with value: " + str(q) + "</body></html>")
        monitorpage.truncate()
        monitorpage.close()
    
    #write hungqstate webpage state
        hungqpage.seek(0)
        hungqpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Q hung with value: " + str(q) + "</body></html>")
        hungqpage.truncate()
        hungqpage.close()
        
    #email the ids team about the Q overload and not processing
        diemailer("ERROR: Paging Q hung with value: " + str(q) + " on server " + pageservername+".   This node does not seem to be processing the Queue. Please investigate the digi connections.")
    
    else:
    #the queue was above acceptable value, but is still being processed correctly notify idsnursecall because the network will be switching automatically
        print(pageserver + " over maximum queue allowed. Emailing ids team and failing over with q value: " + str(q))
    #write webpage q overload    
        monitorpage.seek(0)
        monitorpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>ERROR: Paging Q overloaded with value: " + str(q) + "</body></html>")
        monitorpage.truncate()
        monitorpage.close()

    #write hungqstate webpage state
        hungqpage.seek(0)
        hungqpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>OK: Paging Q overloaded with value: " + str(q) + "</body></html>")
        hungqpage.truncate()
        hungqpage.close()
    #email the idsnursecall team about the Q overload       
        diemailer("ERROR: Paging Q overloaded with value: " + str(q) + " on server " + pageservername+". BIG IP automatic failover active.")
	
else:
    print(pageserver + " OK current Q value: "+str(q))
     #write the current q value webpage
    monitorpage.seek(0)
    monitorpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>OK: Paging Q value: " + str(q) + "</body></html>")
    monitorpage.truncate()
    monitorpage.close()
    #write hungstate q webpage state
    hungqpage.seek(0)
    hungqpage.write("<!DOCTYPE html><html><header><title>R5 Page Q Monitor</title></header><body>OK: Paging Q value: " + str(q) + "</body></html>")
    hungqpage.truncate()
    hungqpage.close()
    

#write current q value to db for historical record
conn = pymysql.connect(host='mysql server address',port=3306,user='db username',passwd='db password',db='db name')
cur = conn.cursor()
insertstring = "INSERT INTO r5psq (ServerName,Qvalue) VALUES (\""+pageservername+"\","+str(q)+")"
cur.execute(insertstring)
conn.commit()
conn.close()
