/*BOARD lli 0x000000 0x3000 A
*/
/*REGSTART32 */

// LLI sender, base address:        0x001000
#define S_SERIAL_NUMBER             0x001000
#define S_STATUS                    0x001004
#define S_CONTROL                   0x001010
// LLI receiver, base address:      0x002000
#define R_SERIAL_NUMBER             0x002000
#define R_STATUS                    0x002004
#define R_DATA0                     0x002008
#define R_DATA1                     0x00200C
#define R_DATA2                     0x002010
#define R_DATA3                     0x002014
#define R_DATA4                     0x002018
#define R_DATA5                     0x00201C
#define R_DATA6                     0x002020
#define R_DATA7                     0x002024
#define R_DATA8                     0x002028
#define R_DATA9                     0x00202C
#define R_CLK_PATTERN               0x002030
#define R_DW_SAVE_DATA              0x002034
#define R_DW_CHECKER_RESET          0x002038
#define R_WORD_ERROR_COUNT          0x00203C
#define R_WORD_ERROR_RATE           0x002040
#define R_BIT_ERROR_COUNT           0x002044
#define R_BIT_ERROR_RATE            0x002048
#define R_DW_DELAY_RESET            0x00204C
#define R_DW_DELAY_VALUE_RESET      0x002050
#define R_DW_DELAY_VALUE_INC        0x002054
#define R_DW_DELAY_VALUE_DEC        0x002058
#define R_DELAY_VALUE_CLOCK         0x00205C
#define R_DELAY_VALUE_DATA0         0x002060
#define R_DELAY_VALUE_DATA1         0x002064
#define R_DELAY_VALUE_DATA2         0x002068
#define R_DW_DELAY_VALUE_PLL_INC    0x00206C
#define R_DW_DELAY_VALUE_PLL_DEC    0x002070
#define R_DELAY_VALUE_PLL           0x002074


/*REGEND */

extern int quit;
#include <string.h>
#include <stdio.h>
#include <unistd.h>   //usleep
#include <sys/param.h>
#include <math.h>
#include "vmewrap.h"
#include "vmeblib.h"
extern char BoardName[];
extern char BoardBaseAddress[];
extern char BoardSpaceLength[];
extern char BoardSpaceAddmod[];

#define R_STATUS_LENGTH (5)
#define BITS_IN_WORD (308)
#define BER_CL (0.95)
// dummy value for use in dummy write commands
#define DUMMY_VALUE (1)

/*FGROUP TOP GUI SenderStatus
Show status of the sender board
*/

/*FGROUP TOP GUI ReceiverStatus
Show status of the receiver board
*/

/* FGROUP
int example(int n, char *string, char c)
int: only >=0
string: \"abc\"
char: 'ch'
float: not supported as parameter
*/
int example(int n, char *strg, char ch) {
	printf("number:%d strg:%s c:%c\n", n, strg, ch);
	return n;
}

/* FGROUP
float not suported neither in function result
*/
float fexa(int ifpn) {
	float rcf;
	printf("fexa.ifpn:%d returning float (not supported!)...\n", ifpn);
	rcf = ifpn;
	return rcf;
}

/*FGROUP
save actual received data to shaddow register and print them (hexa, in raw format)
*/
void printDataRaw() {
	vmew32(R_DW_SAVE_DATA, DUMMY_VALUE);
	printf("receiver data:\n");
	printf("R_DATA0: 0x%x\n", vmer32(R_DATA0));
	printf("R_DATA1: 0x%x\n", vmer32(R_DATA1));
	printf("R_DATA2: 0x%x\n", vmer32(R_DATA2));
	printf("R_DATA3: 0x%x\n", vmer32(R_DATA3));
	printf("R_DATA4: 0x%x\n", vmer32(R_DATA4));
	printf("R_DATA5: 0x%x\n", vmer32(R_DATA5));
	printf("R_DATA6: 0x%x\n", vmer32(R_DATA6));
	printf("R_DATA7: 0x%x\n", vmer32(R_DATA7));
	printf("R_DATA8: 0x%x\n", vmer32(R_DATA8));
	printf("R_DATA9: 0x%x\n", vmer32(R_DATA9));
}

/*FGROUP
save actual received data to shaddow register and print them (hexa)
*/
void printData() {
	vmew32(R_DW_SAVE_DATA, DUMMY_VALUE);
	printf("receiver data:\n0x%05x", vmer32(R_DATA9));
	printf("%08x", vmer32(R_DATA8));
	printf("%08x", vmer32(R_DATA7));
	printf("%08x", vmer32(R_DATA6));
	printf("%08x", vmer32(R_DATA5));
	printf("%08x", vmer32(R_DATA4));
	printf("%08x", vmer32(R_DATA3));
	printf("%08x", vmer32(R_DATA2));
	printf("%08x", vmer32(R_DATA1));
	printf("%08x\n", vmer32(R_DATA0));
}

void printBinary(int bit) {
	if (bit & 1) {
		printf("1");
	} else {
		printf("0");
	}
}

