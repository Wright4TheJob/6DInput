'''
Test program for the open-source 3D mouse

Move a cube around on the screen.

Adrian Bowyer
RepRap Ltd

4 June 2021

https://reprapltd.com

Licence: GPL

Uses code from https://stackoverflow.com/questions/16263727/3d-cube-didnt-show-correctly-writen-by-pyglet

'''


import sys
import pyglet
from pyglet.gl import *
from pyglet import window
import serial
import re
import time
import numpy as np
import math as maths

arduinoPort = '/dev/ttyUSB0'

axes = ('X', 'Y', 'Z', 'Rx', 'Ry', 'Rz')

# Swap directions if needs be

#sense = np.array([1, 1, 1, 1, 1, 1])
mapping = (0, 1, 2, 3, 4, 5)

class OS3DMouse:

 def __init__(self, port):
  self.usb = serial.Serial(port,115200,timeout=0.1)
  time.sleep(3) # Why so long???
  self.ReZero()
  self.SetVectors()
  print("Mouse initialised: ", self.v0)

 def ReZero(self):
  self.v0 = self.GetHallReadings()

 def GetHallReadings(self):
  self.usb.write(str.encode('6\n'))
  data = self.usb.readline()
  data = str(data.decode('ascii'))
  data = re.findall('\d+', data)
  result =  np.zeros(shape=(6))
  for i in range(6):
    result[i] = int(data[mapping[i]])
  return result

 def Movement(self):
  v = np.subtract(self.GetHallReadings(), self.v0)
  v = self.FindVector(v)
  return np.array([v[0], v[1], v[2], 0.0, 0.0, 0.0])

 def Sample(self):
  d2 = -1.0
  big2 = 4.0
  mBig = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
  while d2 < 4000:
   m = self.Movement()
   d2 = np.sum(m**2)
   if d2 > big2:
    big2 = d2
    mBig = m
  return mBig

 def SetVectors(self):
  PXr = np.array([58.0, -3.0, -24.0, 2.0, 7.0, -2.0])
  d2 = np.inner(PXr, PXr)
  d2 = 1.0/maths.sqrt(d2)
  PXr = np.multiply(PXr, d2)

  MXr = np.array([-29.0,   1.0,  56.0,  -4.0,  -5.0,   2.0])
  d2 = np.inner(MXr, MXr)
  d2 = 1.0/maths.sqrt(d2)
  MXr = np.multiply(MXr, d2)

  PYr = np.array([-20.0,   2.0,  -5.0,   0.0,  60.0,  -3.0])
  d2 = np.inner(PYr, PYr)
  d2 = 1.0/maths.sqrt(d2)
  PYr = np.multiply(PYr, d2)

  MYr = np.array([55.0,  -4.0,   8.0,   1.0, -31.0,   3.0])
  d2 = np.inner(MYr, MYr)
  d2 = 1.0/maths.sqrt(d2)
  MYr = np.multiply(MYr, d2)

  PZr = np.array([-43.0,  -4.0, -34.0,  -4.0, -32.0,  -3.0])
  d2 = np.inner(PZr, PZr)
  d2 = 1.0/maths.sqrt(d2)
  PZr = np.multiply(PZr, d2)

  MZr = np.array([-32.0,  27.0, -28.0,  30.0,  -7.0,  28.0])
  d2 = np.inner(MZr, MZr)
  d2 = 1.0/maths.sqrt(d2)
  MZr = np.multiply(MZr, d2)
  
  self.Rotations = [PXr, MXr, PYr, MYr, PZr, MZr]
  self.ROut = [
      np.array([1, 0, 0]),
      np.array([-1, 0, 0]),
      np.array([0, 0, -1]),
      np.array([0, 0, 1]),
      np.array([0, 1, 0]),
      np.array([0, -1, 0])
  ]

 def FindVector(self, v):
  max = -sys.float_info.max
  ip = maths.sqrt(np.inner(v, v))
  if ip < 0.001:
      return np.array([0, 0, 0])
  vN = np.multiply(v, 1.0/ip)
  for r in range(self.Rotations.__len__()):
   ipv = np.inner(vN, self.Rotations[r])
   if ipv > max:
    out = self.ROut[r]
    max = ipv
  return np.multiply(out, ip)


