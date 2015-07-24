#include "BUSYBOARD.h"

int main() {
	int vmesp = -1;
	BUSYBOARD *bb = new BUSYBOARD(vmesp);
	printf("vsp = %i\n", bb->getvsp());
	w32 ver = bb->getFPGAversion();
	printf("Version: 0x%X (%i)\n", ver, ver);
	bb->StopSSM();
	for(int i = 0; i < 2; i++) {
		cout << "Loop " << i << endl;
		bb->SetMode("inmon", 'a');
		bb->StartSSM();
		usleep(50000);
		bb->StopSSM();
		bb->ReadSSM();
		try {
			bb->analSSMTestDDR();
		} catch (int err) {
			cerr << "Error number " << err << endl;
		} catch (char *errStr) {
			cerr << "Error: " << errStr << endl;
		} catch (...) {
			cerr << "An unhandled exception occured!" << endl;
			break;
		}
		//l1->DumpSSM(fileName_S.c_str());
	}
	return 0;
}