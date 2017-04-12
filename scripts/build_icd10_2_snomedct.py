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


MAPPING_FILE = "/home/jiba/sifado/termino/ALIGNEMENT_SNOMED_CT_CIM10_CISMEF.csv"


import sys, os, os.path, stat, sqlite3, tempfile, csv
from collections import defaultdict

import pymedtermino
from pymedtermino.utils.db         import *
from pymedtermino.utils.mapping_db import *

from pymedtermino          import *
from pymedtermino.snomedct import *
from pymedtermino.icd10    import *


HERE        = os.path.dirname(sys.argv[0])
SQLITE_FILE = os.path.join(HERE, "..", "snomedct_2_icd10_reverse.sqlite3")
TXT         = u""

pymedtermino.SHOW_MISSING_CONCEPTS_AT_EXIT = False # Do not show them

db = create_db(SQLITE_FILE)

mapping = defaultdict(list)



for snomedct_code, snomedct_term, icd10_code, icd10_term, align_type, align_quality in list(csv.reader(open(MAPPING_FILE, newline = "")))[1:]:
  snomedct_code = snomedct_code[7:]
  icd10_code    = icd10_code   [7:]
  try:
    snomedct      = SNOMEDCT[snomedct_code]
    icd10         = ICD10   [icd10_code]
  except: continue
  mapping[icd10].append(snomedct)
print("%s mappings" % len(mapping))


for left, match_type, right in parse_mapping(read_file("./pymedtermino/scripts/icd10_2_snomedct_manual_complement.txt"), ):
  icd10 = ICD10[left[0]]
  mapping[icd10] = []
for left, match_type, right in parse_mapping(read_file("./pymedtermino/scripts/icd10_2_snomedct_manual_complement.txt"), ):
  icd10 = ICD10[left[0]]
  mapping[icd10].extend([SNOMEDCT[c] for c in right])

print("%s mappings after manual corrections" % len(mapping))


print(mapping[ICD10["H47.1"]])




nb = 0
for icd10 in ICD10.all_concepts():
  if not mapping[icd10]:
    children_snomedcts = Concepts(child_snomedct
                                  for child_icd10 in icd10.descendants()
                                  for child_snomedct in mapping[child_icd10]
                                  if child_snomedct.is_a(SNOMEDCT[404684003])
    )
    
    if not children_snomedcts: continue
    parent_snomedcts = children_snomedcts.lowest_common_ancestors()
    mapping[icd10] = list(parent_snomedcts)
    nb += 1
print("%s mappings inferred from children" % nb)


# mapping[ICD10["I"    ]] = [SNOMEDCT[40733004]]
# mapping[ICD10["II"   ]] = [SNOMEDCT[399981008]]
# mapping[ICD10["III"  ]] = [SNOMEDCT[414022008], SNOMEDCT[414029004]]
# mapping[ICD10["IV"   ]] = [SNOMEDCT[362969004], SNOMEDCT[2492009], SNOMEDCT[75934005]]
# mapping[ICD10["V"    ]] = [SNOMEDCT[74732009]]
# mapping[ICD10["VI"   ]] = [SNOMEDCT[23853001], SNOMEDCT[42658009]]
# mapping[ICD10["VII"  ]] = [SNOMEDCT[371409005]]
# mapping[ICD10["VIII" ]] = [SNOMEDCT[25906001]]
# mapping[ICD10["IX"   ]] = [SNOMEDCT[56265001], SNOMEDCT[400047006]]
# mapping[ICD10["X"    ]] = [SNOMEDCT[50043002]]
# mapping[ICD10["XI"   ]] = [SNOMEDCT[53619000]]
# mapping[ICD10["XII"  ]] = [SNOMEDCT[95320005]]
# mapping[ICD10["XIII" ]] = [SNOMEDCT[76069003], SNOMEDCT[399269003], SNOMEDCT[75047002], SNOMEDCT[105969002]]
# mapping[ICD10["XIV"  ]] = [SNOMEDCT[362968007], SNOMEDCT[128606002]]
# mapping[ICD10["XV"   ]] = [SNOMEDCT[173300003]]
# mapping[ICD10["XVI"  ]] = [SNOMEDCT[414025005]]
# mapping[ICD10["XVII" ]] = [SNOMEDCT[443341004], SNOMEDCT[409709004]]
#mapping[ICD10["XVIII"]] = [SNOMEDCT[]]
#mapping[ICD10["XIX"  ]] = [SNOMEDCT[]]
#mapping[ICD10["XX"   ]] = [SNOMEDCT[]]
#mapping[ICD10["XXI"  ]] = [SNOMEDCT[]]
#mapping[ICD10["XXII" ]] = [SNOMEDCT[]]

#mapping[ICD10["XXII" ]] = [SNOMEDCT[]]


TXT = u"\n".join(u"%s == %s" % (icd10.code, u" ".join(u"%s" % c.code for c in snomedcts)) for icd10, snomedcts in mapping.items())
  

#sys.stderr.write("%s exact ICD10 => SNOMEDCT matches.\n" % nb_exact)
open("/tmp/t2.txt", "w").write(TXT)

Txt_2_SQLMapping(None, db, code1_type = "TEXT", code2_type = "INTEGER", txt = TXT)
close_db(db, SQLITE_FILE)
