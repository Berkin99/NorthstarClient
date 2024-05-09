#!/usr/bin/env pythonh
# -*- coding: utf-8 -*-
#  __  __ ____ _  __ ____ ___ __  __
#  \ \/ // __// |/ //  _// _ |\ \/ /
#   \  // _/ /    /_/ / / __ | \  / 
#   /_//___//_/|_//___//_/ |_| /_/  
# 
#   2024 Yeniay Uav Flight Control Systems
#   Research and Development Team

import serial
import serial.tools.list_ports
import time

__author__ = 'Yeniay RD'
__all__ = ['NorthPort']

class NorthPort(): 
    """
    NTRP Serial Com Port
    Handles the serial com object.
    Prevents com call intersections. 
    """
    AUTOBAUDRATE    = 0
    NO_CONNECTION   = 0
    READY           = 1
    BUSY            = 2
    
    def __init__(self, com=None, baudrate=AUTOBAUDRATE):
        self.mode = self.NO_CONNECTION
        self.baudrate = None
        self.com      = None
        self.port     = None
        self.setSerial(com,baudrate)

    def setSerial(self,com=None,baudrate=AUTOBAUDRATE):
        
        if self.port != None:
            self.mode = self.NO_CONNECTION  #No Connection info for Rx Thread
            self.port.close()               #Need to close current active port for open new one 
        
        self.com = com
        self.baudrate = baudrate
        try:
            self.port = serial.Serial(self.com,self.baudrate,timeout=1)
            self.mode = self.READY
        except serial.SerialException as error:
            self.errorSerial() #Serial Port Problem 
    
    def errorSerial(self):
            self.mode = self.NO_CONNECTION
            self.port = None 
            print(self.com + " PORT : NO CONNECTION")
            self.destroy()

    def getAvailablePorts():
        return [port.device for port in serial.tools.list_ports.comports()]

    def receive(self):
        if self.mode == self.NO_CONNECTION: return None
        try:
            if not (self.port.in_waiting > 0): return None         
            msg = self.port.read(1) 
            return msg
        except serial.SerialException as error:
            self.errorSerial()
            return
        
    def transmit(self,byt):
        if self.mode == self.NO_CONNECTION: return
        if byt!= None:
            try:
                self.port.write(byt)
            except serial.SerialException:
                self.errorSerial()
            
    def destroy(self):
        self.mode = self.NO_CONNECTION
        if self.port != None:
            self.port.reset_output_buffer()
            self.port.close()
            self.port = None

