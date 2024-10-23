#!/usr/bin/env python3
"""
Utilities for creation and inclusion of new Components in models.

File: pyneuroml/utils/components.py

Copyright 2024 NeuroML contributors
"""

import logging
from typing import Optional

from lems.model.component import Component
from lems.model.model import Model

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def add_new_component(
    component_id: str,
    component_type: str,
    component_filename: Optional[str] = None,
    **kwargs,
) -> Component:
    """Add a new component to a NeuroMLDocument.

    This will create a new component with the provided id, type, and keyword
    arguments and export it to a separate XML file and add that file as an
    includes to the provided NeuroMLDocument object.

    This is the suggested way of including new Components of new ComponentTypes
    because it keeps them separate from the main model that is composed of
    Components from the NeuroML schema---which can be validated. New
    ComponentTypes and their Components can be used to extend NeuroML, but
    since they are not yet included in the NeuroML standard, they cannot be
    validated against the schema.

    .. versionadded:: 1.3.13

    :param nmldoc: NeuroMLDocument object to include component in
    :type nmldoc: NeuroMLDocument
    :param component_id: id of new Component
    :type component_id: str
    :param component_type: name of ComponentType that this Component is an
        instance of. This must be a valid ComponentType that has been included
        in the model. This function will not check this.
    :type component_type: str
    :param component_filename: optional file name to store the XML export of
        the component in
    :type component_filename: str
    :param **kwargs: parameters to pass to the Component
    :returns: the Component Object, and the name of the XML file it was serialised in
    :rtype: tuple(Component, str)
    """
    newmodel = Model()
    newcomp = Component(id_=component_id, type_=component_type, **kwargs)
    newmodel.add_component(newcomp)

    if component_filename is None:
        component_filename = f"component_{component_id}.xml"

    logger.info(
        f"Saving component with id '{component_id}' and type '{component_type}' to {component_filename}"
    )
    newmodel.export_to_file(component_filename)

    logger.info(
        "Component file included in NeuroML document. Note that new components will not validate against the NeuroML schema."
    )
    logger.info(
        f"Please also remember to include {component_filename} in the LEMS simulation file"
    )

    return newcomp, component_filename
