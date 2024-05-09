#!/usr/bin/env pythonh
# -*- coding: utf-8 -*-
#  __  __ ____ _  __ ____ ___ __  __
#  \ \/ // __// |/ //  _// _ |\ \/ /
#   \  // _/ /    /_/ / / __ | \  / 
#   /_//___//_/|_//___//_/ |_| /_/  
# 
#   2024 Yeniay Uav Flight Control Systems
#   Research and Development Team

import time 

import northlib.ntrp.ntrp as ntrp
from northlib.ntrp.ntrp import NTRPMessage,NTRPPacket,NTRPHeader_e
from northlib.ntrp.ntrpbuffer import NTRPBuffer
from northlib.ntrp.northradio import NorthRadio 
import northlib.ntrp as nt

__author__ = 'Yeniay RD'
__all__ = ['NorthPipe','NorthNRF']

class NorthPipe():

    """ 
    NorthPipe Class 
    
    >It communicates with target agent in the RF Network
    >Transmit commands
    >Receive Buffer & newdata callback

    SELF -> UART LORA MODULE 
    NRF CLASS -> NRF ROUTER
    """
    RX_HANDLE_MODE_BUFFER   = 0
    RX_HANDLE_MODE_CALLBACK = 1

    def __init__(self, pipe_id = '1', radio = NorthRadio):
        self.id = pipe_id                    # Agent ID

        # LORA >
        # The Pipe ID is should be same with target agent ID
        
        # RF DONGLE >
        # Agent ID is represents the rf adress when use NTRP_Router Dongle
        # Agent ID identifies the target agent when use UART Lora Module
        
        self.radio = radio    
        self.radio.subPipe(pipe=self)  #Subscribe to Radio

        self.rxbuffer = NTRPBuffer(20) #LIFO Ring Buffer
        self.rxHandleMode = self.RX_HANDLE_MODE_BUFFER

        self.rxCallBack = {
            NTRPHeader_e.NAK:None,
            NTRPHeader_e.ACK:None,
            NTRPHeader_e.MSG:None,
            NTRPHeader_e.CMD:None,
            NTRPHeader_e.GET:None,
            NTRPHeader_e.SET:None,
            NTRPHeader_e.LOG:None,
            NTRPHeader_e.RUN:None
        }

        self.setCallBack(NTRPHeader_e.MSG,self.rxMSG)
            
    def setCallBack(self, header=NTRPHeader_e, callback=callable):
        #Data Ready Callback function 
        #It blocks radio rxThread : keep it small 
        try:
            self.rxCallBack[header] = callback
        except KeyError:
            self.printID("setCallBack : Key Error")        
        
    def setRxHandleMode(self,mode):
        self.rxHandleMode = mode

    def waitConnection(self, timeout = float)->float:
        oldmode = self.rxHandleMode 
        self.rxHandleMode = self.RX_HANDLE_MODE_BUFFER

        timer = 0.0
        while self.rxbuffer.isAvailable()<1 and timer<=timeout:
            self.txMSG("ACK Request")
            time.sleep(0.1)
            timer +=   0.1
        
        self.rxHandleMode = oldmode
        
        if(self.rxbuffer.isAvailable() < 1): return 0
        msg = self.rxbuffer.read()
        return timer

    def receivePacket(self,rxPacket = ntrp.NTRPMessage()):
        if self.rxHandleMode == self.RX_HANDLE_MODE_BUFFER: 
            self.rxbuffer.append(rxPacket)
        elif self.rxHandleMode == self.RX_HANDLE_MODE_CALLBACK:
            rxCallBack = self.rxCallBack.get(rxPacket.header)
            if rxCallBack == None: self.printID("receivePacket Error : " + rxPacket.header.name + " Header CallBack is None")
            else : rxCallBack(rxPacket)

    def rxMSG(self, ntrpmsg = NTRPMessage()):
        pass #Radio Prints Already
        #self.printID(ntrpmsg.data.decode('ascii',errors='ignore'))

    def transmitPacket(self,txPacket = ntrp.NTRPPacket,force=False):
        #Packet with receiver ID = PIPE ID
        self.radio.txHandler(txPacket,self.id,force)    
          
    def txNAK(self):
        self.txpck = ntrp.NTRPPacket('NAK')
        self.transmitPacket(self.txpck)     

    def txACK(self):
        self.txpck = ntrp.NTRPPacket('ACK')
        self.transmitPacket(self.txpck)     

    def txMSG(self,msg=str):        
        self.txpck = ntrp.NTRPPacket('MSG')
        self.txpck.data = msg.encode()
        self.txpck.dataID = len(self.txpck.data)        
        self.transmitPacket(self.txpck)     

    def txGET(self,dataid=int):
        self.txpck = ntrp.NTRPPacket('GET')
        self.txpck.dataID = dataid
        self.transmitPacket(self.txpck)

    def txSET(self,dataid=int,databytes=bytearray):
        self.txpck = ntrp.NTRPPacket('SET')
        self.txpck.dataID = dataid
        self.txpck.data = databytes   
        self.transmitPacket(self.txpck)
        
    def txCMD(self,dataID=0,channels=bytearray,force=False):
        self.txpck = ntrp.NTRPPacket('CMD')
        self.txpck.dataID = dataID
        self.txpck.data = channels   
        self.transmitPacket(self.txpck,force=force)

    def printID(self,msg=str):
        print(self.radio.com + ":/" + self.id + "> " + msg)
        
