#! /usr/bin/env python3
from socket import *
from select import select

# default params
serverAddr = ("", 50001)

import sys
def usage():
    print("usage: %s [--serverPort <port>]"  % sys.argv[0])
    sys.exit(1)

try:
    args = sys.argv[1:]
    while args:
        sw = args[0]; del args[0]
        if sw == "--serverPort":
            serverAddr = ("", int(args[0])); del args[0]
        else:
            print("unexpected parameter %s" % args[0])
            usage();
except:
    usage()

print("binding datagram socket to %s" % repr(serverAddr))

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(serverAddr)
print("ready to receive")

#enum for states of the server
LISTENING, READY, OPEN_FILE, WRITING, DONE, SAVE, CLOSE_FILE = 1,2,3,4,5,6,7
"""Counters for each state. These are the amount of times the server will
try to send the messsage back to the client before dropping it."""
READY_LIMIT = 10
READY_COUNTER = 0
OPEN_FILE_LIMIT = 10
OPEN_FILE_COUNTER = 0
WRITING_LIMIT = 10
WRITING_COUNTER = 0
DONE_LIMIT = 10
DONE_COUNTER = 0
SAVE_LIMIT = 10
SAVE_COUNTER = 0
CLOSE_FILE_LIMIT = 10
CLOSE_FILE_COUNTER = 0

def reset_counters():
    LISTENING_COUNTER = 0
    READY_COUNTER = 0
    OPEN_FILE_COUNTER = 0
    WRITING_COUNTER = 0
    DONE_COUNTER = 0
    SAVE_COUNTER = 0
    CLOSE_FILE_COUNTER = 0
"""
I must implement sequence numbers to enumerate the packets being sent.
I'm going to set a limit on the size of files able to be transmitted. I'm going
to go with 15MB like emails. Each packet will be size 999. So there might be
16 or so many packets. Maybe this may be enqueue'd to the front of the byte
array sent. So only 2 bytes are needed for the beginning and the end for the 
next packet. First 2 bytes are for id, last two bytes are for next. Going from
00 to 15

How do we know if we're done? Should I send what the total number of packets is 
supposed to be? Maybe it isn't as necessary and instead use the last 2 bytes to 
have a special meaning. The server won't have a special rule for knowing how 
large a file is to be transmitted. It will be up to the client to know the 15MB 
size. 
"""

current_state = LISTENING

readSockets = []
writeSockets = []
errorSockets = []

readSockets.append(serverSocket)
dgram = b''
client = None

while 1:
    # Select is mostly for utilizing the timeout as I understand. 
    readReady, writeReady, errorReady = select.select(readSockets, writeSockets,
                                                      errorSockets, 5)
    # If the select timeout occurs, we need to increment the counter.
    if not readReady and not writeready and not errorReady:
        count_state()
        check_timeout()
    # If there is work to do, do it in here. 
    else:
        for sock in readReady:
            dgram, client = sock.recvfrom(999)
            print('dgram received from\t%s\t%s' % (client, dgram))
        if current_state is LISTENING:
            if dgram == b'introduce':
                print('\t>LISTENING: recieved introduce. Switching to READY. \
                Sending ACK...')
                current_state = READY
                serverSocket.sendto(client, b'ACK')
        elif current_state is READY:
            print('\t>READY: recieved dgram. Confirming...')
            serverSocket.sendto(client, dgram)
            current_state = OPEN_FILE
        elif current_state is OPEN_FILE:
            print('\tOPEN_FILE'
        elif current_state is WRITING:
            
        elif current_state is DONE:
            
        elif current_state is SAVE:
            
        elif current_state is CLOSE_FILE:
    

    
    modifiedMessage = message.decode().upper()
    serverSocket.sendto(modifiedMessage.encode(), clientAddrPort)

def check_timeout():
    # Done in order of hypothesis of most likely to timeout.
    if (READY_COUNTER is READY_LIMIT or
        OPEN_FILE_COUNTER is OPEN_FILE_LIMIT or
        WRITING_COUNTER is WRITING_LIMIT or
        DONE_COUNTER is DONE_LIMIT or
        SAVE_COUNTER is SAVE_LIMIT or
        CLOSE_FILE_COUNTER is CLOSE_FILE_LIMIT):
        
        timeout_protocol()
        

def timeout_protocol():
    current_state = LISTENING
    dgram = b''
    client = None
    reset_counters()
    
                
def count_state():
    if current_state is READY:
        READY_COUNTER += 1
    elif current_state is OPEN_FILE:
        OPEN_FILE_COUNTER += 1
    elif current_state is WRITING:
        WRITING_COUNTER += 1
    elif current_state is DONE:
        DONE_COUNTER += 1
    elif current_state is SAVE:
        SAVE_COUNTER += 1
    elif current_state is CLOSE_FILE:
        CLOSE_FILE_COUNTER += 1
