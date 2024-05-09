#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  __  __ ____ _  __ ____ ___ __  __
#  \ \/ // __// |/ //  _// _ |\ \/ /
#   \  // _/ /    /_/ / / __ | \  / 
#   /_//___//_/|_//___//_/ |_| /_/  
# 
#   2024 Yeniay Uav Flight Control Systems
#   Research and Development Team

import time
import threading
import queue
import northlib.ntrp.ntrp as ntrp
from northlib.ntrp.northport import NorthPort
from northlib.ntrp.ntrpbuffer import NTRPBuffer

__author__ = 'Yeniay RD'
__all__ = ['NorthRadio']

class NorthRadio(NorthPort):

    """
    NTRP Radio
    North radio object for each NTRP_Dongle™ module 
    
    > Syncronization with exteral NTRP_Dongle™. (Optional, LoRa module not responds to sync message)  
    > NTRP Pipes can subscribe the radio channel for Rx interrupt & Tx driver.
    > RX thread continuously reads the serial port. If there is a bytearray in the line;
        - Parses the data to NTRP Message 
        - Looks for receiver address in subscribed pipes
        - If found a subscriber calls append(packet) to pipe buffer  
    >TX driver gets NTRP Packet, it makes it NTRP Message, compiles Message to byte array,
    transmits byte array trough serial port.
    """

    DEFAULT_BAUD = 115200
   
    WAIT_TICK     = 0.001     #1 ms  Wait Tick (Do not Change)
    THREAD_SLEEP   = 0.01      #10 ms Thread Stop (Can changable)
    
    def __init__(self, com=None , baud=DEFAULT_BAUD):
        super().__init__(com, baud)
        self.isSync = False
        self.pipes = []                     #NorthPipe Class List
        self.radioid = ntrp.NTRP_MASTER_ID  
        self.txQueue = queue.Queue(5)
        self.isAlive = False

    def syncRadio(self,timeout = 2):
        timer = 0.0
        msg = ""
        while self.isSync == False and timer<timeout:
            temp = self.receive()
            if temp == None :
                timer+=self.THREAD_SLEEP
                time.sleep(self.THREAD_SLEEP) 
                continue
            msg += temp.decode(errors='ignore')

            if ntrp.NTRP_SYNC_DATA in msg:
                self.isSync = True
                self.transmit(ntrp.NTRP_PAIR_DATA.encode())
                time.sleep(0.1)       #Wait remaining data
                self.port.read_all()  #Clear the buffer
                return True
        return False
    
    def beginRadio(self):
        if self.isAlive == True: return False              #Return if already begin
        if self.mode == self.NO_CONNECTION : return False   #Return if port has no connection
        self.isAlive = True  #First set isAlive to <True> so threats can go into while loop
        self.txThread = threading.Thread(target=self.txProcess,daemon=True)
        self.txThread.start()
        self.rxThread = threading.Thread(target=self.rxProcess,daemon=True)
        self.rxThread.start()
        return True 

    def isRadioAlive(self):
        if self.mode == self.NO_CONNECTION: return False
        return True

    def subPipe(self,pipe):
        self.pipes.append(pipe)     #Subscribe to the pipes
        
    def unsubPipe(self,pipe_id):
        for i in range(len(self.pipes)):
            if self.pipes[i].id == pipe_id: self.pipes.pop(i)
    
    def newPipeID(self):
        #New Unique Pipe ID (char) Request
        #Only important thing is, pipe id need to be a char and unique

        max_id_value = ord('1')
        for i in range(len(self.pipes)):
            test_id_value = ord(self.pipes[i].id)
            if  test_id_value > max_id_value : max_id_value = test_id_value 
        return chr(max_id_value)

    def rxHandler(self,msg=ntrp.NTRPMessage):

        """ <DEBUG INCOMING MSG>
        ntrp.NTRP_LogMessage(msg)
        """

        if(msg.header == ntrp.NTRPHeader_e.MSG):
            print(self.com + ":/"+msg.talker+"> " + msg.data.decode('ascii',errors='ignore'))
        elif msg.header == ntrp.NTRPHeader_e.NAK:
            ntrp.NTRP_LogMessage(msg)
        

        for pipe in self.pipes: #Find related pipe
            if pipe.id == msg.talker: 
                pipe.receivePacket(msg)
                return
            
        if msg.talker == 'E': return #Talker is router
        print(self.com + ":/"+msg.talker+"> " + "Talker not recognized.")
    
    def rxProcess(self):
        #If connection lost, Rx process ends.
        while self.isAlive and self.mode!=self.NO_CONNECTION:
            byt = None
            byt = self.receive()
            if byt == None:
                time.sleep(self.WAIT_TICK) 
                continue
            if byt != ntrp.NTRP_STARTBYTE.encode(): continue
            
            arr = bytearray(byt)

            timer = 0 
            while self.port.in_waiting < 3 and timer < 0.1:
                time.sleep(self.WAIT_TICK)
                timer += self.WAIT_TICK     

            arex = self.port.read(2)
            arr.extend(arex)

            packetsize = self.port.read(1)[0]
            if(packetsize>ntrp.NTRP_MAX_MSG_SIZE): continue

            arr.append(packetsize)

            timer = 0
            while self.port.in_waiting < packetsize+1 and timer < 0.1:
                time.sleep(self.WAIT_TICK)
                timer += self.WAIT_TICK     

            arex = self.port.read(packetsize+1)
            arr.extend(arex)

            msg = ntrp.NTRP_Parse(arr)
            if msg == None: 
                #If Parsing error msg == None: Debug NAK bytes
                print(self.com + ":/rxProcess> NAK: " + ntrp.NTRP_bytes(arr))   
            else:
                #Parse Success, handle the NTRPMessage
                self.rxHandler(msg) 


    def txHandler(self,pck=ntrp.NTRPPacket, receiverid='0', force=False):
        if(self.mode == self.NO_CONNECTION): return
        
        msg = ntrp.NTRPMessage(self.radioid,receiverid)
    
        msg.header = pck.header
        msg.dataID = pck.dataID
        msg.data   = pck.data

        arr = ntrp.NTRP_Unite(msg)
        if arr == None :
            print(self.com+":/>" + " Packet Lost" ) 
            return
        
        """ <DEBUG TRANSMIT MSG>
        ntrp.NTRP_LogMessage(msg)
        print(ntrp.NTRP_bytes(arr))
        """
        
        if force==True:
            #self.port.write(arr) 
            try:  
                self.txQueue.put(block=False,item=arr)
            except queue.Full: pass
        else:
            try:    
                self.txQueue.put(block=True,item=arr,timeout=0.1)
                time.sleep(self.THREAD_SLEEP) 
            except queue.Full: print(self.com+":/> Queue Full")

    def txProcess(self):
        while self.isAlive and self.mode!= self.NO_CONNECTION:
            arr = self.txQueue.get()
            if arr != None:
                self.transmit(arr)
                time.sleep(self.THREAD_SLEEP) #Transmit can't speed up to infinity
                self.txQueue.task_done()
            else:
                time.sleep(self.WAIT_TICK)

    def destroy(self):
        self.isAlive = False
        return super().destroy()
