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


# Get MedDRA from :
# https://www.meddra.org/software-packages

MEDDRA_DIRS = {
  "en" : "/home/jiba/telechargements/base_med/meddra/en/MedAscii",
  "fr" : "/home/jiba/telechargements/base_med/meddra/fr/ascii-180",
  # Add / remove languages as desired
}

import sys, os, os.path, stat, sqlite3

HERE = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(HERE, ".."))


from utils.db import *

if len(sys.argv) > 1:
  MEDDRA_DIRS = {}
  for arg in sys.argv[1:]:
    lang, path = arg.split("_", 1)
    MEDDRA_DIRS[lang] = path
    
LANGS = list(MEDDRA_DIRS.keys())

SQLITE_FILE = os.path.join(HERE, "..", "meddra.sqlite3")

db = create_db(SQLITE_FILE)
db_cursor = db.cursor()

#r = open("/tmp/log.sql", "w")
def do_sql(sql):
  #r.write(sql)
  #r.write(";\n")
  db_cursor.execute(sql)
  
def sql_escape(s):
  return s.replace(u'"', u'""').replace(u'\r', u'').replace(u'\x92', u"'")


do_sql(u"PRAGMA synchronous  = OFF")
do_sql(u"PRAGMA journal_mode = OFF")
do_sql(u"PRAGMA locking_mode = EXCLUSIVE")

do_sql(u"""
CREATE TABLE Concept (
  id INTEGER PRIMARY KEY,
  code TEXT,
  active INTEGER,
  %s
  depth INTEGER
)""" % "\n  ".join("term_%s TEXT," % lang for lang in LANGS))

do_sql(u"""
CREATE TABLE Concept_SOC (
  id INTEGER PRIMARY KEY,
  abbrev TEXT,
  international_order INTEGER
)""")

do_sql(u"""
CREATE TABLE Concept_PT (
  id INTEGER PRIMARY KEY,
  primary_soc TEXT
)""")

do_sql(u"""
CREATE TABLE IsA (
  id INTEGER PRIMARY KEY,
  child TEXT,
  parent TEXT
)""")

do_sql(u"""
CREATE TABLE SupportedLanguage (
  id INTEGER PRIMARY KEY,
  lang TEXT
)""")

db.commit()

for lang in LANGS:
  do_sql("""INSERT INTO SupportedLanguage VALUES (NULL, "%s")""" % lang)

db.commit()


CONCEPTS = {}
class Concept(object):
  def __init__(self, code):
    CONCEPTS[code] = self
    self.code      = code
    self.active    = 1
    self.sql_id    = len(CONCEPTS)
    
def get_concept(code):
  if not code in CONCEPTS: return Concept(code)
  return CONCEPTS[code]

ISA = set()
def assert_isa(child_code, parent_code):
  ISA.add((child_code, parent_code))

if sys.version[0] == "2":
  def open_meddra_file(filename, lang):
    filename = os.path.join(MEDDRA_DIRS[lang], "%s.asc" % filename)
    if lang in ["cs", "hu", "zh"]: encoding = "utf8" # Czech, Hungarian, and Chinese
    else:                          encoding = "latin1"
    return open(filename).read().decode(encoding)
else:
  def open_meddra_file(filename, lang):
    filename = os.path.join(MEDDRA_DIRS[lang], "%s.asc" % filename)
    if lang in ["cs", "hu", "zh"]: encoding = "utf8" # Czech, Hungarian, and Chinese
    else:                          encoding = "latin1"
    return open(filename, encoding = encoding).read()
  

for lang in LANGS:
  for depth, filename in [(0, "soc"), (1, "hlgt"), (2, "hlt"), (3, "pt"), (4, "llt")]:
    for line in open_meddra_file(filename, lang).split("\n"):
      if line:
        words = line.split("$")
        concept = get_concept("%s_%s" % (filename.upper(), words[0]))
        concept.depth  = depth
        setattr(concept, "term_%s" % lang, words[1])
        
        if   filename == "soc":
          concept.abbrev = words[2]
          
        elif filename == "pt":
          concept.primary_soc = "SOC_%s" % words[3]
          
        elif filename == "llt":
          assert_isa(concept.code, "PT_%s" % words[2])
          concept.active = int(words[9] == "Y")
          
