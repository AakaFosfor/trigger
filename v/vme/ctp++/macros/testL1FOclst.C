using namespace std;

#include <bitset>

#include "L1BOARD.h"
#include "FOBOARD.h"

//#define DEBUG

// size of SnapShot Memory (both generating/monitoring)
#define SSM_SIZE (1024*1024)
#define SSM_READ_OFFSET 5
#define SSM_SENSE 10
#define ERROR_DISPLAY 15
#define M_ERROR_DISPLAY 15

#define CLUSTERS 8

#define SSM_READ_SIZE (SSM_SIZE-SSM_READ_OFFSET)
#define BITS_CHECKED (SSM_READ_SIZE*CLUSTERS)

#define KNRM  "\x1B[0m"
#define KRED  "\x1B[31m"
#define KGRN  "\x1B[32m"
#define KYEL  "\x1B[33m"
#define KBLU  "\x1B[34m"
#define KMAG  "\x1B[35m"
#define KCYN  "\x1B[36m"
#define KWHT  "\x1B[37m"

#define L1_CLST1 2
#define L1_CLST2 3
#define L1_CLST3 4
#define L1_CLST4 5
#define L1_CLST5 6
#define L1_CLST6 7
#define L1_CLST7 10
#define L1_CLST8 11

// how many consecutive patterns to search for to align for test start
#define STRIKE 5

const w32 patternSingle = 0x135E26BC;
const int shifts[CLUSTERS] = {
	0, 4, 8, 0, 14, 2, 2, 3
};
#define PATTERN_LENGTH 15
unsigned int patterns[PATTERN_LENGTH] = {
	0, 0, 0, 0, 0, 0, 0, 0,
	0, 0, 0, 0, 0, 0, 0
};

void fillPattern() {
	unsigned int word;
	for (int i = 0; i < PATTERN_LENGTH; i++) {
		word = 0;
		for (int cluster = CLUSTERS-1; cluster >= 0; cluster--) {
			word <<= 1;
			word |= (patternSingle >> (31-(shifts[cluster]+i))) & 1;
		}
		patterns[i] = word;
		#ifdef DEBUG
			printf("patternID=%3d: 0x%03x, ", i, word);
			cout << bitset<8>(word) << endl;
		#endif
	}
}

unsigned int LFSRpattern(unsigned int id) {
	return patterns[id%PATTERN_LENGTH];
}

int getLFSRpatternID(unsigned int pattern) {
	for (unsigned int id = 0; id < PATTERN_LENGTH; id++) {
		if (pattern == patterns[id]) {
			return id;
		}
	}
	return -1;
}

unsigned int getClusters(w32 data) {
	// FO:
	// ssh_record[7..2]	=  bp_l1clst[6..1];
	// ssh_record[11..10]	=  bp_l1clst[8..7];
	return (0x3F&(data>>2)) | ((0x3&(data>>10))<<6);
}

unsigned int getHamming(w32 data) {
	// FO: ssh_record[15..12]	=  bp_l1clst_hamming[];
	return 0xF&(data>>12);
}

unsigned int computeHamming(unsigned int data) {
	return 
		(((1&(data>>0)) ^ (1&(data>>1)) ^ (1&(data>>3)) ^ (1&(data>>4)) ^ (1&(data>>6)))<<0) |
		(((1&(data>>0)) ^ (1&(data>>2)) ^ (1&(data>>3)) ^ (1&(data>>5)) ^ (1&(data>>6)))<<1) |
		(((1&(data>>1)) ^ (1&(data>>2)) ^ (1&(data>>3)) ^ (1&(data>>7)))<<2) |
		(((1&(data>>4)) ^ (1&(data>>5)) ^ (1&(data>>6)) ^ (1&(data>>7)))<<3)
	;
}

w32 composeSSMWord(unsigned int data) {
	// L1: ssh_drive[11..10], ssh_drive[7..2]
	return ((0x3F&data)<<2) | ((0x3&(data>>6))<<10);
}

int correctData(unsigned int data, unsigned int hamming) {
	unsigned int syndrom;
	
	syndrom = hamming ^ computeHamming(data);
	switch (syndrom) {
		case 0:
			// no error
			break;
		case 1:
			// error in parity bit
			break;
		case 2:
			// error in parity bit
			break;
		case 3:
			data ^= 1<<0;
			break;
		case 4:
			// error in parity bit
			break;
		case 5:
			data ^= 1<<1;
			break;
		case 6:
			data ^= 1<<2;
			break;
		case 7:
			data ^= 1<<3;
			break;
		case 8:
			// error in parity bit
			break;
		case 9:
			data ^= 1<<4;
			break;
		case 10:
			data ^= 1<<5;
			break;
		case 11:
			data ^= 1<<6;
			break;
		case 12:
			data ^= 1<<7;
			break;
		default:
			// more errors!
			return -1;
	}
	return data;
}

void loadL1SSM() {
	L1BOARD *l1;
	w32 *ssm;

	l1 = new L1BOARD(-1);
	l1->StopSSM();
	
	ssm = l1->GetSSM();
	for (int i = 0; i < SSM_SIZE; i++) {
		ssm[i] = composeSSMWord(LFSRpattern(i));
		//ssm[i] = composeSSMWord((i==0) ? 1 : 0); // just one pulse on cluster 1 per SSM_SIZE
		#ifdef DEBUG
			if (i < SSM_SENSE) {
				printf("[%5i] 0x%08x: ", i, ssm[i]);
				cout << "Clusters: " << bitset<8>(getClusters(ssm[i])) << endl;
			}
		#endif
	}
	l1->WritehwSSM();
	if (l1->SetMode("outgen", 'c')) {
		cerr << "Error in setting SSM mode!" << endl;
	}
	cout << "Starting L1 outgen" << endl;
	l1->StartSSM();
}

