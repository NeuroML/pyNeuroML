#!/usr/bin/env python3
"""
Methods related to annotations

File: pyneuroml/annotations.py

Copyright 2024 NeuroML contributors
"""

import logging
import pprint
import re
import textwrap
import typing

from lxml import etree

from pyneuroml.utils.xml import _find_elements

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    from rdflib import Bag, BNode, Graph, Literal, Namespace, URIRef
    from rdflib.namespace import DC, DCTERMS, FOAF, RDFS
except ImportError:
    logger.warning("Please install optional dependencies to use annotation features:")
    logger.warning("pip install pyneuroml[annotations]")


# From https://docs.biosimulations.org/concepts/conventions/simulation-project-metadata/
# From https://doi.org/10.1515/jib-2021-0020 (page 3)
# rdf, foaf, dc already included in rdflib
NAMESPACES_MAP = {
    "bqmodel": "http://biomodels.net/model-qualifiers/",
    "bqbiol": "http://biomodels.net/biology-qualifiers/",
    "semsim": "http://bime.uw.edu/semsim/",
    "prism": "http://prismstandard.org/namespaces/basic/2.0/",
    "collex": "http://www.collex.org/schema",
    "scoro": "http://purl.org/spar/scoro",
    "orcid": "https://orcid.org/",
}


