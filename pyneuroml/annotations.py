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
from pyneuroml.utils.xml import _find_elements

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from rdflib import BNode, Graph, Literal, Namespace, URIRef, Bag, Container
    from rdflib.namespace import DC, DCTERMS, FOAF, RDFS, RDF
except ImportError:
    logger.warning("Please install optional dependencies to use annotation features:")
    logger.warning("pip install pyneuroml[annotations]")


# From https://docs.biosimulations.org/concepts/conventions/simulation-project-metadata/
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


# create namespaces not included in rdflib
PRISM = Namespace(NAMESPACES_MAP["prism"])
COLLEX = Namespace(NAMESPACES_MAP["collex"])
BQBIOL = Namespace(NAMESPACES_MAP["bqbiol"])
BQMODEL = Namespace(NAMESPACES_MAP["bqmodel"])
SCORO = Namespace(NAMESPACES_MAP["scoro"])


class Annotation(object):
    """For handling NeuroML annotations"""

    # extra mappings
    P_MAP_EXTRA = {
        "hasTaxon": "bqbiol",
        "encodes": "bqbiol",
        "hasVersion": "bqbiol",
        "isVersionOf": "bqbiol",
        "hasPart": "bqbiol",
        "isPartOf": "bqbiol",
        "hasProperty": "bqbiol",
        "isPropertyOf": "bqbiol",
        "isInstanceOf": "bqmodel",
        "hasInstance": "bqmodel",
        "isDerivedFrom": "bqmodel",
        "successor": "scoro",
        "is": "bqmodel",
        "isDescribedBy": "bqmodel",
        "funder": "scoro",
    }

    def __init__(self):
        self.doc = Graph()

        # namespaces not in rdflib
        self.doc.bind("prism", PRISM)
        self.doc.bind("collex", COLLEX)
        self.doc.bind("bqbiol", BQBIOL)
        self.doc.bind("bqmodel", BQMODEL)
        self.doc.bind("scoro", SCORO)

        for k, v in self.P_MAP_EXTRA.items():
            self.doc.bind(f"{v}:{k}", f"v.upper()/{k}")

        self.ARG_MAP = {
            "title": DC.title,
            "abstract": DCTERMS.abstract,
            "description": DC.description,
            "keywords": PRISM.keyword,
            "thumbnails": COLLEX.thumbnail,
            "organisms": BQBIOL.hasTaxon,
            "encodes_other_biology": BQBIOL.encodes,
            "has_version": BQBIOL.hasVersion,
            "is_version_of": BQBIOL.isVersionOf,
            "has_part": BQBIOL.hasPart,
            "is_part_of": BQBIOL.isPartOf,
            "has_property": BQBIOL.hasProperty,
            "is_property_of": BQBIOL.isPropertyOf,
            "sources": DC.source,
            "is_instance_of": BQMODEL.isInstanceOf,
            "has_instance": BQMODEL.hasInstance,
            "predecessors": BQMODEL.isDerivedFrom,
            "successors": SCORO.successor,
            "see_also": RDFS.seeAlso,
            "references": DCTERMS.references,
            "other_ids": BQMODEL.IS,
            "citations": BQMODEL.isDescribedBy,
            "license": DCTERMS.license,
            "funders": SCORO.funder,
            "authors": DC.creator,
            "contributors": DC.contributor,
            "creation_date": DCTERMS.created,
            "modified_dates": DCTERMS.modified,
        }

    def create_annotation(
        self,
        subject: str,
        title: typing.Optional[str] = None,
        abstract: typing.Optional[str] = None,
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
            - a dictionary where the keys are author names and values are
              dictionaries of more metadata:

              {"Author A": {"https://../": "accountname", "..": ".."}}

            The inner dictionary should have the reference or literal as key, and
            can take a "label", which can be any of the FOAF attributes:

            http://xmlns.com/foaf/spec/#sec-glance

        :type authors: dict(str, dict(str, str) or set
        :param contributors: other contributors, follows the same format as authors
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
        # if subject is a file
        if subject.endswith(".omex"):
            fileprefix = f"http://omex-library.org/{subject}"
            subjectobj = URIRef(fileprefix)
        elif subject.endswith(".nml"):
            fileprefix = "http://omex-library.org/ArchiveName.omex"
            subjectobj = URIRef(f"{fileprefix}/{subject}")
        else:
            subjectobj = Literal(subject)

        # get the args passed to this function
        mylocals = locals()

        self.doc.add((subjectobj, self.ARG_MAP["title"], Literal(title)))

        # loop over the rest
        for arg, val in mylocals.items():
            if arg in self.ARG_MAP.keys():
                # handle any special cases
                if arg == "thumbnails":
                    prefixed = [
                        f"{fileprefix}/{t}" if (not t.startswith("http")) else t
                        for t in val
                    ]
                    self._add_element(
                        subjectobj, prefixed, self.ARG_MAP[arg], annotation_style
                    )

                elif arg == "license":
                    assert len(val.items()) == 1
                    self._add_element(
                        subjectobj, val, self.ARG_MAP[arg], annotation_style
                    )

                elif arg == "authors" or arg == "contributors":
                    self._add_humans(
                        subjectobj, val, self.ARG_MAP[arg], annotation_style
                    )
                elif arg == "creation_date":
                    ac = BNode()
                    self.doc.add((subjectobj, self.ARG_MAP[arg], ac))
                    self.doc.add((ac, DCTERMS.W3CDTF, Literal(val)))

                elif arg == "modified_dates":
                    ac = BNode()
                    self.doc.add((subjectobj, self.ARG_MAP[arg], ac))
                    if annotation_style == "biosimulations":
                        for d in val:
                            self.doc.add((ac, DCTERMS.W3CDTF, Literal(d)))
                    else:
                        another = BNode()
                        self.doc.add((ac, DCTERMS.W3CDTF, another))
                        newbag = Bag(self.doc, another)
                        for d in val:
                            newbag.append(Literal(d))
                else:
                    self._add_element(
                        subjectobj, val, self.ARG_MAP[arg], annotation_style
                    )

        annotation = self.doc.serialize(format=serialization_format)

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
        self,
        subjectobj: typing.Union[URIRef, Literal],
        info_dict: typing.Union[typing.Iterable[str], typing.Dict[str, str]],
        node_type: URIRef,
        annotation_style: str,
    ):
        """Add an new element to the RDF annotation

        :param subjectobj: main object being referred to
        :type subjectobj: URIRef or Literal
        :param info_dict: dictionary of entries and their labels, or Iterable if no labels
        :type info_dict: dict or Iterable
        :param node_type: node type
        :type node_type: URIRef
        :param annotation_style: type of annotation
        :type annotation_style: str
        """
        if annotation_style not in ["biosimulations", "miriam"]:
            raise ValueError(
                "Annotation style must either be 'miriam' or 'biosimulations'"
            )

        logger.debug(f"Processing element {node_type}: {info_dict} ({type(info_dict)})")

        # do nothing if an empty dict is passed
        if info_dict is None:
            return

        # for biosimulations, we do not use bags
        if annotation_style == "biosimulations":
            if isinstance(info_dict, dict):
                for idf, label in info_dict.items():
                    # add a top level node
                    top_node = BNode()
                    self.doc.add((subjectobj, node_type, top_node))
                    self.doc.add((top_node, DC.identifier, URIRef(idf)))
                    if len(label) > 0:
                        self.doc.add((top_node, RDFS.label, Literal(label)))
            elif isinstance(info_dict, list):
                for it in info_dict:
                    self.doc.add((subjectobj, node_type, _URIRef_or_Literal(it)))
            elif isinstance(info_dict, str):
                self.doc.add((subjectobj, node_type, _URIRef_or_Literal(info_dict)))
            else:
                raise ValueError(f"Could not parse: {node_type}: {info_dict}")

        elif annotation_style == "miriam":
            # even if there's only one entry, we still create a bag.
            # this seems to be the norm in the SBML examples
            # https://raw.githubusercontent.com/combine-org/combine-specifications/main/specifications/files/sbml.level-3.version-2.core.release-2.pdf
            if isinstance(info_dict, str):
                self.doc.add((subjectobj, node_type, _URIRef_or_Literal(info_dict)))
            else:
                top_node = BNode()
                self.doc.add((subjectobj, node_type, top_node))
                bag = Bag(self.doc, top_node, [])
                if isinstance(info_dict, list):
                    for idf in info_dict:
                        bag.append(_URIRef_or_Literal(idf))
                elif isinstance(info_dict, dict):
                    for idf, label in info_dict.items():
                        bag.append(_URIRef_or_Literal(idf))
                else:
                    raise ValueError(f"Could not parse: {node_type}: {info_dict}")

    def _add_humans(
        self,
        subjectobj: typing.Union[URIRef, Literal],
        info_dict: typing.Union[typing.Dict[str, typing.Dict[str, str]], typing.Set],
        node_type: URIRef,
        annotation_style: str,
    ):
        """Add an new elements related to humans to the RDF annotation.

        This covers authors/contributors where the same person can have multiple
        annotations related to them.

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
            raise ValueError(
                "Annotation style must either be 'miriam' or 'biosimulations'"
            )

        # if not a dict, create a dict with blank values
        if not isinstance(info_dict, dict):
            copy_dict = {}  # type: typing.Dict[str, typing.Dict]
            for i in info_dict:
                copy_dict[i] = {}
            info_dict = copy_dict

        if annotation_style == "biosimulations":
            for name, info in info_dict.items():
                top_node = BNode()
                self.doc.add((subjectobj, node_type, top_node))

                self.doc.add((top_node, FOAF.name, Literal(name)))
                self.doc.add((top_node, RDFS.label, Literal(name)))

                # other fields
                for idf, label in info.items():
                    try:
                        foaf_type = getattr(FOAF, label)
                    except AttributeError:
                        logger.info("Not a FOAF attribute, using DC.identifier")
                        foaf_type = DC.identifier
                    self.doc.add((top_node, foaf_type, _URIRef_or_Literal(idf)))
        elif annotation_style == "miriam":
            # top level node: creator/contributor etc.
            top_node = BNode()
            self.doc.add((subjectobj, node_type, top_node))

            for name, info in info_dict.items():
                # individual references in a list
                ref = URIRef(f"#{name.replace(' ', '_')}")
                bag = Bag(self.doc, top_node, [])
                bag.append(ref)

                # individual nodes for details
                self.doc.add((ref, FOAF.name, Literal(name)))
                for idf, label in info.items():
                    try:
                        foaf_type = getattr(FOAF, label)
                    except AttributeError:
                        logger.info("Not a FOAF attribute, using DC.identifier")
                        foaf_type = DC.identifier
                    self.doc.add((ref, foaf_type, _URIRef_or_Literal(idf)))

    def extract_annotations(self, nml2_file: str) -> None:
        """Extract and print annotations from a NeuroML 2 file.

        :param nml2_file: name of NeuroML2 file to parse
        :type nml2_file: str
        """
        pp = pprint.PrettyPrinter()
        test_file = open(nml2_file)
        root = etree.parse(test_file).getroot()
        annotations = {}  # type: dict

        for a in _find_elements(root, "annotation"):
            for r in _find_elements(a, "RDF", rdf=True):
                contents = etree.tostring(r, pretty_print=True).decode("utf-8")
                logger.debug(contents)
                self.doc.parse(data=contents, format="application/rdf+xml")

                for desc, pred in self.ARG_MAP.items():
                    annotations[desc] = []
                    objs = self.doc.objects(predicate=pred)
                    for obj in objs:
                        print(f"Iterating: {desc}: {obj} ({type(obj)})")
                        if isinstance(obj, Literal):
                            annotations[desc] = str(obj)
                        if isinstance(obj, BNode):
                            for cobj in self.doc.objects(obj):
                                print(f"Iterating BNode: {desc}: {cobj} ({type(cobj)})")
                                if isinstance(cobj, URIRef):
                                    # a bag, ignore
                                    if str(cobj).endswith("ns#Bag"):
                                        continue

                                    # check if it's a subject for other triples
                                    # (authors/contributors)
                                    gen = self.doc.predicate_objects(subject=cobj)
                                    lenitems = sum(1 for _ in gen)
                                    print(f"Len items is {lenitems}")

                                    # a "plain" URIRef
                                    if lenitems == 0:
                                        annotations[desc].append(str(cobj))

                                    # local reference
                                    if lenitems > 0:
                                        gen = self.doc.predicate_objects(subject=cobj)
                                        bits = []
                                        for pred, pobj in gen:
                                            print(
                                                f"Found: {desc}: {pred} {pobj} ({type(pobj)})"
                                            )
                                            bits.append(str(pobj))
                                        annotations[desc].append(bits)

                                elif isinstance(cobj, Literal):
                                    annotations[desc].append(str(cobj))
                                # another bnode: parse it again (recurse?)
                                else:
                                    print(f"BNod else: {desc}: {cobj} ({type(cobj)})")

            # for r in _find_elements(a, "Description", rdf=True):
            #     desc = _get_attr_in_element(r, "about", rdf=True)
            #     annotations[desc] = []
            #
            #     annotations[desc] = g.serialize(format="turtle2")
            #
            # for info in r:
            #     if isinstance(info.tag, str):
            #         kind = info.tag.replace(
            #             "{http://biomodels.net/biology-qualifiers/}", "bqbiol:"
            #         )
            #         kind = kind.replace(
            #             "{http://biomodels.net/model-qualifiers/}", "bqmodel:"
            #         )
            #
            #         for li in _find_elements(info, "li", rdf=True):
            #             attr = _get_attr_in_element(li, "resource", rdf=True)
            #             if attr:
            #                 annotations[desc].append({kind: attr})

        logger.info("Annotations in %s: " % (nml2_file))
        pp.pprint(annotations)


def _URIRef_or_Literal(astr: str) -> typing.Union[URIRef, Literal]:
    """Create a URIRef or Literal depending on string.

    If a string begins with http:, https:, or file:, it is assumed to be a
    URIRef.

    :param astr: a string to create URIRef or Literal for
    :type astr: str
    :returns: a URIRef or Literal

    """
    prefixes = ["http:", "https:", "file:"]
    for p in prefixes:
        if astr.startswith(p):
            return URIRef(astr)

    return Literal(astr)


def create_annotation(*args, **kwargs):
    """Wrapper around the Annotations.create_annotation method.

    :param **kwargs: TODO
    :returns: TODO

    """
    new_annotation = Annotation()
    return new_annotation.create_annotation(*args, **kwargs)


def extract_annotations(nml2_file: str):
    """Wrapper around the Annotations.extract_annotations method.

    :param *args: TODO
    :param **kwargs: TODO
    :returns: TODO

    """
    new_annotation = Annotation()
    return new_annotation.extract_annotations(nml2_file)
