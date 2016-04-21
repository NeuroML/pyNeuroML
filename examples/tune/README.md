## Tuning a single cell

Install https://github.com/NeuralEnsemble/pyelectro and https://github.com/NeuralEnsemble/neurotune.

To run the single cell example, install NEURON:

    jnml LEMS_OnePyr.xml -neuron
    nrnivmodl
    nrngui LEMS_OnePyr_nrn.py
    
or:

    python tunePyr.py
  
To (re)tune the cell:

    python tunePyr.py -tune
    
![pic](https://raw.githubusercontent.com/NeuroML/pyNeuroML/master/examples/tune/Selection_817.jpg)

    
