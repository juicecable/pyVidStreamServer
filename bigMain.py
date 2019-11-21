#Copyright (c) 2019 Derek Frombach

#Python Video Streaming Server over MJPEG
#Compatible with VLC as HTTP stream
#Server Runs on Ubuntu, Requires Camera
from PIL import Image
import numpy as np
import cv2
import io
import time
import socket

ip="0.0.0.0" #Don't Change This
port=8080 #Hosting Port, Don't Change This
buff=1500 #Also Don't Change This

#Initalisation of TCP Socket Server
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP/IP Socket
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Unbind when Done
s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1) #Zero-Latency TCP
s.bind((ip,port)) #Start Server
s.listen(1) #Listen for Connections

#Initalisation of Camera
cap = cv2.VideoCapture(0)

#Initalisation of Log File
f = open('vidDebug.log','a') #Don't Change This

#Mandatory HTTP Headers (Required for Functionality)
iostr="\r\n--R2lpaXUgU3dmYW5iY2o0\r\nContent-Type: image/jpeg\r\nContent-Length: ".encode("utf-8")
estr="\r\n\r\n".encode("utf-8")

#Function Call Speedups
tc=time.clock
tt=time.time
ts=time.sleep
cr=cap.read
cvt=cv2.cvtColor
bgr=cv2.COLOR_BGR2RGB
ifa=Image.fromarray
bio=io.BytesIO
fw=f.write
ff=f.flush
st=s.settimeout
ste=socket.timeout
rdwr=socket.SHUT_RDWR
se=socket.error

#Initalisation of Address
print("READY!")
addr=["NC","NC"]

#Continuity Loop
while True:
    
    #Do Not Change Anything Below, All of this is Security
    print("Disconnected")
    print(tt())
    print(addr)
    fw("Disconnected\n")
    fw(str(tt())+"\n")
    fw(str(addr[0])+", ")
    fw(str(addr[1])+"\n")
    ff()
    
    #Ctrl-C Handler
    st(None)
    try:
        conn,addr=s.accept()
    except KeyboardInterrupt:
        break
    
    print("Connected")
    print(tt())
    print(addr)
    fw("Connected\n")
    fw(str(tt())+"\n")
    fw(str(addr[0])+", ")
    fw(str(addr[1])+"\n")
    ff()
    ct=conn.settimeout
    ct(1.0)
    #Do Not Change Anything Above
    
    
    #Header Communication with Client
    cs=conn.sendall #Connection Speedup
    #Client Timeout Handler
    try:
        data=conn.recv(buff)
    except ste:
        print("BOT!")
        fw("BOT!\n")
        conn.shutdown(rdwr)
        conn.close()
        continue
    except se:
        conn.shutdown(rdwr)
        conn.close()
        continue
    
    #Also Mandatory HTTP Headers
    ostr="HTTP/1.1 200 OK\r\nConnection: close\r\nServer: PyVidStreamServer MJPEG SERVER\r\nCache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0\r\nPragma: no-cache\r\nExpires: -1\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: multipart/x-mixed-replace;boundary=R2lpaXUgU3dmYW5iY2o0\r\n\r\n"

    o=ostr.encode("utf-8")
    #Server Connection Failure Handler
    try:
        cs(o) #Sending Header
    except ste:
        print("BOT!")
        fw("BOT!\n")
        conn.shutdown(rdwr)
        conn.close()
        continue
    except se:
        conn.shutdown(rdwr)
        conn.close()
        continue
    
    
    #grab initial image here
    ret, frame = cr()
    frame = cvt(frame, bgr)
    img=ifa(frame)
    
    #getting image height and width for future use
    h=img.height
    w=img.width
    
    #Capture Loop
    while True:
        
        a=tc()#Start Time for Frame Limiting
        
        #img grabbing goes here
        ret, frame = cr()
        frame = cvt(frame, bgr)
        img=ifa(frame)
        
        #Converting Raw Image into Compressed JPEG Bytes
        with bio() as output:
            img.save(output,format="JPEG",quality=25)
            contents=output.getvalue()
            
        #Concatenating Contents and Headers
        o=iostr
        o+=str(len(contents)).encode("utf-8")
        o+=estr
        o+=contents
        
        #Sending Contents to Client
        try:
            cs(o)
        except:
            break
            
        #frame rate limiter
        b=tc() #End Time for Frame Limiting
        c=b-a
        t=1/5 #seconds per frame
        if t-c>0.0:
            ts(t-c) #delay remaining seconds
        elif c>t:
            pass
            #print(c)
            
#End of Program (when Ctrl-C)
f.close()
cap.release()
s.close()
