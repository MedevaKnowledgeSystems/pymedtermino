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

import sys, os, os.path, sqlite3
from pymedtermino.utils.mapping_db import *


HERE              = os.path.dirname(sys.argv[0])
ONTOLOGY_PATH     = os.path.join(HERE, "..", "icpc2_onto")
SQLITE_FILE1      = os.path.join(HERE, "..", "icpc2.sqlite3")
SQLITE_FILE2      = os.path.join(HERE, "..", "icpc2_2_vcm.sqlite3")

db = create_db(SQLITE_FILE1)
OWL_2_SQL       ([os.path.join(ONTOLOGY_PATH, "icpc2_onto.owl")], db, code_type = u"TEXT")

#do_sql(db.cursor(), u"""
#CREATE INDEX Concept_category_text_code_index ON Concept(category, text_code)""")

cursor = db.cursor()
do_sql(cursor, u"""CREATE VIRTUAL TABLE Concept_fts USING fts4(content="Concept", term);""")
do_sql(cursor, u"""INSERT INTO Concept_fts(docid, term) SELECT id, term FROM Concept;""")
do_sql(cursor, u"""INSERT INTO Concept_fts(Concept_fts) VALUES('optimize');""")

close_db(db, SQLITE_FILE1)


db = create_db(SQLITE_FILE2)
Txt_2_SQLMapping(os.path.join(ONTOLOGY_PATH, "icpc2_2_vcm.txt"), db, code1_type = "TEXT", code2_type = "TEXT")
close_db(db, SQLITE_FILE2)

  
