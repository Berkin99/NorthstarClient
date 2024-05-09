#!/usr/bin/env pythonh
# -*- coding: utf-8 -*-
#  __  __ ____ _  __ ____ ___ __  __
#  \ \/ // __// |/ //  _// _ |\ \/ /
#   \  // _/ /    /_/ / / __ | \  / 
#   /_//___//_/|_//___//_/ |_| /_/  
# 
#   2024 Yeniay Uav Flight Control Systems
#   Research and Development Team

import threading
import pygame
import time
import math

__author__ = 'Yeniay RD'
__all__ = ['Controller','Dynamo']

class Controller():
    """ 
    NTRP Joystick Controller
    Dynamic Throttle 
    """
    THREAD_SLEEP = 0.002
    
    def __init__(self,dynamic=False):
        self.isAlive = False
        self.axis = [0,0,0,0,0,0] # x : y : z : throttle : break : HZ 
        self.battery = 1
        self.dynamic = dynamic
        if dynamic:
            self.dynChannel = Dynamo()

        pygame.init()
        pygame.joystick.init()

        if not self.findController(): 
            print("NPX:/> Joystick Not Found.")
        
    
    def findController(self):
        if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)  # First Founded JOYSTICK 
                self.joystick.init()
                self.ctrlThread = threading.Thread(target=self.ctrlProcess,daemon=True)
                self.ctrlThread.start()
                return True
        else:
            return False 
        
    def ctrlProcess(self):
        self.isAlive = True
        while self.isAlive:
            for event in pygame.event.get(pygame.JOYAXISMOTION):
                self.axis[0] = int(((self.joystick.get_axis(1)+1)*255)/2)
                self.axis[1] = int(((self.joystick.get_axis(0)+1)*255)/2)
                self.axis[2] = 254 - int(((self.joystick.get_axis(2)+1)*255)/2)
                self.axis[3] = int(((self.joystick.get_axis(5)+1)*255)/2) #Throttle
                self.axis[4] = int(((self.joystick.get_axis(4)+1)*255)/2) #Break
            
            for event in pygame.event.get(pygame.JOYBUTTONDOWN):
                self.axis[5] = int(self.joystick.get_button(9))
            for event in pygame.event.get(pygame.JOYBUTTONUP):
                self.axis[5] = int(self.joystick.get_button(9))

            if self.dynamic and self.axis[5]==0:
                self.dynChannel.calculate(self.axis[3],self.axis[4],self.THREAD_SLEEP)

            time.sleep(self.THREAD_SLEEP)
            # print(self.getAxisRaw())

        print("NPX:/> CTRL Process end.")

    def getAxisRaw(self):
        if not self.dynamic:
            return self.axis[0:4]
        arr =  self.axis[0:3] # x : y : z [0,255]
        arr.append(int(self.dynChannel.chval)) # power [0,255]
        arr.append(int(self.axis[5]))
        return arr
    
    def getAxis(self):
        return bytearray(self.getAxisRaw())

    def destroy(self):
        self.isAlive = False

class Dynamo:
    """
    Dynamic Channel:
    channel = 0 to 255 int
    """
    CH_MAX = 255
    CH_MIN = 0
    MELTPOINT = 10
    CF_MELT = 1
    
    def __init__(self,throttle_ps=1.0, break_ps=1.4):
        self.throttle_ps = throttle_ps
        self.break_ps = break_ps
        self.chval = 0
        self.energy = 0.0
    
    #dt = deltatime in seconds  
    def calculate (self,ch_t=int,ch_b=int, dt=float):    
        self.chval += ch_t*self.throttle_ps*dt
        self.chval -= ch_b*self.break_ps*dt
        
        if ch_t<self.MELTPOINT: 
            self.energy -= self.energy *dt
            self.chval -= self.energy*dt
            self.chval -= self.CF_MELT * dt
        else : self.energy = (self.chval*dt)+(self.energy*(1-dt))

        if self.chval < self.CH_MIN : self.chval = self.CH_MIN
        elif self.chval > self.CH_MAX : self.chval = self.CH_MAX
        return self.chval
    

# print("REMOVE TESTING PRINT")
# test = Controller(True)
# while 1:
#     pass




