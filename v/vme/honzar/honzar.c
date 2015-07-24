/*BOARD simple 0x002000 0x1000 A24
*/

/*REGSTART32 */
#define SERIAL_NUMBER         0x000
#define STATUS                0x004
//#define XXXXXXXXXXX           0x008
#define DW_RECEIVER_RESET     0x00C
#define DW_CHECKER_RESET      0x010
#define CLOCK_DELAY           0x014
#define DATA_DELAY            0x018
//#define XXXXXXXXXXX           0x01C
#define SCOPE_DATA            0x020
#define CHECKER_SCOPE         0x024
#define START_COUNT           0x028
#define WORD_ERROR_COUNT      0x02C
#define WORD_ERROR_RATE       0x030
#define BIT_ERROR_COUNT       0x034
#define BIT_ERROR_RATE        0x038
//
#define TEMP_START            0x058
#define TEMP_STATUS           0x05c
#define TEMP_READ             0x060
/*REGEND */

extern int quit;
#include <string.h>
#include <stdio.h>
#include <unistd.h>   //usleep
#include <sys/time.h>
#include "vmewrap.h"
#include "vmeblib.h"
//#include "vmeblib.h"
extern char BoardName[];
extern char BoardBaseAddress[];
extern char BoardSpaceLength[];
extern char BoardSpaceAddmod[];

/*FGROUP TOP GUI Status
Show status of the board
*/

/* FGROUP
int example(int n, char *string, char c)
int: only >=0
string: \"abc\"
char: 'ch'
float: not supported as parameter
*/
int example(int n, char *strg, char ch) {
	//printf("number:%d fpn:%f strg:%s c:%c\n", n,fpn, strg, c);
	printf("number:%d strg:%s c:%c\n", n, strg, ch);
	return(n);
}

/* FGROUP
float not suported neither in function result
*/
float fexa(int ifpn) {
	float rcf;
	printf("fexa.ifpn:%d returning float (not supported!)...\n",ifpn); rcf=ifpn;
	return(rcf);
}

/*FGROUP
address: rel. adress (4, 8, 12,... for 32 bits words readings)
loops: 0: endless loop
value: 0: read only
       1: read + print
      >1: write, no print
mics: mics between vme reads/writes. 0: do not wait between vme r/w
*/
void vmeloop(w32 address, int loops, w32 value, int mics, int inc) {
	int todoloops= loops;
	while(1) {
		if(loops>0) {
			if(todoloops>0) {
				todoloops--;
			} else {
				break;
			};
		};
		if(value<=1) {
			w32 val;
			printf("vmer32(0x%x);\n", address); val = vmer32(address);
			if(value==1) {
				printf("read [0x%x]: 0x%x (%u)\n", address, val, val); 
				fflush(stdout);   //nebavi
			};
		} else {   
			vmew32(address, value);
		};
		if(mics>0) micwait(mics);
		address += inc;
	};
}

int readTemp() {
	w32 status;
	bool tempOK = false;
	
	vmew32(TEMP_START, 0x123);
	for(int i = 0; i < 3; i++) {
		usleep(300);
		status = vmer32(TEMP_STATUS);
		if((status & 0x1) == 0) {
			tempOK = true;
			break;
		}
	};
	if (tempOK) {
		return vmer32(TEMP_READ)&0xff;
	} else {
		return -1000;
	}
}

/*FGROUP
read temperature in loop, with 1 s intervals
loops: integer, how many times to read
*/
void tempLoop(int loops) {
	int temp;
	while (loops--) {
		temp = readTemp();
		if (temp == -1000) {
			printf("Temperature read error!\n");
		} else {
			printf("Temperature: %d °C\n", temp);
		}
		micwait(1000000);
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
	int nn=0, nerrors=0;
	setseeds(7,3);
	while(1) {
		int ixreg; w32 address, val, val2;
		for(ixreg=0; ixreg<Nregs; ixreg++) {
			val= rounddown(bitmask * rnlx()); val= bitmask&val;
			address= fromaddr+(ixreg*4);
			vmew32(address, val);
			val2= vmer32(address)&bitmask;
			if((val!= val2) || (loops==(nn+1))) { // print last loop
				printf("Addr:0x%x Written:0x%x Read:0x%x\n", address, val, val2);
				if(val!=val2) nerrors++;
			}; 
			if(nerrors>10) goto STOPTEST;
		};
		nn++;
		if(nn>=loops) break;
	};
	STOPTEST: 
	printf("Loops:%d errors:%d\n", nn, nerrors);
	return;
}

/*FGROUP
Test data a look for errror

count: number of pattern to test
*/
void testData(int count) {
	w32 data;
	int j, i, errors;
	bool found;
	const w32 pattern[15] = {
		0x80786655,
		0x786655F8,
		0x6655F81E,
		0x55F81E33,
		0xF81E33AD,
		0x1E33ADE6,
		0x33ADE62D,
		0xADE62D9E,
		0xE62D9E4B,
		0x2D9E4BCB,
		0x9E4BCBB3,
		0x4BCBB3D5,
		0xCBB3D580,
		0xB3D58078,
		0xD5807866
	};
	
	errors = 0;
	for (i = 0; i < count; i++) {
		data = vmer32(SCOPE_DATA);
		found = false;
		for (j = 0; j < 15; j++) {
			if (data == pattern[j]) {
				found = true;
				break;
			}
		}
		if (!found) {
			if (errors <= 20) {
				printf("Found unknown pattern: 0x%x\n", data);
			}
			if (errors == 21) {
				printf("... and more.\n");
			}
			errors++;
		}
	}
	
	printf("\nFound %u errors out of %u data sampled (%2.2f %%).\n", errors, count, (100*errors/(float)count));
}

double time_diff(struct timeval x , struct timeval y)
{
	double x_ms, y_ms, diff;

	x_ms = (double)x.tv_sec*1000000 + (double)x.tv_usec;
	y_ms = (double)y.tv_sec*1000000 + (double)y.tv_usec;

	diff = (double)y_ms - (double)x_ms;

	return diff;
}

/*FGROUP
Collect actual error rates to make a plot

count: number of data points to get
*/
void makePlot(int points) {
	FILE * fp;
	w32 count, countOld;
	struct timeval t, tOld;
	
	fp = fopen("./WORK/plot.csv", "w");
	gettimeofday(&t, NULL);
	count = vmer32(WORD_ERROR_COUNT);
	for (int i = 0; i < points; i++) {
		sleep(1);
		tOld = t;
		countOld = count;
		gettimeofday(&t, NULL);
		count = vmer32(WORD_ERROR_COUNT);
		fprintf(fp, "%e; %u\n", time_diff(tOld, t), (count-countOld));
	}
	fclose(fp);
}


void initmain() {
	printf(
		"Here initmain. BoardName:%s\nBoardBaseAddress:%s BoardSpaceLength%s BoardSpaceAddmod:%s\n",
		BoardName, BoardBaseAddress, BoardSpaceLength, BoardSpaceAddmod);
	micwait(1);   // calibrate micwait
}

void boardInit() {
	printf("boardInit called...\n");
}

void endmain() {
	printf("endmain called...\n");
}

