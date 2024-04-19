#!/usr/bin/env python3
"""
Methods related to annotations

File: pyneuroml/annotations.py

Copyright 2024 NeuroML contributors
"""


import logging
import pprint
import typing

from lxml import etree
from rdflib import RDF, BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, RDFS

from pyneuroml.utils.xml import _find_elements, _get_attr_in_element

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    isinstance_of: typing.Optional[typing.Dict[str, str]] = None,
    has_instance: typing.Optional[typing.Dict[str, str]] = None,
    predecessors: typing.Optional[typing.Dict[str, str]] = None,
    successors: typing.Optional[typing.Dict[str, str]] = None,
    see_also: typing.Optional[typing.Dict[str, str]] = None,
    references: typing.Optional[typing.Dict[str, str]] = None,
    other_ids: typing.Optional[typing.Dict[str, str]] = None,
    citations: typing.Optional[typing.Dict[str, str]] = None,
    authors: typing.Optional[typing.Dict[str, str]] = None,
    contributors: typing.Optional[typing.Dict[str, str]] = None,
    license: typing.Optional[typing.Dict[str, str]] = None,
    funders: typing.Optional[typing.Dict[str, str]] = None,
    creation_date: typing.Optional[str] = None,
    modified_dates: typing.Optional[typing.List[str]] = None,
    serialization_format: str = "pretty-xml",
    write_to_file: typing.Optional[str] = None,
):
    """Create an RDF annotation from the provided fields

    .. versionadded:: 1.2.10

    This can be used to create an RDF annotation for a subject---a model or a
    file like an OMEX archive file. It supports most qualifiers and will be
    continuously updated to support more as they are added.

    It merely uses rdflib to make life easier for users to create annotations
    by coding in the various predicates for each subject.

    For information on the specifications, see:

    - https://github.com/combine-org/combine-specifications/blob/main/specifications/qualifiers-1.1.md
    - https://docs.biosimulations.org/concepts/conventions/simulation-project-metadata/

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
    :param isinstance_of: is an instance of
    :type isinstance_of: dict(str, str)
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
    :type authors: dict(str, str)
    :param contributors: other contributors
    :type contributors: dict(str, str)
    :param license: license
    :type license: dict(str, str)
    :param funders: funders
    :type funders: dict(str, str)
    :param creation_date: date in YYYY-MM-DD format when this was created (eg: 2024-04-19)
    :type creation_date: str
    :param modified_dates: dates in YYYY-MM-DD format when modifications were made
    :type modified_dates: list(str)
    :param serialization_format: format to serialize in using `rdflib.serialize`
    :type serialization_format: str
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
        for idf, label in organisms.items():
            hasTaxon = BNode()
            doc.add((subjectobj, BQBIOL.hasTaxon, hasTaxon))
            doc.add((hasTaxon, DC.identifier, URIRef(idf)))
            doc.add((hasTaxon, RDFS.label, Literal(label)))
    if encodes_other_biology:
        doc.bind("bqbiol:encodes", BQBIOL + "/encodes")
        for idf, label in encodes_other_biology.items():
            encodes = BNode()
            doc.add((subjectobj, BQBIOL.encodes, encodes))
            doc.add((encodes, DC.identifier, URIRef(idf)))
            doc.add((encodes, RDFS.label, Literal(label)))
    if has_version:
        doc.bind("bqbiol:hasVersion", BQBIOL + "/hasVersion")
        for idf, label in has_version.items():
            hasVersion = BNode()
            doc.add((subjectobj, BQBIOL.hasVersion, hasVersion))
            doc.add((hasVersion, DC.identifier, URIRef(idf)))
            doc.add((hasVersion, RDFS.label, Literal(label)))
    if is_version_of:
        doc.bind("bqbiol:isVersionOf", BQBIOL + "/isVersionOf")
        for idf, label in is_version_of.items():
            isVersionOf = BNode()
            doc.add((subjectobj, BQBIOL.isVersionOf, isVersionOf))
            doc.add((isVersionOf, DC.identifier, URIRef(idf)))
            doc.add((isVersionOf, RDFS.label, Literal(label)))
    if has_part:
        doc.bind("bqbiol:hasPart", BQBIOL + "/hasPart")
        for idf, label in has_part.items():
            hasPart = BNode()
            doc.add((subjectobj, BQBIOL.hasPart, hasPart))
            doc.add((hasPart, DC.identifier, URIRef(idf)))
            doc.add((hasPart, RDFS.label, Literal(label)))
    if is_part_of:
        doc.bind("bqbiol:isPartOf", BQBIOL + "/isPartOf")
        for idf, label in is_part_of.items():
            isPartOf = BNode()
            doc.add((subjectobj, BQBIOL.isPartOf, isPartOf))
            doc.add((isPartOf, DC.identifier, URIRef(idf)))
            doc.add((isPartOf, RDFS.label, Literal(label)))
    if has_property:
        doc.bind("bqbiol:hasProperty", BQBIOL + "/hasProperty")
        for idf, label in has_property.items():
            hasProperty = BNode()
            doc.add((subjectobj, BQBIOL.hasProperty, hasProperty))
            doc.add((hasProperty, DC.identifier, URIRef(idf)))
            doc.add((hasProperty, RDFS.label, Literal(label)))
    if is_property_of:
        doc.bind("bqbiol:isPropertyOf", BQBIOL + "/isPropertyOf")
        for idf, label in is_property_of.items():
            isPropertyOf = BNode()
            doc.add((subjectobj, BQBIOL.isPropertyOf, isPropertyOf))
            doc.add((isPropertyOf, DC.identifier, URIRef(idf)))
            doc.add((isPropertyOf, RDFS.label, Literal(label)))
    if sources:
        for idf, label in sources.items():
            s = BNode()
            doc.add((subjectobj, DC.source, s))
            doc.add((s, DC.identifier, URIRef(idf)))
            doc.add((s, RDFS.label, Literal(label)))
    if isinstance_of:
        doc.bind("bqmodel:isInstanceOf", BQMODEL + "/isInstanceOf")
        for idf, label in isinstance_of.items():
            isInstanceOf = BNode()
            doc.add((subjectobj, BQMODEL.isInstanceOf, isInstanceOf))
            doc.add((isInstanceOf, DC.identifier, URIRef(idf)))
            doc.add((isInstanceOf, RDFS.label, Literal(label)))
    if has_instance:
        doc.bind("bqmodel:hasInstance", BQMODEL + "/hasInstance")
        for idf, label in has_instance.items():
            hasInstance = BNode()
            doc.add((subjectobj, BQMODEL.hasInstance, hasInstance))
            doc.add((hasInstance, DC.identifier, URIRef(idf)))
            doc.add((hasInstance, RDFS.label, Literal(label)))
    if predecessors:
        doc.bind("bqmodel:isDerivedFrom", BQMODEL + "/isDerivedFrom")
        for idf, label in predecessors.items():
            isDerivedFrom = BNode()
            doc.add((subjectobj, BQMODEL.isDerivedFrom, isDerivedFrom))
            doc.add((isDerivedFrom, DC.identifier, URIRef(idf)))
            doc.add((isDerivedFrom, RDFS.label, Literal(label)))
    if successors:
        doc.bind("scoro:successor", SCORO + "/successor")
        for idf, label in successors.items():
            succ = BNode()
            doc.add((subjectobj, SCORO.successor, succ))
            doc.add((succ, DC.identifier, URIRef(idf)))
            doc.add((succ, RDFS.label, Literal(label)))
    if see_also:
        for idf, label in see_also.items():
            sa = BNode()
            doc.add((subjectobj, RDFS.seeAlso, sa))
            doc.add((sa, DC.identifier, URIRef(idf)))
            doc.add((sa, RDFS.label, Literal(label)))
    if references:
        for idf, label in references.items():
            r = BNode()
            doc.add((subjectobj, DCTERMS.references, sa))
            doc.add((r, DC.identifier, URIRef(idf)))
            doc.add((r, RDFS.label, Literal(label)))
    if other_ids:
        doc.bind("bqmodel:is", BQMODEL + "/is")
        for idf, label in other_ids.items():
            oi = BNode()
            doc.add((subjectobj, BQMODEL.IS, oi))
            doc.add((oi, DC.identifier, URIRef(idf)))
            doc.add((oi, RDFS.label, Literal(label)))
    if citations:
        doc.bind("bqmodel:isDescribedBy", BQMODEL + "/isDescribedBy")
        for idf, label in citations.items():
            cit = BNode()
            doc.add((subjectobj, BQMODEL.isDescribedBy, cit))
            doc.add((cit, DC.identifier, URIRef(idf)))
            doc.add((cit, RDFS.label, Literal(label)))
    if authors:
        for idf, label in authors.items():
            ac = BNode()
            doc.add((subjectobj, DC.creator, ac))
            doc.add((ac, FOAF.name, Literal(idf)))
            doc.add((ac, FOAF.label, Literal(label)))
    if contributors:
        for idf, label in contributors.items():
            ac = BNode()
            doc.add((subjectobj, DC.contributor, ac))
            doc.add((ac, FOAF.name, Literal(idf)))
            doc.add((ac, FOAF.label, Literal(label)))
    if license:
        assert len(license.items()) == 1
        for idf, label in license.items():
            ac = BNode()
            doc.add((subjectobj, DCTERMS.license, ac))
            doc.add((ac, FOAF.name, Literal(idf)))
            doc.add((ac, FOAF.label, Literal(label)))
    if funders:
        doc.bind("scoro:funder", SCORO + "/funder")
        for idf, label in funders.items():
            ac = BNode()
            doc.add((subjectobj, SCORO.funder, ac))
            doc.add((ac, FOAF.name, Literal(idf)))
            doc.add((ac, FOAF.label, Literal(label)))
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

    if write_to_file:
        with open(write_to_file, "w") as f:
            print(annotation, file=f)

    return annotation
