#! /bin/python
import sys, re
import time, random
from socket import *

def usage():
    print "usage: %s [--clientPort <port#>] [--serverAddr <host:port>]\n [--byteRate <bytes-per-second>] [--propLat <latency_secs>]\n [--pDelay <prob-delayed msg>] [--delayMin <seconds, default=1> ] [--delayMax <seconds default=1>]\n [--pDrop <prob-drop-msg>] \n [-v]" % sys.argv[0]
    sys.exit(1)

startTime = time.time()
def relTime(when): 
    return when-startTime


clientPort = 50000
serverAddr = ("localhost", 50001)
toClientAddr = ("", 50000)
qCap = 4
byteRate = 1.0e5                        # 100k bytes/sec (roughly 1Mbit/sec)
propLat = 1.0e-2                        # 10 ms
pDelay = 0.0
pDrop = 0.0
verbose = 0
delayMin = 1.0
delayMax = 1.0

print "argv=", sys.argv

try:
    args = sys.argv[1:]
    while args:
        sw = args[0]; del args[0]
        if sw == "--toClientPort":
            toClientAddr = ("", int(args[0])); del args[0]
        elif sw == "--serverAddr":
            addr, port = re.split(":", args[0]); del args[0]
            serverAddr = (addr, int(port))
        elif sw == "--byteRate":
            byteRate = float(args[0]); del args[0]
        elif sw == "--propLat":
            propLat = float(args[0]); del args[0]
        elif sw == "--qCap":
            qCap = int(args[0]); del args[0]
        elif sw == "--pDelay":
            pDelay = float(args[0]); del args[0]
        elif sw == "--delayMin":
            delayMin= float(args[0]); del args[0]
        elif sw == "--delayMax":
            delayMax= float(args[0]); del args[0]
        elif sw == "pDrop":
            pDrop = float(args[0]); del args[0]
        elif sw == "-v" or sw == "--verbose":
            verbose = 1
        else:
            print "unexpected parameter %s" % sw
            usage();
except:
    usage()


print "Parameters: toClientAddr=%s, serverAddr=%s, byteRate=%g, propLat=%g, \nqCap=%d, pDelay=%g, pDrop=%g, verbose=%d" % \
      (repr(toClientAddr), repr(serverAddr), byteRate, propLat, qCap, pDelay, pDrop, verbose)
toServerSocket = socket(AF_INET, SOCK_DGRAM)
toClientSocket = socket(AF_INET, SOCK_DGRAM)
toClientSocket.bind(toClientAddr)
otherSocket = {toClientSocket:toServerSocket, toServerSocket:toClientSocket}
sockName = {toClientSocket:"toClientSocket", toServerSocket:"toServerSocket"}

class TransmissionSim:
    def __init__(self, outSock, destAddr, byteRate, propLat, qCap, pDelay=0.0, pDrop=0.0):
        self.outSock, self.destAddr, self.byteRate, self.propLat, self.qCap, self.pDelay, self.pDrop = \
         outSock, destAddr, 1.0*byteRate, propLat, qCap, pDelay, pDrop
        self.busyUntil = time.time()
        self.transmitTimes = []

    def scheduleDelivery(self, msg):
        now = time.time()
        if verbose:
            global sockName
            print "msg for %s rec'd at relTime %f" % (sockName[self.outSock], relTime(now))

        length = len(msg)
        q = self.transmitTimes  # flush messages transmitted in the past
        while len(q) and q[0] > now:
            del q[0]
        if len(q) >= self.qCap: # drop if q full
            if verbose: print "... queue full (oldest relTime = %f).  :(" % relTime(q[0])
            return 

        startTransmissionTime = max(now, self.busyUntil)
        endTransmissionTime = startTransmissionTime + length/self.byteRate

        if verbose:
            print "... will be transmitted at reltime %f" % relTime(endTransmissionTime)

        q.append(endTransmissionTime) # in transmit q until transmitted
        self.busyUntil = endTransmissionTime # earliest time for next msg

        deliveryTime = endTransmissionTime + self.propLat

        if pDrop > 0.0 and self.pDrop < random.random(): # random drops
            if verbose: print "... random drop ;)"
            return
        if pDelay > 0.0 and self.pDelay < random.random(): # random extra delay
            delay = random.randrange(int(delayMin * 1000), int(delayMax * 1000))/1000.0 # in millisec
            deliveryTime += delay
            if verbose: print "... delaying %d ms" % int(delay * 1000)
        if verbose: print "... scheduled for delivery at relTime %f" % relTime(deliveryTime)
        timeActions.put((deliveryTime, lambda : TransmissionSim.deliver(self, msg)))
        
    def setDest(self, destAddr):        # allows dest addr to be updated
        self.destAddr = destAddr

    def deliver(self, msg):
        if verbose: print "sending <%s> to %s at relTime=%f" % (msg, repr(self.destAddr), relTime(time.time()))
        self.outSock.sendto(msg, self.destAddr)

transmissionSims = {}                   # inSock -> simulatorForOutSock
for inSock, outAddr in ((toClientSocket, serverAddr), (toServerSocket, ("", None))): # client's addr will be set when msg rec'd
    transmissionSims[inSock] = TransmissionSim(otherSocket[inSock], outAddr, byteRate, propLat, qCap) # send to other sock!

rSet = set([toClientSocket, toServerSocket])
wSet = set()
xSet = set([toClientSocket, toServerSocket])



import Queue
timeActions = Queue.PriorityQueue()     # minheap of (when, action).   <Action>() should be called at time <when>.

from select import select

while True:                             # forever
    now = time.time()
    sleepUntil = now+1.0                # default, 1s from now
    while not timeActions.empty():      # deal with all actions in the past
        when, action = timeActions.get() 
        if when > now:                  # if when in the future
            sleepUntil = min(sleepUntil, when) #   awaken no later than when
            timeActions.put((when, action)) # and put back in heap
            break;                          # done with scheduled events thus far
        action()                        # otherwise, when is in the past, therefore perform the action
    rReady, wReady, xReady = select(rSet, wSet, xSet, sleepUntil - now) # select uses relative time
    for sock in rReady:
        msg,addr = sock.recvfrom(2048)
        if sock == toClientSocket:      # if from client, update dest of toServer's transmission simulator 
            transmissionSims[toServerSocket].setDest(addr)
        transmissionSims[sock].scheduleDelivery(msg)
    for sock in xReady:
        print "weird.  UDP socket reported an error.  Bye."
        sys.exit(1)

