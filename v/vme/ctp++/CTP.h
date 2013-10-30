#ifndef _CTP_h
#define _CTP_h
#include <list>
#include "BOARD.h"
#include "DETECTOR.h"
#include "libctp++.h"
using namespace std;
#define NUMOFFO 6
#define NUMOFCON 4
//#define NUMOFLTU (NUMOFFO*NUMOFCON)
class CTP
{
 public:
	 CTP();
         ~CTP();
         BOARD *busy;
         BOARD *l0;     //Here should be pointers instead objects
	 BOARD *l1;     // otherwise compiler crashes probably due to the memory
         BOARD *l2;
         BOARD *inter;
	 BOARD *fo[NUMOFFO];
         BOARD *ltu[NUMOFFO*NUMOFCON];
         DETECTOR *fo2det[NUMOFFO][NUMOFCON];
	 int readCFG(string const &name);
	 list<BOARD*> boards;
 private:
	 int numofltus;  //Number of ltus in crate, up to 4
         int numoffos;   //Number of fos in crate up to 6
	 void readBICfile();
	 void readDBVALIDLTUS();
         void getboard(string const &line);
         void getdetector(string const &line);
         void getdetectorold(string const &line);
         void printboards();
         void checkFPGAversions() const;
         int vspctp;      // ctp vme space
         int vspltu;	  // ltu vmespace				     
};
#endif
