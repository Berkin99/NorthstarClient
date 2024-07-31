#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  __  __ ____ _  __ ____ ___ __  __
#  \ \/ // __// |/ //  _// _ |\ \/ /
#   \  // _/ /    /_/ / / __ | \  / 
#   /_//___//_/|_//___//_/ |_| /_/  
# 
#   2024 Yeniay Uav Flight Control Systems
#   Research and Development Team

from enum import Enum
import struct

from northlib.ntrp.northpipe import NorthNRF
from northlib.ntrp.ntrpbuffer import NTRPBuffer
import northlib.ntrp.ntrp as ntrp
import northlib.ncmd.nrx as nrx

__author__ = 'Yeniay RD'
__all__ = ['NrxTable']

class NrxTable:

    MAX_GROUP_NX = 6
    MAX_TABLE_LEN = 255

    def __init__(self) -> None:
        self.table      = []
        self.indexMap   = []
        self.ingroup = False

    def tableAppend(self,rawbytes):
        nrxElement = nrx.NrxParse(rawbytes)
        if nrxElement.index != len(self.table): return #Append error

        """ DEBUG ELEMENT
        nrx.NrxLog(nrxElement)
        """

        self.table.append(nrxElement)
        if self.ingroup == False: 
            self.indexMap.append(nrxElement.index)

        if nrxElement.type.varType == nrx.NrxType_e.GROUPSTART:
            self.ingroup = True
        elif nrxElement.type.varType == nrx.NrxType_e.GROUPSTOP:
            self.ingroup = False
    
    """ 
    Search with given string
    @return : Found Nrx object 
    """
    def search(self,name = str)->nrx.Nrx:
        part = name.split('.',1)
        nx = None
        for ix in self.indexMap:
            if self.table[ix].name == part[0]:
                nx = self.table[ix]
        
        if len(part)<2: return nx 
        if nx==None: return None

        inx = nx.index+1

        while not self.table[inx].type.group:
            if self.table[inx].name == part[1]:
                return self.table[inx]
            inx+=1

        return None

    """
    Search with table index int
    @return : nrx bytearray value 
    """
    def getByIndex(self,index=int)->bytearray:
        if index>len(self.table): return None
        nx = nrx.Nrx()
        nx = self.table[index]
        if not nx.type.group: return nx.getValueRaw()
        arr = bytearray()
        inx = nx.index+1
        while not self.table[inx].type.group:
            altarr = self.table[inx].getValueRaw()
            arr.extend(altarr)
            inx += 1
            if inx>nx.index+self.MAX_GROUP_NX: break
            if inx>=len(self.table):break
        
        return arr

    def getByName(self,name = str)->any:
        nx = self.search(name)
        if not nx.type.group: return nx.value
        arr = []
        inx = nx.index+1
        while not self.table[inx].type.group:
            altarr = self.table[inx].value
            arr.append(altarr)
            inx += 1
            if inx>nx.index+self.MAX_GROUP_NX: break
            if inx>=len(self.table) :break
        
        return arr
        

    def setByIndex(self,index = int, rawbytes = bytearray()):
        nx = self.table[index]
        if nx == None: return False

        if not nx.type.group:
            nx.setValueRaw(rawbytes) 
            return True
        
        index+=1
        nx = self.table[index]
        byteindex = 0
        bytemax = len(rawbytes)
        
        while not nx.type.group:
            nx = self.table[index]
            if nx == None: return False
            if bytemax < (byteindex + nx.type.varBytes): break
            altbytes = rawbytes[byteindex:byteindex+nx.type.varBytes]
            byteindex += nx.type.varBytes
            nx.setValueRaw(altbytes)
            index += 1
        
        return True
        

    def setByName(self,name=str, value = any):
        nx = self.search(name)
        if nx == None: return
        if not nx.type.group: 
            nx.value = value
            return
        inx = nx.index+1

        for i in range(len(value)):
            if self.table[inx+i].type.group: break
            self.table[inx+i].value = value[i]



def NrxTableLog(table = NrxTable()):
    for i in range(len(table.table)):
        nrx.NrxLog(table.table[i])