# create namespaces not included in rdflib
PRISM = Namespace(NAMESPACES_MAP["prism"])
COLLEX = Namespace(NAMESPACES_MAP["collex"])
BQBIOL = Namespace(NAMESPACES_MAP["bqbiol"])
BQMODEL = Namespace(NAMESPACES_MAP["bqmodel"])
SCORO = Namespace(NAMESPACES_MAP["scoro"])
ORCID = Namespace(NAMESPACES_MAP["orcid"])


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
        self.doc.bind("orcid", ORCID)

        for k, v in self.P_MAP_EXTRA.items():
            self.doc.bind(f"{v}:{k}", f"v.upper()/{k}")

        self.ARG_MAP = {
            "title": DC.title,
            "abstract": DCTERMS.abstract,
            "description": DC.description,
            "keywords": PRISM.keyword,
            "thumbnails": COLLEX.thumbnail,
            "is_": getattr(BQBIOL, "is"),
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
        is_: typing.Optional[typing.List[str]] = None,
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
        :param is_: biological entity represented by the model
        :type is_: dict(str, str)
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

            - a set: :code:`{"Author A", "Author B"}`
            - a dictionary where the keys are author names and values are
              dictionaries of more metadata:

              :code:`{"Author A": {"https://../": "accountname", "..": ".."}}`

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

        # loop over the rest
        for arg, val in mylocals.items():
            if arg in self.ARG_MAP.keys():
                if val is None:
                    continue
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
                    if annotation_style == "miriam":
                        l_string = list(val.keys())[0]
                    else:
                        l_string = val
                    self._add_element(
                        subjectobj, l_string, self.ARG_MAP[arg], annotation_style
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

        # do nothing if an empty dict is passed
        if info_dict is None:
            return

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
                    if label == "orcid":
                        foaf_type = ORCID.id
                    else:
                        foaf_type = getattr(FOAF, label, None)

                    if foaf_type is None:
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
                    if label == "orcid":
                        foaf_type = ORCID.id
                    else:
                        foaf_type = getattr(FOAF, label, None)

                    if foaf_type is None:
                        logger.info("Not a FOAF attribute, using DC.identifier")
                        foaf_type = DC.identifier
                    self.doc.add((ref, foaf_type, _URIRef_or_Literal(idf)))

    def extract_annotations(
        self, nml2_file: str
    ) -> typing.Dict[str, typing.Dict[typing.Any, typing.Any]]:
        """Extract and print annotations from a NeuroML 2 file.

        :param nml2_file: name of NeuroML2 file to parse
        :type nml2_file: str
        :returns: dictionaries with annotations information
        :rtype: dict
        """
        pp = pprint.PrettyPrinter(width=100)
        annotations = {}  # type: typing.Dict

        with open(nml2_file, "r") as f:
            root = etree.parse(f).getroot()

            for a in _find_elements(root, "annotation"):
                parent = a.getparent()
                logger.debug(f"Parent is {parent}")
                # TODO: debug
                # _get_attr_in_element doesn't quite work correctly
                try:
                    obj_id = parent.attrib["id"]
                except KeyError:
                    obj_id = ""
                annotations[obj_id] = self.parse_rdf(a)

            logger.info("Annotations in %s: " % (nml2_file))
            pp.pprint(annotations)
        return annotations

    def extract_annotations_from_string(
        self, xml_string: str
    ) -> typing.Dict[str, typing.Dict[typing.Any, typing.Any]]:
        """Extract and print annotations from a NeuroML 2 string.

        :param xml_string: XML string to parse
        :type xml_string: str
        :returns: list of dictionaries with annotations information
        :rtype: list of dict
        """
        pp = pprint.PrettyPrinter()
        annotations = {}  # type: typing.Dict

        root = etree.fromstring(xml_string).getroot()
        for a in _find_elements(root, "annotation"):
            parent = a.getparent()
            logger.debug(f"Parent is {parent}")
            try:
                obj_id = parent.attrib["id"]
            except KeyError:
                obj_id = ""
            annotations[obj_id] = self.parse_rdf(a)

        logger.info("Annotations:")
        pp.pprint(annotations)
        return annotations

    def parse_rdf(
        self, annotation_element: etree.Element
    ) -> typing.Dict[str, typing.Any]:
        """Parse RDF from an :code:`<annotation>` element.

        Note that this is not a general purpose RDF parser.
        It is a specific parser for the RDF annotations that are used in
        NeuroML (which the :py:func:`pyneuroml.annotations.Annotation.create_annotation` method can write).

        :param annotation_element: an <annotation> element
        :type annotation_element: etree.Element
        :returns: annotation dictionary

        """
        annotations = {}  # type: typing.Dict
        # guess if it's biosimulations format or MIRIAM
        # biosimulations does not use bags
        bags = _find_elements(annotation_element, "Bag", rdf=True)

        if len(list(bags)) > 0:
            logger.debug("Parsing MIRIAM style annotation")
            # MIRIAM annotations, as written by create_annotation can be of a
            # few forms:

            # 1. elements without any nesting, that contain literals as the
            # objects (the root node is the subject, ex: title, description,
            # abstract)

            # 2. elements that may contain multiple objects and are so contained
            # in containers (bags)
            # for these, the top level node is a "blank node" that includes the
            # bag, which includes the items.
            # note that the objects here may refer to other local subjects,
            # eg: creators/contributors will contain a list of local reference
            # to other elements

            # 3. elements that may contain multiple objects contained in another
            # element (modification date)
            # for these, there are two levels of blank nodes before the
            # bags/items.
            for r in _find_elements(annotation_element, "RDF", rdf=True):
                contents = etree.tostring(r, pretty_print=True).decode("utf-8")
                logger.debug(contents)
                self.doc.parse(data=contents, format="application/rdf+xml")

                for desc, pred in self.ARG_MAP.items():
                    annotations[desc] = []
                    # get all objects that use the predicate and iterate over
                    # them
                    objs = self.doc.objects(predicate=pred)
                    for obj in objs:
                        logger.debug(
                            f"Iterating {pred} objects: {desc}: {obj} ({type(obj)})"
                        )

                        # handle specially to return in the form supplied to
                        # create_annotation
                        if desc == "license":
                            annotations[desc] = {str(obj)}
                            continue

                        # top level Literals or URIRefs: description, title, abstract
                        if isinstance(obj, Literal) or isinstance(obj, URIRef):
                            annotations[desc] = str(obj)

                        # nested elements: ones with blank nodes that contain
                        # bags with lists; the lists can contain local
                        # references to other elements

                        elif isinstance(obj, BNode):
                            # the objects for the top level BNode subject will
                            # be the bags, and the items in the bags, all
                            # returned as a list
                            for cobj in self.doc.objects(obj):
                                logger.debug(
                                    f"Iterating BNode objects: {desc}: {cobj} ({type(cobj)})"
                                )
                                if isinstance(cobj, URIRef):
                                    # a bag, ignore
                                    bagged = False
                                    if str(cobj).endswith("ns#Bag"):
                                        bagged = True
                                        logger.debug("Ignoring Bag")
                                        continue

                                    # the list item can be a local reference to
                                    # another triple (authors/contributors)
                                    # so, check if it's a subject for other triples
                                    # (authors/contributors)
                                    gen = self.doc.predicate_objects(subject=cobj)
                                    lenitems = sum(1 for _ in gen)
                                    logger.debug(f"Len items is {lenitems}")

                                    # no: it's a "plain" URIRef
                                    if lenitems == 0:
                                        annotations[desc].append(str(cobj))

                                    # yes, it's a local reference
                                    if lenitems > 0:
                                        gen = self.doc.predicate_objects(subject=cobj)
                                        bits = []
                                        for pred, pobj in gen:
                                            logger.debug(
                                                f"Found: {desc}: {pred} {pobj} ({type(pobj)})"
                                            )
                                            bits.append(str(pobj))
                                        if len(bits) == 1:
                                            annotations[desc].append(bits[0])
                                        else:
                                            annotations[desc].append(bits)

                                # a literal, eg: creation date
                                elif isinstance(cobj, Literal):
                                    if bagged:
                                        annotations[desc].append(str(cobj))
                                    else:
                                        annotations[desc] = str(cobj)
                                # another bnode: eg: modification date
                                else:
                                    logger.debug(
                                        f"BNode nested in BNode: {desc}: {cobj} ({type(cobj)})"
                                    )
                                    for ccobj in self.doc.objects(cobj):
                                        logger.debug(
                                            f"Iterating nested BNode: {desc}: {ccobj} ({type(ccobj)})"
                                        )
                                        if str(ccobj).endswith("ns#Bag"):
                                            logger.debug("Ignoring Bag")
                                            continue
                                        # a literal, eg: creation date
                                        elif isinstance(ccobj, Literal):
                                            annotations[desc].append(str(ccobj))

                        else:
                            raise ValueError(f"Unrecognised element type: {obj}")

        # biosimulations has a flat structure, since no containers (bags) are
        # used.
        else:
            logger.debug("Parsing biosimulations style annotation")
            for r in _find_elements(annotation_element, "RDF", rdf=True):
                contents = etree.tostring(r, pretty_print=True).decode("utf-8")
                logger.debug(contents)
                self.doc.parse(data=contents, format="application/rdf+xml")

                for desc, pred in self.ARG_MAP.items():
                    # Since containers are not used, we cannot tell if there
                    # are multiple objects of the same predicate
                    # Even if we count them, a multi-element object could just
                    # have one element, which will be equivalent to an object
                    # that should not have multiple elements
                    # So, we initialize manually
                    if desc in ["title", "abstract", "description", "creation_date"]:
                        annotations[desc] = None
                    # Everything else is an iterable
                    # Most are dicts, others are lists
                    else:
                        annotations[desc] = {}

                    for obj in self.doc.objects(predicate=pred):
                        logger.debug(f"Iterating: {desc}: {obj} ({type(obj)})")
                        if isinstance(obj, BNode):
                            idfs = []
                            labels = []
                            for pred_, cobj in self.doc.predicate_objects(obj):
                                logger.debug(
                                    f"Iterating BNode objects: {desc}: {pred_}: {cobj} ({type(cobj)})"
                                )
                                if pred_ == RDFS.label:
                                    labels.append(str(cobj))
                                else:
                                    idfs.append(str(cobj))

                            logger.debug(f"idfs: {idfs}")
                            logger.debug(f"labels: {labels}")
                            # id/label pairs
                            if len(idfs) == 1 and len(labels) == 1:
                                # using dict(zip..) splits the space separated
                                # strings into different labels
                                biosim_bits = dict(zip(idfs, labels))
                                # predicate with single entry
                                if annotations[desc] is None:
                                    annotations[desc] = biosim_bits
                                else:
                                    annotations[desc].update(biosim_bits)
                            # label with multiple idfs
                            if len(idfs) > 1 and len(labels) == 1:
                                annotations[desc].update({labels[0]: set(idfs)})
                            # no label, nested data
                            if len(idfs) == 1 and len(labels) == 0:
                                if annotations[desc] is None:
                                    annotations[desc] = idfs[0]
                                else:
                                    annotations[desc].append(idfs)
                            if len(idfs) > 1 and len(labels) == 0:
                                if len(annotations[desc]) == 0:
                                    annotations[desc] = idfs
                                else:
                                    annotations[desc].extend(idfs)
                        # not bnodes, top level objects
                        else:
                            # text objects (literals)
                            if annotations[desc] is None:
                                annotations[desc] = str(obj)
                            # objects that may be lists: keywords, thumbnails
                            else:
                                if len(annotations[desc]) == 0:
                                    annotations[desc] = [str(obj)]
                                else:
                                    annotations[desc].append(str(obj))
        return annotations


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

    .. versionadded:: 1.2.13

    Please see :py:func:`pyneuroml.annotations.Annotation.create_annotation` for detailed
    documentation. The doc string is pasted below for convenience:

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
    :param is_: biological entity represented by the model
    :type is_: dict(str, str)
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

        - a set: :code:`{"Author A", "Author B"}`
        - a dictionary where the keys are author names and values are
          dictionaries of more metadata:

          :code:`{"Author A": {"https://../": "accountname", "..": ".."}}`

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
    new_annotation = Annotation()
    return new_annotation.create_annotation(*args, **kwargs)


def extract_annotations(nml2_file: str):
    """Wrapper around the Annotations.extract_annotations method.

    Please see :py:func:`pyneuroml.annotations.Annotation.extract_annotations` for detailed
    documentation.

    .. versionadded:: 1.2.13

    :param nml2_file: name of NeuroML2 file to parse
    :type nml2_file: str
    :returns: dictionaries with annotations information
    :rtype: dict

    """
    new_annotation = Annotation()
    return new_annotation.extract_annotations(nml2_file)
