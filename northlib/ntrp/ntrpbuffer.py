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
import northlib.ntrp.ntrp as ntrp
__author__ = 'Yeniay RD'
__all__ = ['NTRPBuffer']

class NTRPBuffer():

    """ 
    LIFO Ring buffer.
    NTRP Protocol needs to fast communication
    So LIFO ring buffer helps get latest data
    & memory management. 
    """
    
    def __init__(self, size=30):

        self.rxbuffer = []
        for i in range(size+1):self.rxbuffer.append(None)

        self.rxsize = size+1
        self.index = 1
        self.mutex = False
        self.sp = 0

    def _waitMutex(self):
        time.sleep(0.0001)
        while self.mutex == True:
            time.sleep(0.0001)
    
    def append(self,msg):
        self._waitMutex()
        self.mutex = True
        self.index += 1
        if self.index >= self.rxsize: self.index = 0
        if self.index == self.sp: self.sp += 1
        if self.sp == self.rxsize: self.sp = 0

        self.rxbuffer[self.index] = msg

        self.mutex = False
            
    def read(self)->ntrp.NTRPMessage:
        if not self.isAvailable(): return None
        self._waitMutex()
        self.mutex = True
        msg = self.rxbuffer[self.index]
        self.index -= 1
        if self.index < 0: self.index = self.rxsize-1
        self.mutex = False
        return msg
    
    def isAvailable(self):
        dif = self.index - self.sp
        if dif == 1: return 0
        return abs(dif)-1 
    
    def getBuffer(self):
        return self.rxbuffer
    
    def flush(self):
        while self.isAvailable()>0:
            self.read()
