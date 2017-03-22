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


### Generates vcm_concept_monoaxial.owl
### from vcm_concept.owl

HERE = os.path.dirname(sys.argv[0]) or "."


multiaxial_isas = set()

for line in read_file(os.path.join(HERE, "..", "vcm_onto", "vcm_concept_multiaxial_isa.txt"), "utf8").split(u"\n"):
  if u"#" in line: line = line.split(u"#")[0]
  if not line.strip(): continue
  isa_type, child_code, parent_code = line.split()
  if isa_type == "multi":
    multiaxial_isas.add((int(child_code), int(parent_code)))


print("%s multiaxial isa relations" % len(multiaxial_isas))

    
owl = read_file(os.path.join(HERE, "..", "vcm_onto", "vcm_concept.owl"), "utf8")

owl = owl.replace(u'''<!ENTITY vcm_concept "http://localhost/~jiba/vcm_onto/vcm_concept.owl#"''',
                  u'''<!ENTITY vcm_concept_monoaxial "http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#"''')

owl = owl.replace(u'''xmlns="http://localhost/~jiba/vcm_onto/vcm_concept.owl#"''',
                  u'''xmlns="http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#"''')

owl = owl.replace(u'''xml:base="http://localhost/~jiba/vcm_onto/vcm_concept.owl"''',
                  u'''xml:base="http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl"''')

owl = owl.replace(u'''xmlns:vcm_concept="http://localhost/~jiba/vcm_onto/vcm_concept.owl#"''',
                  u'''xmlns:vcm_concept_monoaxial="http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#"''')

owl = owl.replace(u'''<owl:Ontology rdf:about="http://localhost/~jiba/vcm_onto/vcm_concept.owl"''',
                  u'''<owl:Ontology rdf:about="http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl"''')

owl = owl.replace(u'''<!-- http://localhost/~jiba/vcm_onto/vcm_concept.owl''',
                  u'''<!-- http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl''')

owl = owl.replace(u'''"http://localhost/~jiba/vcm_onto/vcm_concept.owl#''',
                  u'''"#''')

owl = owl.replace(u'''"&vcm_concept;''',
                  u'''"#''')

owl = owl.replace(u'''<rdfs:label xml:lang="fr">Concept_(multiaxial)</rdfs:label>''',
                  u'''<rdfs:label xml:lang="fr">Concept_(monoaxial)</rdfs:label>''')

owl = owl.replace(u'''<rdfs:label xml:lang="en">Concept_(multiaxial)</rdfs:label>''',
                  u'''<rdfs:label xml:lang="en">Concept_(monoaxial)</rdfs:label>''')

isa_regexp = re.compile(u'''(<owl:Class\\s+rdf:about="(.*?)".*?)(<rdfs:subClassOf\\s+rdf:resource="(.*?)"/>)''', re.UNICODE | re.DOTALL)




nb = 0
for child_code, parent_code in multiaxial_isas:
  owl, n = re.subn(u'''(<owl:Class\\s+rdf:about="#%s".*?)(<rdfs:subClassOf\\s+rdf:resource="#%s"/>)''' % (child_code, parent_code),
                   u'''\\1''',
                   owl,
                   flags = re.UNICODE | re.DOTALL)
  if n: nb += n
  else: print("Not found: %s is_a %s" % (child_code, parent_code))


print("%s isa relations found" % nb)


write_file(os.path.join(HERE, "..", "vcm_onto", "vcm_concept_monoaxial.owl"), owl, "utf8")
