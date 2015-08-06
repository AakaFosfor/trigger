#include "CTP.h"
#include <cmath>
int main()
{
  CTP* ctp = new CTP;
  //ctp->readBCStatus(1000000);
  ctp->readCounters();
  usleep(1000000);
  ctp->readCounters();
  //
  if (ctp->l0) {
    ctp->l0->printCountersDiff();
  }
  if (ctp->l1) {
    ctp->l1->printCountersDiff();
  }
  if (ctp->l2) {
    ctp->l2->printCountersDiff();
  }
  //ctp->busy->printCountersDiff();
  for (int i = 0; i < NUMOFFO; i++) {
    if (ctp->fo[i]) {
      ctp->fo[i]->printCountersDiff();
	}
  }
  //ctp->fo[0]->printCounters();

  printf(">-----------------------------Checking counters for no configuration \n");
  if (ctp->l0) {
    ctp->l0->CheckCountersNoTriggers();
  }
  if (ctp->l1) {
    ctp->l1->CheckCountersNoTriggers();
  }
  if (ctp->l2) {
    ctp->l2->CheckCountersNoTriggers();
  }
  for (int i = 0; i < NUMOFFO; i++) {
    if (ctp->fo[i]) {
      ctp->fo[i]->CheckCountersNoTriggers();
	}
  }
  if (ctp->inter) {
    ctp->inter->CheckCountersNoTriggers();
  }
  return 0;
}
