pynml-modchananalysis -stepV 5  NaConductance -dt 0.01 -temperature 22

ncpl -b NaConductance.m.tau.dat NaConductance.h.tau.dat test/mtau_NaConductance.dat test/htau_NaConductance.dat & 
ncpl -b NaConductance.m.inf.dat NaConductance.h.inf.dat test/minf_NaConductance.dat test/hinf_NaConductance.dat &
