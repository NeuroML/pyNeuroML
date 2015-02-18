'''

A package of utilities for exporting NEURON models to NeuroML 2 & for analysing/comparing NEURON models to NeuroML versions

Will use some some utilities from https://github.com/OpenSourceBrain/NEURONShowcase

'''

from pyneuroml.pynml import validate_neuroml1
from pyneuroml.pynml import validate_neuroml2

def export_to_neuroml2(hoc_file, nml2_file_name, includeBiophysicalProperties=True, validate=True):
    
    from neuron import *
    from nrn import *
    
    h.load_file(hoc_file)

    print "Loaded NEURON file: %s"%hoc_file

    h.load_file("mview.hoc")
    
    h('objref mv')
    h('mv = new ModelView()')
    
    h.load_file("%s/mview_neuroml2.hoc"%(os.path.dirname(__file__)))
    
    h('objref mvnml')
    h('mvnml = new ModelViewNeuroML2(mv)')
    
    nml2_level = 2 if includeBiophysicalProperties else 1
    
    h.mvnml.exportNeuroML2(nml2_file_name, nml2_level)
    

    if validate:
        
        validate_neuroml2(nml2_file_name)
        

def export_to_neuroml1(hoc_file, nml1_file_name, level=1, validate=True):
    
    if not (level==1 or level == 2):
        print("Only options for Levels in NeuroMLv1.8.1 are 1 or 2")
        return None
    
    from neuron import *
    from nrn import *
    
    h.load_file(hoc_file)

    print "Loaded NEURON file: %s"%hoc_file

    h.load_file("mview.hoc")

    h('objref mv')
    h('mv = new ModelView()')
    
    h.load_file("%s/mview_neuroml1.hoc"%(os.path.dirname(__file__)))
    
    h('objref mvnml1')
    h('mvnml1 = new ModelViewNeuroML1(mv)')

    h.mvnml1.exportNeuroML(nml1_file_name, level)

    if validate:
        
        validate_neuroml1(nml1_file_name)