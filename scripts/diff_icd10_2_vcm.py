# -*- coding: utf-8 -*-
# PyMedTermino
# Copyright (C) 2014 Jean-Baptiste LAMY
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
from collections import defaultdict
import pymedtermino
pymedtermino.LANGUAGE = "fr"
from pymedtermino       import *
from pymedtermino.vcm   import *
from pymedtermino.icd10 import *


icd10_2_vcm_A = SQLMapping(ICD10, VCM, os.path.join(DATA_DIR, "icd10_2_vcm_manual_rouen.sqlite3"), has_and = 0)
icd10_2_vcm_B = SQLMapping(ICD10, VCM, os.path.join(DATA_DIR, "icd10_2_vcm.sqlite3"), has_and = 0)

CONCEPTS = ICD10["IX"].self_and_descendants()

nb = nb_diff = 0
for icd10 in CONCEPTS:
  nb     += 1
  icons_A = icd10_2_vcm_A(icd10)
  icons_B = icd10_2_vcm_B(icd10)
  if icons_A != icons_B:
    nb_diff += 1
    print("%s : %s  %s => %s" % (icd10.code, icd10.term, ",".join(icon.code for icon in icons_A), ",".join(icon.code for icon in icons_B)))
    
print("%s differences / %s concepts = %.1f%%" % (nb_diff, nb, 100.0 * nb_diff / nb))


