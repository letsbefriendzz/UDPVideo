from contextlib import nullcontext
from re import T
from tkinter import Frame
from tkinter.tix import DisplayStyle
import cv2, imutils, socket
import numpy as np
import time
import base64
import threading
import queue;

# of all files to leave grossly uncommented, it's the one that actually needs it!

# FPS (in caps) represents the FPS rate of the video we're loading.
# currently we have 24 hardcoded because that's the framerate of the
# hardcoded video the server is dishing us. In a perfect world, I'd
# send the framerate over a packet first but that's down the line.
FPS = 24

# Then we have a queue of frames that need to be parsed.
# The server just shoots frames as fast as it can, which often leads
# to frames being sent at 60+ fps. This means that if we process them
# as fast as we receive them, we'll be playing the video far faster
# than originally inteded.
UnparsedFrames = queue.Queue(4096)

# a flag used to wrap up multithreaded badness, currently useless because
# I just abort the program everytime I run it lol
flag = False


# ProcessFrames()
# This function is launched on its own thread, where it runs through an
# infinite loop. If the correct approximate amount of time has elapsed
# between the last time a frame was shown and the current time, we can
# display a new frame.
#
# The frames in the queue are just straight up byte arrays, as far as my
# knowledge goes. We do some decoding with OpenCV, put an FPS counter in
# the corner of the image, and using imshow, show the frame. Then, the
# previous time tracker is updated to present time.
#
# We then execute some fps logic and checking if q is pressed, dump the
# current and target framerates to the console, and continue on to another
# loop iteration.
def ProcessFrames():
    # FrameInterval represents the elapsed time, in seconds, between frames
    # so it's just 1 / FPS lol
    FrameInterval = 1 / FPS
    fps, st, framesToCount, cnt = (0,0,26,0)
    PreviousTime = time.time()
    while True:
        try:
            if (time.time() - PreviousTime) < FrameInterval + 0.0025 and (time.time() - PreviousTime) > FrameInterval - 0.0025:
                data = UnparsedFrames.get()
                npdata = np.frombuffer(data, dtype = np.uint8)
                frame = cv2.imdecode(npdata, 1)
                frame = cv2.putText(frame, 'FPS: ' + str(fps), (10,40), cv2.FONT_ITALIC, 0.7, (0.0,255))

                cv2.imshow("receiving frames", frame)
                PreviousTime = time.time()

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    flag = True
                    break

                #fps logic
                if cnt == framesToCount:
                    try:
                        fps = round(framesToCount/(time.time()-st), 15)
                        st = time.time()
                        cnt = 0
                    except:
                        pass
                cnt += 1

                print("CURRENT FRAMERATE: ", fps)
                print("TARGET FRAMERATE: ", FPS)
        except:
            print("No Frames!")
            pass

# UDPGetFrames()
# This function is the networking side of the client application. It also runs on
# its own thread. Using socket stuffs, it receives packets from the specified server
# (hardcoded to be local, in this case) and sends the partially decoded frame to the
# UnparsedFrames queue for further processing.
#
# If the bool flag is set, we close the socket and break the loop.
def UDPGetFrames():
    BUFF_SIZE = 65536
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

    # IP AND PORT SETTINGS HERE:
    host_name = socket.gethostname()
    host_ip = "127.0.0.1"
    port = 9999
    message = b'Hello'

    client_socket.sendto(message, (host_ip, port))

#copy pasting getting me down ngl
    while True:
        packet,_ = client_socket.recvfrom(BUFF_SIZE)
        data = base64.b64decode(packet, ' /')

        UnparsedFrames.put(data)

        if flag == True:
            client_socket.close()
            break

# MAIN THREAD
# The main thread just creates two threads for the networking and frame processing
# functions respectively. The threads are started, and then waits for them to join.

NetworkThread = threading.Thread(target=UDPGetFrames)
VideoThread = threading.Thread(target=ProcessFrames)

VideoThread.start()
NetworkThread.start()

VideoThread.join()
NetworkThread.join()