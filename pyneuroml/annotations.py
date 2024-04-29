#!/usr/bin/env python3
"""
Methods related to annotations

File: pyneuroml/annotations.py

Copyright 2024 NeuroML contributors
"""

import re
import logging
import pprint
import typing
import textwrap

from lxml import etree
from pyneuroml.utils.xml import _find_elements, _get_attr_in_element

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from rdflib import BNode, Graph, Literal, Namespace, URIRef, Bag
    from rdflib.namespace import DC, DCTERMS, FOAF, RDFS
except ImportError:
    logger.warning("Please install optional dependencies to use annotation features:")
    logger.warning("pip install pyneuroml[annotations]")


# From https://docs.biosimulations.org/concepts/conventions/simulation-project-metadata/
PREDICATES_MAP = {
    "keyword": "http://prismstandard.org/namespaces/basic/2.0/keyword",
    "thumbnail": "http://www.collex.org/schema#thumbnail",
}

# From https://doi.org/10.1515/jib-2021-0020 (page 3)
# rdf, foaf, dc already included in rdflib
NAMESPACES_MAP = {
    "orcid": "https://orcid.org/",
    "bqmodel": "http://biomodels.net/model-qualifiers/",
    "bqbiol": "http://biomodels.net/biology-qualifiers/",
    "pubmed": "https://identifiers.org/pubmed:",
    "NCBI_Taxon": "https://identifiers.org/taxonomy:",
    "biomod": "https://identifiers.org/biomodels.db:",
    "chebi": "https://identifiers.org/CHEBI:",
    "uniprot": "https://identifiers.org/uniprot:",
    "obp": "https://identifiers.org/opb:",
    "fma": "https://identifiers.org/FMA:",
    "semsim": "http://bime.uw.edu/semsim/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "collex": "http://www.collex.org/schema",
    "scoro": "http://purl.org/spar/scoro",
}


def extract_annotations(nml2_file: str) -> None:
    """Extract and print annotations from a NeuroML 2 file.

    :param nml2_file: name of NeuroML2 file to parse
    :type nml2_file: str
    """
    pp = pprint.PrettyPrinter()
    test_file = open(nml2_file)
    root = etree.parse(test_file).getroot()
    annotations = {}  # type: dict

    for a in _find_elements(root, "annotation"):
        for r in _find_elements(a, "Description", rdf=True):
            desc = _get_attr_in_element(r, "about", rdf=True)
            annotations[desc] = []

            for info in r:
                if isinstance(info.tag, str):
                    kind = info.tag.replace(
                        "{http://biomodels.net/biology-qualifiers/}", "bqbiol:"
                    )
                    kind = kind.replace(
                        "{http://biomodels.net/model-qualifiers/}", "bqmodel:"
                    )

                    for li in _find_elements(info, "li", rdf=True):
                        attr = _get_attr_in_element(li, "resource", rdf=True)
                        if attr:
                            annotations[desc].append({kind: attr})

    logger.info("Annotations in %s: " % (nml2_file))
    pp.pprint(annotations)


