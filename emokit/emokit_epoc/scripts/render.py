#!/usr/bin/python


try:
	import psyco
	psyco.full()
except:
	print 'No psyco.  Expect poor performance.'

import pygame, sys, time, logging
from emotiv import Emotiv

from scipy.fftpack import rfft, fft, fftshift
from scipy import *

ranges = [float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13)]
avgs = [float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13), float(1<<13)]

class Grapher(object):
	def __init__(self, screen, name, i):
		self.screen = screen
		self.name = name
		self.range = ranges[i]
		#self.range = float(1 << 13)
		self.xoff = 40
		self.y = i * gheight
		self.buffer = []
		self.nxbuffer = []
		self.fftnxbuffer = []
		font = pygame.font.Font(None, 24)
		self.text = font.render(self.name, 1, (255, 0, 0))
		self.textpos = self.text.get_rect()
		self.textpos.centery = self.y + hgheight
		self.avg = avgs[i]
	
	def update(self, packet):
		if len(self.buffer) == screen_w - self.xoff:
			self.buffer = self.buffer[1:]
		self.buffer.append(getattr(packet, self.name))
		(x,strength) = getattr(packet, self.name)
		nx = self.calcNY(x)
		if len(self.nxbuffer) == screen_w - self.xoff:
			self.nxbuffer = self.nxbuffer[1:]
		self.nxbuffer.append(nx)
		
		if len(self.nxbuffer) > 1:
                        self.fftnxbuffer = fft(self.nxbuffer)
                        #print self.nxbuffer, self.fftnxbuffer
	
	def calcNY(self, val):
		# normalized data range between 0 and 1
		self.avg = (self.avg*99 + val)/100
		return (val / self.range - self.avg/self.range)

	def calcY(self, val):
		# data adjusted to screen pixel height
		return int(val * gheight * 50 + self.avg/self.range*gheight)
	
	def calcfftY(self, val):
		# data adjusted to screen pixel height
		return int(val * gheight)
	
	def draw(self):
		if len(self.buffer) == 0:
			print "no data"
			return
		nx = self.calcNY(self.buffer[0][0])
		pos = self.xoff, self.calcY(nx) + self.y
		for i, (x, strength) in enumerate(self.buffer):
			nx= self.calcNY(x)
			y = self.calcY(nx) + self.y
			if strength == 0:
				color = (0, 0, 0)
			elif strength == 1:
				color = (255, 0, 0)
			elif strength == 2:
				color = (255, 165, 0)
			elif strength == 3:
				color = (255, 255, 0)
			elif strength == 4:
				color = (0, 255, 0)
			else:
				color = (255, 255, 255)
			pygame.draw.line(self.screen, color, pos, (self.xoff + i, y))
			pos = (self.xoff+i, y)
		self.screen.blit(self.text, self.textpos)

	def drawfft(self):
		if len(self.fftnxbuffer) == 0:
			print "no data"
			return
		#print self.fftnxbuffer[0]
		nx = self.fftnxbuffer[0]
		pos = self.xoff, self.calcfftY(abs(nx)) + self.y
		for i, x in enumerate(self.fftnxbuffer[0:len(self.fftnxbuffer)/2]):  #[5:60]):
			y = self.calcfftY(abs(x)) + self.y
                        color = (0, 165, 255)
			pygame.draw.line(self.screen, color, pos, (self.xoff + 2*i, y))
			pos = (self.xoff+2*i, y)
		self.screen.blit(self.text, self.textpos)

def main(debug=False):
	global gheight, screen_w, screen_h
	
	pygame.init()
	screen = pygame.display.set_mode((screen_w, screen_h))
	
	curX, curY = screen_w / 2, screen_h / 2
	
	graphers = []
	for name in 'AF3 F7 F3 FC5 T7 P7 O1 O2 P8 T8 FC6 F4 F8 AF4'.split(' '):
		graphers.append(Grapher(screen, name, len(graphers)))
	
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				return
		
		updated = False
		for packet in emotiv.dequeue():
			updated = True
			if abs(packet.gyroX) > 1:
				curX -= packet.gyroX - 1
			if abs(packet.gyroY) > 1:
				curY += packet.gyroY
			curX = max(0, min(curX, screen_w))
			curY = max(0, min(curY, screen_h))
			map(lambda x: x.update(packet), graphers)
		
		if updated:
			screen.fill((75, 75, 75))
			map(lambda x: x.drawfft(), graphers)
			map(lambda x: x.draw(), graphers)
			pygame.draw.rect(screen, (255, 255, 255), (curX-5, curY-5, 10, 10), 0)
			pygame.display.flip()
		time.sleep(1.0/120)


emotiv = None

try:
	logger = logging.getLogger('emotiv')
	logger.setLevel(logging.INFO)
	log_handler = logging.StreamHandler()
	logger.addHandler(log_handler)

	emotiv = Emotiv()

	screen_w = 1200
        screen_h = 800


	gheight = screen_h / 16
	hgheight = gheight >> 1
	
	main(*sys.argv[1:])

finally:
	if emotiv:
		emotiv.close()
