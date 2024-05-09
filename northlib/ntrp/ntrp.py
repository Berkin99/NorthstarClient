#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  __  __ ____ _  __ ____ ___ __  __
#  \ \/ // __// |/ //  _// _ |\ \/ /
#   \  // _/ /    /_/ / / __ | \  / 
#   /_//___//_/|_//___//_/ |_| /_/  
# 
#   2024 Yeniay Uav Flight Control Systems
#   Research and Development Team

__author__ = 'Yeniay RD'
__all__ = ['NTRPHeader_e, NTRPRouterHeader_e, NTRPMessage']

from enum import Enum
import binascii

NTRP_SYNC_DATA  = "*NC"
NTRP_PAIR_DATA  = "*OK"
NTRP_STARTBYTE  = '*'
NTRP_ENDBYTE    = '\n'
NTRP_ROUTER_ID  = 'E'
NTRP_MASTER_ID  = '0'   

NTRP_MAX_MSG_SIZE 		= 32
NTRP_MAX_PACKET_SIZE 	= 28

class NTRPHeader_e(Enum):
    NAK 		= 0
    ACK 		= 1
    MSG 		= 2 #Debug Message + NOP
    CMD 		= 3 #Commander + CMD ID + COMMANDARGV
    GET 		= 4 #Param Get + ParamID
    SET 		= 5 #Param Set + ParamID + DATA
    LOG         = 6
    RUN		    = 7 #Func Run  + FuncID 

    OPENPIPE    = 21 #PipeID + (channel,speedid,address[5])    
    CLOSEPIPE   = 22
    TRX         = 23 #Router Transceiver MODE
    FULLRX      = 24 #Router FULL RX 
    FULLTX      = 25 #Router FULL TX
    EXIT        = 26

class NTRPPacket():
    MAX_PACKET_SIZE = 28
    MAX_DATA_SIZE = 26

    def __init__(self,header='ACK', dataID=0):
        #NTRP_Packet_t
        self.header  = NTRPHeader_e.ACK
        self.setHeader(headername=header)
        self.dataID  = dataID       #data id or pipeno
        self.data    = bytearray()         #payload

    #Set Header With Name
    def setHeader(self,headername):
        for header in NTRPHeader_e:
            if header.name == headername:        
                self.header = header

    #TODO: set dataid with name
    def setDataID(self,dataid):        
        self.dataID = dataid

class NTRPMessage(NTRPPacket):
    MAX_MESSAGE_SIZE = 32

    def __init__(self,talker='0',receiver='0'):
        super().__init__()
        self.talker      = talker           #char
        self.receiver    = receiver         #char
        self.packetsize  = 3                #int
    
    def setPacket(self,packet=NTRPPacket):
        self.header = packet.header
        self.dataID = packet.setDataID
        self.data   = packet.data
        
# @param raw_bytearray = bytearray
# if error : returns None 
# return NTRPMessage 
def NTRP_Parse(raw_bytearray=bytearray):
    if chr(raw_bytearray[0]) != NTRP_STARTBYTE : return None
    msg = NTRPMessage()
    msg.talker   = chr(raw_bytearray[1])
    msg.receiver = chr(raw_bytearray[2])
    msg.packetsize = int(raw_bytearray[3])

    msg.data = bytearray()

    if (msg.packetsize<2 or msg.packetsize>NTRP_MAX_PACKET_SIZE) : return None 
    datasize = msg.packetsize-2

    found = 0
    for header in NTRPHeader_e:
        if header.value == raw_bytearray[4]:    
            msg.header = header
            found = 1
            break
    if found==0: return None

    msg.dataID = int(raw_bytearray[5])
    
    if(msg.header==NTRPHeader_e.MSG.value): datasize = msg.dataID
    for i in range(datasize):
        msg.data.append(raw_bytearray[i+6])

    if chr(raw_bytearray[msg.packetsize+4]) != NTRP_ENDBYTE : return None
    return msg

# @param message = NTRPMessage
# if error : returns None 
# return bytearray 
def NTRP_Unite(message=NTRPMessage):
    arr = bytearray([ord(NTRP_STARTBYTE),ord(message.talker),ord(message.receiver)])
    # arr.append(ord(NTRP_STARTBYTE))
    # arr.append(ord(message.talker))
    # arr.append(ord(message.receiver))
    
    if len(message.data)+2>NTRP_MAX_PACKET_SIZE: return None
    arr.append(len(message.data)+2)
    
    #NTRP_Packet_t
    arr.append(message.header.value)
    arr.append(message.dataID)
    arr.extend(message.data)
    #NTRP_Packet_t

    arr.append(ord(NTRP_ENDBYTE))
    return arr

def NTRP_LogMessage(message=NTRPMessage):
    print("TALKERID: ",message.talker)
    print("RECEIVERID: ",message.receiver)
    print("PACKETLEN: ",message.packetsize)
    print("HEADER: ", message.header.name)
    print("DATID: ", message.dataID)
    print("DATA: ", NTRP_bytes(message.data))


def NTRP_bytes(byt):
    msg = binascii.hexlify(byt)
    txt = "/x"
    ct = 0
    for ch in msg:
        if ct == 2: 
            txt += "/x"
            ct = 0
        txt += chr(ch).upper()
        ct+=1
    return txt