for filename in ["soc_hlgt", "hlgt_hlt", "hlt_pt"]:
  parent_type, child_type = filename.upper().split("_")
  for line in open_meddra_file(filename, lang).split("\n"):
    if line:
      words = line.split("$")
      assert_isa("%s_%s" % (child_type, words[1]), "%s_%s" % (parent_type, words[0]))
      
for line in open_meddra_file("intl_ord", lang).split("\n"):
  if line:
    words = line.split("$")
    concept = get_concept("SOC_%s" % words[1])
    concept.international_order = int(words[0])


for concept in CONCEPTS.values():
  data = [concept.code, concept.active]
  for lang in LANGS: data.append(sql_escape(getattr(concept, "term_%s" % lang)))
  data.append(concept.depth)
  do_sql("""INSERT INTO Concept VALUES (%s, %s)""" % (concept.sql_id, ", ".join('"%s"' % i for i in data)))
  
  if concept.depth == 0:
    #do_sql("""INSERT INTO Concept_SOC VALUES (NULL, "%s", "%s", "%s")""" % (concept.code, sql_escape(concept.abbrev), concept.international_order))
    do_sql("""INSERT INTO Concept_SOC VALUES (%s, "%s", "%s")""" % (concept.sql_id, sql_escape(concept.abbrev), concept.international_order))
    
  if concept.depth == 3:
    #do_sql("""INSERT INTO Concept_PT VALUES (NULL, "%s", "%s")""" % (concept.code, concept.primary_soc))
    do_sql("""INSERT INTO Concept_PT VALUES (%s, "%s")""" % (concept.sql_id, concept.primary_soc))
    
db.commit()

    
for child_code, parent_code in ISA:
  do_sql("""INSERT INTO IsA VALUES (NULL, "%s", "%s")""" % (child_code, parent_code))

db.commit()



sys.stderr.write("Indexing ...\n")

do_sql(u"""CREATE INDEX Concept_code_index             ON Concept    (code)""")
do_sql(u"""CREATE INDEX Concept_depth_index            ON Concept    (depth)""")
#do_sql(u"""CREATE INDEX Concept_SOC_code_index         ON Concept_SOC(code)""")
#do_sql(u"""CREATE INDEX Concept_PT_code_index          ON Concept_PT (code)""")

do_sql(u"""CREATE INDEX IsA_parent_index      ON IsA(parent)""")
do_sql(u"""CREATE INDEX IsA_child_index       ON IsA(child)""")


do_sql(u"""CREATE VIRTUAL TABLE Concept_fts USING fts4(content="Concept", term);""")
for lang in LANGS:
  do_sql(u"""INSERT INTO Concept_fts(docid, term) SELECT id, term_%s FROM Concept;""" % lang)

# ALREADY_DONE = set()
# for depth in [4, 3, 2, 1, 0]:
#   for concept in CONCEPTS.values():
#     if concept.depth != depth: continue
#     for lang in LANGS:
#       term = getattr(concept, "term_%s" % lang)
#       if term in ALREADY_DONE: continue
#       do_sql(u"""INSERT INTO Concept_fts(docid, term) VALUES ("%s", "%s")""" % (concept.code, sql_escape(term)))
#       ALREADY_DONE.add(term)


do_sql(u"""INSERT INTO Concept_fts(Concept_fts) VALUES('optimize');""")

db.commit()

do_sql(u"""VACUUM;""")

db.commit()

do_sql(u"""PRAGMA integrity_check;""")
for l in db_cursor.fetchall():
  print(" ".join(l))

close_db(db, SQLITE_FILE)
