from Tkinter import *
import tkFileDialog
import os, os.path, string, shelve
import myw
import threading

class Status:
	def __init__(self, vb, VMEaddress, bitNames, title):
		self.vb = vb
		self.tl = myw.NewToplevel(title)
		self.readLeft = 0
		
		self.VMEaddress = VMEaddress
		self.bitNames = bitNames
		self.title = title
		
		self.buildGui()
		self.refresh()
	
	def setLabel(self, i, value):
		if self.bitNames[i] == '':
			self.lblStatus[i].label(str(i)+' - (not used)')
			self.lblStatus[i].setColor('blue')
			self.lblStatus[i].configure(foreground='white')
		else:
			if value == '0':
				self.lblStatus[i].setColor('red')
			elif value == '1':
				self.lblStatus[i].setColor('green')
			elif value == '?':
				self.lblStatus[i].setColor('orange')
			else:
				self.lblStatus[i].setColor('white')
			self.lblStatus[i].label(str(i)+' - '+self.bitNames[i]+': '+value)
	
	def buildGui(self):
		self.lblTitle = myw.MywLabel(self.tl, self.title, LEFT)
		self.lblStatus = [0 for i in range(len(self.bitNames))]
		for i in range(len(self.bitNames)):
			self.lblStatus[i] = myw.MywLabel(self.tl, '', LEFT, anchor='w')
			self.setLabel(i, '?')
		self.btnRefresh = myw.MywButton(self.tl, 'Refresh', self.refresh, side=LEFT, helptext='Refresh status')
		#self.btnPeriodicRefresh = myw.MywButton(self.tl, 'Periodic refresh', myw.curry(self.periodicRefresh, 5), side=LEFT, helptext='Periodicaly refresh status')

	def refresh(self):
		statusHex = self.vb.io.execute('vmeopr32('+self.VMEaddress+')').strip()
		status = int(statusHex, 0)
		for i in range(len(self.bitNames)):
			if self.bitNames[i] == '':
				continue
			if status == 0xffffffff:
				self.setLabel(i, '?')
			else:
				val = (status >> i) & 1
				self.setLabel(i, str(val))
		if self.readLeft > 0:
			print 'starting timer...'
			self.readLeft -= 1
			self.timer = threading.Timer(2, self.refresh)
			self.timer.start()
	
	def periodicRefresh(self, count):
		self.readLeft = count
		self.refresh()
