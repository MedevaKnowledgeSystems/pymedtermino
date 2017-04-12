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

from pymedtermino                  import *
from pymedtermino.vcm              import *
from pymedtermino.icpc2            import *
from pymedtermino.utils.mapping_db import *
import pymedtermino.icpc2_2_vcm

HERE        = os.path.dirname(sys.argv[0])
SQLITE_FILE = os.path.join(HERE, "..", "icpc2_vcm_lexicon_index.sqlite3")
db = create_db(SQLITE_FILE)
index_terminology_by_vcm_lexicon(ICPC2, db, code_type = "TEXT")
close_db(db, SQLITE_FILE)
