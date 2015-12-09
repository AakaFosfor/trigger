from status import *

def SenderStatus(vb):
	bitNames = [
		'PLL_LOCKED',
		'RESET'
	]
	Status(vb, '0x001004', bitNames, "Status of the LLI sender")

def ReceiverStatus(vb):
	bitNames = [
		'DATA_VALID',
		'CLOCK_VALID',
		'CHECKER_RUNNING',
		'WORD_ERROR',
		'DELAY_READY'
	]
	Status(vb, '0x002004', bitNames, "Status of the LLI receiver")
