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

#__all__ = ["snomedct_2_icd10", "icd10_2_snomedct"]

import os, os.path
from pymedtermino          import *
from pymedtermino.snomedct import *
from pymedtermino.icd10    import *

#snomedct_2_icd10 = SQLMapping(SNOMEDCT, ICD10, os.path.join(DATA_DIR, "snomedct_2_icd10.sqlite3"), has_and = 1)
#snomedct_2_icd10.register()
#icd10_2_snomedct = SQLMapping(ICD10, SNOMEDCT, os.path.join(DATA_DIR, "snomedct_2_icd10_reverse.sqlite3"), has_and = 0)
#icd10_2_snomedct.register()

icd10_2_snomedct = SQLMapping(ICD10, SNOMEDCT, os.path.join(DATA_DIR, "snomedct_2_icd10_reverse.sqlite3"), has_and = 0)
icd10_2_snomedct.register()
snomedct_2_icd10 = icd10_2_snomedct._create_reverse_mapping()
snomedct_2_icd10.register()