# return a ctype array - GLfloat, GLuint

def vector(type, *args):
    return (type*len(args))(*args)


class model:
    def __init__(self, vertices, colorMatrix, index, mouse):
        self.vertices = vector(GLfloat, *vertices)
        self.colourMatrix = vector(GLfloat, *colorMatrix)
        self.index = vector(GLuint, *index)
        self.Recentre()
        self.mouse = mouse

    def update(self):
        move = self.mouse.Movement()
        a = np.multiply(np.array([move[0], move[1], move[2]]), 1.0/20.0)
        p = np.multiply(np.array([move[3], move[4], move[5]]), 1.0/60.0)
        self.angle = np.remainder(np.add(self.angle, a), 360)
        self.position = np.add(self.position, p)

    def Recentre(self):
        self.angle = np.array([0.0, 0.0, 0.0])
        self.position = np.array([0.0, 0.0, 0.0])

    def draw(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glRotatef(self.angle[0], 1, 0, 0)
        glRotatef(self.angle[1], 0, 1, 0)
        glRotatef(self.angle[2], 0, 0, 1)
        glTranslatef(self.position[0], self.position[1], self.position[2])

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)

        glColorPointer(3, GL_FLOAT, 0, self.colourMatrix)
        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glDrawElements(GL_QUADS, len(self.index), GL_UNSIGNED_INT, self.index)

        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)



class world:
    def __init__(self):
        self.element = []
        self.callCount = 0

    def update(self, dt):
        for obj in self.element:
            obj.update()

    def addModel(self, model):
        self.element.append(model)

    def draw(self):
        self.callCount += 1
        for obj in self.element:
            #if self.callCount >= 200:
            #    obj.Recentre()
            #    self.callCount = 0
            obj.draw()


def setup():
    # look for GL_DEPTH_BUFFER_BIT
    glEnable(GL_DEPTH_TEST)


cube = (
    3, 3, 3, #0
    -3, 3, 3, #1
    -3, -3, 3, #2
    3, -3, 3, #3
    3, 3, -3, #4
    -3, 3, -3, #5
    -3, -3, -3, #6
    3, -3, -3 #7
)


colour = (
    1, 0, 0,
    1, 0, 0,
    1, 0, 0,
    1, 0, 0,
    0, 1, 0,
    0, 1, 0,
    0, 0, 1,
    0, 0, 1
)

index = (
    0, 1, 2, 3, # front face
    0, 4, 5, 1, # top face
    4, 0, 3, 7, # right face
    1, 5, 6, 2, # left face
    3, 2, 6, 7, # bottom face
    4, 7, 6, 5  #back face
)

mouse = OS3DMouse(arduinoPort)

'''
print("+Xr")
vector = mouse.Sample()
print(vector)
time.sleep(2)
mouse.ReZero()
print("-Xr")
vector = mouse.Sample()
print(vector)
time.sleep(2)
mouse.ReZero()
print("+Yr")
vector = mouse.Sample()
print(vector)
time.sleep(2)
mouse.ReZero()
print("-Yr")
vector = mouse.Sample()
print(vector)
time.sleep(2)
mouse.ReZero()
print("+Zr")
vector = mouse.Sample()
print(vector)
time.sleep(2)
mouse.ReZero()
print("-Zr")
vector = mouse.Sample()
print(vector)
mouse.ReZero()

'''



win = window.Window(fullscreen=False, vsync=True, resizable=True, height=600, width=600)
mWorld = world()
obj = model(cube, colour, index, mouse)
mWorld.addModel(obj)

@win.event
def on_resize(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-10, 10, -10, 10, -10, 10)
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED

@win.event
def on_draw():
    glClearColor(0.2, 0.2, 0.2, 0.8)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    mWorld.draw()


pyglet.clock.schedule(mWorld.update)
setup()
pyglet.app.run()

