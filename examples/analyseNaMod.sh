pynml-modchananalysis -stepV 5  NaConductance2 -dt 0.01 -temperature 22

# Uses https://github.com/NeuralEnsemble/neuroConstruct/blob/master/nCplot.sh
ncpl -b NaConductance2.m.tau.dat NaConductance2.h.tau.dat test/mtau_NaConductance.dat test/htau_NaConductance.dat & 
ncpl -b NaConductance2.m.inf.dat NaConductance2.h.inf.dat test/minf_NaConductance.dat test/hinf_NaConductance.dat &
