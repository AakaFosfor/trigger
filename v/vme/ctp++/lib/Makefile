ObjSuf        = o
SrcSuf        = cc
CXX           = g++
CXXFLAGS      = -g -Wall -fPIC -I$(VMEBDIR)/vmeblib

libctp++.a: time.o convert.o CTPRDIRD.o parse.o
	ar -q libctp++.a *.o

.$(SrcSuf).$(ObjSuf):
	$(CXX) $(CXXFLAGS) -c $<

clean:
	rm libctp++.a
	rm *.o