def create_annotation(
    subject,
    title=None,
    abstract=None,
    annotation_style: typing.Literal["miriam", "biosimulations"] = "biosimulations",
    serialization_format: str = "pretty-xml",
    write_to_file: typing.Optional[str] = None,
    xml_header: bool = True,
    indent: int = 12,
    description: typing.Optional[str] = None,
    keywords: typing.Optional[typing.List[str]] = None,
    thumbnails: typing.Optional[typing.List[str]] = None,
    organisms: typing.Optional[typing.Dict[str, str]] = None,
    encodes_other_biology: typing.Optional[typing.Dict[str, str]] = None,
    has_version: typing.Optional[typing.Dict[str, str]] = None,
    is_version_of: typing.Optional[typing.Dict[str, str]] = None,
    has_part: typing.Optional[typing.Dict[str, str]] = None,
    is_part_of: typing.Optional[typing.Dict[str, str]] = None,
    has_property: typing.Optional[typing.Dict[str, str]] = None,
    is_property_of: typing.Optional[typing.Dict[str, str]] = None,
    sources: typing.Optional[typing.Dict[str, str]] = None,
    is_instance_of: typing.Optional[typing.Dict[str, str]] = None,
    has_instance: typing.Optional[typing.Dict[str, str]] = None,
    predecessors: typing.Optional[typing.Dict[str, str]] = None,
    successors: typing.Optional[typing.Dict[str, str]] = None,
    see_also: typing.Optional[typing.Dict[str, str]] = None,
    references: typing.Optional[typing.Dict[str, str]] = None,
    other_ids: typing.Optional[typing.Dict[str, str]] = None,
    citations: typing.Optional[typing.Dict[str, str]] = None,
    authors: typing.Optional[
        typing.Union[typing.Dict[str, typing.Dict[str, str]], typing.Set]
    ] = None,
    contributors: typing.Optional[
        typing.Union[typing.Dict[str, typing.Dict[str, str]], typing.Set]
    ] = None,
    license: typing.Optional[typing.Dict[str, str]] = None,
    funders: typing.Optional[typing.Dict[str, str]] = None,
    creation_date: typing.Optional[str] = None,
    modified_dates: typing.Optional[typing.List[str]] = None,
):
    """Create an RDF annotation from the provided fields

    .. versionadded:: 1.2.10

    This can be used to create an RDF annotation for a subject---a model or a
    file like an OMEX archive file. It supports most qualifiers and will be
    continuously updated to support more as they are added.

    It merely uses rdflib to make life easier for users to create annotations
    by coding in the various predicates for each subject.

    For information on the specifications, see:

    - COMBINE specifications: https://github.com/combine-org/combine-specifications/blob/main/specifications/qualifiers-1.1.md
    - Biosimulations guidelines: https://docs.biosimulations.org/concepts/conventions/simulation-project-metadata/
    - MIRIAM guidelines: https://drive.google.com/file/d/1JqjcH0T0UTWMuBj-scIMwsyt2z38A0vp/view


    Note that:

    - not all qualifiers have been included yet
    - the qualifiers and their representations may change in the future

    For any arguments here that take a dictionary of strings, the key is the
    resource reference URI, and the value is the string label. For example:

    .. code-block:: python

        encodes_other_biology={
            "http://identifiers.org/GO:0009653": "anatomical structure morphogenesis",
            "http://identifiers.org/kegg:ko04111": "Cell cycle - yeast",
        }

    :param subject: subject/target of the annotation
        could be a file, a mode component
    :type subject: str
    :param title: title of annotation
        This is required for publishing models on biosimulations.org
    :type title: str
    :param abstract: an abstract
    :type abstract: str
    :param annotation_style: type of annotation: either "miriam" or
        "biosimulations" (default).

        There's a difference in the annotation "style" suggested by MIRIAM and
        Biosimulations. MIRIAM suggests the use of RDF containers (bags)
        wherewas Biosimulations does not. This argument allows the user to
        select what style they want to use for the annotation.
    :type annotation_style: str
    :param serialization_format: format to serialize in using `rdflib.serialize`
        See: https://rdflib.readthedocs.io/en/stable/plugin_serializers.html
    :type serialization_format: str
    :param xml_header: toggle inclusion of xml header if serializing in xml format
    :type xml_header: bool
    :param indent: number of spaces to use to indent the annotation block
    :type indent: int
    :param description: a longer description
    :type description: str
    :param keywords: keywords
    :type keywords: list(str)
    :param thumbnails: thumbnails
    :type thumbnails: list(str)
    :param organisms: of organisms
    :type organisms: dict(str, str)
    :param encodes_other_biology:  other biological entities
    :type encodes_other_biology: dict(str, str)
    :param has_version: other versions
    :type has_version: dict(str, str)
    :param is_version_of: is a version of
    :type is_version_of: dict(str, str)
    :param has_part: includes another as a part
    :type has_part: dict(str, str)
    :param is_part_of: is a part of another entity
    :type is_part_of: dict(str, str)
    :param has_property: has a property
    :type has_property: dict(str, str)
    :param is_property_of: is a property of another entity
    :type is_property_of: dict(str, str)
    :param sources: links to sources (on GitHub and so on)
    :type sources: dict(str, str)
    :param is_instance_of: is an instance of
    :type is_instance_of: dict(str, str)
    :param has_instance: has instance of another entity
    :type has_instance: dict(str, str)
    :param predecessors: predecessors of this entity
    :type predecessors: dict(str, str)
    :param successors: successors of this entity
    :type successors: dict(str, str)
    :param see_also: more information
    :type see_also: dict(str, str)
    :param references: references
    :type references: dict(str, str)
    :param other_ids: other IDs
    :type other_ids: dict(str, str)
    :param citations: related citations
    :type citations: dict(str, str)
    :param authors: authors
        This can either be:

        - a set: {"Author A", "Author B"}
        - a dictionary: {"Author A": {"https://../": "accountname", "..": ".."}}

        All labels apart from "accountname" are ignored
    :type authors: dict(str, dict(str, str) or set
    :param contributors: other contributors, follws the same format as authors
    :type contributors: dict(str, dict(str, str) or set
    :param license: license
    :type license: dict(str, str)
    :param funders: funders
    :type funders: dict(str, str)
    :param creation_date: date in YYYY-MM-DD format when this was created (eg: 2024-04-19)
    :type creation_date: str
    :param modified_dates: dates in YYYY-MM-DD format when modifications were made
    :type modified_dates: list(str)
    :param write_to_file: path to file to write to
    :type write_to_file: str
    :returns: the annotation string in the requested format.

    """
    doc = Graph()

    # namespaces not in rdflib
    PRISM = Namespace(NAMESPACES_MAP["prism"])
    doc.bind("prism", PRISM)
    COLLEX = Namespace(NAMESPACES_MAP["collex"])
    doc.bind("collex", COLLEX)
    BQBIOL = Namespace(NAMESPACES_MAP["bqbiol"])
    doc.bind("bqbiol", BQBIOL)
    BQMODEL = Namespace(NAMESPACES_MAP["bqmodel"])
    doc.bind("bqmodel", BQMODEL)
    SCORO = Namespace(NAMESPACES_MAP["scoro"])
    doc.bind("scoro", SCORO)

    # if subject is a file
    if subject.endswith(".omex"):
        fileprefix = f"http://omex-library.org/{subject}"
        subjectobj = URIRef(fileprefix)
    elif subject.endswith(".nml"):
        fileprefix = "http://omex-library.org/ArchiveName.omex"
        subjectobj = URIRef(f"{fileprefix}/{subject}")
    else:
        subjectobj = Literal(subject)

    doc.add((subjectobj, DC.title, Literal(title)))
    if abstract:
        doc.add((subjectobj, DCTERMS.abstract, Literal(abstract)))
    if description:
        doc.add((subjectobj, DC.description, Literal(description)))
    if keywords:
        for k in keywords:
            doc.add((subjectobj, PRISM.keyword, Literal(k)))
    if thumbnails:
        for t in thumbnails:
            doc.add((subjectobj, COLLEX.thumbnail, URIRef(f"{fileprefix}/{t}")))
    if organisms:
        doc.bind("bqbiol:hasTaxon", BQBIOL + "/hasTaxon")
        _add_element(doc, subjectobj, organisms, BQBIOL.hasTaxon, annotation_style)
    if encodes_other_biology:
        doc.bind("bqbiol:encodes", BQBIOL + "/encodes")
        _add_element(
            doc, subjectobj, encodes_other_biology, BQBIOL.encodes, annotation_style
        )
    if has_version:
        doc.bind("bqbiol:hasVersion", BQBIOL + "/hasVersion")
        _add_element(doc, subjectobj, has_version, BQBIOL.hasVersion, annotation_style)
    if is_version_of:
        doc.bind("bqbiol:isVersionOf", BQBIOL + "/isVersionOf")
        _add_element(
            doc, subjectobj, is_version_of, BQBIOL.isVersionOf, annotation_style
        )
    if has_part:
        doc.bind("bqbiol:hasPart", BQBIOL + "/hasPart")
        _add_element(doc, subjectobj, has_part, BQBIOL.hasPart, annotation_style)
    if is_part_of:
        doc.bind("bqbiol:isPartOf", BQBIOL + "/isPartOf")
        _add_element(doc, subjectobj, is_part_of, BQBIOL.isPartOf, annotation_style)
    if has_property:
        doc.bind("bqbiol:hasProperty", BQBIOL + "/hasProperty")
        _add_element(
            doc, subjectobj, has_property, BQBIOL.hasProperty, annotation_style
        )
    if is_property_of:
        doc.bind("bqbiol:isPropertyOf", BQBIOL + "/isPropertyOf")
        _add_element(
            doc, subjectobj, is_property_of, BQBIOL.isPropertyOf, annotation_style
        )
    if sources:
        _add_element(doc, subjectobj, sources, DC.source, annotation_style)
    if is_instance_of:
        doc.bind("bqmodel:isInstanceOf", BQMODEL + "/isInstanceOf")
        _add_element(
            doc, subjectobj, is_instance_of, BQMODEL.isInstanceOf, annotation_style
        )
    if has_instance:
        doc.bind("bqmodel:hasInstance", BQMODEL + "/hasInstance")
        _add_element(
            doc, subjectobj, has_instance, BQMODEL.hasInstance, annotation_style
        )
    if predecessors:
        doc.bind("bqmodel:isDerivedFrom", BQMODEL + "/isDerivedFrom")
        _add_element(
            doc, subjectobj, predecessors, BQMODEL.isDerivedFrom, annotation_style
        )
    if successors:
        doc.bind("scoro:successor", SCORO + "/successor")
        _add_element(doc, subjectobj, successors, SCORO.successor, annotation_style)
    if see_also:
        _add_element(doc, subjectobj, see_also, RDFS.seeAlso, annotation_style)
    if references:
        _add_element(doc, subjectobj, references, DCTERMS.references, annotation_style)
    if other_ids:
        doc.bind("bqmodel:is", BQMODEL + "/is")
        _add_element(doc, subjectobj, other_ids, BQMODEL.IS, annotation_style)
    if citations:
        doc.bind("bqmodel:isDescribedBy", BQMODEL + "/isDescribedBy")
        _add_element(
            doc, subjectobj, citations, BQMODEL.isDescribedBy, annotation_style
        )
    if authors:
        _add_humans(doc, subjectobj, authors, DC.creator, annotation_style)
    if contributors:
        _add_humans(doc, subjectobj, contributors, DC.contributor, annotation_style)
    if license:
        assert len(license.items()) == 1
        _add_element(doc, subjectobj, license, DCTERMS.license, annotation_style)
    if funders:
        doc.bind("scoro:funder", SCORO + "/funder")
        _add_element(doc, subjectobj, funders, SCORO.funder, annotation_style)
    if creation_date:
        ac = BNode()
        doc.add((subjectobj, DCTERMS.created, ac))
        doc.add((ac, DCTERMS.W3CDTF, Literal(creation_date)))
    if modified_dates:
        ac = BNode()
        doc.add((subjectobj, DCTERMS.modified, ac))
        for d in modified_dates:
            doc.add((ac, DCTERMS.W3CDTF, Literal(d)))

    annotation = doc.serialize(format=serialization_format)

    # indent
    if indent > 0:
        annotation = textwrap.indent(annotation, " " * indent)

    # xml issues
    if "xml" in serialization_format:
        # replace rdf:_1 etc with rdf:li
        # our LEMS definitions only know rdf:li
        # https://github.com/RDFLib/rdflib/issues/1374#issuecomment-885656850
        rdfli_pattern = re.compile(r"\brdf:_\d+\b")
        annotation = rdfli_pattern.sub("rdf:li", annotation)

        # remove nodeids for rdflib BNodes: these aren't required
        rdfbnode_pattern = re.compile(r' rdf:nodeID="\S+"')
        annotation = rdfbnode_pattern.sub("", annotation)

        # remove xml header, not used when embedding into other NeuroML files
        if xml_header is False:
            annotation = annotation[annotation.find(">") + 1 :]

    if write_to_file:
        with open(write_to_file, "w") as f:
            print(annotation, file=f)

    return annotation


