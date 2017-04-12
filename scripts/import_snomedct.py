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


# Get SNOMED CT from (choose RF2 format) :
# http://www.nlm.nih.gov/research/umls/licensedcontent/snomedctfiles.html

# Get SNOMED CT CORE Problem list from :
# http://www.nlm.nih.gov/research/umls/Snomed/core_subset.html

SNOMEDCT_DIR       = "/home/jiba/telechargements/base_med/SnomedCT_RF2Release_INT_20150131"
SNOMEDCT_CORE_FILE = "/home/jiba/telechargements/base_med/SNOMEDCT_CORE_SUBSET_201502.txt"
#SNOMEDCT_DIR       = "/home/jiba/telechargements/base_med/SnomedCT_Release_INT_20140131/RF2Release"
#SNOMEDCT_CORE_FILE = "/home/jiba/telechargements/base_med/SNOMEDCT_CORE_SUBSET_201408.txt"

#ONLY_ACTIVE_CONCEPT = 1
ONLY_ACTIVE_CONCEPT = 0


import sys, os, os.path, stat, sqlite3

HERE = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(HERE, ".."))


from utils.db import *

if len(sys.argv) >= 3:
  SNOMEDCT_DIR       = sys.argv[1]
  SNOMEDCT_CORE_FILE = sys.argv[2]

LANGUAGE    = "en"
NB          = SNOMEDCT_DIR.split("_")[-1]
if NB.endswith("/RF2Release"): NB = NB.replace("/RF2Release", "")

SQLITE_FILE = os.path.join(HERE, "..", "snomedct.sqlite3")

db = create_db(SQLITE_FILE)
db_cursor = db.cursor()

#r = open("/tmp/log.sql", "w")
def do_sql(sql):
  #r.write(sql.encode("utf8"))
  #r.write(";\n")
  db_cursor.execute(sql)
  
def sql_escape(s):
  return s.replace(u'"', u'""').replace(u'\r', u'').replace(u'\x92', u"'")


do_sql(u"PRAGMA synchronous  = OFF")
do_sql(u"PRAGMA journal_mode = OFF")
do_sql(u"PRAGMA locking_mode = EXCLUSIVE")

do_sql(u"""
CREATE TABLE Concept (
  id BIGINT PRIMARY KEY,
  effectiveTime DATE,
  active INTEGER,
  moduleId BIGINT,
  definitionStatusId BIGINT,
  is_in_core INTEGER
)""")

do_sql(u"""
CREATE TABLE Description (
  id BIGINT PRIMARY KEY,
  effectiveTime DATE,
  active INTEGER,
  moduleId BIGINT,
  conceptId BIGINT,
  languageCode CHAR(2),
  typeId BIGINT,
  term TEXT,
  caseSignificanceId BIGINT
)""")

do_sql(u"""
CREATE TABLE TextDefinition (
  id BIGINT PRIMARY KEY,
  effectiveTime DATE,
  active INTEGER,
  moduleId BIGINT,
  conceptId BIGINT,
  languageCode CHAR(2),
  typeId BIGINT,
  term TEXT,
  caseSignificanceId BIGINT
)""")

do_sql(u"""
CREATE TABLE Relationship (
  id BIGINT PRIMARY KEY,
  effectiveTime DATE,
  active INTEGER,
  moduleId BIGINT,
  sourceId BIGINT,
  destinationId BIGINT,
  relationshipGroup INTEGER,
  typeId BIGINT,
  characteristicTypeId BIGINT
)""")


CORE_IDS = set()
if SNOMEDCT_CORE_FILE:
  for line in open(SNOMEDCT_CORE_FILE).read().split("\n")[1:]:
    if line:
      words = line.split("|")
      if words[7] == "False": CORE_IDS.add(words[0])

sys.stderr.write("%s SNOMED CT terms in CORE Problem list.\n" %  len(CORE_IDS))

ACTIVE_CONCEPTS = set()

for table, language_dependent in [
    ("Concept"       , False),
    ("TextDefinition", True),
    ("Description"   , True),
    ("Relationship"  , False),
  ]:
  if language_dependent:
    filename = os.path.join(SNOMEDCT_DIR, "Snapshot", "Terminology", "sct2_%s_Snapshot-%s_INT_%s.txt" % (table, LANGUAGE, NB))
  else:
    filename = os.path.join(SNOMEDCT_DIR, "Snapshot", "Terminology", "sct2_%s_Snapshot_INT_%s.txt" % (table, NB))
    
  sys.stderr.write("Importing %s ...\n" % filename)
  
  for line in read_file(filename).split(u"\n")[1:]:
    if line:
      words = line.replace(u"\r", u"").split(u"\t")
      
      if   table == "Concept":
        if words[2] == u"1": ACTIVE_CONCEPTS.add(words[0])
        if words[0]in CORE_IDS: words.append("1")
        else:                   words.append("0")
        
      #elif table == "Description":
        #if not words[4] in ACTIVE_CONCEPTS:
          #continue # Active description of an inactive concept...!
          #words[2] = u"0"
          
      #elif table == "TextDefinition":
        #if not words[4] in ACTIVE_CONCEPTS:
          #continue # Active def of an inactive concept...!
          #words[2] = u"0"
        
      #elif table == "Relationship":
        #if (not words[4] in ACTIVE_CONCEPTS) or (not words[5] in ACTIVE_CONCEPTS):
          #continue # Active relation with an inactive concept...!
          #words[2] = u"0"
          
      #del words[1:3]
      
      if table == "Relationship": del words[-1] # modifierId is unused yet
      
      data = u"""("%s")""" % '", "'.join(map(sql_escape, words))
      sql  = u"""INSERT INTO %s VALUES %s""" % (table, data)
      do_sql(sql)
    
  if ONLY_ACTIVE_CONCEPT and (table == "Concept"): sys.stderr.write("%s active concepts\n" % len(ACTIVE_CONCEPTS))

  db.commit()
  
sys.stderr.write("Indexing ...\n")

do_sql(u"""CREATE INDEX Description_conceptId_index             ON Description(conceptId)""")

do_sql(u"""CREATE INDEX TextDefinition_conceptId_index          ON TextDefinition(conceptId)""")

do_sql(u"""CREATE INDEX Relationship_sourceId_typeId_index      ON Relationship(sourceId, typeId)""")
do_sql(u"""CREATE INDEX Relationship_destinationId_typeId_index ON Relationship(destinationId, typeId)""")


do_sql(u"""CREATE VIRTUAL TABLE Description_fts USING fts4(content="Description", term);""")
do_sql(u"""INSERT INTO Description_fts(docid, term) SELECT id, term FROM Description;""")
do_sql(u"""INSERT INTO Description_fts(Description_fts) VALUES('optimize');""")

do_sql(u"""CREATE VIRTUAL TABLE TextDefinition_fts USING fts4(content="TextDefinition", term);""")
do_sql(u"""INSERT INTO TextDefinition_fts(docid, term) SELECT id, term FROM TextDefinition;""")
do_sql(u"""INSERT INTO TextDefinition_fts(TextDefinition_fts) VALUES('optimize');""")

db.commit()

do_sql(u"""VACUUM;""")

db.commit()

do_sql(u"""PRAGMA integrity_check;""")
for l in db_cursor.fetchall():
  print(" ".join(l))

close_db(db, SQLITE_FILE)
