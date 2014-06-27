/* generated by comp.py */
#include <stdio.h>
#include "vmewrap.h"
#include "lexan.h"
#include "vmeaistd.h"

char BoardName[]="simple";
char BoardBaseAddress[11]="0x829000";
char BoardSpaceLength[11]="0xd000";
char BoardSpaceAddmod[11]="A24";
Tpardesc vmeloop_parameters[4]={
{"address", 2},
{"loops", 1},
{"value", 2},
{"mics", 1}};
char vmeloop_usagehelp[]="address: rel. adress (4, 8, 12,... for 32 bits words readings)\n\
loops: 0: endless loop\n\
value: 0: read + print\n\
       1: read only\n\
      >1: write, no print\n\
mics: mics between vme reads/writes. 0: do not wait between vme r/w\n\
";

Tpardesc rndtest_parameters[4]={
{"fromaddr", 2},
{"Nregs", 1},
{"bitmask", 2},
{"loops", 1}};
char rndtest_usagehelp[]="Write/read random value into array of registers\n\
\n\
fromaddr: first address to be tested\n\
Nregs:    number of consecutive addresses to be tested\n\
bitmask:  e.g. 0xff -> test only bits 7..0\n\
loops:    number of loops over the array of registers\n\
";

void vmeloop(w32 address, int loops, w32 value, int mics);
void rndtest(w32 fromaddr, int Nregs, w32 bitmask, int loops);

int nnames=12;
Tname allnames[MAXNAMES]={
{"simple", tSYMNAME, NULL, {0}, 0.0, NULL, {0}, NULL},
{"CODE_ADD", tVMEADR, NULL, {0}, 0.0, NULL, {0x4}, NULL},
{"SERIAL_NUMBER", tVMEADR, NULL, {0}, 0.0, NULL, {0x8}, NULL},
{"VMEVERSION_ADD", tVMEADR, NULL, {0}, 0.0, NULL, {0xc}, NULL},
{"FPGAVERSION_ADD", tVMEADR, NULL, {0}, 0.0, NULL, {0x80}, NULL},
{"L0_CONDITIONr2", tVMEADR, NULL, {0}, 0.0, NULL, {0x400}, NULL},
{"L0_INVERTr2", tVMEADR, NULL, {0}, 0.0, NULL, {0x600}, NULL},
{"L0_VETOr2", tVMEADR, NULL, {0}, 0.0, NULL, {0x800}, NULL},
{"SCOPE_A_FRONT_PANEL", tVMEADR, NULL, {0}, 0.0, NULL, {0x244}, NULL},
{"SCOPE_B_FRONT_PANEL", tVMEADR, NULL, {0}, 0.0, NULL, {0x248}, NULL},
{"vmeloop", tFUN+0x400, (funcall)vmeloop, {0xdead}, 0.0, vmeloop_parameters, {4}, vmeloop_usagehelp},
{"rndtest", tFUN+0x400, (funcall)rndtest, {0xdead}, 0.0, rndtest_parameters, {4}, rndtest_usagehelp}};
