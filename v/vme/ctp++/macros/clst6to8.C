#include <cmath>

#include "BOARD.h"
#include "BUSYBOARD.h"

/*
 * analyze SSM - test for DDR link
 * Pospisil, July 2015
 *
 * Listen for input signals from LM0 board (cluster signals) and check for
 * pseudo-random pattern (4bit LFSR). It uses custom generator design in LM0
 * FPGA. It test LM0-BUSY DDR links for L0 clusters.
 */

// debug stuff:
//#define DEBUG
//#define POISON_INNER
//#define POISON_OUTER

// BER confidence level
#define BER_CL (0.95)
// specified BER
#define BER_S (1.0e-13)

#define SSM_OFFSET 5
#define SSM_LENGTH (1024*1024-SSM_OFFSET)

const w32 patternSingle = 0x135E26BC;
#define CLUSTERS (8+1)
const int shifts[CLUSTERS] = {
	0, 1, 4, 2, 8, 5, 14, 3, 12
};
#define PATTERN_LENGTH 15
w32 pattern[PATTERN_LENGTH] = {
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0
};

#define L0CLST1BIT 21
#define L0CLST2BIT 22
#define L0CLST3BIT 23
#define L0CLST4BIT 24
#define L0CLST5BIT 25
#define L0CLST6BIT 26
#define L0CLST7BIT 27
#define L0CLST8BIT 28
#define L0CLSTTBIT 29

const int clusterPosition[CLUSTERS] = {
	L0CLST1BIT,
	L0CLST2BIT,
	L0CLST3BIT,
	L0CLST4BIT,
	L0CLST5BIT,
	L0CLST6BIT,
	L0CLST7BIT,
	L0CLST8BIT,
	L0CLSTTBIT
};

#define L0CLST1 (1<<L0CLST1BIT)
#define L0CLST2 (1<<L0CLST2BIT)
#define L0CLST3 (1<<L0CLST3BIT)
#define L0CLST4 (1<<L0CLST4BIT)
#define L0CLST5 (1<<L0CLST5BIT)
#define L0CLST6 (1<<L0CLST6BIT)
#define L0CLST7 (1<<L0CLST7BIT)
#define L0CLST8 (1<<L0CLST8BIT)
#define L0CLSTT (1<<L0CLSTTBIT)

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
	unsigned long long bitErrors;
	unsigned long long wordErrors;
} t_errors;

w32 clusters2SSM(w32 clusters) {
	w32 ssm = 0;
	for (int i = 0; i < CLUSTERS; i++) {
		ssm |= (1 & (clusters >> i)) << clusterPosition[i];
	}
	return ssm;
}

w32 SSM2Clusters(w32 ssm) {
	w32 clusters = 0;
	for (int i = 0; i < CLUSTERS; i++) {
		clusters |= (1 & (ssm >> clusterPosition[i])) << i;
	}
	return clusters;
}

void fillPattern() {
	w32 word;
	for (int i = 0; i < PATTERN_LENGTH; i++) {
		word = 0;
		for (int cluster = CLUSTERS-1; cluster >= 0; cluster--) {
			word <<= 1;
			word |= (patternSingle >> (31-(shifts[cluster]+i))) & 1;
		}
		pattern[i] = clusters2SSM(word);
	}
}

