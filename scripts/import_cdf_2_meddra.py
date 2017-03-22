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


# Import into PyMedTermino the CDF (Thériaque) to MedDRA mapping, from the Vigiterme research project.
# (mapping data available on request to the LIMICS lab)

MAPPING_FILE = "/home/jiba/viiip/ei_vigiterme/EI_Theriaque_Meddra.txt"


import sys, os, os.path, stat, sqlite3, tempfile
from pymedtermino.utils.db         import *
from pymedtermino.utils.mapping_db import *

from pymedtermino.cdf    import *
from pymedtermino.meddra import *

connect_to_theriaque_db()


HERE        = os.path.dirname(sys.argv[0])
SQLITE_FILE = os.path.join(HERE, "..", "cdf_2_meddra.sqlite3")
TXT         = u""

db = create_db(SQLITE_FILE)

nb = 0
cdf_codes = set()
meddra_codes    = set()

missing_cdfs    = set()
missing_meddras = set()

already_done = set()

for line in read_file(MAPPING_FILE, encoding = "latin").split("\n")[1:]:
  if line:
    words = line.split("\t")
    cdf_code    = words[0]
    meddra_code = words[2]
    
    try: cdf = CDF["EN_%s" % cdf_code]
    except:
      missing_cdfs.add(cdf_code)
      continue
      
    try: meddra = MEDDRA.get_by_meddra_code(meddra_code)[0]
    except:
      missing_meddras.add(meddra_code)
      continue

    if (cdf.code, meddra.code) in already_done: continue
    
    TXT += u"%s == %s\n" % (cdf.code, meddra.code)
    
    already_done.add((cdf.code, meddra.code))
    cdf_codes   .add(cdf.code)
    meddra_codes.add(meddra.code)
    nb  += 1
      
sys.stderr.write("%s mappings involving %s CDF concepts and %s MedDRA concepts.\n" % (nb, len(cdf_codes), len(meddra_codes)))
sys.stderr.write("%s missing CDF concepts: %s.\n" % (len(missing_cdfs), missing_cdfs))
sys.stderr.write("%s missing MedDRA concepts: %s.\n" % (len(missing_meddras), missing_meddras))
write_file("/tmp/t.txt", TXT)

Txt_2_SQLMapping(None, db, code1_type = "TEXT", code2_type = "TEXT", txt = TXT)
close_db(db, SQLITE_FILE)



