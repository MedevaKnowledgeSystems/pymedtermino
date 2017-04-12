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

import sys, os, os.path

import pymedtermino
pymedtermino.LANGUAGE = "fr"

from pymedtermino       import *
from pymedtermino.vcm   import *



for concept in VCM_CONCEPT[55].descendants_no_double():
  for parent in concept.parents:
    if not parent is VCM_CONCEPT[55]:
      print("%s %s # %s is_a %s" % (concept.code, parent.code, concept.term, parent.term))
  print()
  
