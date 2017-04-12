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


### Generates vcm_repr.owl
### from vcm_concept_monoaxial_2_vcm_lexicon.txt

HERE = os.path.dirname(sys.argv[0]) or "."


# Skeleton

owl = u"""<?xml version="1.0" ?>

<!DOCTYPE rdf:RDF [
    <!ENTITY owl 'http://www.w3.org/2002/07/owl#' >
    <!ENTITY xsd 'http://www.w3.org/2001/XMLSchema#' >
    <!ENTITY owl2xml 'http://www.w3.org/2006/12/owl2-xml#' >
    <!ENTITY rdfs 'http://www.w3.org/2000/01/rdf-schema#' >
    <!ENTITY rdf 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' >
    <!ENTITY vcm_repr 'http://localhost/~jiba/vcm_onto/vcm_repr.owl#' >
    <!ENTITY vcm_lexique 'http://localhost/~jiba/vcm_onto/vcm_lexique.owl#' >
    <!ENTITY vcm_concept_monoaxial 'http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#' >
    <!ENTITY vcm_graphique 'http://localhost/~jiba/vcm_onto/vcm_graphique.owl#' >
]>


<rdf:RDF xmlns='http://localhost/~jiba/vcm_onto/vcm_repr.owl#'
     xml:base='http://localhost/~jiba/vcm_onto/vcm_repr.owl'
     xmlns:rdfs='http://www.w3.org/2000/01/rdf-schema#'
     xmlns:vcm_graphique='http://localhost/~jiba/vcm_onto/vcm_graphique.owl#'
     xmlns:owl2xml='http://www.w3.org/2006/12/owl2-xml#'
     xmlns:owl='http://www.w3.org/2002/07/owl#'
     xmlns:xsd='http://www.w3.org/2001/XMLSchema#'
     xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
     xmlns:vcm_lexique='http://localhost/~jiba/vcm_onto/vcm_lexique.owl#'
     xmlns:vcm_concept_monoaxial='http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#'
     xmlns:vcm_repr='http://localhost/~jiba/vcm_onto/vcm_repr.owl#'>
    <owl:Ontology rdf:about=''>
        <owl:imports rdf:resource='http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl'/>
        <owl:imports rdf:resource='http://localhost/~jiba/vcm_onto/vcm_graphique.owl'/>
    </owl:Ontology>

    <owl:ObjectProperty rdf:about='#750'>
        <rdfs:label xml:lang="fr">est_représenté_par</rdfs:label>
        <rdfs:label xml:lang="en">is_represent_by</rdfs:label>
    </owl:ObjectProperty>
    <owl:ObjectProperty rdf:about='#751'>
        <rdfs:label xml:lang="fr">représente</rdfs:label>
        <rdfs:label xml:lang="en">represent</rdfs:label>
        <owl:inverseOf rdf:resource='#750'/>
    </owl:ObjectProperty>

    <owl:Class rdf:about='http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#54'>
        <owl:disjointWith rdf:resource='http://localhost/~jiba/vcm_onto/vcm_graphique.owl#744'/>
    </owl:Class>

    <owl:Class rdf:about='http://localhost/~jiba/vcm_onto/vcm_graphique.owl#745'>
        <rdfs:subClassOf>
            <owl:Restriction>
                <owl:onProperty rdf:resource='http://localhost/~jiba/vcm_onto/vcm_repr.owl#751'/>
                <owl:onClass rdf:resource='http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#477'/>
                <owl:minQualifiedCardinality rdf:datatype='&xsd;nonNegativeInteger'>1</owl:minQualifiedCardinality>
            </owl:Restriction>
        </rdfs:subClassOf>
    </owl:Class>
"""


# Reads mapping and translates it into OWL

con_mappings = defaultdict(Concepts)
lex_mappings = defaultdict(Concepts)

mappings = parse_mapping(read_file(os.path.join(HERE, "..", "vcm_onto", "vcm_concept_monoaxial_2_vcm_lexicon.txt"), "utf8"))
for cons, match_type, lexs in mappings:
  cons = MappingAnd([VCM_CONCEPT_MONOAXIAL[c] for c in cons])
  lexs = MappingAnd([VCM_LEXICON          [c] for c in lexs])
  if len(cons) == 1: con = tuple(cons)[0]
  else:              con = frozenset(cons)
  if len(lexs) == 1: lex = tuple(lexs)[0]
  else:              lex = frozenset(lexs)

  if isinstance(con, Concept): con_mappings[con].add(lex)
  else:
    for c in con: con_mappings[c].add(lex)
    
  if isinstance(lex, Concept): lex_mappings[lex].add(con)
  else:
    for l in lex: lex_mappings[l].add(con)
  
  
    
for lex in lex_mappings.copy():
  cons = Concepts()
  ands = set()
  for descendant_lex in lex.self_and_descendants():
    for descendant_con in lex_mappings[descendant_lex]:
      if isinstance(descendant_con, frozenset): ands.add(descendant_con)
      else:                                     cons.add(descendant_con)
  cons.keep_most_generic()
  cons = set(cons) | ands
    
  owl_clazz = Clazz(VCM_LEXICON, lex.code)

  restriction = Or()
  for con in cons:
    if isinstance(con, Concept):
      restriction.append(Some(state_related_to, Clazz(VCM_CONCEPT_MONOAXIAL, con.code)))
    else:
      restriction.append(And([Some(state_related_to, Clazz(VCM_CONCEPT_MONOAXIAL, c.code)) for c in con]))
      
    
  owl_clazz.add_restriction(Only(category2relation_repr[lex.category], Only(represent, restriction)))
  owl += owl_clazz.owl()
  
  

for con in con_mappings.copy():
  lexs = Concepts()
  ands = set()
  for descendant_con in con.self_and_descendants():
    for descendant_lex in con_mappings[descendant_con]:
      if isinstance(descendant_lex, frozenset): ands.add(descendant_lex)
      else:                                     lexs.add(descendant_lex)
  lexs.keep_most_generic()
  lexs = set(lexs) | ands
  
  owl_clazz = Clazz(VCM_CONCEPT_MONOAXIAL, con.code)
  
  restriction = Or()
  for lex in lexs:
    if isinstance(lex, Concept):
      restriction.append(Some(category2relation_irepr[lex.category], Clazz(VCM_LEXICON, lex.code)))
    else:
      restriction.append(And([Some(category2relation_irepr[l.category], Clazz(VCM_LEXICON, l.code)) for l in lex]))
      
      
  owl_clazz.add_restriction(Only(related_to_state, Only(is_represented_by, restriction)))
  owl += owl_clazz.owl()
  
      
owl += u"""
</rdf:RDF>"""


write_file(os.path.join(HERE, "..", "vcm_onto", "vcm_repr.owl"), owl, "utf8")


