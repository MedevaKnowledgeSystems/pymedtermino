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

from __future__ import print_function

import sys, os, os.path, re, csv
from collections        import defaultdict
import pymedtermino
pymedtermino.LANGUAGE = "fr"
from pymedtermino       import *
from pymedtermino.vcm   import *
from pymedtermino.snomedct         import *
from pymedtermino.snomedct_2_vcm   import *


f = csv.writer(open("/tmp/anatmical_structure_analysis.csv", "w"))
f.writerow(["Probleme", "Code SNOMED", "Terme"])

already = set()
def traite_structure(anatomical_structure):
  if anatomical_structure in already: return
  already.add(anatomical_structure)
  
  cons = anatomical_structure >> VCM_CONCEPT
  if not cons:
    cons = Concepts(anatomical_structure.ancestor_parts()) >> VCM_CONCEPT
  
  if cons:
    for i in anatomical_structure.self_and_descendants_no_double():
      i.ok = 1
      
  else:
    anatomical_structure.ok = 0
    for i in anatomical_structure.children: traite_structure(i)

traite_structure(SNOMEDCT[91723000]) # Anatomical structure




feuilles_a_probleme = Concepts()

already = set()
def traite_structure2(anatomical_structure):
  global nb
  
  if anatomical_structure in already: return
  already.add(anatomical_structure)
  
  if anatomical_structure.ok:
    pass
  
  else:
    enfants_ok = set(i.ok for i in anatomical_structure.descendants_no_double())
    if (not enfants_ok) or (enfants_ok == set([0])):
      if   anatomical_structure.is_a(SNOMEDCT[4421005]): pass # Cell structure
      elif anatomical_structure.is_a(SNOMEDCT[116011005]): pass # Non-human body structure
      else:
        feuilles_a_probleme.add(anatomical_structure)
    else:
      for i in anatomical_structure.children: traite_structure2(i)
      
traite_structure2(SNOMEDCT[91723000]) # Anatomical structure


feuilles_a_probleme.keep_most_generic()

for i in feuilles_a_probleme:
  print(i)
  f.writerow([1, i.code, i.term])
print(len(feuilles_a_probleme))
print()
print()


branches_a_probleme = Concepts()



already = set()
def traite_structure3(anatomical_structure):
  if anatomical_structure in already: return
  already.add(anatomical_structure)

  if anatomical_structure.ok:
    pass
  
  else:
    enfants_ok = set(i.ok for i in anatomical_structure.descendants_no_double())
    if (enfants_ok == set([0, 1])) or (enfants_ok == set([1])):
      if   anatomical_structure.is_a(SNOMEDCT[4421005]): pass # Cell structure
      elif anatomical_structure.is_a(SNOMEDCT[116011005]): pass # Non-human body structure
      else:
        branches_a_probleme.add(anatomical_structure)
    for i in anatomical_structure.children: traite_structure3(i)

traite_structure3(SNOMEDCT[91723000]) # Anatomical structure

branches_a_probleme.keep_most_specific()

for i in branches_a_probleme:
  print(i)
  f.writerow([2, i.code, i.term])
print(len(branches_a_probleme))