void printBinaryVector(w32 high, w32 middle, w32 low, int offset, int length) {
	int i;
	// int x = 0;
	int highLeft = MIN(MAX(offset+length-1-64, 0), 31);
	int highRight = MIN(MAX(offset-64, 0), 31);
	int middleLeft = MIN(MAX(offset+length-1-32, 0), 31);
	int middleRight = MIN(MAX(offset-32, 0), 31);
	int lowLeft = MIN(offset+length-1, 31);
	int lowRight = MIN(offset, 31);
	
	if (highLeft != highRight) {
		for (i = highLeft; i >= highRight; i--) {
			printBinary((high >> i) & 1);
			// x++;
		}
	}
	if (middleLeft != middleRight) {
		for (i = middleLeft; i >= middleRight; i--) {
			printBinary((middle >> i) & 1);
			// x++;
		}
	}
	if (lowLeft != lowRight) {
		for (i = lowLeft; i >= lowRight; i--) {
			printBinary((low >> i) & 1);
			// x++;
		}
	}
	// printf("(printed %d)", x);
}

/*FGROUP
save actual received data to shaddow register and print them (binary)
*/
void printDataBinary() {
	w32 high, middle, low;
	vmew32(R_DW_SAVE_DATA, DUMMY_VALUE);
	printf("receiver data:\n");

	high = vmer32(R_DATA9); // 20 bits
	middle = vmer32(R_DATA8);
	low = vmer32(R_DATA7);
	printf("0b");
	printBinaryVector(high, middle, low, 40, 44);
	printf("\n");

	high = middle;
	middle = low;
	low = vmer32(R_DATA6);
	printf("0b");
	printBinaryVector(high, middle, low, 28, 44);
	printf("\n");

	high = middle;
	middle = low;
	low = vmer32(R_DATA5);
	printf("0b");
	printBinaryVector(high, middle, low, 16, 44);
	printf("\n");

	high = middle;
	middle = low;
	low = vmer32(R_DATA4);
	printf("0b");
	printBinaryVector(high, middle, low, 4, 44);
	printf("\n");

	high = low;
	middle = vmer32(R_DATA3);
	low = vmer32(R_DATA2);
	printf("0b");
	printBinaryVector(high, middle, low, 24, 44);
	printf("\n");

	high = middle;
	middle = low;
	low = vmer32(R_DATA1);
	printf("0b");
	printBinaryVector(high, middle, low, 12, 44);
	printf("\n");

	high = middle;
	middle = low;
	low = vmer32(R_DATA0);
	printf("0b");
	printBinaryVector(high, middle, low, 0, 44);
	printf("\n");

}

/*FGROUP
read receiver status 10000 times and print % of individual bits in 1
*/
void testStatus() {
	w32 status;
	int counts[R_STATUS_LENGTH];
	int i, j;
	
	for (i = 0; i < R_STATUS_LENGTH; i++) {
		counts[i] = 0;
	}
	
	printf("Reading status 10000 times...\n");
	for (i = 0; i < 10000; i++) {
		status = vmer32(R_STATUS);
		for (j = 0; j < R_STATUS_LENGTH; j++) {
			if ((status>>j) & 1) {
				counts[j]++;
			}
		}
	}
	
	for (i = 0; i < R_STATUS_LENGTH; i++) {
		printf("Status[%d] in log.1 in %7.2f %% cases.\n", i, 100*(counts[i]/10000.0));
	}
}

// return number of different bits
int compareW32(w32 a, w32 b) {
	int i, result = 0;
	
	a ^= b;
	for (i = 0; i < 32; i++) {
		if ((a>>i) & 1) {
			result++;
		}
	}
	return result;
}

void getBitErrorRate(int count, int *bits, int *errors, float *ber) {
	int i;
	w32 oldControl;

	// check input to prevent overflow of errors
	if (count > (INT_MAX / BITS_IN_WORD)) {
		printf("Count is too large! Upper limit is %d.\n", INT_MAX / BITS_IN_WORD);
		return;
	}

	// backup sender mode and set it to MODE_FRAME_TOGGLE
	oldControl = vmer32(S_CONTROL);
	vmew32(S_CONTROL, 8);
	
	*errors = 0;
	// check 'count' words
	for (i = 0; i < count; i++) {
		// save received data to shaddow register
		vmew32(R_DW_SAVE_DATA, DUMMY_VALUE);
		// count errors
		*errors += compareW32(vmer32(R_DATA0), 0x00000000);
		*errors += compareW32(vmer32(R_DATA1), 0xfffff000);
		*errors += compareW32(vmer32(R_DATA2), 0x00ffffff);
		*errors += compareW32(vmer32(R_DATA3), 0x00000000);
		*errors += compareW32(vmer32(R_DATA4), 0xfffffff0);
		*errors += compareW32(vmer32(R_DATA5), 0x0000ffff);
		*errors += compareW32(vmer32(R_DATA6), 0xf0000000);
		*errors += compareW32(vmer32(R_DATA7), 0xffffffff);
		*errors += compareW32(vmer32(R_DATA8), 0x000000ff);
		*errors += compareW32(vmer32(R_DATA9),    0x00000);
	}
	// restore original sender mode
	vmew32(S_CONTROL, oldControl);	

	// calculate and print results
	*bits = count * BITS_IN_WORD;
	if (*errors == 0) {
		// calculate estimated BER for BER_CL
		// https://www.jitterlabs.com/support/calculators/ber-confidence-level-calculator/
		// VALID ONLY IF ERRORS == 0 !!!
		*ber = -log(1.0l-BER_CL)/(*bits);
	} else {
		*ber = *errors / ((float)(*bits));
	}
}