def _add_element(
    doc: Graph,
    subjectobj: typing.Union[URIRef, Literal],
    info: typing.Dict[str, str],
    node_type: URIRef,
    annotation_style: str,
):
    """Add an new element to the RDF annotation

    :param doc: main rdf document object
    :type doc: RDF.Graph
    :param subjectobj: main object being referred to
    :type subjectobj: URIRef or Literal
    :param info: dictionary of entries and their labels
    :type info: dict
    :param node_type: node type
    :type node_type: URIRef
    :param annotation_style: type of annotation
    :type annotation_style: str
    """
    if annotation_style not in ["biosimulations", "miriam"]:
        raise ValueError("Annotation style must either be 'miriam' or 'biosimulations'")

    for idf, label in info.items():
        top_node = BNode()
        doc.add((subjectobj, node_type, top_node))
        if annotation_style == "biosimulations":
            doc.add((top_node, DC.identifier, URIRef(idf)))
            doc.add((top_node, RDFS.label, Literal(label)))
        elif annotation_style == "miriam":
            Bag(doc, top_node, [URIRef(idf)])


def _add_humans(
    doc: Graph,
    subjectobj: typing.Union[URIRef, Literal],
    info_dict: typing.Union[typing.Dict[str, typing.Dict[str, str]], typing.Set],
    node_type: URIRef,
    annotation_style: str,
):
    """Add an new elements related to humans to the RDF annotation.

    This covers authors/contributors where the same person can have multiple
    annotations related to them.

    :param doc: main rdf document object
    :type doc: RDF.Graph
    :param subjectobj: main object being referred to
    :type subjectobj: URIRef or Literal
    :param info_dict: dictionary of information
    :type info_dict: dict
    :param node_type: node type
    :type node_type: URIRef
    :param annotation_style: type of annotation
    :type annotation_style: str
    """
    if annotation_style not in ["biosimulations", "miriam"]:
        raise ValueError("Annotation style must either be 'miriam' or 'biosimulations'")

    if isinstance(info_dict, dict):
        for name, info in info_dict.items():
            top_node = BNode()
            doc.add((subjectobj, node_type, top_node))

            # add name
            if annotation_style == "biosimulations":
                doc.add((top_node, FOAF.name, Literal(name)))
                doc.add((top_node, RDFS.label, Literal(name)))
            elif annotation_style == "miriam":
                bag = Bag(doc, top_node, [Literal(name)])

            # other fields
            for idf, label in info.items():
                if annotation_style == "biosimulations":
                    if label == "accountname":
                        doc.add((top_node, FOAF.accountName, URIRef(idf)))
                    else:
                        doc.add((top_node, DC.identifier, URIRef(idf)))
                elif annotation_style == "miriam":
                    if idf.startswith("http:"):
                        bag.append(URIRef(idf))
                    else:
                        bag.append(Literal(idf))
    else:
        for name in info_dict:
            top_node = BNode()
            doc.add((subjectobj, node_type, top_node))
            # add name
            if annotation_style == "biosimulations":
                doc.add((top_node, FOAF.name, Literal(name)))
                doc.add((top_node, RDFS.label, Literal(name)))
            elif annotation_style == "miriam":
                bag = Bag(doc, top_node, [Literal(name)])
