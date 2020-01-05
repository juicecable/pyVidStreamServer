#Copyright (c) 2019 UofRobotics

#Python Video Streaming Server over MJPEG
#Compatible with VLC as HTTP stream
#Server Runs on Linux/Windows, Requires Camera
import cv2
from PIL import Image
import time
import socket
import io
from multiprocessing import shared_memory, Lock, Process

#Definitons

#Core reciever
def get_data(smin,smon,smfn,smsn,l,port_name):
    
    #Apperantly this is the correct way to do shared memory
    smi=shared_memory.SharedMemory(name=smin) #Image (write only)
    smo=shared_memory.SharedMemory(name=smon) #Options (read only)
    smf=shared_memory.ShareableList(name=smfn) #Frame rate (read only)
    sms=shared_memory.ShareableList(name=smsn) #Image size (write only)
    
    #Speedups
    la=l.acquire
    lr=l.release
    cvt=cv2.cvtColor
    bgr=cv2.COLOR_BGR2RGB
    ifa=Image.fromarray
    bio=io.BytesIO
    tc=time.perf_counter
    ts=time.sleep
    smib=smi.buf
    smob=smo.buf
    try:
        while True: #Retry loop
            
            #Init Loop
            while True:
                la()
                runn=smob[0]
                qual=smob[1]
                stop=smob[2]
                fram=smf[0]
                if stop: break
                if not runn:
                    lr()
                    ts(0.25) #Check options every 250ms
                else: break
            
            #Capture loop
            if not stop:
                cap=cv2.VideoCapture(port_name)
                lr()
                cr=cap.read
            while not stop:
                a=tc()#Start time for frame limiting
                
                #Image grabbing goes here
                ret, frame = cr()
                frame = cvt(frame, bgr)
                img=ifa(frame)
                
                #Converting raw image into compressed JPEG bytes
                with bio() as output:
                    img.save(output,format="JPEG",quality=qual)
                    la()
                    content=output.getvalue()
                    y=len(content)
                    sms[0]=y #Set Image Size
                    smib[:y]=content
                runn=smob[0]
                qual=smob[1]
                stop=smob[2]
                fram=smf[0]
                lr()
                if (not runn) or stop: break
                    
                #Frame rate limiter
                b=tc() #End time for frame limiting
                c=b-a
                if fram-c>0.0:
                    ts(fram-c) #Delay remaining seconds

            #Breaker bar
            cap.release()
            if stop: break
    
    except ValueError as e:
        print('Failure Due to Access Bug')
        print(e)
    except KeyboardInterrupt as e:
        pass
       
    #End of daemon     
    if l.locked(): lr() #Allow code to run
    try: cap.release() #Attempt to close camera if error
    except: pass
    smi.close()
    smo.close()
    smf.shm.close()
    sms.shm.close()
    print('CAMERA STOPPED!')

