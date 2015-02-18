'''

A package of utilities for exporting NEURON models to NeuroML 2 & for analysing/comparing NEURON models to NeuroML versions

Will use some some utilities from https://github.com/OpenSourceBrain/NEURONShowcase

'''

from pyneuroml.pynml import validate_neuroml1

def export_to_neuromlv1(hoc_file, nml1_file_name, level=1, validate=True):
    
    if not (level==1 or level == 2):
        print("Only options for Levels in NeuroMLv1.8.1 are 1 or 2")
        return None
    
    from neuron import *
    from nrn import *
    
    h.load_file(hoc_file)

    print "Loaded NEURON file: %s"%hoc_file

    h.load_file("mview.hoc")

    mv = h.ModelView()

    mv.xml.exportNeuroML(nml1_file_name, level)

    if validate:
        
        validate_neuroml1(nml1_file_name)