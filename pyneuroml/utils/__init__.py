#!/usr/bin/env python3
"""
The utils package contains various utility functions to aid users working with
PyNeuroML

Copyright 2021 NeuroML Contributors
Author: Ankur Sinha <sanjay DOT ankur AT gmail DOT com>
"""

from typing import Any
import neuroml


def component_factory(
    component_type: str,
    **kwargs: Any
):
    """Factory function to create a NeuroML Component object.

    Users can provide the name of the component, along with its named
    constructor arguments, and this function will create a new object of the
    Component and return it.

    Users can use the `add()` helper function to further modify components

    :param component_type: name of component type to create component from
    :type component_type: str
    :param **kwargs: named arguments to be passed to ComponentType constructor
    :type **kwargs: named arguments
    :returns: new Component (object) of provided ComponentType

    """
    comp_type_class = getattr(neuroml.nml.nml, component_type)
    comp = comp_type_class(**kwargs)
    check_component_parameters_are_set(comp)


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
