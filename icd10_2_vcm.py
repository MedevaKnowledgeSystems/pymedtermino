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

__all__ = ["icd10_2_vcm", "vcm_2_icd10"]

import os, os.path
from pymedtermino       import *
from pymedtermino.icd10 import *
from pymedtermino.icd10 import ICD10DaggerStarConcept
from pymedtermino.vcm   import *
from pymedtermino.vcm   import VCMLexiconIndex

class ICD102VCMMapping(SQLMapping):
  #def __init__(self, terminology1, terminology2, db_filename, has_and = 1, reversed = 0, get_concept_parents = None):
  #  SQLMapping.__init__(self, terminology1, terminology2, db_filename, has_and, reversed, get_concept_parents)
    
  def map_concepts(self, concepts, use_ancestors = True, cumulated_concepts = None):
    non_dagger_stars = Concepts()
    vcms             = Concepts()
    for concept in concepts:
      if isinstance(concept, ICD10DaggerStarConcept):
        dagger_vcms = concept.dagger >> VCM
        star_vcms   = concept.star   >> VCM
        etiologies  = Concepts(dagger_vcm.etiology for dagger_vcm in dagger_vcms)
        if etiologies:
          etiologies.keep_most_generic()
          for star_vcm in star_vcms:
            star_vcm = star_vcm.derive_lexs(etiologies)
            if etiologies.find(VCM_LEXICON[512]): # Infection
              if VCM_LEXICON[529] in star_vcm.lexs: # Inflammation
                star_vcm = star_vcm.derive(modifiers = star_vcm.modifiers - { VCM_LEXICON[529] })
            vcms.add(star_vcm)
        else:
          vcms.update(star_vcms)
      else:
        non_dagger_stars.add(concept)
    return vcms | SQLMapping.map_concepts(self, non_dagger_stars, use_ancestors, cumulated_concepts)
  
icd10_2_vcm = ICD102VCMMapping(ICD10, VCM, os.path.join(DATA_DIR, "icd10_2_vcm.sqlite3"), has_and = 0)
icd10_2_vcm.register()
vcm_2_icd10 = icd10_2_vcm._create_reverse_mapping()
vcm_2_icd10.register()

ICD10.vcm_lexicon_index = VCMLexiconIndex(ICD10, os.path.join(DATA_DIR, "icd10_vcm_lexicon_index.sqlite3"))

