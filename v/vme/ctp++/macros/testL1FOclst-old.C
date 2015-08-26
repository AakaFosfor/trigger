using namespace std;

// test of old system - 6 clusters, SDR

#include <bitset>

#include "L1BOARD.h"
#include "FOBOARD.h"

#define SSM_SIZE (1024*1024)
#define SSM_READ_OFFSET 5
#define SSM_SENSE 10
#define ERROR_DISPLAY 15
#define M_ERROR_DISPLAY 15

#define CLUSTERS 3
#define HAMMING_BITS 3

#define SSM_READ_SIZE (SSM_SIZE-SSM_READ_OFFSET)
#define BITS_CHECKED (SSM_READ_SIZE*(CLUSTERS+HAMMING_BITS))

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

unsigned int getClusters(w32 data) {
	// FO:
	// ssh_record[4..2]	=  bp_l1clst[3..1];
	return (0x7&(data>>2));
}

unsigned int getHamming(w32 data) {
	// FO:
	// ssh_record[7..5]	=  bp_l1clst[6..4];
	return (0x7&(data>>5));
}

unsigned int computeHamming(unsigned int data) {
	return 
		(((1&(data>>0)) ^ (1&(data>>1)))<<0) |
		(((1&(data>>0)) ^ (1&(data>>2)))<<1) |
		(((1&(data>>1)) ^ (1&(data>>2)))<<2)
	;
}

w32 composeSSMWord(unsigned int data) {
	// L1: ssh_drive[7..2]
	return ((0x7&data)<<2) | ((0x7&computeHamming(0x7&data))<<5);
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
		ssm[i] = composeSSMWord(i);
		if (i < SSM_SENSE) {
			printf("[%5i] 0x%08x: ", i, ssm[i]);
			cout << "Clusters: " << bitset<3>(getClusters(ssm[i]));
			cout << ", Hamming: " << bitset<3>(getHamming(ssm[i])) << endl;
		}
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
	unsigned int pattern = 0;
	
	for (unsigned int i = 0; i < SSM_READ_SIZE; i++) {
		clusters = getClusters(ssm[i]);
		hamming = getHamming(ssm[i]);
		computedHamming = computeHamming(clusters);
		if (hamming != computedHamming) {
			strike = 0;
			continue;
		}
		if (strike == 0) {
			pattern = 0x7&clusters;
		} else {
			pattern = 0x7&(pattern+1);
		}
		if (clusters != pattern) {
			strike = 0;
			pattern = 0x7&clusters;
		} else {
			strike++;
		}
		if (strike == 5) {
			return 0x7&(clusters-i);
		}
	}
	fprintf(stderr, KRED "No usable pattern found in whole snapshot memory!!!" KNRM "\n");
	return 0;
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
	unsigned int predictedClusters;
	int displaySimple, error, multiError;
	
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

	for (i = 0, predictedClusters = getFirstClusters(ssm); i < SSM_READ_SIZE; i++, predictedClusters=0x7&(predictedClusters+1)) {
		// gather data
		clusters = getClusters(ssm[i]);
		hamming = getHamming(ssm[i]);
		computedHamming = computeHamming(clusters);
		correctedClusters = correctData(clusters, hamming);

		// check status
		displaySimple = (hamming == computedHamming);
		error = (hamming != computedHamming);
		multiError =
			(displaySimple && (clusters != predictedClusters)) ||
			(error && (correctedClusters >= 0) && ((unsigned int)correctedClusters != predictedClusters));
		
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
		cout << "Clusters: " << bitset<3>(clusters);
		cout << ", Hamming: " << bitset<3>(hamming);
		cout << ", Computed Hamming: " << bitset<3>(computedHamming);
		if (error) {
			printf("  " KRED "Error in Hamming!");
			if (correctedClusters == -1) {
				printf(" Uncorrectable errors!");
			} else {
				printf(KGRN " (Corrected clusters: ");
				cout << bitset<3>(correctedClusters) << ")";
			}
		}
		if (multiError) {
			printf(KMAG "\n          Unexpected (corrected) clusters! Multiple errors?");
			cout << " Predicted clusters: " << bitset<3>(predictedClusters);
		}
		if (displaySimple && !multiError) {
			dispayed++;
		}
		printf(KNRM "\n");
	}
	
	printf("\nTotal errors: %i\n", errors);
	printf("Total multi(?) errors: %i\n", multiErrors);

	return EXIT_SUCCESS;
}
