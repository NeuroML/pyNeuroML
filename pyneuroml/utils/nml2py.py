"""NeuroML XML to Python code generator.

This module provides the ``NmlPythonizer`` class, which loads a NeuroML XML file
and generates a Python script that recreates the model using the libNeuroML API
(component_factory, add, etc.).

Cells, channels, and synapses that are expanded inline in the source XML are
extracted into separate files following NeuroML file naming conventions
({id}.cell.nml, {id}.channel.nml, {id}.synapse.nml). Components that were
already in separate included files are preserved as includes.

Copyright 2026 NeuroML contributors
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path
from typing import Any

import neuroml
import neuroml.writers as writers
from neuroml.utils import component_factory

import pyneuroml.utils.cli as pynmluc
from pyneuroml.io import read_neuroml2_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Type classification helper
# ---------------------------------------------------------------------------


def _is_scalar_type(type_name: str) -> bool:
    """Return True if the type is a scalar attribute, not a child component.

    Mirrors libNeuroML's approach in ``get_class_hierarchy``: if the type name
    cannot be resolved to a class in the ``neuroml`` module, it is a simple
    (scalar) type like ``NmlId``, ``Float``, ``xs:string``, etc.
    """
    return getattr(neuroml, type_name, None) is None


def _is_extractable(type_name: str) -> bool:
    """Return True if the component type should be extracted to a separate file.

    Covers cells, channels, and synapses.
    """
    return "Cell" in type_name or "Channel" in type_name or "Synapse" in type_name


def _get_file_suffix(type_name: str) -> str | None:
    """Derive the NeuroML file suffix from a component type name.

    Follows conventions: {id}.cell.nml, {id}.channel.nml, {id}.synapse.nml
    """
    if "Cell" in type_name:
        return "cell.nml"
    if "Channel" in type_name:
        return "channel.nml"
    if "Synapse" in type_name:
        return "synapse.nml"
    return None


def _sanitize_var_name(name: str | int) -> str:
    """Convert a NeuroML id to a valid Python variable name."""
    name = str(name)
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if name and name[0].isdigit():
        name = "_" + name
    if not name:
        name = "_unnamed"
    return name


# ---------------------------------------------------------------------------
# Component ordering -- human-logical model construction order
# ---------------------------------------------------------------------------


def _order_key(type_name: str) -> int:
    """Return an ordering key for a component type.

    Follows human-logical model construction order rather than schema
    dependency order: network -> populations -> cells -> channels ->
    synapses -> projections -> connections -> inputs -> metadata.
    """
    if type_name == "IncludeType":
        return 0
    if type_name == "Network":
        return 1
    if type_name == "Population":
        return 2
    if "Channel" in type_name:
        return 3
    if "Cell" in type_name:
        return 4
    if "Synapse" in type_name:
        return 5
    if "Projection" in type_name:
        return 6
    if type_name in ("Connection", "ConnectionW"):
        return 7
    if type_name in ("InputList", "InputW", "ExplicitInput"):
        return 8
    # PulseGenerator, SineGenerator, Property, Annotation, Layout, etc.
    return 9


# ---------------------------------------------------------------------------
# NmlPythonizer
# ---------------------------------------------------------------------------


class NmlPythonizer:
    """Load a NeuroML XML file and generate Python code to recreate it.

    Cells, channels, and synapses that are expanded inline in the source XML
    are extracted into separate files. Components from included files are
    preserved as includes.

    :param nml_file: Path to the NeuroML XML file.
    :param output_dir: Directory for output files. Defaults to the same
        directory as ``nml_file``.
    """

    def __init__(self, nml_file: str, output_dir: str | None = None) -> None:
        self.nml_file = nml_file
        self.output_dir = Path(output_dir) if output_dir else Path(nml_file).parent

        # id -> variable_name mapping
        self.id_to_var: dict[str, str] = {}
        # object identity -> variable_name mapping (for components without ids)
        self._obj_to_var: dict[int, str] = {}
        # Collected components: (obj, parent_var_name)
        self._components: list[tuple[Any, str | None]] = []
        # Variable name counter for duplicates
        self._var_counters: dict[str, int] = {}

        # Original include hrefs to preserve
        self._original_includes: list[str] = []
        # Extracted components that need to be written to separate files
        self._extracted: list[tuple[Any, str]] = []  # (obj, filename)

        # Load raw doc (no includes)  ---  this is what we walk for code generation
        self.raw_doc = read_neuroml2_file(nml_file, include_includes=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self) -> list[str]:
        """Generate and write all output files.

        Returns list of written file paths.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        written: list[str] = []

        # Collect components from raw doc and identify extractions
        self._collect_components()

        # Write extracted component files
        for comp, filename in self._extracted:
            filepath = self.output_dir / filename
            self._write_component_file(comp, filepath)
            written.append(str(filepath))

        # Generate and write Python script
        code = self.generate()
        script_path = self.output_dir / self._script_filename()
        script_path.write_text(code)
        written.append(str(script_path))

        return written

    def generate(self) -> str:
        """Generate and return the Python script as a string."""
        lines: list[str] = []
        lines.extend(self._gen_header())
        lines.extend(self._gen_includes())
        lines.extend(self._gen_body())
        lines.extend(self._gen_footer())
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Collection phase
    # ------------------------------------------------------------------

    def _collect_components(self) -> None:
        """Recursively collect all components from the raw document."""
        # First, collect include hrefs from the raw doc
        for inc in self.raw_doc.includes:
            self._original_includes.append(inc.href)

        # Walk the raw doc's children
        self._walk_children(self.raw_doc, parent_var="nml_doc")

    def _walk_children(self, obj: Any, parent_var: str) -> None:
        """Walk the children of a component, collecting them."""
        info_dict = obj.info(show_contents=True, return_format="dict")

        for member_name, member_info in info_dict.items():
            contents = member_info.get("members")
            if contents is None:
                continue
            if isinstance(contents, list) and len(contents) == 0:
                continue

            child_type = member_info.get("type", "")

            if not _is_scalar_type(child_type):
                if isinstance(contents, list):
                    for child in contents:
                        if hasattr(child, "info"):
                            child_var = self._collect_one(child, parent_var)
                            if child_var is not None:
                                self._walk_children(child, child_var)
                elif hasattr(contents, "info"):
                    child_var = self._collect_one(contents, parent_var)
                    if child_var is not None:
                        self._walk_children(contents, child_var)

    def _collect_one(self, obj: Any, parent_var: str) -> str | None:
        """Collect a single component, assigning a variable name.

        Returns the variable name assigned, or None if the component was skipped.
        """
        type_name = type(obj).__name__

        # Skip IncludeType  ---  handled separately
        if type_name == "IncludeType":
            return None

        # Extractable types (cells, channels, synapses) at root level
        if parent_var == "nml_doc" and _is_extractable(type_name):
            obj_id = getattr(obj, "id", None)
            if obj_id is not None:
                suffix = _get_file_suffix(type_name)
                if suffix:
                    filename = f"{obj_id}.{suffix}"
                    self._extracted.append((obj, filename))
                    # Skip from Python code generation
                    return None

        # Assign variable name
        var_name = self._make_var_name(obj, type_name)

        # Track all components by object identity
        self._obj_to_var[id(obj)] = var_name

        # Track components that have an id (referenceable by NmlId)
        if hasattr(obj, "id") and obj.id is not None:
            self.id_to_var[obj.id] = var_name

        self._components.append((obj, parent_var))
        return var_name

    def _make_var_name(self, obj: Any, type_name: str) -> str:
        """Create a unique Python variable name for a component."""
        if hasattr(obj, "id") and obj.id is not None:
            base = _sanitize_var_name(obj.id)
        else:
            base = type_name.lower()

        if base not in self._var_counters:
            self._var_counters[base] = 0
            return base

        self._var_counters[base] += 1
        return f"{base}_{self._var_counters[base]}"

    # ------------------------------------------------------------------
    # Component file extraction
    # ------------------------------------------------------------------

    def _write_component_file(self, comp: Any, filepath: Path) -> None:
        """Write a single component to a minimal NeuroML file."""
        comp_id = getattr(comp, "id", "unnamed")
        doc = component_factory("NeuroMLDocument", id=f"{comp_id}_doc")
        doc.add(comp, validate=False)
        writers.NeuroMLWriter.write(doc, str(filepath))

    # ------------------------------------------------------------------
    # Code generation
    # ------------------------------------------------------------------

    def _gen_header(self) -> list[str]:
        """Generate the script header with imports and root document."""
        lines = [
            "#!/usr/bin/env python3",
            f'"""Auto-generated from {self.nml_file} by NmlPythonizer."""',
            "",
            "from neuroml import NeuroMLDocument",
            "from neuroml.utils import component_factory",
            "",
        ]

        doc_id = getattr(self.raw_doc, "id", None) or "nml_doc"
        lines.append(f'nml_doc = component_factory("NeuroMLDocument", id={doc_id!r})')

        # Include root doc attributes (notes, etc.)
        root_kwargs = self._build_kwargs(self.raw_doc)
        # Filter out 'id' since we're using doc_id
        root_kwargs = [(k, v) for k, v in root_kwargs if k != "id"]
        if root_kwargs:
            kw_str = self._format_kwargs(root_kwargs)
            # Replace the simple line with one that includes kwargs
            lines[-1] = (
                f'nml_doc = component_factory("NeuroMLDocument", id={doc_id!r}, {kw_str}, validate=False)'
            )

        lines.append("")
        return lines

    def _gen_includes(self) -> list[str]:
        """Generate include statements."""
        if not self._original_includes and not self._extracted:
            return []

        lines = ["# --- Includes ---"]

        # Original includes (preserved as-is)
        for href in self._original_includes:
            lines.append(f'nml_doc.add("IncludeType", href={href!r}, validate=False)')

        # Extracted inline components
        for comp, filename in self._extracted:
            lines.append(
                f'nml_doc.add("IncludeType", href={filename!r}, validate=False)'
            )

        lines.append("")
        return lines

    def _gen_body(self) -> list[str]:
        """Generate component creation code, ordered by dependency."""
        sorted_components = sorted(
            self._components,
            key=lambda item: _order_key(type(item[0]).__name__),
        )

        lines: list[str] = []
        current_section = None

        for comp, parent_var in sorted_components:
            type_name = type(comp).__name__
            section = _get_section_name(type_name)

            if section != current_section:
                if lines:
                    lines.append("")
                lines.append(f"# --- {section} ---")
                current_section = section

            lines.extend(self._gen_component(comp, parent_var))

        return lines

    def _gen_component(self, obj: Any, parent_var: str | None) -> list[str]:
        """Generate the add() call for a single component."""
        type_name = type(obj).__name__
        var_name = self._obj_to_var.get(id(obj), _sanitize_var_name(type_name.lower()))

        if parent_var is None:
            parent_var = "nml_doc"

        kwargs = self._build_kwargs(obj)

        kw_str = self._format_kwargs(kwargs)
        call = f"{var_name} = {parent_var}.add({type_name!r}, {kw_str}, validate=False)"

        return [call]

    def _build_kwargs(self, obj: Any) -> list[tuple[str, str]]:
        """Build a list of (name, value_str) kwargs for the add() call."""
        info_dict = obj.info(show_contents=True, return_format="dict")
        kwargs: list[tuple[str, str]] = []

        for member_name, member_info in info_dict.items():
            member_type = member_info.get("type", "")
            required = member_info.get("required", True)

            if not _is_scalar_type(member_type):
                continue

            value = getattr(obj, member_name, None)

            if value is None and not required:
                continue

            if self._is_default_value(obj, member_name, value):
                continue

            value_str = self._format_value(member_name, member_type, value)
            if value_str is None:
                continue

            kwargs.append((member_name, value_str))

        return kwargs

    def _is_default_value(self, obj: Any, member_name: str, value: Any) -> bool:
        """Check if a value matches the component's default for that member."""
        try:
            type_cls = type(obj)
            default_obj = type_cls()
            default_value = getattr(default_obj, member_name, None)
            return value == default_value
        except Exception:
            return False

    def _format_value(
        self, member_name: str, member_type: str, value: Any
    ) -> str | None:
        """Format a scalar attribute value for inclusion in add() kwargs."""
        if value is None:
            return None

        if (
            member_type in ("NmlId", "Nml2PopulationReferencePath")
            and member_name != "id"
        ):
            return repr(str(value))

        if isinstance(value, bool):
            return repr(value)

        if isinstance(value, (int, float)):
            return repr(value)

        if isinstance(value, str):
            return repr(value)

        return repr(str(value))

    def _format_kwargs(self, kwargs: list[tuple[str, str]]) -> str:
        """Format kwargs into a comma-separated string for the add() call."""
        if not kwargs:
            return ""

        parts = []
        for name, value in kwargs:
            parts.append(f"{name}={value}")

        return ", ".join(parts)

    def _gen_footer(self) -> list[str]:
        """Generate the final validation call."""
        return [
            "",
            "# --- Validate ---",
            "nml_doc.validate()",
            "",
        ]

    def _script_filename(self) -> str:
        """Derive the output script filename from the input file."""
        return Path(self.nml_file).with_suffix(".py").name


