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

# (Re)build ICD10 => VCM mapping.

from __future__ import print_function

import sys, os, os.path, re, csv
from collections        import defaultdict
import pymedtermino
pymedtermino.LANGUAGE = "fr"
pymedtermino.REMOVE_SUPPRESSED_CONCEPTS = 0

from pymedtermino       import *
from pymedtermino.vcm   import *
from pymedtermino.icd10            import *
from pymedtermino.snomedct         import *
from pymedtermino.snomedct_2_icd10 import *
from pymedtermino.snomedct_2_vcm   import *
from pymedtermino.utils.mapping_db import *




PATHOLOGICAL_CHAPTERS = [
  ICD10[u"I"]  # Certain infectious and parasitic diseases
, ICD10[u"II"]  # Neoplasms
, ICD10[u"III"]  # Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism
, ICD10[u"IV"]  # Endocrine, nutritional and metabolic diseases
, ICD10[u"V"]  # Mental and behavioural disorders
, ICD10[u"VI"]  # Diseases of the nervous system
, ICD10[u"VII"]  # Diseases of the eye and adnexa
, ICD10[u"VIII"]  # Diseases of the ear and mastoid process
, ICD10[u"IX"]  # Diseases of the circulatory system
, ICD10[u"X"]  # Diseases of the respiratory system
, ICD10[u"XI"]  # Diseases of the digestive system
, ICD10[u"XII"]  # Diseases of the skin and subcutaneous tissue
, ICD10[u"XIII"]  # Diseases of the musculoskeletal system and connective tissue
, ICD10[u"XIV"]  # Diseases of the genitourinary system
, ICD10[u"XVI"]  # Certain conditions originating in the perinatal period
, ICD10[u"XVII"]  # Congenital malformations, deformations and chromosomal abnormalities
, ICD10[u"XIX"]  # Injury, poisoning and certain other consequences of external causes
]
def is_pathological(icd10):
  for chapter in PATHOLOGICAL_CHAPTERS:
    if icd10.is_a(chapter): return 1

def has_tissular_non_transversal_concept(concepts):
  for concept in concepts:
    if concept.is_a(VCM_CONCEPT[414]) and not concept.is_a(VCM_CONCEPT[258]): # Tissular_structure, Structure_anatomique_transverse
      return True
  return False

d   = {}
nb  = 0
rep = defaultdict(lambda: 0)
nb_no_snomed = 0
all_icons = Concepts()

for icd10 in ICD10.all_concepts():
  snomedcts = icd10 >> SNOMEDCT
  
  if not snomedcts: nb_no_snomed += 1
  
  active_snomedcts = Concepts([snomedct for snomedct in snomedcts if snomedct.active])
  if active_snomedcts:
    snomedcts = active_snomedcts
    
  if icd10.parents: # Chapters have been treated manually
    snomedcts.keep_most_generic()
  
  vcms = snomedcts >> VCM
  if icd10.parents: # Chapters have been treated manually
    vcms = keep_most_graphically_specific_icons(vcms)
    
  has_tissular_anatomical_structure = 0
  for vcm in vcms:
    if has_tissular_non_transversal_concept(vcm.concepts):
      has_tissular_anatomical_structure = 1
      break
  if has_tissular_anatomical_structure:
    vcms = Concepts(vcm for vcm in vcms if not vcm.concepts.find(VCM_CONCEPT[224])) # Anatomical_region
    
  if is_pathological(icd10) and icd10.parents: # Chapters have been treated manually
    vcms = Concepts(vcm.derive_lexs([VCM_LEXICON[1, "patho"]]) for vcm in vcms)
    vcms = keep_most_graphically_specific_icons(vcms)
    
  all_icons.update(vcms)

  vcm_codes = [vcm.code for vcm in vcms]
  vcm_codes.sort()
  d[icd10] = vcm_codes
  nb += 1
  rep[len(vcms)] += 1
  
  if (nb % 100) == 0: print("%s..." % nb, file = sys.stderr)


TXT = u""
for icd10 in ICD10.all_concepts():
  if icd10.parents and (d[icd10] == d[icd10.parents[0]]): continue
  TXT += u" ".join([icd10.code, u"==", u" ".join(d[icd10]), u" #", icd10.term]) + u"\n"

#print(TXT)

HERE        = os.path.dirname(sys.argv[0])
SQLITE_FILE = os.path.join(HERE, "..", "icd10_2_vcm.sqlite3")
db = create_db(SQLITE_FILE)
Txt_2_SQLMapping(None, db, "TEXT", "TEXT", txt = TXT)
close_db(db, SQLITE_FILE)

  
print(file = sys.stderr)
print(nb, file = sys.stderr)
print(rep, file = sys.stderr)
print(len(all_icons), "icônes différentes", file = sys.stderr)
print("Pas de correspondance vers la SNOMEDCT pour %s concepts" % nb_no_snomed, file = sys.stderr)

import pymedtermino.icd10_2_vcm
SQLITE_FILE = os.path.join(HERE, "..", "icd10_vcm_lexicon_index.sqlite3")
db = create_db(SQLITE_FILE)
index_terminology_by_vcm_lexicon(ICD10, db, code_type = "TEXT")
close_db(db, SQLITE_FILE)
