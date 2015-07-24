from Tkinter import *
import tkFileDialog
import os, os.path, string, shelve
import myw
import threading

def neco():
	print 'neco...'

class Status:
	def __init__(self,vb):
		self.vb = vb
		self.tl = myw.NewToplevel("Status")
		self.readLeft = 0
		
		self.bitName = [
			'RECEIVER_CLK_PRESENT',
			'DELAY_READY',
			'ALIGNED',
			'',
			'CHECKER_EN',
			'CHECKER_RUNNING'
		]
		
		self.buildGui()
		self.refresh()
	
	def getLabel(self, i, valueInt):
		return self.getLabelS(i, str(valueInt))
	
	def getLabelS(self, i, valueStr):
		if self.bitName[i] == '':
			return str(i)+' - (not used)'
		else:
			return str(i)+' - '+self.bitName[i]+': '+valueStr
	
	def buildGui(self):
		self.lblTitle = myw.MywLabel(self.tl, 'Status of receiver board:', LEFT)
		self.lblStatus = [0 for i in range(len(self.bitName))]
		for i in range(len(self.bitName)):
			self.lblStatus[i] = myw.MywLabel(self.tl, self.getLabelS(i, '(unknown)'), LEFT, anchor='w')
			if self.bitName[i] == '':
				self.lblStatus[i].setColor('blue');
				self.lblStatus[i].configure(foreground='white');
		self.btnRefresh = myw.MywButton(self.tl, 'Refresh', self.refresh, side=LEFT, helptext='Refresh status')
		#self.btnPeriodicRefresh = myw.MywButton(self.tl, 'Periodic refresh', myw.curry(self.periodicRefresh, 5), side=LEFT, helptext='Periodicaly refresh status')

	def refresh(self):
		statusHex = self.vb.io.execute('vmeopr32(0x004)').strip()
		status = int(statusHex, 0)
		for i in range(len(self.bitName)):
			val = (status >> i) & 1
			self.lblStatus[i].label(self.getLabel(i, val))
			if self.bitName[i] != '':
				if val == 0:
					self.lblStatus[i].setColor("red")
				else:
					self.lblStatus[i].setColor("green")
		if self.readLeft > 0:
			print 'starting timer...'
			self.readLeft -= 1
			self.timer = threading.Timer(2, self.refresh)
			self.timer.start()
	
	def periodicRefresh(self, count):
		self.readLeft = count
		self.refresh()

class vbio2:
	def __init__(self):
		pass
	def execute(self,cmd):
		print "vbio:", cmd
		return ["0"]

class vbio:
	def __init__(self,master):
		self.master = master
		self.io = vbio2()

def main(vb):
	Status(vb)

if __name__ == "__main__":
	master = Tk()
	vb = vbio(master)
	main(vb)
	master.mainloop()