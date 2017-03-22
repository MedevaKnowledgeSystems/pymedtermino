# -*- coding: utf-8 -*-
# PyMedTermino
# Copyright (C) 2012-2013 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Paris 13, Sorbonne paris-Cité, Bobigny, France

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# (Re)build VCM ontology.

from __future__ import print_function

import sys, os, os.path, re
from collections        import defaultdict
from pymedtermino       import *
from pymedtermino.vcm   import *
from pymedtermino.utils.db import *
from pymedtermino.utils.mapping_db import *
from pymedtermino.utils.owl_file_reasoner import *


### Generates vcm_search_concept.owl


HERE = os.path.dirname(sys.argv[0]) or "."

owl = u"""<?xml version="1.0" ?>

<!DOCTYPE rdf:RDF [
    <!ENTITY owl 'http://www.w3.org/2002/07/owl#' >
    <!ENTITY xsd 'http://www.w3.org/2001/XMLSchema#' >
    <!ENTITY owl2xml 'http://www.w3.org/2006/12/owl2-xml#' >
    <!ENTITY rdfs 'http://www.w3.org/2000/01/rdf-schema#' >
    <!ENTITY rdf 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' >
    <!ENTITY vcm_search_concept 'http://localhost/~jiba/vcm_onto/vcm_search_concept.owl#' >
    <!ENTITY vcm_repr 'http://localhost/~jiba/vcm_onto/vcm_repr.owl#' >
    <!ENTITY vcm_lexique 'http://localhost/~jiba/vcm_onto/vcm_lexique.owl#' >
    <!ENTITY vcm_concept_monoaxial 'http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#' >
    <!ENTITY vcm_graphique 'http://localhost/~jiba/vcm_onto/vcm_graphique.owl#' >
]>


<rdf:RDF xmlns='http://localhost/~jiba/vcm_onto/vcm_search_concept.owl#'
     xml:base='http://localhost/~jiba/vcm_onto/vcm_search_concept.owl'
     xmlns:rdfs='http://www.w3.org/2000/01/rdf-schema#'
     xmlns:vcm_graphique='http://localhost/~jiba/vcm_onto/vcm_graphique.owl#'
     xmlns:owl2xml='http://www.w3.org/2006/12/owl2-xml#'
     xmlns:owl='http://www.w3.org/2002/07/owl#'
     xmlns:xsd='http://www.w3.org/2001/XMLSchema#'
     xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
     xmlns:vcm_lexique='http://localhost/~jiba/vcm_onto/vcm_lexique.owl#'
     xmlns:vcm_concept_monoaxial='http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#'
     xmlns:vcm_repr='http://localhost/~jiba/vcm_onto/vcm_repr.owl#'
     xmlns:vcm_search_concept='http://localhost/~jiba/vcm_onto/vcm_search_concept.owl#'
     >
    <owl:Ontology rdf:about=''>
        <owl:imports rdf:resource='http://localhost/~jiba/vcm_onto/vcm_repr.owl'/>
    </owl:Ontology>

    <owl:Class rdf:about='&vcm_search_concept;SEARCH'>
    </owl:Class>
"""
  
for con in VCM_CONCEPT_MONOAXIAL.all_concepts():
  lexs = (VCM_CONCEPT_MONOAXIAL >> VCM_LEXICON)(con)
  if not lexs: continue
  
  owl += u"""
    <owl:Class rdf:about='&vcm_search_concept;SEARCH_icon_repr_%s'>
        <rdfs:subClassOf rdf:resource='&vcm_search_concept;SEARCH'/>
        <rdfs:subClassOf>
            <owl:Restriction>
                <owl:onProperty rdf:resource='&vcm_repr;751'/>
                <owl:someValuesFrom>
                    <owl:Restriction>
                        <owl:onProperty rdf:resource='&vcm_concept_monoaxial;13'/>
                        <owl:someValuesFrom rdf:resource='&vcm_concept_monoaxial;%s'/>
                    </owl:Restriction>
                </owl:someValuesFrom>
            </owl:Restriction>
        </rdfs:subClassOf>
    </owl:Class>
""" % (con.code, con.code)
    
owl += u"""
</rdf:RDF>"""

write_file(os.path.join(HERE, "..", "vcm_onto", "vcm_search_concept.owl"), owl, "utf8")
