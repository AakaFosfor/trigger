#include <unistd.h>
#include <time.h>

#include "CTP.h"
#include "BOARD.h"

typedef enum {BBUSY, BL0, BL1, BL2, BFO1, BFO2, BFO3, BFO4, BFO5, BFO6, BINT} boards_e;

typedef struct {
	boards_e board;
	const char *name;
} counter_s;

counter_s counters[] = {
	{BL1, "l1time"},
	{BFO1, "fo1time"},
	{BFO1, "fo1l0hamming_error"},
	{BFO1, "fo1l1hamming_error"},
	{BFO1, "fo1bcerror"},
	{BL1, "l1temp"},
	{BFO1, "fo1temp"},
	{BBUSY, "busytemp"},
	{BBUSY, "byl0hamming_error"}
};

BOARD *getBoard(CTP *ctp, boards_e board) {
	switch (board) {
		case BBUSY:
			return ctp->busy;
		case BL0:
			return ctp->l0;
		case BL1:
			return ctp->l1;
		case BL2:
			return ctp->l2;
		case BFO1:
			return ctp->fo[0];
		case BFO2:
			return ctp->fo[1];
		case BFO3:
			return ctp->fo[2];
		case BFO4:
			return ctp->fo[3];
		case BFO5:
			return ctp->fo[4];
		case BFO6:
			return ctp->fo[5];
		case BINT:
			return ctp->inter;
		default:
			return NULL;
	}
}

#define CNTS_COUNT (sizeof(counters)/sizeof(counters[0]))

#define OUT_FILE "./counters.csv"

#define DIVIDER ";"

int main() {
	CTP *ctp = new CTP();
	BOARD *board;
	FILE *fp;
	w32 value;

/*	fp = fopen(OUT_FILE, "a");
	fprintf(fp, "\"time\"");
	for (unsigned int i = 0; i < CNTS_COUNT; i++) {
		fprintf(fp, DIVIDER "\"%s\"", counters[i].name);
	}
	fprintf(fp, "\n");
	fclose(fp);
*/
	while (true) {
		fp = fopen(OUT_FILE, "a");
		ctp->readCounters();
		fprintf(fp, "%ld", time(NULL));
		for (unsigned int i = 0; i < CNTS_COUNT; i++) {
			board = getBoard(ctp, counters[i].board);
			if (!board) {
				fprintf(fp, DIVIDER "boardNotIn");
				continue;
			}
			if (strstr(counters[i].name, "temp")) {
				// hack for special temperaturre reading
				value = board->getTemperature();
			} else {
				try {
					value = board->getCounterValue(counters[i].name);
				} catch (char const *msg) {
					if (!strcmp(msg, "Counter not found!")) {
						fprintf(fp, DIVIDER "counterNotFound");
						continue;
					}
					printf("An exception occured: %s\n", msg);
					exit(-1);
				}
			}
			fprintf(fp, DIVIDER "%u", value);
		}
		fprintf(fp, "\n");
		fclose(fp);
		sleep(60);
	}
	
	return 0;
}