/*FGROUP
Sets sending mode to 8 (MODE_FRAME_TOGGLE) and capture 'count' words, compares
them to known pattern and print average BER. Then sets sending mode back.
*/
void printBitErrorRate(int count) {
	int bits, errors;
	float ber;
	
	printf("Reading received data %d times...\n", count);

	getBitErrorRate(count, &bits, &errors, &ber);

	printf("Found %d errors in %d bits read.\n", errors, bits);
	printf("BER %c %.2e\n", (errors == 0) ? '~' : '=', ber);
	if (errors == 0) {
		printf("  (at condidence level %.2f %%)\n", BER_CL);
	}
}

/*FGROUP
Scans all delays in range 0 to 31 and for every delay counts BER
from 'count' words.
*/
void scanDelays(int count) {
	int i;
	w32 delay, oldDelay;
	int bits, errors;
	float ber;
	
	// backup delay
	oldDelay = vmer32(R_DELAY_VALUE_CLOCK);
	
	// scan delays
	printf("Scanning delays...\n");
	for (i = 0; i < 32; i++) {
		delay = vmer32(R_DELAY_VALUE_CLOCK);
		printf("delay = %d:\n", delay);
		getBitErrorRate(count, &bits, &errors, &ber);
		printf("BER %c %.2e\n", (errors == 0) ? '~' : '=', ber);
		vmew32(R_DW_DELAY_VALUE_INC, DUMMY_VALUE);
	}

	// restore delay
	i = 0;
	delay = vmer32(R_DELAY_VALUE_CLOCK);
	while ((delay != oldDelay) && (i < 32)) {
		vmew32(R_DW_DELAY_VALUE_INC, DUMMY_VALUE);
		delay = vmer32(R_DELAY_VALUE_CLOCK);
		i++;
	}
	
	if (delay != oldDelay) {
		printf("ERROR: unable to sync back to delay %d, actual delay is %d!\n", oldDelay, delay);
	}
}

/*FGROUP
address: rel. adress (4, 8, 12,... for 32 bits words readings)
loops: 0: endless loop
value: 0: read + print
       1: read only
      >1: write, no print
mics: mics between vme reads/writes. 0: do not wait between vme r/w
*/
void vmeloop(w32 address, int loops, w32 value, int mics) {
	int todoloops = loops;
	while (1) {
		if (loops > 0) {
			if (todoloops > 0) {
				todoloops--;
			} else {
				break;
			}
		}
		if (value <= 1) {
			w32 val;
			val = vmer32(address);
			if(value == 1) {
				printf("read:0x%x %u\n", val, val); 
				fflush(stdout);   //nebavi
			}
		} else {   
			vmew32(address, value);
		}
		if (mics > 0) {
			micwait(mics);
		}
	}
}

/*FGROUP
Write/read random value into array of registers

fromaddr: first address to be tested
Nregs:    number of consecutive addresses to be tested
bitmask:  e.g. 0xff -> test only bits 7..0
loops:    number of loops over the array of registers
*/
void rndtest(w32 fromaddr, int Nregs, w32 bitmask, int loops) {
	int nn = 0, nerrors = 0;
	setseeds(7,3);
	while (1) {
		int ixreg;
		w32 address, val, val2;
		for (ixreg = 0; ixreg < Nregs; ixreg++) {
			val = rounddown(bitmask * rnlx());
			val = bitmask&val;
			address = fromaddr+(ixreg*4);
			vmew32(address, val);
			val2 = vmer32(address)&bitmask;
			if ((val != val2) || (loops == (nn+1))) { // print last loop
				printf("Addr:0x%x Written:0x%x Read:0x%x\n", address, val, val2);
				if(val != val2) {
					nerrors++;
				}
			}
			if (nerrors > 10) {
				goto STOPTEST;
			}
		}
		nn++;
		if (nn >= loops) {
			break;
		}
	}
	STOPTEST: 
	printf("Loops:%d errors:%d\n", nn, nerrors);
	return;
}

void initmain() {
	printf("Here initmain. BoardName:%s\n"\
		"BoardBaseAddress:%s BoardSpaceLength%s BoardSpaceAddmod:%s\n",
		BoardName, BoardBaseAddress, BoardSpaceLength, BoardSpaceAddmod);
	micwait(1);   // calibrate micwait
}

void boardInit() {
	printf("boardInit called...\n");
}

void endmain() {
	printf("endmain called...\n");
}

