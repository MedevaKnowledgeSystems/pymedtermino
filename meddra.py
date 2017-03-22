# -*- coding: utf-8 -*-
# PyMedTermino
# Copyright (C) 2012-2014 Jean-Baptiste LAMY
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

"""
pymedtermino.meddra
*******************

PyMedtermino module for MedDRA.

Several concepts can share the same code in MedDRA.
For example, a preferred term (PT) and a low-level term (LLT) can have the same code and label.
In order to distinguish them, PyMedTermino does not use directly the MedDRA codes,
but associates the term's level with the code to obtain a unique code, for example "SOC_10019805" or "PT_10069435".

.. class:: MEDDRA
   
   The MedDRA terminology. See :class:`pymedtermino.Terminology` for common terminology members; only MedDRA-specific members are described here.

   .. method:: first_levels()

      Returns the root concepts in MedDRA (=the SOC), in international order.

   .. method:: get_by_meddra_code(meddra_code)

      Returns a list of MedDRA concepts corresponding to the given MedDRA numeric code (e.g. 10073496).

"""

__all__ = ["MEDDRA"]

import sys, os, os.path
import pymedtermino


db        = pymedtermino.connect_sqlite3("meddra")
db_cursor = db.cursor()
db_cursor.execute("PRAGMA synchronous  = OFF;")
db_cursor.execute("PRAGMA journal_mode = OFF;")

import atexit
atexit.register(db.close)

class MEDDRA(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "MEDDRA")
    
    db_cursor.execute("SELECT lang FROM SupportedLanguage")
    self.langs = [lang for (lang,) in db_cursor.fetchall()]
    
  def _create_Concept(self): return MEDDRAConcept
  
  def first_levels(self):
    db_cursor.execute("SELECT Concept.code FROM Concept WHERE Concept.depth = 0")
    db_cursor.execute("SELECT Concept.code FROM Concept_SOC, Concept WHERE Concept.id = Concept_SOC.id ORDER BY Concept_SOC.international_order")
    return [self[code] for (code,) in db_cursor.fetchall()]

  def get_by_meddra_code(self, meddra_code):
    concepts = []
    for depth in range(5):
      concept = self.get("%s_%s" % (_DEPTH_2_TYPE[depth], meddra_code))
      if concept: concepts.append(concept)
    return concepts
    
  def search(self, text):
    if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
      db_cursor.execute("SELECT DISTINCT Concept.code FROM Concept, Concept_fts WHERE (Concept_fts.term MATCH ?) AND (Concept.id = Concept_fts.docid) AND (Concept.active = 1)", (text,))
    else:
      db_cursor.execute("SELECT DISTINCT Concept.code FROM Concept, Concept_fts WHERE (Concept_fts.term MATCH ?) AND (Concept.id = Concept_fts.docid)", (text,))
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l

_DEPTH_2_TYPE = { 0 : "SOC", 1 : "HLGT", 2 : "HLT", 3 : "PT", 4 : "LLT" }


class MEDDRAConcept(pymedtermino.MultiaxialConcept, pymedtermino._StringCodeConcept):
  """A MedDRA concept. See :class:`pymedtermino.Concept` for common terminology members; only MedDRA-specific members are described here.

Additional attributes are available for relations, and are listed in the :attr:`relations <pymedtermino.Concept.relations>` attribute.

.. attribute:: meddra_code

   The original numeric MedDRA code.

.. attribute:: meddra_type

   The type of MedDRA term (SOC, HLGT, HLT, PT or LLT).

.. attribute:: abbrev

   The abbreviated name associated to a SOC (only available for SOC).

.. attribute:: international_order

   The international order associated to a SOC (only available for SOC).

.. attribute:: primary_soc

   The primary SOC associated to a PT (only available for PT).
"""
  
  def __init__(self, code):
    db_cursor.execute(_CONCEPT[pymedtermino.LANGUAGE], (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    self.sql_id, term, self.depth, self.active = r
    
    if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS and not self.active: raise ValueError()
    
    pymedtermino.MultiaxialConcept.__init__(self, code, term)
    
  def _get_meddra_code(self): return int(self.code.split("_")[1])
  meddra_code = property(_get_meddra_code)
  
  def _get_meddra_type(self): return _DEPTH_2_TYPE[self.depth]
  meddra_type = property(_get_meddra_type)
  
  def __getattr__(self, attr):
    if   attr == "parents":
      if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
        db_cursor.execute("SELECT parent FROM IsA, Concept WHERE (child=?) AND (Concept.code = child) AND (Concept.active)", (self.code,))
      else:
        db_cursor.execute("SELECT parent FROM IsA WHERE child=?", (self.code,))
      self.parents = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      return self.parents
      
    elif attr == "children":
      if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
        db_cursor.execute("SELECT child FROM IsA, Concept WHERE (parent=?) AND (Concept.code = child) AND (Concept.active)", (self.code,))
      else:
        db_cursor.execute("SELECT child FROM IsA WHERE parent=?", (self.code,))
      self.children = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      return self.children
      
    elif attr == "relations":
      if   self.depth == 0: return ["meddra_code", "meddra_type", "abbrev", "international_order"]
      elif self.depth == 3: return ["meddra_code", "meddra_type", "primary_soc"]
      return ["meddra_code", "meddra_type"]
      
    elif (attr == "abbrev") and (self.depth == 0):
      db_cursor.execute("SELECT abbrev FROM Concept_SOC WHERE id=?", (self.sql_id,))
      self.abbrev = db_cursor.fetchone()[0]
      return self.abbrev
      
    elif (attr == "international_order") and (self.depth == 0):
      db_cursor.execute("SELECT international_order FROM Concept_SOC WHERE id=?", (self.sql_id,))
      self.international_order = db_cursor.fetchone()[0]
      return self.international_order
      
    elif (attr == "primary_soc") and (self.depth == 3):
      db_cursor.execute("SELECT primary_soc FROM Concept_PT WHERE id=?", (self.sql_id,))
      self.primary_soc = self.terminology[db_cursor.fetchone()[0]]
      return self.primary_soc
    
    elif (attr == "primary_soc") and (self.depth == 4):
      return self.parents[0].primary_soc
    
    elif attr == "terms":
      return [self.term]
      
    raise AttributeError(attr)
  
  def get_translation(self, language):
    db_cursor.execute("SELECT term_%s FROM Concept WHERE code=?" % language, (self.code,))
    return db_cursor.fetchone()[0]



MEDDRA = MEDDRA()


_CONCEPT = {}
for lang in MEDDRA.langs:
  _CONCEPT[lang] = "SELECT id, term_%s, depth, active FROM Concept WHERE code=?" % lang

if not pymedtermino.LANGUAGE in _CONCEPT: _CONCEPT[pymedtermino.LANGUAGE] = _CONCEPT["en"]
