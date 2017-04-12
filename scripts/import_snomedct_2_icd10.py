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


# Get SNOMED CT to ICD10 mapping from :
# http://www.nlm.nih.gov/research/umls/mapping_projects/snomedct_to_icd10cm.html

MAPPING_FILE = "/home/jiba/telechargements/base_med/SnomedCT_Icd10CrossMapCandidateBaseline_INT_20130201/RF2Release/Snapshot/Refset/Crossmap/der2_iisssccRefset_ComplexMapIcd10Snapshot_INT_20130201.txt"




#SNOMEDCT_2_ICD10_DIR = "/home/jiba/telechargements/base_med/SNOMEDCT_ICD10_MAPPING/"


import sys, os, os.path, stat, sqlite3, tempfile
from pymedtermino.utils.db         import *
from pymedtermino.utils.mapping_db import *

from pymedtermino.snomedct import *
from pymedtermino.icd10    import *

#for filename in os.listdir(SNOMEDCT_2_ICD10_DIR):
#  if filename.startswith("tls"):
#    MAPPING_FILE = os.path.join(SNOMEDCT_2_ICD10_DIR, filename)
#    break
#else: raise ValueError



HERE        = os.path.dirname(sys.argv[0])
SQLITE_FILE = os.path.join(HERE, "..", "snomedct_2_icd10.sqlite3")
TXT         = u""

db = create_db(SQLITE_FILE)

nb = 0
snomedct_codes = set()
icd10_codes    = set()
for line in read_file(MAPPING_FILE).split("\n")[1:]:
  if line:
    words = line.split("\t")
    if words[2] != "1": continue # Not active
    if not words[10]:   continue # Not mappable
    
    try:    snomedct = SNOMEDCT[words[5]]
    except: continue
    
    try: icd10 = ICD10[words[10]]
    except:
      try: icd10 = ICD10[words[10][:-1]]
      except:
        try: icd10 = ICD10[words[10][:-2]]
        except:
          try: icd10 = ICD10[words[10][:-3]]
          except:
            continue
          
    rule = words[8]
    
    if   rule.startswith("IFA "):
      try: and_concept = SNOMEDCT[rule.split()[1]]
      except: continue
      
      snomedct_codes.add(and_concept.code)
      TXT += u"%s+%s =~ %s\n" % (snomedct.code, and_concept.code, icd10.code)
      
    elif (rule == "TRUE") or (rule == "OTHERWISE TRUE"): # XXX not exactely true for OTHERWISE TRUE !
      TXT += u"%s =~ %s\n" % (snomedct.code, icd10.code)
      
    snomedct_codes.add(snomedct.code)
    icd10_codes   .add(icd10.code)
    nb  += 1
      
sys.stderr.write("%s mappings involving %s SNOMEDCT concepts and %s ICD10 concepts.\n" % (nb, len(snomedct_codes), len(icd10_codes)))
write_file("/tmp/t.txt", TXT)

Txt_2_SQLMapping(None, db, code1_type = "INTEGER", code2_type = "TEXT", txt = TXT)
close_db(db, SQLITE_FILE)



from pymedtermino.snomedct_2_icd10 import *
icd10_2_snomedct = snomedct_2_icd10._create_reverse_mapping()
icd10_2_snomedct._has_and = 0 # AND mapping are meaningful only in the SNOMEDCT => ICD10 direction
icd10_2_snomedct.register()

SQLITE_FILE = os.path.join(HERE, "..", "snomedct_2_icd10_reverse.sqlite3")

db  = create_db(SQLITE_FILE)
TXT = u""

nb_exact = 0
for icd10 in ICD10.all_concepts():
  snomedcts = icd10 >> SNOMEDCT
  snomedcts_exact_map = Concepts([c for c in snomedcts if (c >> ICD10) == Concepts([icd10])])
  if snomedcts_exact_map:
    snomedcts = snomedcts_exact_map
    nb_exact += 1
  snomedcts.keep_most_generic()

  snomedcts_sans_associe = Concepts(snomedcts)
  for snomedct in snomedcts:
    if "INVERSE_associated_with" in snomedct.relations:
      for associe in snomedct.INVERSE_associated_with:
        snomedcts_sans_associe.discard(associe)
  if snomedcts_sans_associe: snomedcts = snomedcts_sans_associe
  
  snomedcts_in_core = Concepts([c for c in snomedcts if c.is_in_core])
  if snomedcts_in_core: snomedcts = snomedcts_in_core
  
  TXT += u"%s == %s\n" % (icd10.code, u" ".join(u"%s" % c.code for c in snomedcts))

sys.stderr.write("%s exact ICD10 => SNOMEDCT matches.\n" % nb_exact)
write_file("/tmp/t2.txt", TXT)

Txt_2_SQLMapping(None, db, code1_type = "TEXT", code2_type = "INTEGER", txt = TXT)
close_db(db, SQLITE_FILE)

