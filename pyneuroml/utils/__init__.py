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

    Users can provide the case insensitive name of the component, along with
    its named constructor arguments, and this function will create a new object
    of the Component and return it.

    Users can use the `add()` helper function to further modify components

    :param component_type: name of component type to create component from
    :type component_type: str
    :param **kwargs: named arguments to be passed to ComponentType constructor
    :type **kwargs: named arguments
    :returns: new Component (object) of provided ComponentType

    """
    obj = None  # type: Any
    try:
        comp_type_class = getattr(neuroml.nml.nml, component_type.upper())
        obj = comp_type_class(**kwargs)
    except AttributeError as e:
        print(e)

    return obj
