/* generated by comp.py */
#include <stdio.h>
#include "vmewrap.h"
#include "lexan.h"
#include "vmeaistd.h"

char BoardName[]="simple";
char BoardBaseAddress[11]="0x0";
char BoardSpaceLength[11]="0x1000";
char BoardSpaceAddmod[11]="A24";
Tpardesc example_parameters[3]={
{"n", 1},
{"strg", 3| 0x80000000},
{"c", 3}};
char example_usagehelp[]="int example(int n, char *string, char c)\n\
int: only >=0\n\
string: \"abc\"\n\
char: 'c'\n\
float: not supported as parameter\n\
";

Tpardesc fexa_parameters[1]={
{"ifpn", 1}};
char fexa_usagehelp[]="float not suported neither in function result\n\
";

int example(int n, char *strg, char c);
float fexa(int ifpn);

int nnames=4;
Tname allnames[MAXNAMES]={
{"", tSYMNAME, NULL, (w32)BoardSpaceLength, 0.0, NULL, (w32)BoardBaseAddress, NULL},
{"REGA", tVMEADR, NULL, 0, 0.0, NULL, 0x20, NULL},
{"example", tFUN+0x200, (funcall)example, 0xdead, 0.0, example_parameters, 3, example_usagehelp},
{"fexa", tFUN+0x300, (funcall)fexa, 0xdead, 0.0, fexa_parameters, 1, fexa_usagehelp}};
