#include "BUSYBOARD.h"

/*
 * analyze SSM - test for DDR link
 * Pospisil, July 2015
 *
 * Listen for input signals from LM0 board (cluster signals) and check for
 * pseudo-random pattern (4bit LFSR). It uses custom generator design in LM0
 * FPGA. It test LM0-BUSY DDR links for L0 clusters.
 */

//#define DEBUG

//#define POISON_INNER
//#define POISON_OUTER

const w32 patternSingle = 0x135E26BC;
#define CLUSTERS (8+1)
const int shifts[CLUSTERS] = {
	0, 4, 8, 12, 14, 3, 6, 7, 2
};
#define PATTERN_LENGTH 15
w32 pattern[PATTERN_LENGTH] = {
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0
};
#define SSM_LENGTH (1024*1024-5)
#define L0CLST1 (1<<21)
#define L0CLST2 (1<<22)
#define L0CLST3 (1<<23)
#define L0CLST4 (1<<24)
#define L0CLST5 (1<<25)
#define L0CLST6 (1<<26)
#define L0CLST7 (1<<27)
#define L0CLST8 (1<<28)
#define L0CLSTT (1<<29)
#define MASK (L0CLST1 | L0CLST2 | L0CLST3 | L0CLST4 | L0CLST5 | L0CLST6 | \
				L0CLST7 | L0CLST8 | L0CLSTT)

// http://stackoverflow.com/a/1644898
#ifdef DEBUG
	#define DEBUG_BOOL true
#else
	#define DEBUG_BOOL false
#endif
#define debug_print(fmt, ...) \
        do { if (DEBUG_BOOL) fprintf(stderr, "%s:%d:%s(): " fmt, __FILE__, \
                                __LINE__, __func__, __VA_ARGS__); } while (0)
#define debug_print_s(fmt) \
        do { if (DEBUG_BOOL) fprintf(stderr, "%s:%d:%s(): " fmt, __FILE__, \
                                __LINE__, __func__); } while (0)

typedef struct {
	int bitErrors;
	int wordErrors;
} t_errors;

void fillPattern() {
	w32 word;
	for (int i = 0; i < PATTERN_LENGTH; i++) {
		word = 0;
		for (int cluster = CLUSTERS-1; cluster >= 0; cluster--) {
			word |= (patternSingle >> (31-(shifts[cluster]+i))) & 1;
			word <<= 1;
		}
		word <<= 21-1;
		pattern[i] = word & MASK;
	}
}

void printClusters(w32 *data, int offset = 0) {
	cout << endl;
	cout << "         : 0: 1: 2: 3: 4: 5: 6: 7: 8: 9:10:11:12:13:14:" << endl;
	for (int cluster = 0; cluster < CLUSTERS; cluster++) {
		printf("Cluster %d:", cluster+1);
		for (int i = 0; i < PATTERN_LENGTH; i++) {
			if ((data[(i - offset + PATTERN_LENGTH) % PATTERN_LENGTH] >> (cluster + 21)) & 1) {
				cout << "^^^";
			} else {
				cout << "___";
			}
		}
		cout << endl;
		cout << "         :  :  :  :  :  :  :  :  :  :  :  :  :  :  :  :" << endl;
	}
	cout << endl;
}

t_errors analSSMTestDDR(w32 *sm, int snapshot) {
	w32 word;
	w32 data = 0;
	int i;
	t_errors errors = {0, 0};

	debug_print_s("Analysing...\n");

	// find pattern start at L0CLST1
	for (i = 0; i < SSM_LENGTH; i++) {
		word = sm[i];
		data = (data << 1) | ((word & L0CLST1)>>21);
		if (data == patternSingle) {
			debug_print("got it! i = %d\n", i);
			break;
		}
	}
	if (i < (32 - PATTERN_LENGTH)) {
		cout << "Pattern seen too early! i = " << i << endl;
	}
	if (i > (32-1 + PATTERN_LENGTH-1)) {
		cout << "Pattern seen too late! i = " << i << endl;
	}

	int offset = (i - (32-PATTERN_LENGTH) + 1) % PATTERN_LENGTH; // start pointer
	#ifdef DEBUG
	cout << "offset = " << offset << endl;
	cout << "Pattern:" << endl;
	printClusters(pattern, offset);
	cout << "Data:" << endl;
	printClusters(sm);
	#endif
	
	// check snapshot
	w32 test;
	w32 error;
	
	for (i = 0; i < SSM_LENGTH; i++) {
		word = sm[i] & MASK;
		#ifdef POISON_INNER
		if ((i%52429) == 0) {
			word ^= L0CLST3 | L0CLST7;
		}
		#endif
		test = pattern[(i - offset + PATTERN_LENGTH) % PATTERN_LENGTH];
		if (word != test) {
			error = word^test;
			errors.wordErrors++;
			if (errors.wordErrors < 21) {
				printf("Error! ssm = %d, i = %7d, word = 0x%08x, test = 0x%08x, error = 0x%08x\n", snapshot, i, word, test, error);
			}
			while (error) {
				errors.bitErrors += error & 1;
				error >>= 1;
			}
			if (errors.wordErrors == 21) {
				printf("More than 20 word error in this snapshot, suppressing further errors output for this snapshot.\n");
			}
		}
	}
	
	return errors;
}

int main() {
	int vmesp = -1;
	w32 *ssm;
	t_errors errors = {0, 0};
	t_errors totalErrors = {0, 0};
	BUSYBOARD *bb = new BUSYBOARD(vmesp);
	float errorRate;
	char oper;

	debug_print("vsp = %i\n", bb->getvsp());
	w32 ver = bb->getFPGAversion();
	debug_print("Version: 0x%X (%i)\n", ver, ver);
	bb->StopSSM();
	fillPattern();
	for(int snapshot = 0; true; snapshot++) {
		bb->SetMode("outmon", 'a');
		bb->StartSSM();
		usleep(50000);
		bb->StopSSM();
		bb->ReadSSM();
		ssm = bb->GetSSM()+5;
		#ifdef POISON_OUTER
		if ((snapshot % 3) == 2) {
			ssm[1234] ^= L0CLST5;
		}
		#endif
		errors = analSSMTestDDR(ssm, snapshot);
		totalErrors.bitErrors += errors.bitErrors;
		totalErrors.wordErrors += errors.wordErrors;
		if (totalErrors.bitErrors == 0) {
			errorRate = 1.0 / (float) ((snapshot+1) * SSM_LENGTH * CLUSTERS);
			oper = '<';
		} else {
			errorRate = (float) totalErrors.bitErrors / (float) ((snapshot+1) * SSM_LENGTH * CLUSTERS);
			oper = '=';
		}
		printf(
			"Snapshot %d checked, found %d/%d errors (%d/%d total), BER %c %.2e so far.\n",
			snapshot,
			errors.bitErrors, errors.wordErrors, totalErrors.bitErrors, totalErrors.wordErrors,
			oper, errorRate
		);
		fflush(stdout);
		fflush(stderr);
	}
	return 0;
}