if __name__ == "__main__":

    ip='0.0.0.0' #Don't change This
    port=8080 #Hosting port, don't change this
    buff=1500 #Also don't change this
    port_name=0 #Also don't change this
    max_img_size=25000000 #Max possible image size in bytes
    debug=False
    logging=True

    #Initalisation of TCP socket server
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP/IP socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Unbind when done
    s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1) #Zero latency TCP
    s.bind((ip,port)) #Start server
    s.listen(1) #Listen for connections

    #Initalisation of log file
    f=open('lidarVidDebug.log','a') #Don't change this

    #Mandatory HTTP headers (required for functionality)
    iostr="\r\n--R2lpaXUgU3dmYW5iY2o0\r\nContent-Type: image/jpeg\r\nContent-Length: ".encode("utf-8")
    estr="\r\n\r\n".encode("utf-8")

    #Function call speedups
    tc=time.perf_counter
    tt=time.time
    ts=time.sleep
    bio=io.BytesIO
    fw=f.write
    ff=f.flush
    st=s.settimeout
    ste=socket.timeout
    rdwr=socket.SHUT_RDWR
    se=socket.error

    #Initalisation of address
    print("READY!")
    addr=["NC","NC"]

    #Now the Actual Code
    #Run Before Connect
    l=Lock()
    smi=shared_memory.SharedMemory(create=True,size=max_img_size) #Image
    smo=shared_memory.SharedMemory(create=True,size=3) #Currently capturing signal, Quality, Stop signal
    smf=shared_memory.ShareableList([False]) #Frame rate
    sms=shared_memory.ShareableList([max_img_size]) #Image size

    #Setting default parameters
    smo.buf[0]=False #Currently capturing signal
    smo.buf[1]=35 #Quality
    smo.buf[2]=False #Stop signal
    smf[0]=1/60 #Frame rate (seconds per frame)

    #Making sure the client doesn't break on the first connection attempt
    img=Image.new('RGB',(100,100))
    with io.BytesIO() as output:
        img.save(output,format="JPEG",quality=35)
        content=output.getvalue()
        y=len(content)
        sms[0]=y #Set Image Size
        smi.buf[:y]=content
    img.close()

    #Apperantly You have to Pass the Names, not the Objects of the Shared Memory
    p1=Process(target=get_data,args=(smi.name,smo.name,smf.shm.name,sms.shm.name,l,port_name),daemon=True)
    p1.start() #Start Daemon

    #Continuity Loop
    while True:
        
        #Do Not Change Anything Below, All of this is Security
        print("Disconnected")
        print(tt())
        print(addr)
        if logging:
            fw("Disconnected\n") #File Append
            fw(str(tt())+"\n")
            fw(str(addr[0])+", ")
            fw(str(addr[1])+"\n")
            ff() #Write to File
        
        #Ctrl-C Handler
        st(0.1) #Set Timeout
        try:
            while True:
                try:
                    conn,addr=s.accept()
                except ste:
                    pass
                else:
                    break
        except KeyboardInterrupt:
            break
        
        print("Connected")
        print(tt())
        print(addr)
        if logging:
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
            if len(data)==0:
                print("BOT!")
                if logging: fw("BOT!\n")
                conn.shutdown(rdwr)
                conn.close()
                continue
        except ste:
            print("BOT!")
            if logging: fw("BOT!\n")
            conn.shutdown(rdwr)
            conn.close()
            continue
        except se:
            conn.shutdown(rdwr)
            conn.close()
            continue
        except KeyboardInterrupt:
            conn.shutdown(rdwr)
            conn.close()
            print("Disconnected")
            print(tt())
            print(addr)
            if logging:
                fw("Disconnected\n") 
                fw(str(tt())+"\n")
                fw(str(addr[0])+", ")
                fw(str(addr[1])+"\n")
                ff()
            break
        
        #Also Mandatory HTTP Headers
        ostr="HTTP/1.1 200 OK\r\nConnection: close\r\nServer: PyVidStreamServer MJPEG SERVER\r\nCache-Control: no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0\r\nPragma: no-cache\r\nExpires: -1\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: multipart/x-mixed-replace;boundary=R2lpaXUgU3dmYW5iY2o0\r\n\r\n"

        o=ostr.encode("utf-8")
        #Server Connection Failure Handler
        try:
            cs(o) #Sending Header
        except ste:
            print("BOT!")
            if logging: fw("BOT!\n")
            conn.shutdown(rdwr)
            conn.close()
            continue
        except se:
            conn.shutdown(rdwr)
            conn.close()
            continue
        except KeyboardInterrupt:
            conn.shutdown(rdwr)
            conn.close()
            print("Disconnected")
            print(tt())
            print(addr)
            if logging:
                fw("Disconnected\n") 
                fw(str(tt())+"\n")
                fw(str(addr[0])+", ")
                fw(str(addr[1])+"\n")
                ff()
            break

        #Quick Pre-Loop Speedup
        la=l.acquire
        lr=l.release
        smib=smi.buf

        #Camera Initalisation
        la()
        smo.buf[0]=True
        lr()
        
        #Capture Loop
        while True:
            
            a=tc() #Start Time for Frame Limiting

            #Getting Camera Frame
            la()
            clc=sms[0]
            contents=bytes(smib[:clc])
            lr()
                
            #Concatenating Contents and Headers
            o=iostr
            o+=str(clc).encode("utf-8")
            o+=estr
            o+=contents
            
            #Sending Contents to Client
            try:
                cs(o)
            except ste:
                print("Network Issues!")
                if logging: fw("Network Issues!\n")
                conn.shutdown(rdwr)            
                conn.close()
                break
            except se:
                conn.shutdown(rdwr)
                conn.close()
                break
            except KeyboardInterrupt:
                conn.shutdown(rdwr)
                conn.close()
                break
                
                
            #frame rate limiter
            try:
                b=tc() #End Time for Frame Limiting
                c=b-a
                t=1/60 #seconds per frame
                if t-c>0.0:
                    ts(t-c) #delay remaining seconds
                elif c>t:
                    pass
                    if debug: print(c)
                    
            except KeyboardInterrupt:
                conn.shutdown(rdwr)
                conn.close()
                break
        
        #Proper Memory Usage
        la()
        smo.buf[0]=False
        lr()
                
    #End of Program (when Ctrl-C)
    f.close()
    s.close()

    #Gracefully Kill RPLidar
    l.acquire() #Locking
    smo.buf[2]=True #Graceful Shutdown Signal
    l.release() #Unlocking
    p1.join() #Wait for Process to Finish
    p1.close() #Destroy the Daemon Process Object

    #Proper Shared Memory Closing
    smi.close()
    smi.unlink()
    smo.close()
    smo.unlink()
    smf.shm.close()
    smf.shm.unlink()
    sms.shm.close()
    sms.shm.unlink()