class NorthNRF(NorthPipe):
        
    """
    NorthNRF Class

    NorthNRF represents RF module on external router. 
    No use case without router.
    >OPENPIPE in the router. The PIPE ID need to be same
    with NorthPipe Object. NorthNRF requests new unique ID
    from NorthRadio for PIPE ID. 
    """
    NRF_250KBPS  = 0
    NRF_1000KBPS = 1
    NRF_2000KBPS = 2

    def __init__(self, radioindex = 0, ch = 0, bandwidth = NRF_1000KBPS, address = "E7E7E7E301"):
        super().__init__(pipe_id='0', radio=nt.getRadio(radioindex))
    
        self.channel = ch                       #int
        self.bandwidth = bandwidth              #int[0,1,2]
        self.setAddress(address)

        #If Use NRF Router module, Agents has nrf address instead of ID
        #ID needs to be defined to identify the pipe, so get new tag from radio
        self.id = self.radio.newPipeID() #Unique ID Request
        self.txOPENPIPE()
    
    def setChannel(self,ch=0):
        self.channel = ch

    def setBandwidth(self,bw=NRF_1000KBPS):
        self.bandwidth = bw
    
    def setAddress(self, adr="E7E7E7E301"):
        self.address = bytes.fromhex(adr)
        if(len(self.address) != 5): raise ValueError() #NRF Address is 5 bytes
    
    def txOPENPIPE(self):
        packet = ntrp.NTRPPacket('OPENPIPE',ord(self.id))
        packet.data   = self.pipeType()
        self.radio.txHandler(packet,ntrp.NTRP_ROUTER_ID)
    
    def txCLOSEPIPE(self):
        packet = ntrp.NTRPPacket('CLOSEPIPE',ord(self.id))
        self.radio.txHandler(packet,ntrp.NTRP_ROUTER_ID)

    def txFULLRX(self):
        packet = ntrp.NTRPPacket('FULLRX',ord(self.id))
        self.radio.txHandler(packet,ntrp.NTRP_ROUTER_ID)
    
    def txFULLTX(self):
        packet = ntrp.NTRPPacket('FULLTX',ord(self.id))
        self.radio.txHandler(packet,ntrp.NTRP_ROUTER_ID)

    def txTRX(self):
        packet = ntrp.NTRPPacket('TRX',ord(self.id))
        self.radio.txHandler(packet,ntrp.NTRP_ROUTER_ID)
        

    def pipeType(self):
        #NRTP_Pipe_t in the router
        arr = bytearray()
        arr.append(self.channel)    #Channelbyte
        arr.append(self.bandwidth)  #Bandwidthbyte 
        arr.extend(self.address)    #5 byte address
        return arr                  #[CH,BANDWIDTH,[0,0,0,0,1]]
        
    def destroy(self):
        self.txCLOSEPIPE()  
        self.radio.unsubPipe(self.id)

