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
from northlib.ntrp.northpipe import NorthNRF
from northlib.ntrp.ntrpbuffer import NTRPBuffer
from northlib.ncmd.nrxtable import NrxTable
from northlib.ncmd.nrxtable import NrxTableLog

import northlib.ncmd.nrx as nrx
import northlib.ntrp.ntrp as ntrp

__author__ = 'Yeniay RD'
__all__ = ['NorthCOM']


class NorthCOM(NorthNRF):

    """ 
    NorthCommander Core Class
    Set URI : radio:/radioindex/ch/bandwidth/address

    Communicates with agent.
    Parameter, Function Syncronisation
    """

    CMD_PARAM_CONTENT    = 1
    CMD_FUNCTION_CONTENT = 2

    def __init__(self, uri="radio:/0/76/2/E7E7E7E301"):
        self.uri = uri
        part = uri.split('/')
        super().__init__(int(part[1]),int(part[2]),int(part[3]),part[4])

        #Set UAVCOM Based Callback Functions        
        self.setCallBack(ntrp.NTRPHeader_e.ACK,self.rxACK)
        self.setCallBack(ntrp.NTRPHeader_e.NAK,self.rxNAK)
        self.setCallBack(ntrp.NTRPHeader_e.SET,self.rxSET)
        self.setCallBack(ntrp.NTRPHeader_e.LOG,self.rxSET)
        self.setCallBack(ntrp.NTRPHeader_e.CMD,self.rxCMD)        
        self.setCallBack(ntrp.NTRPHeader_e.MSG,self.rxMSG)
        #Default mode : Received value handled by callback functions
        self.setRxHandleMode(self.RX_HANDLE_MODE_CALLBACK)
        #Set Dongle to Transceiver Mode
        self.txTRX()

        self.connection = False
        self.paramtable = NrxTable()

    """ ACK Request to Sended MESSAGE """
    def connect(self,timeout = 30):
        rettime = self.waitConnection(timeout)
        if rettime > 0 : 
            self.printID("connected in " + str(rettime) + " seconds.")
            self.connection = True
        else: self.connection = False

    """ NRX Table Synchronisation """
    def synchronize(self):
        self.setRxHandleMode(self.RX_HANDLE_MODE_BUFFER)
        i=0
        miss = 0
        self.rxbuffer.flush()
        while 1:
            self.txCMD(dataID=self.CMD_PARAM_CONTENT,channels=bytearray([i]))
            time.sleep(0.01)
            if self.rxbuffer.isAvailable()<1:
                miss+=1 
                if miss > 50: self.printID("Too much missing command! : " + str(miss))
                continue

            msg = self.rxbuffer.read()
            if (msg.header == ntrp.NTRPHeader_e.ACK): break
            if not (msg.header == ntrp.NTRPHeader_e.CMD) : continue
            if not (msg.dataID == self.CMD_PARAM_CONTENT): continue 
            self.paramtable.tableAppend(msg.data)
            i+=1

        NrxTableLog(self.paramtable)
        self.setRxHandleMode(self.RX_HANDLE_MODE_CALLBACK)

    def getParamTable(self):
        return self.paramtable

    def SET(self,name=str,value=any):
        self.paramtable.setByName(name,value)
        nx = self.paramtable.search(name)
        if nx == None: return 
        arr = self.paramtable.getByIndex(nx.index)
        self.txSET(nx.index,arr)

    def GET(self,name=str)->nrx.Nrx:
        nx = self.paramtable.search(name)
        if nx == None: return None
        self.txGET(nx.index)
        return self.paramtable.getByName(name)

    def rxNAK(self,msg):
        self.printID('NAK')

    def rxACK(self,msg):
        self.printID('ACK')

    def rxCMD(self,msg=ntrp.NTRPMessage()):
        if msg.dataID == self.CMD_PARAM_CONTENT:
            self.paramtable.tableAppend(msg.data)

    def rxSET(self,msg=ntrp.NTRPMessage()):
        if not self.paramtable.setByIndex(msg.dataID,msg.data):
            self.printID("rxSET Not found in the table : " + str(msg.dataID))
            return