void printClusters(w32 *data, int offset = 0) {
	cout << endl;
	cout << "         : 0: 1: 2: 3: 4: 5: 6: 7: 8: 9:10:11:12:13:14:" << endl;
	for (int cluster = 0; cluster < CLUSTERS; cluster++) {
		printf("Cluster %d:", cluster+1);
		for (int i = 0; i < PATTERN_LENGTH; i++) {
			if ((SSM2Clusters(data[(i - offset + PATTERN_LENGTH) % PATTERN_LENGTH]) >> cluster) & 1) {
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
		data = (data << 1) | SSM2Clusters(sm[i] & L0CLST1);
		if (data == patternSingle) {
			debug_print("got it! i = %d\n", i);
			break;
		}
	}
	if (data != patternSingle) {
		cerr << "No pattern found!" << endl;
		#ifndef DEBUG
			cerr << "Ending..." << endl;
			exit(-1);
		#endif
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

int main(int argc, char *argv[]) {
	w32 *ssm;
	t_errors errors = {0, 0};
	t_errors totalErrors = {0, 0};
	BOARD *board;
	double errorRate, berCL, berS, iFact;
	char oper;
	unsigned long long snapshot;
	unsigned long long pastSnapshots = 0;
	unsigned long long totalBits;
	unsigned long long i;
	
	if (argc > 2) {
		cout << "usage : " << argv[0] << " [past_snapshots_checked]" << endl;
		cout << "  past_snapshots_checked - snapshots checked without error so far" << endl;
		cout << "                         - can be -1: only read SSM, no analysis" << endl;
		return EXIT_FAILURE;
	}
	
	if (argc == 2) {
		pastSnapshots = atol(argv[1]);
	}
	
	board = new BUSYBOARD(-1);
	debug_print("vsp = %i\n", board->getvsp());
	w32 ver = board->getFPGAversion();
	debug_print("Version: 0x%X (%i)\n", ver, ver);
	board->StopSSM();
	fillPattern();
	for(snapshot = 1; true; snapshot++) {
		// get snapshot
		board->SetMode("outmon", 'a');
		board->StartSSM();
		usleep(50000);
		board->StopSSM();
		board->ReadSSM();
		if (pastSnapshots == -1) {
			cout << "No analysis, just SSM read (" << snapshot << " reads so far)" << endl;
			continue;
		}
		ssm = board->GetSSM()+SSM_OFFSET;
		#ifdef POISON_OUTER
			if ((snapshot % 3) == 2) {
				ssm[1234] ^= L0CLST5;
			}
		#endif
		// calculate errors in snapshot
		errors = analSSMTestDDR(ssm, snapshot);
		totalErrors.bitErrors += errors.bitErrors;
		totalErrors.wordErrors += errors.wordErrors;
		// calcuate estimated BER
		totalBits = (snapshot+pastSnapshots) * SSM_LENGTH * CLUSTERS;
		if (totalErrors.bitErrors == 0) {
			errorRate = 1.0 / ((double) totalBits);
			oper = '<';
		} else {
			errorRate = (double) totalErrors.bitErrors / ((double) totalBits);
			oper = '~';
		}
		// calculate BER confidence level for BER_S
		// https://www.jitterlabs.com/support/calculators/ber-confidence-level-calculator/
		berCL = 1;
		iFact = 1;
		for (i = 1; i <= totalErrors.bitErrors; i++) {
			iFact *= i;
			berCL += pow(totalBits * BER_S, i)/iFact;
		}
		berCL *= exp(-(totalBits*BER_S));
		berCL = 1-berCL;
		// output results
		printf(
			"Snapshots checked: %llu (in this run: %llu), found %llu/%llu errors (%llu/%llu total), approx. BER %c %.2e (BER=%.2e @ %.2f%%",
			(pastSnapshots + snapshot), snapshot,
			errors.bitErrors, errors.wordErrors, totalErrors.bitErrors, totalErrors.wordErrors,
			oper, errorRate,
			BER_S, (100*berCL)
		);
		if (totalErrors.bitErrors == 0) {
			// calculate estimated BER for BER_CL
			// https://www.jitterlabs.com/support/calculators/ber-confidence-level-calculator/
			// VALID ONLY IF ERRORS=0 !!!
			berS = -log(1.0l-BER_CL)/totalBits;
			printf("; BER=%.2e @ %.2f%%", berS, (100*BER_CL));
		}
		printf(").\n");
		fflush(stdout);
		fflush(stderr);
		#ifdef DEBUG
			break;
		#endif
	}
	return EXIT_SUCCESS;
}
