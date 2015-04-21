#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <limits.h>
#include <errno.h>

#ifdef CPLUSPLUS
#include <dis.hxx>
#else
#include <dis.h>
#endif
#define MYNAME "TTCMI"

int qpllstat=0, quit=0;
int QPLLid;

void gotsignal(int signum) {
char msg[100];
switch(signum) {
case SIGUSR1:  // kill -s USR1 pid
  signal(SIGUSR1, gotsignal); siginterrupt(SIGUSR1, 0);
  sprintf(msg, "got SIGUSR1 signal:%d, fflush(stdout)\n", signum);
  printf(msg);
  fflush(stdout);
  break;
case SIGINT:
  signal(SIGINT, gotsignal); siginterrupt(SIGINT, 0);
  printf("got SIGINT signal, quitting...:%d\n", signum);
  quit=signum;
  break;
case SIGQUIT:
  signal(SIGQUIT, gotsignal); siginterrupt(SIGQUIT, 0);
  printf("got SIGQUIT signal, quitting...:%d\n", signum);
  quit=signum;
  break;
case SIGBUS: 
  //vmeish(); not to be called (if called, it kills dims process)
  printf(msg, "got SIGBUS signal:%d\n", signum); //prtLog(msg);
  break; 
default:
  printf("got unknown signal:%d\n", signum);
};
}

int update_qpll() {
int rc;
qpllstat=qpllstat+1;
rc= dis_update_service(QPLLid);
printf("QPLL update qpllstat:%d rc:%d\n", qpllstat, rc);
return(rc);
}

int main(int argc, char **argv)  {
char command[200];
setlinebuf(stdout);
signal(SIGUSR1, gotsignal); siginterrupt(SIGUSR1, 0);
signal(SIGQUIT, gotsignal); siginterrupt(SIGQUIT, 0);
signal(SIGBUS, gotsignal); siginterrupt(SIGBUS, 0);
strcpy(command, MYNAME); strcat(command, "/QPLL");
QPLLid=dis_add_service(command, "L", &qpllstat, sizeof(qpllstat),
//  QPLLcaba, QPLLtag);  printf("%s\n", command);
  NULL, 88);  printf("%s\n", command);

printf("serving...\n");
dis_start_serving(MYNAME);  
while(1)  {  
  int rc;
  rc= update_qpll();
  if(rc!=0) break;
  printf("sleteping 10secs...\n"); fflush(stdout);
  //sleep(10) ; 
  dtq_sleep(10);
  printf("slept 10secs...\n"); fflush(stdout);
};  
dis_remove_service(QPLLid);
exit(0);
}   

