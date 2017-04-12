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

__all__ = ["snomedct_2_vcm_concept", "vcm_concept_2_snomedct", "snomedct_2_vcm", "vcm_2_snomedct"]

import os, os.path
from pymedtermino          import *
from pymedtermino.snomedct import *
from pymedtermino.vcm      import *

# Skeletal muscle structure,  Spinal cord, roots and ganglia structure,  Structure of vertebral artery
_non_skelettons = set([SNOMEDCT[127954009], SNOMEDCT[91715002], SNOMEDCT[85234005]])

def _get_concept_parents(concept):
  #if "part_of" in concept.relations: r = list(set(concept.parents + concept.part_of))
  #else: r = list(concept.parents)
  r = list(concept.parents)
  
  # Skeletal muscles, spinal cord and vertebral artery are considered
  # as part of the skeletal system structure in SNOMED CT (error ?)...
  
  #if concept.is_a(SNOMEDCT[127954009]) or concept.is_a(SNOMEDCT[91715002]) or concept.is_a(SNOMEDCT[85234005]): # Skeletal muscle structure,  Spinal cord, roots and ganglia structure,  Structure of vertebral artery
  #if not _non_skelettons.isdisjoint(set(concept.ancestors())):
  for ancestor in concept.ancestors_no_double():
    if ancestor in _non_skelettons:
      skeletton = SNOMEDCT[113192009] # Skeletal system structure
      r = [c for c in r if not c.is_a(skeletton)]
      break
  return r

snomedct_2_vcm_concept = SQLMapping(SNOMEDCT, VCM_CONCEPT, os.path.join(DATA_DIR, "snomedct_2_vcm_concept.sqlite3"), has_and = 0, get_concept_parents = _get_concept_parents)
snomedct_2_vcm_concept.register()
vcm_concept_2_snomedct = snomedct_2_vcm_concept._create_reverse_mapping()
vcm_concept_2_snomedct.register()

snomedct_2_vcm = SQLMapping(SNOMEDCT, VCM, os.path.join(DATA_DIR, "snomedct_2_vcm.sqlite3"), has_and = 0)
snomedct_2_vcm.register()
vcm_2_snomedct = snomedct_2_vcm._create_reverse_mapping()
vcm_2_snomedct.register()
