from email.mime import message
import cv2, imutils, socket
from cv2 import putText
import numpy as nm
import time
import base64
import sys
import threading

# function that sends a packet
# why did I make this a separate function again?
def SendPacket(packet, socket, client):
    socket.sendto(packet, client)
    return

# const for buffer size
# sadly can't have a buffer that's bigger than this
# this buffer size is some sort of network maximum!
# so if you want to transfer HD video frames, you need to split the message into
# multiple packets, send them, and somehow reassemble them on the client side. that's
# the next plan for this!
BUFF_SIZE = 65536

# socket init stuff - read docs bc i don't understand it
# update: i read the docs last night and now i kinda understand it ! :)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

# HOST IP AND PORT SETTINGS HERE:
host_name = socket.gethostname()
host_ip = "127.0.0.1"
port = 9999

# binding the socket
socket_address = (host_ip, port)
server_socket.bind(socket_address)

# checks if we can listen at this address
print("Listening at:", socket_address)

vid = cv2.VideoCapture("F:\_PIRACY\TV\Corner Gas\s1\Corner.Gas.s01e01.Ruby.Reborn.avi") #replace name with 0 for webcam????
FPS = vid.get(cv2.CAP_PROP_FPS)

# get fps info
# fps is self explanatory
# idk what st means
# framesToCount likely means the number of frames we need to iterate through
# cnt maybe the running count?
fps, st, framesToCount, cnt = (0,0,24,0)

while True:
    msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
    print("GOT conn from ", client_addr)
    print(msg)
    print(FPS)

    WIDTH = 800
    jpegQuality = 40
    #so roughly speaking here's what this does
    #while the video is opened, we call vid,.read
    #then we take a frame, resize it to our defined width,
    #encode it as a jpeg with 80% quality, encode it using
    #b64, and transmit it
    while(vid.isOpened()):

        # vid.read() rips the next frame from the vid,
        # acts like a queue in my best estimation
        _,frame = vid.read()

        # resizes the current frame with our WIDTH const
        frame = imutils.resize(frame, width=WIDTH)

        # encodes the frame in jpg format, specifies the compression % using jpeqQuality variable
        # default set to 40%
        encoded,buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpegQuality])
        
        # creates a message with b64encoded buffer
        message = base64.b64encode(buffer)

        # quick dump of frame data to console (JPEG quality, size of packet)
        print("FRAME DATA:")
        print("JPEG:\t%", jpegQuality)
        print("FPS:\t", fps)
        print(message.__sizeof__())

        # if the message is larger than 64kb, don't send it because network exception
        if(message.__sizeof__() < 65536):
            SendPacket(message, server_socket, client_addr)


        # uncomment the below two lines to display vidoe stream on server side
        # frame = cv2.putText(frame, 'FPS: ' + str(fps), (10,40), cv2.FONT_ITALIC, 0.7, (0.0,255))
        # cv2.imshow('TRANSMITTING VIDEO', frame)

        # exit condition that I'm fairly certain doesn't work
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            server_socket.close()
            break

        # fps calcuilation
        # if the number of frames passed since the previous execution of this logic
        # is equal to the fps of the video...
        if cnt == framesToCount:
            try:
                fps = round(framesToCount/(time.time()-st), 10)
                st = time.time()
                cnt = 0
            except:
                pass
        cnt += 1

# dynamic jpeg quality -- cool idea but bad in practice because lag

        #while sys.getsizeof(message) < 65536:
        #    if(jpegQuality == 100):
        #        break
        #    jpegQuality += 2
        #    encoded,buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpegQuality])
        #    message = base64.b64encode(buffer)


        #while sys.getsizeof(message) > 65536:
        #    jpegQuality -= 2
        #    encoded,buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpegQuality])
        #    message = base64.b64encode(buffer)