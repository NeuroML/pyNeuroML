'''

A package of utilities for exporting NEURON models to NeuroML 2 & for analysing/comparing NEURON models to NeuroML versions

Will use some some utilities from https://github.com/OpenSourceBrain/NEURONShowcase

'''

from pyneuroml.pynml import validate_neuroml1
from pyneuroml.pynml import validate_neuroml2

from pyneuroml.pynml import print_comment, print_comment_v
import os

from pyneuroml.neuron.nrn_export_utils import set_erev_for_mechanism
from neuron import *
from nrn import *

def export_to_neuroml2(hoc_or_python_file, 
                       nml2_file_name, 
                       includeBiophysicalProperties=True, 
                       separateCellFiles=False, 
                       known_rev_potentials={},
                       validate=True):
    
    if hoc_or_python_file is not None:
        if hoc_or_python_file.endswith(".py"):
            print_comment_v("***************\nImporting Python scripts not yet implemented...\n***************")
        else:
            if not os.path.isfile(hoc_or_python_file):
                print_comment_v("***************\nProblem importing file %s (%s)..\n***************"%(hoc_or_python_file, os.path.abspath(hoc_or_python_file)))
            h.load_file(1, hoc_or_python_file) # Using 1 to force loading of the file, in case file with same name was loaded before...
    else:
        print_comment_v("hoc_or_python_file variable is None; exporting what's currently in memory...")

    for ion in known_rev_potentials.keys():
        set_erev_for_mechanism(ion,known_rev_potentials[ion])

    print_comment_v("Loaded NEURON file: %s"%hoc_or_python_file)

    h.load_file("mview.hoc")
    
    h('objref mv')
    h('mv = new ModelView(0)')
    
    h.load_file("%s/mview_neuroml2.hoc"%(os.path.dirname(__file__)))
    
    h('objref mvnml')
    h('mvnml = new ModelViewNeuroML2(mv)')
    
    nml2_level = 2 if includeBiophysicalProperties else 1
    
    h.mvnml.exportNeuroML2(nml2_file_name, nml2_level, int(separateCellFiles))
    
    if validate:
        validate_neuroml2(nml2_file_name)
        
        
    h('mv.destroy()')
        
        
        

def export_to_neuroml1(hoc_file, nml1_file_name, level=1, validate=True):
    
    if not (level==1 or level == 2):
        print_comment_v("Only options for Levels in NeuroMLv1.8.1 are 1 or 2")
        return None
    
    h.load_file(hoc_file)

    print_comment_v("Loaded NEURON file: %s"%hoc_file)

    h.load_file("mview.hoc")

    h('objref mv')
    h('mv = new ModelView()')
    
    h.load_file("%s/mview_neuroml1.hoc"%(os.path.dirname(__file__)))
    
    h('objref mvnml1')
    h('mvnml1 = new ModelViewNeuroML1(mv)')

    h.mvnml1.exportNeuroML(nml1_file_name, level)

    if validate:
        
        validate_neuroml1(nml1_file_name)
