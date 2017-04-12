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


# Creates VCM SQL databases from the VCM ontology.

import sys, os, os.path, sqlite3
from pymedtermino.utils.mapping_db import *


HERE              = os.path.dirname(sys.argv[0])
ONTOLOGY_PATH     = os.path.join(HERE, "..", "vcm_onto")
SQLITE_FILE2      = os.path.join(HERE, "..", "vcm_lexicon.sqlite3")

db = create_db(SQLITE_FILE2)
OWL_2_SQL       ([os.path.join(ONTOLOGY_PATH, "vcm_lexique.owl")], db, annotations = [(u"category", u"INTEGER"), (u"text_code", u"TEXT"), (u"priority", u"INTEGER"), (u"second_priority", u"INTEGER")])
do_sql(db.cursor(), u"""
CREATE INDEX Concept_category_text_code_index ON Concept(category, text_code)""")
close_db(db, SQLITE_FILE2, close = 1, set_readonly = 0)


from pymedtermino.vcm import *

categories = [VCM_LEXICON.CENTRAL_COLOR, VCM_LEXICON.MODIFIER, VCM_LEXICON.CENTRAL_PICTOGRAM, VCM_LEXICON.TOP_RIGHT_COLOR, VCM_LEXICON.TOP_RIGHT_PICTOGRAM, VCM_LEXICON.SECOND_TOP_RIGHT_PICTOGRAM, VCM_LEXICON.SHADOW]
for i in range(len(categories)):
  for term in categories[i].self_and_descendants_no_double():
    term.db_cursor.execute(u"""UPDATE Concept SET category=? WHERE code=?""", (i, term.code))
VCM_LEXICON.db.commit()
close_db(None, SQLITE_FILE2, close = 0, set_readonly = 1)
