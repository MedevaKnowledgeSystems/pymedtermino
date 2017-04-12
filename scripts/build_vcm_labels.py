import sys, os, os.path, csv
from collections import defaultdict

import pymedtermino
pymedtermino.READ_ONLY_DATABASE = False

from pymedtermino.all import *
from pymedtermino.vcm_label import icon_2_label


HERE = os.path.dirname(sys.argv[0]) or "."
sys.path.append(os.path.join(HERE, ".."))

from utils.db import *

SQLITE_FILE = os.path.join(HERE, "..", "vcm_label.sqlite3")

db = create_db(SQLITE_FILE)
db_cursor = db.cursor()

def do_sql(*sql):
  #r.write(sql.encode("utf8"))
  #r.write(";\n")
  db_cursor.execute(*sql)
  
def sql_escape(s):
  return s.replace(u'"', u'""').replace(u'\r', u'').replace(u'\x92', u"'")


do_sql(u"PRAGMA synchronous  = OFF")
do_sql(u"PRAGMA journal_mode = OFF")

do_sql(u"""
CREATE TABLE Label (
  id INTEGER PRIMARY KEY,
  code TEXT,
  term_en TEXT,
  term_fr TEXT
)""")



def get_all_useful_current_patho_icons():
  (SNOMEDCT >> VCM).db_cursor.execute("SELECT DISTINCT code2 FROM Mapping")
  icons = (SNOMEDCT >> VCM).db_cursor.fetchall()
  icons = [i[0] for i in icons]
  print("%s icons in the SNOMED CT mapping." % len(icons))
  return icons

def get_all_useful_icons():
  for base_icon in get_all_useful_current_patho_icons():
    base_icon = VCM[base_icon]
    yield base_icon
    yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"]])
    yield base_icon.derive_lexs([VCM_LEXICON[0, "antecedent"]])
    yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "medicament"]])
    
    if len(icon.lexs) <= 3:
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "procedure"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "implant"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "radiothe"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "greffe"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "ectomie"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "chirurgie"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "alimentation"]])
      yield base_icon.derive_lexs([VCM_LEXICON[3, "traitement"], VCM_LEXICON[4, "sport"]])
      
      yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"], VCM_LEXICON[3, "surveillance"], VCM_LEXICON[4, "clinique"]])
      yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"], VCM_LEXICON[3, "surveillance"], VCM_LEXICON[4, "bio"]])
      yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"], VCM_LEXICON[3, "surveillance"], VCM_LEXICON[4, "fonctionnelle"]])
      yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"], VCM_LEXICON[3, "surveillance"], VCM_LEXICON[4, "radio"]])
      yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"], VCM_LEXICON[3, "surveillance"], VCM_LEXICON[4, "biopsie"]])
      yield base_icon.derive_lexs([VCM_LEXICON[0, "risque"], VCM_LEXICON[3, "surveillance"], VCM_LEXICON[4, "diagnostic"]])
      

for icon in get_all_useful_icons():
  if not icon.consistent: continue
  
  #print(icon.code)
  
  label = icon_2_label(icon).langs
  do_sql(u"INSERT INTO Label VALUES (NULL, ?, ?, ?)", (icon.code, label["en"], label["fr"]))


do_sql(u"""VACUUM;""")
close_db(db, SQLITE_FILE)

