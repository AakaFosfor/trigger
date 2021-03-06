#define MAXNUM_THREADS 5    
#define true 1    
#define false 0    
typedef struct {
int Maxn;
int Entering[MAXNUM_THREADS]; // T: entering phase F: not entering phase
int Number[MAXNUM_THREADS];   // 0: this one is not locked
char name[16];   // ccread or swtriggers
unsigned int lastsecs,lastusecs;  // last usage
unsigned int minUsecs;            // minimum between 2 locks
unsigned int Nlocks;            // +1 when lock
unsigned int Nunlocks;          // -1 when unlock
} Tbakery;

/*
"initBakery(swtriggers,4): 0:SOD/EOD/SYNC 1:gcalib 2:ctp.exe  3:dims\n"
"initBakery(ccread,5): 0:proxy 1:dims 2:ctp+busytool 3:smaq 4:inputs\n"
 clgroups timer counters: just sending DIM cmd to dims, i.e. the locking managed
                 by dims (still problem with ending  -is it really done before
                 releasing triggers?)
          [un]setPartDAQBusy: initBakery(clusterbusys,2)
*/

void initBakery(Tbakery *bakery, char *name, int maxn);
void lockBakery(Tbakery *bakery, int customer);
void unlockBakery(Tbakery *bakery, int customer);
void printBakery(Tbakery *bakery);

