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

# (Re)build SNOMED CT => VCM mapping.

from __future__ import print_function

import sys, os, os.path, re, csv
from collections        import defaultdict
import pymedtermino
pymedtermino.LANGUAGE = "fr"
from pymedtermino       import *
from pymedtermino.vcm   import *
from pymedtermino.umls  import *
from pymedtermino.snomedct         import *
from pymedtermino.snomedct_2_vcm   import *
from pymedtermino.utils.mapping_db import *

#pymedtermino.umls.REMOVE_SUPPRESSED_CONCEPTS = 0


connect_to_umls_db("10.10.100.12", "jiba", "vicking", "umls")

UMLS_ICPC2EENG = UMLS_AUI.extract_terminology("ICPC2EENG")
#UMLS_ICPC2P = UMLS_AUI.extract_terminology("ICPC2P")
#UMLS_ICPC2EENG = UMLS_AUI.extract_terminology("ICD10")
UMLS_SNOMEDCT  = UMLS_AUI.extract_terminology("SNOMEDCT", 1)
UMLS_ICD10     = UMLS_AUI.extract_terminology("ICD10", 0)

#UMLS_ICPC2EENG["T90"] >> UMLS_SNOMEDCT >> SNOMEDCT



SUBSET = u"""cisp2:K86
cisp2:T90
cisp2:T93
cisp2:R96
cisp2:P17
cisp2:D88
cisp2:D98
cisp2:K74
cisp2:K75
cisp2:K90
cisp2:K95
cisp2:D89
cisp2:T86
cisp2:R97
cisp2:K94
cisp2:F92
cisp2:D75
cisp2:X76
cisp2:K78
cisp2:K87
cisp2:Y77
cisp2:T92
cisp2:S77
cisp2:U95
cisp2:R74
cisp2:L86
cisp2:D72
cisp2:K80
cisp2:L95
cisp2:N93
cisp2:X11
cisp2:T82
cisp2:L88
cisp2:N89
cisp2:Y85
cisp2:L99
cisp2:K93
cisp2:U14
cisp2:K83
cisp2:D86
cisp2:D84
cisp2:T81
cisp2:F93
cisp2:A70
cisp2:U99
cisp2:D90
cisp2:P76
cisp2:L84
cisp2:L89
cisp2:D92
cisp2:D85
cisp2:R79
cisp2:P70
cisp2:W11
cisp2:L03
cisp2:K77
cisp2:D99
cisp2:D97
cisp2:N87
cisp2:R84
cisp2:P15
cisp2:P73
cisp2:R99
cisp2:D94
cisp2:T89
cisp2:U77
cisp2:T99
cisp2:R81
cisp2:S91
cisp2:R76
cisp2:L90
cisp2:T85
cisp2:B74
cisp2:L85
cisp2:K84
cisp2:K96
cisp2:U75
cisp2:N99
cisp2:D87
cisp2:X77
cisp2:L76
cisp2:K92
cisp2:U71
cisp2:N86
cisp2:N88
cisp2:R75
cisp2:S87
cisp2:L72
cisp2:W82
cisp2:B73
cisp2:U04
cisp2:D77
cisp2:R90
cisp2:D95
cisp2:N28
cisp2:N07
cisp2:R78
cisp2:L77
cisp2:L75
cisp2:S70
cisp2:X87"""

#SUBSET = [UMLS_ICPC2EENG[code.replace(u"cisp2:", u"")] for code in SUBSET.split()]
SUBSET = UMLS_ICPC2EENG.all_concepts()
#SUBSET = UMLS_ICPC2EENG["7"].children

d = {}

nb  = 0
rep = defaultdict(lambda: 0)
nb_no_snomed = 0
all_icons = Concepts()

f = csv.writer(open("/tmp/t.csv", "w"))

for icpc in sorted(SUBSET, key = lambda c: c.code):
  #print()
  #print()
  #print(icpc)
  snomedcts = icpc >> UMLS_SNOMEDCT >> SNOMEDCT
  if not snomedcts:
    snomedcts = snomedcts = icpc >> UMLS_ICD10 >> UMLS_SNOMEDCT >> SNOMEDCT
    
  snomedcts.keep_most_specific()
  if len(snomedcts) > 2: snomedcts = Concepts()
  
  #if not snomedcts: snomedcts = icpc >> UMLS_CUI >> UMLS_SNOMEDCT >> SNOMEDCT
  if not snomedcts: nb_no_snomed += 1
  
  #print(snomedcts)
  vcms      = Concepts(snomedcts >> VCM)
  keep_most_graphically_specific_icons(vcms, add_shadow = 0)
  #print(vcms)
  
  
  all_icons.update(vcms)
  
  d[icpc.code] = [vcm.code for vcm in vcms]
  nb += 1
  rep[len(vcms)] += 1
  
  #f.writerow([icpc.code, icpc.term,
  #            u",".join(unicode(c.code) for c in snomedcts), u",".join(c.term for c in snomedcts),
  #            u",".join(        c.code  for c in vcms     ),
  #           ])
  
  #print(icpc.code, "==", " ".join(unicode(c.code) for c in snomedcts), " #", icpc.term, "==", " ".join(c.term for c in snomedcts), " ", " ".join(c.code for c in vcms))
  print(icpc.code, "==", " ".join(unicode(c.code) for c in vcms), " #", icpc.term)
  
  if (nb % 100) == 0: print("%s..." % nb, file = sys.stderr)
  
print(file = sys.stderr)
print(nb, file = sys.stderr)
print(rep, file = sys.stderr)
print(len(all_icons), "icônes différentes", file = sys.stderr)
print("Pas de correspondance vers la SNOMEDCT pour %s concepts" % nb_no_snomed, file = sys.stderr)
print(file = sys.stderr)
print(file = sys.stderr)

#for root in UMLS_ICPC2EENG.first_levels():
#  root_rep = defaultdict(lambda: 0)
#  for icpc in root.self_and_descendants_no_double():
#    print(icpc.code)
#    vcms = d[icpc.code]
#    root_rep[len(vcms)] += 1
#  print(root, root_rep)
#  print()

