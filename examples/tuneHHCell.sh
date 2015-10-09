pynml-tune TestHHsh test_data/HHCellNetwork.net.nml HHCellNetwork \
    [cell:hhcell/channelDensity:naChans/mS_per_cm2,cell:hhcell/channelDensity:kChans/mS_per_cm2] \
    [200,60] [50,10] [hhpop[0]/v:max_peak_no:30] [hhpop[0]/v:max_peak_no:1] \
    -simTime 700 -populationSize 10 -maxEvaluations 20 -numSelected 5 -numOffspring 5 $1 $2 $3 $4
