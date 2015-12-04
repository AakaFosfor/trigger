/*BOARD lli 0x001000 0x2000 A24
*/
/*REGSTART32 */

// LLI sender, base address: 0x001000
#define SERIAL_NUMBER     0x001000
#define STATUS            0x001004
#define CONTROL           0x001010
// LLI receiver, base address: 0x002000
#define SERIAL_NUMBER     0x002000
#define STATUS            0x002004
#define DATA0             0x002008
#define DATA1             0x00200C
#define DATA2             0x002010
#define DATA3             0x002014
#define DATA4             0x002018
#define DATA5             0x00201C
#define DATA6             0x002020
#define DATA7             0x002024
#define DATA8             0x002028
#define DATA9             0x00202C
#define CLK_PATTERN       0x002030
#define DW_SAVE_DATA      0x002034
#define DW_CHECKER_RESET  0x002038
#define WORD_ERROR_COUNT  0x00203C
#define WORD_ERROR_RATE   0x002040
#define BIT_ERROR_COUNT   0x002044
#define BIT_ERROR_RATE    0x002048

/*REGEND */

extern int quit;
#include <string.h>
#include <stdio.h>
#include <unistd.h>   //usleep
#include "vmewrap.h"
#include "vmeblib.h"
extern char BoardName[];
extern char BoardBaseAddress[];
extern char BoardSpaceLength[];
extern char BoardSpaceAddmod[];

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