unsigned int getFirstClusters(w32 *ssm) {
	unsigned int clusters, hamming, computedHamming;
	int strike = 0;
	int patternID = 0;
	unsigned int firstPattern = 0;
	
	for (unsigned int i = 0; i < SSM_READ_SIZE; i++) {
		// get all data
		clusters = getClusters(ssm[i]);
		hamming = getHamming(ssm[i]);
		computedHamming = computeHamming(clusters);
		// is parity OK?
		if (hamming != computedHamming) {
			// if not, start over again
			strike = 0;
			continue;
		}
		// parity is OK
		if (strike == 0) {
			// first in the row
			patternID = getLFSRpatternID(clusters);
			if (patternID == -1) {
				// not usable pattern
				continue;
			}
			strike++;
			continue;
		}
		// next in the row
		patternID = (patternID+1)%PATTERN_LENGTH;
		if (getLFSRpatternID(clusters) != patternID) {
			// not as expected, start over again
			strike = 0;
			continue;
		}
		strike++;
		if (strike == STRIKE) {
			// if STRIKE patterns in the row was as expected
			firstPattern = (PATTERN_LENGTH + patternID - i) % PATTERN_LENGTH;
			printf("Found pattern %d at position %d after %d valid entries, first pattern should be %d.\n", patternID, i, STRIKE, firstPattern);
			return firstPattern;
		}
	}
	fprintf(stderr, KRED "No usable pattern found in whole snapshot memory!!!" KNRM "\n");
	return firstPattern;
}

int main(int argc, char *argv[]) {
	FOBOARD *fo;
	w32 *ssm;
	unsigned int clusters, hamming, computedHamming;
	int dispayed = 0;
	int errors = 0;
	int multiErrors = 0;
	int correctedClusters;
	int i;
	unsigned int predictedClustersID;
	int displaySimple, error, multiError;
	unsigned int overflows = 0;
	
	fillPattern();

	if ((argc > 1)) {
		if ((strcmp(argv[1], "load") == 0)) {
			loadL1SSM();
		}
	}
	
	fo = new FOBOARD((w32) 0x821000, -1);
	fo->StopSSM();
	fo->SetMode("inmonl1", 'a');
	fo->StartSSM();
	usleep(50000);
	fo->StopSSM();
	fo->ReadSSM();
	ssm = fo->GetSSM();
	ssm += SSM_READ_OFFSET;

	for (i = 0, predictedClustersID = getFirstClusters(ssm); i < SSM_READ_SIZE; i++, predictedClustersID=(predictedClustersID+1)%PATTERN_LENGTH) {
		// gather data
		clusters = getClusters(ssm[i]);
		hamming = getHamming(ssm[i]);
		computedHamming = computeHamming(clusters);
		correctedClusters = correctData(clusters, hamming);
		
		// correction for case when generating SSM_SIZE != n*PATTERN_LENGTH
		if ((SSM_SIZE % PATTERN_LENGTH) != 0) {
			if (clusters != LFSRpattern(predictedClustersID)) {
				// possible SSM overflow
				if ((getLFSRpatternID(clusters) == 0) && (predictedClustersID == (SSM_SIZE % PATTERN_LENGTH))) {
					// possible SSM overflow according to actual/last clusters
					predictedClustersID = 0;
					overflows++;
				}
			}
		}

		// check status
		displaySimple = (hamming == computedHamming);
		error = (hamming != computedHamming);
		multiError =
			(displaySimple && (clusters != LFSRpattern(predictedClustersID))) ||
			(error && (correctedClusters >= 0) && ((unsigned int)correctedClusters != LFSRpattern(predictedClustersID)));
		
		// count states
		if (error) errors++;
		if (multiError) multiErrors++;

		// skip display, if full
		if (
			(displaySimple && !multiError && (dispayed >= SSM_SENSE)) ||
			(error && !multiError && (errors > ERROR_DISPLAY)) ||
			(multiError && (multiErrors > M_ERROR_DISPLAY))
		) {
			continue;
		}
		
		// display
		printf(KYEL "[%7i]" KNRM " 0x%08x: ", i, ssm[i]);
		cout << "Clusters: " << bitset<8>(clusters);
		cout << ", Hamming: " << bitset<4>(hamming);
		cout << ", Computed Hamming: " << bitset<4>(computedHamming);
		if (error) {
			printf("  " KRED "Error in Hamming!");
			if (correctedClusters == -1) {
				printf(" Uncorrectable errors!");
			} else {
				printf(KGRN " (Corrected clusters: ");
				cout << bitset<8>(correctedClusters) << ")";
			}
		}
		if (multiError) {
			printf(KMAG "\n          Unexpected (corrected) clusters! Multiple errors?");
			cout << " Predicted clusters: " << bitset<8>(LFSRpattern(predictedClustersID));
		}
		if (displaySimple && !multiError) {
			dispayed++;
		}
		printf(KNRM "\n");
	}
	
	printf("\nTotal errors: %i\n", errors);
	printf("Total multi(?) errors: %i\n", multiErrors);
	printf("Total SSM overflows: %i", overflows);
	if (overflows > 1) {
		printf(KRED " Should be <= 1 !!!" KNRM);
	}
	printf("\n");

	return EXIT_SUCCESS;
}
