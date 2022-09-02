#!/usr/bin/env python3
"""
The utils package contains various utility functions to aid users working with
PyNeuroML

Copyright 2021 NeuroML Contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

from typing import Any, Union
import neuroml


def component_factory(
    component_type: Union[str, type],
    **kwargs: Any
) -> Any:
    """Factory function to create a NeuroML Component object.

    Users can provide the name of the component as a string or the class
    variable, along with its named constructor arguments, and this function
    will create a new object of the Component and return it.

    Users can use the `add()` helper function to further modify components

    :param component_type: component type to create component from:
        this can either be the name of the component as a string, e.g.
        "NeuroMLDocument", or it can be the class type itself: NeuroMLDocument.
        Note that when providing the class type, one will need to import it,
        e.g.: `import NeuroMLDocument`, to ensure that it is defined, whereas
        this will not be required when using the string.
    :type component_type: str/type
    :param **kwargs: named arguments to be passed to ComponentType constructor
    :type **kwargs: named arguments
    :returns: new Component (object) of provided ComponentType
    :rtype: object

    """
    if isinstance(component_type, str):
        comp_type_class = getattr(neuroml.nml.nml, component_type)
    else:
        comp_type_class = getattr(neuroml.nml.nml, component_type.__name__)

    comp = comp_type_class(**kwargs)
    check_component_parameters_are_set(comp)
    return comp


def check_component_parameters_are_set(comp: Any) -> None:
    """Check if all compulsory parameters of a component are set.

    Throws a Python `ValueError` if a compulsory parameter has not been set in
    the component. If you wish to set this parameter later, handle this error
    in a try/except block and continue.

    Note: validating your NeuroML file will also check this.

    :param comp: component to check
    :type comp: Any
    :returns: None
    """
    members = comp.get_members()
    for m in members:
        name = m.get_name()
        optional = m.get_optional()
        value = getattr(comp, name)

        if optional == 0 and value is None:
            print(f"{name} is a compulsory parameter and must be set.")
            print("If you wish to ignore this error and set this parameter later, please handle the exception and continue.\n")
            comp.info()
            raise ValueError


def extract_position_info(nml_model, verbose):

    cell_id_vs_cell = {}
    positions = {}
    pop_id_vs_cell = {}
    pop_id_vs_color = {}
    pop_id_vs_radii = {}

    cell_elements = []
    cell_elements.extend(nml_model.cells)
    cell_elements.extend(nml_model.cell2_ca_poolses)

    for cell in cell_elements:
        cell_id_vs_cell[cell.id] = cell

    if len(nml_model.networks)>0:
        popElements = nml_model.networks[0].populations
    else:
        popElements = []
        net = neuroml.Network(id='x')
        nml_model.networks.append(net)
        cell_str = ''
        for cell in cell_elements:
            pop = neuroml.Population(id='dummy_population_%s'%cell.id, size=1, component=cell.id)
            net.populations.append(pop)
            cell_str+=cell.id+'__'
        net.id=cell_str[:-2]

        popElements = nml_model.networks[0].populations


    for pop in popElements:
        name = pop.id
        celltype = pop.component
        instances = pop.instances

        if pop.component in cell_id_vs_cell.keys():
            pop_id_vs_cell[pop.id] = cell_id_vs_cell[pop.component]
        else:
            pop_id_vs_cell[pop.id] = None

        info = "Population: %s has %i positioned cells of type: %s" % (
            name,
            len(instances),
            celltype,
        )
        if verbose: print(info)

        colour = "b"
        substitute_radius = None

        props = []
        props.extend(pop.properties)
        ''' TODO
        if pop.annotation:
            props.extend(pop.annotation.properties)'''

        for prop in props:
            #print(prop)
            if prop.tag == "color":
                color = prop.value
                color = (float(color.split(' ')[0]),
                         float(color.split(' ')[1]),
                         float(color.split(' ')[2]))

                pop_id_vs_color[pop.id]=color
                #print("Colour determined to be: %s"%str(color))
            if prop.tag == "radius":
                substitute_radius = float(prop.value)
                pop_id_vs_radii[pop.id]=substitute_radius

        pop_positions = {}

        if len(instances)>0:
            for instance in instances:
                location = instance.location
                id = int(instance.id)

                x = float(location.x)
                y = float(location.y)
                z = float(location.z)
                pop_positions[id] = (x, y, z)
        else:
            for id in range(pop.size):
                pop_positions[id] = (0,0,0)

        positions[name] = pop_positions

    return cell_id_vs_cell, pop_id_vs_cell, positions, pop_id_vs_color, pop_id_vs_radii