def _get_section_name(type_name: str) -> str:
    """Return the section header name for a component type."""
    if type_name == "IncludeType":
        return "Includes"
    if type_name == "Network":
        return "Networks"
    if type_name == "Population":
        return "Populations"
    if "Cell" in type_name:
        return "Cells"
    if "Channel" in type_name:
        return "Channels"
    if "Synapse" in type_name:
        return "Synapses"
    if "Projection" in type_name:
        return "Projections"
    if type_name in ("Connection", "ConnectionW"):
        return "Connections"
    if type_name in ("InputList", "InputW", "ExplicitInput"):
        return "Inputs"
    return "Other"


def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "A script to convert NeuroML XML serializations into Python scripts"
        )
    )

    parser.add_argument(
        "file",
        type=str,
        metavar="<NeuroML 2 file>",
        help="Name of the NeuroML 2 file",
    )

    parser.add_argument(
        "-outputDirectory",
        type=str,
        metavar="<output_directory>",
        default=".",
        help="Output directory",
    )
    return parser.parse_args()


def main(args=None):
    """Main runner method"""
    if args is None:
        args = process_args()

    cli(a=args)


def cli(a: Any | None = None, **kwargs: str):
    """Main cli caller method"""
    a = pynmluc.build_namespace({}, a, **kwargs)

    nmlfile = a.file
    output_dir = a.output_directory

    converter = NmlPythonizer(nmlfile, output_dir)
    converter.write()
