from pyneuroml.neuron import export_to_neuroml2

export_to_neuroml2(
    "test.hoc", "test.morphonly.cell.nml", includeBiophysicalProperties=False
)
export_to_neuroml2(
    "test.hoc", "test.biophys.cell.nml", includeBiophysicalProperties=True
)
