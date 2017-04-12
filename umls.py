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

"""
pymedtermino.umls
*****************

PyMedtermino module for UMLS.

.. class:: UMLS_CUI
   
   The UMLS CUI terminology (concepts). See :class:`pymedtermino.Terminology` for common terminology members; only UMLS-specific members are described here.
   
.. class:: UMLS_AUI
   
   The UMLS AUI terminology (atoms). See :class:`pymedtermino.Terminology` for common terminology members; only UMLS-specific members are described here.
   
   .. automethod:: extract_terminology
   
.. class:: UMLS_SRC
   
   The UMLS SRC terminology (source terminology). See :class:`pymedtermino.Terminology` for common terminology members; only UMLS-specific members are described here.

"""

__all__ = ["UMLS_CUI", "UMLS_AUI", "UMLS_SRC", "connect_to_umls_db"]

import sys, os, os.path
import pymedtermino
from pymedtermino import Concepts, _MAPPINGS

_encoding = "latin1"
db = db_cursor = None
def connect_to_umls_db(host, user, password, db_name = "umls", encoding = "latin1"):
  """Connects to an UMLS MySQL database.
This function **must** be called before using UMLS."""
  global db, db_cursor, _encoding
  _encoding = encoding
  
  try: import cymysql as sql_module
  except:
    try: import pymysql as sql_module
    except:
      import MySQLdb as sql_module
  db        = sql_module.connect(host = host, user = user, passwd = password, db = db_name)
  db_cursor = db.cursor()
  
  
class UMLSBase(pymedtermino.Terminology):
  def __init__(self, name, umls_code_attr, original_terminology_name = u"", has_int_code = 0):
    self._original_terminology_name = original_terminology_name
    self._has_int_code              = has_int_code
    self._umls_code_attr            = umls_code_attr
    pymedtermino.Terminology.__init__(self, name)
    
    if not original_terminology_name: # Whole MetaThesaurus
      self._SEARCH_QUERY   = "SELECT DISTINCT " + umls_code_attr + " FROM MRCONSO WHERE STR LIKE %s"
      self._SUPPRESS_QUERY = "SELECT DISTINCT SUPPRESS FROM MRCONSO WHERE " + umls_code_attr + "=%s"
      self._GET_STR_QUERY  = "SELECT STR FROM MRCONSO WHERE " + umls_code_attr + "=%s"
      self._PARENT_QUERY   = "SELECT DISTINCT " + umls_code_attr + "1 FROM MRREL WHERE " + umls_code_attr + "2='%s' AND REL='CHD'"
      self._CHILDREN_QUERY = "SELECT DISTINCT " + umls_code_attr + "1 FROM MRREL WHERE " + umls_code_attr + "2='%s' AND REL='PAR'"
      self._ORIG_QUERY     = "SELECT DISTINCT SAB FROM MRCONSO WHERE " + umls_code_attr + "=%s"
      self._DEF_QUERY      = "SELECT SAB, DEF FROM MRDEF WHERE " + umls_code_attr + "='%s'"
      self._REL1_QUERY     = "SELECT DISTINCT REL, RELA FROM MRREL WHERE " + umls_code_attr + "2='%s'"
      self._REL2_QUERY     = "SELECT DISTINCT REL, RELA FROM MRREL WHERE " + umls_code_attr + "1='%s'"
      self._INV_REL_QUERY  = "SELECT DISTINCT " + umls_code_attr + "2 FROM MRREL WHERE " + umls_code_attr + "1='%s' AND (REL='%s' OR RELA='%s')"
      self._GET_REL_QUERY  = "SELECT DISTINCT " + umls_code_attr + "1 FROM MRREL WHERE " + umls_code_attr + "2='%s' AND (REL='%s' OR RELA='%s')"
      self._TRANS_QUERY    = "SELECT STR FROM MRCONSO WHERE " + umls_code_attr + "=%s AND LAT=%s ORDER BY ISPREF DESC"
      self._TRANS2_QUERY   = "SELECT DISTINCT STR FROM MRCONSO WHERE " + umls_code_attr + "=%s AND LAT=%s"
      if umls_code_attr == "CUI":
        self._ATTR_QUERY   = "SELECT DISTINCT ATN FROM MRSAT WHERE CUI='%s'"
        self._GET_ATTR_QUERY = "SELECT DISTINCT ATV FROM MRSAT WHERE CUI='%s' AND ATN='%s'"
      else:
        self._ATTR_QUERY   = "SELECT DISTINCT ATN FROM MRSAT WHERE METAUI='%s'"
        self._GET_ATTR_QUERY = "SELECT DISTINCT ATV FROM MRSAT WHERE METAUI='%s' AND ATN='%s'"
        
    else: # An extracted terminology
      if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
        self._GET_UI_QUERY = "SELECT AUI FROM MRCONSO WHERE CODE=%s AND SAB='" + original_terminology_name + "' AND (SUPPRESS in ('', 'N'))"
      else:
        self._GET_UI_QUERY = "SELECT AUI FROM MRCONSO WHERE CODE=%s AND SAB='" + original_terminology_name + "'"
      self._SEARCH_QUERY   = "SELECT DISTINCT AUI FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND STR LIKE %s"
      self._SUPPRESS_QUERY = "SELECT DISTINCT SUPPRESS FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND AUI=%s"
      self._GET_CODE_QUERY = "SELECT DISTINCT CODE FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND AUI=%s"
      self._GET_CODE2_QUERY= "SELECT DISTINCT CODE FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND CUI=%s"
      self._GET_STR_QUERY  = "SELECT STR FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND CODE=%s"
      self._PARENT_QUERY   = "SELECT DISTINCT AUI1 FROM MRREL WHERE SAB='" + original_terminology_name + "' AND AUI2 IN %s AND REL='CHD'"
      self._CHILDREN_QUERY = "SELECT DISTINCT AUI1 FROM MRREL WHERE SAB='" + original_terminology_name + "' AND AUI2 IN %s AND REL='PAR'"
      self._DEF_QUERY      = "SELECT SAB, DEF FROM MRDEF WHERE SAB='" + original_terminology_name + "' AND AUI in %s"
      self._REL1_QUERY     = "SELECT DISTINCT REL, RELA FROM MRREL WHERE SAB='" + original_terminology_name + "' AND AUI2 IN %s"
      self._REL2_QUERY     = "SELECT DISTINCT REL, RELA FROM MRREL WHERE SAB='" + original_terminology_name + "' AND AUI1 IN %s"
      self._INV_REL_QUERY  = "SELECT DISTINCT AUI2 FROM MRREL WHERE SAB='" + original_terminology_name + "' AND AUI1 IN %s AND (REL='%s' OR RELA='%s')"
      self._GET_REL_QUERY  = "SELECT DISTINCT AUI1 FROM MRREL WHERE SAB='" + original_terminology_name + "' AND AUI2 IN %s AND (REL='%s' OR RELA='%s')"
      self._TRANS_QUERY    = "SELECT STR FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND CODE=%s AND LAT=%s AND ISPREF='Y'"
      self._TRANS2_QUERY   = "SELECT DISTINCT STR FROM MRCONSO WHERE SAB='" + original_terminology_name + "' AND CODE=%s AND LAT=%s"
      self._ATTR_QUERY     = "SELECT DISTINCT ATN FROM MRSAT WHERE METAUI IN %s"
      self._GET_ATTR_QUERY = "SELECT DISTINCT ATV FROM MRSAT WHERE SAB='" + original_terminology_name + "' AND METAUI IN %s AND ATN='%s'"
      
      
  def _create_Concept(self):
    if self._has_int_code:
      class MyConcept(UMLSConcept, pymedtermino._IntCodeConcept): pass
    else:
      class MyConcept(UMLSConcept, pymedtermino._StringCodeConcept): pass
    return MyConcept
  
  def _concepts_from_uis(self, uis):
    l = []
    if not self._original_terminology_name:
      for (ui,) in uis:
        concept = self.get(ui)
        if concept: l.append(concept)
        
    else:
      for (ui,) in uis:
        db_cursor.execute(self._GET_CODE_QUERY, (ui,))
        r = db_cursor.fetchall()
        for (code,) in r:
          concept = self.get(code)
          if concept: l.append(concept)
    return l
  
  def search(self, text):
    text = text.replace("*", "%")
    #raise NotImplementedError()
    db_cursor.execute(self._SEARCH_QUERY, (text,))
    #return [self[code] for (code,) in db_cursor.fetchall()]
    return self._concepts_from_uis(db_cursor.fetchall())
  

class UMLS_CUI(UMLSBase):
  def __init__(self): UMLSBase.__init__(self, "UMLS_CUI", "CUI", u"", 0)
    
class UMLS_AUI(UMLSBase):
  def __init__(self): UMLSBase.__init__(self, "UMLS_AUI", "AUI", u"", 0)
  
  def extract_terminology(self, original_terminology_name, has_int_code = 0):
    """Extract a terminology from UMLS.

:param original_terminology_name: the name of the terminology in UMLS (see UMLS docs).
:param has_int_code: True if the source terminology uses integer code (in this case, PyMedtermino will accept both integer and string as code).
:returns: a new terminology, that uses the source codes (and not UMLS AUI codes)."""
    extracted_terminology = UMLSExtractedTerminology("UMLS_%s" % original_terminology_name, "AUI", original_terminology_name, has_int_code)
    ExtractedTerminology_2_UMLS_AUI_Mapping(extracted_terminology, UMLS_AUI).register()
    ExtractedTerminology_2_UMLS_CUI_Mapping(extracted_terminology, UMLS_CUI).register()
    UMLS_AUI_2_ExtractedTerminology_Mapping(UMLS_AUI, extracted_terminology).register()
    UMLS_CUI_2_ExtractedTerminology_Mapping(UMLS_CUI, extracted_terminology).register()
    if   original_terminology_name == "SNOMEDCT":
      try: from pymedtermino.snomedct import SNOMEDCT; ok = 1
      except: ok = 0
      if ok:
        pymedtermino.SameCodeMapping(extracted_terminology, SNOMEDCT).register()
        pymedtermino.SameCodeMapping(SNOMEDCT, extracted_terminology).register()
        (SNOMEDCT >> extracted_terminology >> UMLS_AUI).register()
        (SNOMEDCT >> extracted_terminology >> UMLS_CUI).register()
        (UMLS_AUI >> extracted_terminology >> SNOMEDCT).register()
        (UMLS_CUI >> extracted_terminology >> SNOMEDCT).register()
    elif original_terminology_name == "ICD10":
      try: from pymedtermino.icd10 import ICD10; ok = 1
      except: ok = 0
      if ok:
        ICD10SameCodeMapping(extracted_terminology, ICD10, 1).register()
        ICD10SameCodeMapping(ICD10, extracted_terminology, 0).register()
        (ICD10    >> extracted_terminology >> UMLS_AUI).register()
        (ICD10    >> extracted_terminology >> UMLS_CUI).register()
        (UMLS_AUI >> extracted_terminology >> ICD10   ).register()
        (UMLS_CUI >> extracted_terminology >> ICD10   ).register()
    elif original_terminology_name.startswith("MDR"): # MDR, MDRFRE,...
      try: from pymedtermino.meddra import MEDDRA; ok = 1
      except: ok = 0
      if ok:
        pymedtermino.SameCodeMapping(extracted_terminology, MEDDRA).register()
        pymedtermino.SameCodeMapping(MEDDRA, extracted_terminology).register()
        (MEDDRA   >> extracted_terminology >> UMLS_AUI).register()
        (MEDDRA   >> extracted_terminology >> UMLS_CUI).register()
        (UMLS_AUI >> extracted_terminology >> MEDDRA  ).register()
        (UMLS_CUI >> extracted_terminology >> MEDDRA  ).register()
        
    return extracted_terminology
  
class UMLSExtractedTerminology(UMLSBase):
  def first_levels(self):
    source          = tuple(UMLS_SRC["V-%s" % self._original_terminology_name] >> UMLS_CUI)[0]
    sources_in_self = source >> UMLS_AUI >> self
    if sources_in_self: return list(sources_in_self)
    
    roots = Concepts(source.children) >> UMLS_AUI >> self
    return list(root for root in roots if not root.parents)
    
  def _concepts_from_cui(self, cui):
    l = []
    db_cursor.execute(self._GET_CODE2_QUERY, (cui,))
    r = db_cursor.fetchall()
    for (code,) in r:
      concept = self.get(code)
      if concept: l.append(concept)
    return l
  
  def __rshift__(origin, destination):
    mapping = _MAPPINGS.get((origin, destination))
    if mapping is None:
      if isinstance(destination, UMLSExtractedTerminology):
        mapping = ExtractedTerminology_2_ExtractedTerminology_Mapping(origin, destination)
        mapping.register()
      else:
        raise ValueError("No mapping available or loaded between %s and %s!" % (origin, destination))
    return mapping


class UMLSConcept(pymedtermino.CycleSafeMultiaxialConcept):
  """A UMLS concept. See :class:`pymedtermino.Concept` for common terminology members; only UMLS-specific members are described here.

.. attribute:: original_terminologies
   
   The name of the terminology this concept comes from.

.. attribute:: definitions
   
   The concept's definitions (if available); in a dict mapping original terminology names to the definition in these terminologies.

.. attribute:: attributes

.. attribute:: active
   
   True if this concept is still active in UMLS; False if it has been removed / suppressed.

Additional attributes are available for relations, and are listed in the :attr:`relations <pymedtermino.Concept.relations>` attribute.
"""
  def __init__(self, code):
    if not self.terminology._original_terminology_name:
      if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
        db_cursor.execute(self.terminology._SUPPRESS_QUERY, (str(code),))
        suppresss = set(i[0] for i in db_cursor.fetchall())
        if (not "N" in suppresss) and (not "" in suppresss): raise ValueError("%s:%s is a suppressed concept!" % (self.terminology.name, code))
      self._uis     = [code]
      self._sql_uis = "%s" % code.replace("'", "")
      
    else:
      db_cursor.execute(self.terminology._GET_UI_QUERY, (str(code),))
      r = db_cursor.fetchall()
      if not r: raise ValueError()
      self._uis     = [i for (i,) in r]
      self._sql_uis = "(%s)" % (", ".join("'%s'" % ui.replace("'", "") for ui in self._uis))
      
    pymedtermino.MultiaxialConcept.__init__(self, code, None)
    
  if sys.version[0] == "2":
    def __unicode__(self): return u'%s[u"%s"]  # %s (%s)\n' % (self.terminology.name, self.code, self.term.replace(u"\n", u" "), u", ".join(self.original_terminologies))
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u'%s[u"%s"]  # %s (%s)\n' % (self.terminology.name, self.code, self.term.replace(u"\n", u" "), u", ".join(self.original_terminologies))
    
  def __getattr__(self, attr):
    if   attr == "parents":
      db_cursor.execute(self.terminology._PARENT_QUERY % self._sql_uis)
      self.parents = self.terminology._concepts_from_uis(db_cursor.fetchall())
      return self.parents
    
    elif attr == "children":
      db_cursor.execute(self.terminology._CHILDREN_QUERY % self._sql_uis)
      self.children = self.terminology._concepts_from_uis(db_cursor.fetchall())
      return self.children
    
    elif attr == "term":
      db_cursor.execute(self.terminology._GET_STR_QUERY + " AND LAT=%s ORDER BY ISPREF DESC", (str(self.code), _iso2umls_lang[pymedtermino.LANGUAGE]))
      r = db_cursor.fetchone()
      if not r:
        if pymedtermino.LANGUAGE != "en":
          db_cursor.execute(self.terminology._GET_STR_QUERY + " AND LAT=%s ORDER BY ISPREF DESC", (str(self.code), "ENG"))
          r = db_cursor.fetchone()
        if not r:
          db_cursor.execute(self.terminology._GET_STR_QUERY + " ORDER BY ISPREF DESC", (str(self.code),))
          r = db_cursor.fetchone()
          if not r:
            raise ValueError()
      if hasattr(r, "decode"):
        try:
          r = r[0].decode(_encoding)
        except:
          r = r[0]
          print("PyMedTermino * WARNING : Cannot decode UMLS terms for %s!" % code)
      else: r = r[0]
      self.term = r
      return r
        
    elif attr == "terms":
      self.terms = self.get_translations(pymedtermino.LANGUAGE)
      return self.terms
    
    elif attr == "original_terminologies":
      if self.terminology._original_terminology_name: return set([self.terminology._original_terminology_name])
      db_cursor.execute(self.terminology._ORIG_QUERY, (str(self.code),))
      self.original_terminologies = set(sab for (sab,) in db_cursor.fetchall())
      return self.original_terminologies
    
    elif attr == "definitions":
      db_cursor.execute(self.terminology._DEF_QUERY % self._sql_uis)
      self.definitions = { sab : definition for sab, definition in db_cursor.fetchall()}
      return self.definitions
    
    elif attr == "relations":
      self.relations = set()
      db_cursor.execute(self.terminology._REL1_QUERY % self._sql_uis)
      for (rel, rela) in db_cursor.fetchall():
        if (rel != "PAR") and (rel != "CHD"):
          self.relations.add(rel)
          self.relations.add(rela)
      db_cursor.execute(self.terminology._REL2_QUERY % self._sql_uis)
      for (rel, rela) in db_cursor.fetchall():
        if (rel != "PAR") and (rel != "CHD"):
          self.relations.add("INVERSE_%s" % rel)
          self.relations.add("INVERSE_%s" % rela)
      return self.relations
    
    elif attr == "attributes":
      db_cursor.execute(self.terminology._ATTR_QUERY % self._sql_uis)
      self.attributes = set(attr for (attr,) in db_cursor.fetchall())
      return self.attributes
    
    elif attr == "suppressed":
      db_cursor.execute(self.terminology._SUPPRESS_QUERY, (str(self.code),))
      suppresss = set(i[0] for i in db_cursor.fetchall())
      if (not "N" in suppresss) and (not "" in suppresss): return 1
      return 0
    
    elif attr == "active": return not self.suppressed
    
    elif attr.startswith(u"INVERSE_"):
      rel = attr[8:].replace("'", "")
      db_cursor.execute(self.terminology._INV_REL_QUERY % (self._sql_uis, rel, rel))
      l = self.terminology._concepts_from_uis(db_cursor.fetchall())
      setattr(self, attr, l)
      return l
    
    elif attr in self.relations:
      rel = attr.replace("'", "")
      db_cursor.execute(self.terminology._GET_REL_QUERY % (self._sql_uis, rel, rel))
      l = self.terminology._concepts_from_uis(db_cursor.fetchall())
      setattr(self, attr, l)
      return l
    
    elif attr in self.attributes:
      attr = attr.replace("'", "")
      db_cursor.execute(self.terminology._GET_ATTR_QUERY % (self._sql_uis, attr))
      l = [value for (value,) in db_cursor.fetchall()]
      setattr(self, attr, l)
      return l
    
    raise AttributeError(attr)
  
  def get_translation(self, language):
    db_cursor.execute(self.terminology._TRANS_QUERY, (str(self.code), _iso2umls_lang[language]))
    r = db_cursor.fetchone()
    if r: return r[0]
    
  def get_translations(self, language):
    db_cursor.execute(self.terminology._TRANS2_QUERY, (str(self.code), _iso2umls_lang[language]))
    return [e[0] for e in db_cursor.fetchall()]
  

class CUI_AUI_Mapping(pymedtermino.Mapping):
  def __init__(self, terminology1, terminology2):
    pymedtermino.Mapping.__init__(self, terminology1, terminology2)
    self._MAP_QUERY = "SELECT DISTINCT " + terminology2._umls_code_attr + " FROM MRCONSO WHERE " + terminology1._umls_code_attr + "=%s"
    if terminology1._original_terminology_name:
      self._MAP_QUERY += " AND SAB='" + original_terminology_name + "'"
      
  def _create_reverse_mapping(self): return CUI_AUI_Mapping(self.terminology2, self.terminology1)
  def map_concepts(self, concepts):
    r = Concepts()
    for concept in concepts:
      db_cursor.execute(self._MAP_QUERY, (str(concept.code),))
      for (code,) in db_cursor.fetchall():
        concept = self.terminology2.get(code) # get() because it might be a suppressed concept
        if concept: r.add(concept)
    return r

class ExtractedTerminology_2_UMLS_AUI_Mapping(pymedtermino.Mapping):
  def _create_reverse_mapping(self): return UMLS_2_ExtractedTerminology_Mapping(self.terminology2, self.terminology1)
  def map_concepts(self, concepts):
    return Concepts([self.terminology2[ui] for concept in concepts for ui in concept._uis])

class ExtractedTerminology_2_UMLS_CUI_Mapping(pymedtermino.Mapping):
  def _create_reverse_mapping(self): return UMLS_CUI_2_ExtractedTerminology_Mapping(self.terminology2, self.terminology1)
  def map_concepts(self, concepts):
    r = Concepts()
    for concept in concepts:
      db_cursor.execute("SELECT DISTINCT CUI FROM MRCONSO WHERE AUI IN %s"  % concept._sql_uis)
      for (code,) in db_cursor.fetchall():
        concept = self.terminology2.get(code) # get() because it might be a suppressed concept
        if concept: r.add(concept)
    return r

class UMLS_AUI_2_ExtractedTerminology_Mapping(pymedtermino.Mapping):
  def _create_reverse_mapping(self): return ExtractedTerminology_2_UMLS_Mapping(self.terminology2, self.terminology1)
  
  def _get_concept_parents(self, concept): return concept.parents
  
  def map_concepts(self, concepts, cumulated_concepts = None):
    r                          = Concepts()
    cumulated_concepts         = cumulated_concepts or set(concepts)
    concepts_partially_matched = Concepts(concepts)
    
    for concept in tuple(concepts_partially_matched):
      corresponding_concepts = self.terminology2._concepts_from_uis([(concept.code,)])
      if corresponding_concepts:
        for c in corresponding_concepts: r.add(c)
        concepts_partially_matched.discard(concept)
        
    if concepts_partially_matched:
      concepts = Concepts(sum([self._get_concept_parents(concept) for concept in concepts_partially_matched], []))
      
      concepts = concepts - cumulated_concepts
      if concepts:
      #if concepts and not concepts.issubset(cumulated_concepts):
        cumulated_concepts.update(concepts)
        r.update(self.map_concepts(concepts, cumulated_concepts))
        
    return r
  
class UMLS_CUI_2_ExtractedTerminology_Mapping(pymedtermino.Mapping):
  def _create_reverse_mapping(self): return ExtractedTerminology_2_UMLS_CUI_Mapping(self.terminology2, self.terminology1)
  
  def _get_concept_parents(self, concept): return concept.parents
  
  def map_concepts(self, concepts, cumulated_concepts = None):
    r                          = Concepts()
    cumulated_concepts         = cumulated_concepts or set(concepts)
    concepts_partially_matched = Concepts(concepts)
    
    for concept in tuple(concepts_partially_matched):
      corresponding_concepts = self.terminology2._concepts_from_cui(concept.code)
      if corresponding_concepts:
        for c in corresponding_concepts: r.add(c)
        concepts_partially_matched.discard(concept)
        
    if concepts_partially_matched:
      concepts = Concepts(sum([self._get_concept_parents(concept) for concept in concepts_partially_matched], []))
      concepts = concepts - cumulated_concepts
      if concepts:
        cumulated_concepts.update(concepts)
        r.update(self.map_concepts(concepts, cumulated_concepts))
    return r
  
class ExtractedTerminology_2_ExtractedTerminology_Mapping(pymedtermino.Mapping):
  def __init__(self, terminology1, terminology2):
    pymedtermino.Mapping.__init__(self, terminology1, terminology2)
    self._MAP_QUERY = "SELECT DISTINCT dest.CODE FROM MRCONSO orig, MRCONSO dest WHERE orig.AUI IN %s AND dest.CUI=orig.CUI and dest.SAB='" + terminology2._original_terminology_name + "'"
    if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS: self._MAP_QUERY += " AND (dest.SUPPRESS in ('', 'N'))"
    self._umls_mapping = _find_umls_mapping(terminology1, terminology2)
    
  def _create_reverse_mapping(self): return ExtractedTerminology_2_ExtractedTerminology_Mapping(self.terminology2, self.terminology1)
  
  def _get_concept_parents(self, concept): return concept.parents
  
  def map_concepts(self, concepts, cumulated_concepts = None):
    r                          = Concepts()
    cumulated_concepts         = cumulated_concepts or set(concepts)
    concepts_partially_matched = Concepts(concepts)
    
    for concept in tuple(concepts_partially_matched):
      r2 = None
      if self._umls_mapping: r2 = self._umls_mapping.map_concept(concept)
      if r2:
        r.update(r2)
        concepts_partially_matched.discard(concept)
      else:
        db_cursor.execute(self._MAP_QUERY % concept._sql_uis)
        for (code,) in db_cursor.fetchall():
          c = self.terminology2.get(code)
          if c:
            r.add(c)
            concepts_partially_matched.discard(concept)
            
    if concepts_partially_matched:
      concepts = Concepts(sum([self._get_concept_parents(concept) for concept in concepts_partially_matched], []))
      
      concepts = concepts - cumulated_concepts
      if concepts:
        cumulated_concepts.update(concepts)
        r.update(self.map_concepts(concepts, cumulated_concepts))
        
    return r


class _UMLSMapping(pymedtermino.Mapping):
  def __init__(self, terminology1, terminology2, mapsetcui, reversed = 0):
    pymedtermino.Mapping.__init__(self, terminology1, terminology2)
    self.mapsetcui = mapsetcui
    self.reversed  = reversed
    if reversed: self._MAP_QUERY = "SELECT FROMEXPR FROM MRMAP WHERE MAPSETCUI = '%s' AND TOEXPR = '%%s'" % mapsetcui
    else:        self._MAP_QUERY = "SELECT TOEXPR FROM MRMAP WHERE MAPSETCUI = '%s' AND FROMEXPR = '%%s'" % mapsetcui
    
  def __repr__(self): return "_UMLSMapping(%s, %s, %s, %s)" % (self.terminology1, self.terminology2, self.mapsetcui, self.reversed)
  
  def _create_reverse_mapping(self): return _UMLSMapping(self.terminology2, self.terminology1, self.mapsetcui, not(self.reversed))
  
  def map_concept(self, concept):
    r = Concepts()
    db_cursor.execute(self._MAP_QUERY % concept.code)
    for (code,) in db_cursor.fetchall():
      c = self.terminology2.get(code)
      if c: r.add(c)
    return r
  
  def map_concepts(self, concepts):
    r = Concepts()
    for concept in concepts:
      db_cursor.execute(self._MAP_QUERY % concept.code)
      for (code,) in db_cursor.fetchall():
        c = self.terminology2.get(code)
        if c: r.add(c)
    return r


_ICD10_CHAPTER_MAPPING = {
  "I"     : "A00-B99.9",
  "II"    : "C00-D48.9",
  "III"   : "D50-D89.9",
  "IV"    : "E00-E90.9",
  "V"     : "F00-F99.9",
  "VI"    : "G00-G99.9",
  "VII"   : "H00-H59.9",
  "VIII"  : "H60-H95.9",
  "IX"    : "I00-I99.9",
  "X"     : "J00-J99.9",
  "XI"    : "K00-K93.9",
  "XII"   : "L00-L99.9",
  "XIII"  : "M00-M99.9",
  "XIV"   : "N00-N99.9",
  "XV"    : "O00-O99.9",
  "XVI"   : "P00-P96.9",
  "XVII"  : "Q00-Q99.9",
  "XVIII" : "R00-R99.9",
  "XIX"   : "S00-T98.9",
  "XX"    : "V01-Y98.9",
  "XXI"   : "Z00-Z99.9",
  "XXII"  : "U00-U99.9",
  }
_ICD10_CHAPTER_MAPPING_REVERSE = { v : k for (k, v) in _ICD10_CHAPTER_MAPPING.items() }

class ICD10SameCodeMapping(pymedtermino.SameCodeMapping):
  # UMLS uses code like "K70-K77.9" while ICD10 uses code like "K70-K77"...!
  def __init__(self, terminology1, terminology2, reversed = 0):
    self.reversed = reversed
    pymedtermino.SameCodeMapping.__init__(self, terminology1, terminology2)
    
  def _create_reverse_mapping(self): return ICD10SameCodeMapping(self.terminology2, self.terminology1, reversed = 1)
  
  def map_concepts(self, concepts):
    r = Concepts()
    for concept in concepts:
      try:
        code = concept.english_code
        if       self.reversed  and (code in _ICD10_CHAPTER_MAPPING_REVERSE): code = _ICD10_CHAPTER_MAPPING_REVERSE[code]
        elif not(self.reversed) and (code in _ICD10_CHAPTER_MAPPING        ): code = _ICD10_CHAPTER_MAPPING        [code]
        elif "-" in code:
          if self.reversed:
            if code.endswith(".9"): code = code[:-2]
          else: code += ".9"
        c = self.terminology2[code]
        r.add(c)
      except ValueError: pass
    return r
  
  
def _find_umls_mapping(terminology1, terminology2, try_reverse = 1):
  db_cursor.execute("SELECT a.CUI FROM MRSAT a, MRSAT b WHERE a.ATN = 'FROMRSAB' AND a.ATV = %s AND b.ATN = 'TORSAB' AND b.ATV=%s AND a.CUI = b.CUI", (terminology1._original_terminology_name, terminology2._original_terminology_name))
  mapsetcuis = db_cursor.fetchall()
  if mapsetcuis: return _UMLSMapping(terminology1, terminology2, mapsetcuis[0][0], 0)
  if try_reverse:
    umls_mapping = _find_umls_mapping(terminology2, terminology1, 0)
    if umls_mapping: return umls_mapping._create_reverse_mapping()
  
  

_iso2umls_lang = { "aa" : "AAR", "ab" : "ABK", "af" : "AFR", "ak" : "AKA", "sq" : "ALB", "am" : "AMH", "ar" : "ARA", "an" : "ARG", "hy" : "ARM", "as" : "ASM", "av" : "AVA", "ae" : "AVE", "ay" : "AYM", "az" : "AZE", "ba" : "BAK", "bm" : "BAM", "eu" : "BAQ", "be" : "BEL", "bn" : "BEN", "bh" : "BIH", "bi" : "BIS", "bs" : "BOS", "br" : "BRE", "bg" : "BUL", "my" : "BUR", "ca" : "CAT", "ch" : "CHA", "ce" : "CHE", "zh" : "CHI", "cu" : "CHU", "cv" : "CHV", "kw" : "COR", "co" : "COS", "cr" : "CRE", "cs" : "CZE", "da" : "DAN", "dv" : "DIV", "nl" : "DUT", "dz" : "DZO", "en" : "ENG", "eo" : "EPO", "et" : "EST", "ee" : "EWE", "fo" : "FAO", "fj" : "FIJ", "fi" : "FIN", "fr" : "FRE", "fy" : "FRY", "ff" : "FUL", "ka" : "GEO", "de" : "GER", "gd" : "GLA", "ga" : "GLE", "gl" : "GLG", "gv" : "GLV", "el" : "GRE", "gn" : "GRN", "gu" : "GUJ", "ht" : "HAT", "ha" : "HAU", "he" : "HEB", "hz" : "HER", "hi" : "HIN", "ho" : "HMO", "hr" : "HRV", "hu" : "HUN", "ig" : "IBO", "is" : "ICE", "io" : "IDO", "ii" : "III", "iu" : "IKU", "ie" : "ILE", "ia" : "INA", "id" : "IND", "ik" : "IPK", "it" : "ITA", "jv" : "JAV",  "ja" : "JPN",  "kl" : "KAL",  "kn" : "KAN", "ks" : "KAS",  "kr" : "KAU",  "kk" : "KAZ",  "km" : "KHM",  "ki" : "KIK",  "rw" : "KIN",  "ky" : "KIR",  "kv" : "KOM",  "kg" : "KON",  "ko" : "KOR",  "kj" : "KUA",  "ku" : "KUR",  "lo" : "LAO",  "la" : "LAT",  "lv" : "LAV",  "li" : "LIM",  "ln" : "LIN",  "lt" : "LIT",  "lb" : "LTZ",  "lu" : "LUB",  "lg" : "LUG",  "mk" : "MAC",  "mh" : "MAH",  "ml" : "MAL",  "mi" : "MAO",  "mr" : "MAR",  "ms" : "MAY",  "mg" : "MLG",  "mt" : "MLT",  "mo" : "MOL",  "mn" : "MON",  "na" : "NAU",  "nv" : "NAV",  "nr" : "NBL",  "nd" : "NDE",  "ng" : "NDO",  "ne" : "NEP",  "nn" : "NNO",  "nb" : "NOB",  "no" : "NOR",  "ny" : "NYA",  "oc" : "OCI",  "oj" : "OJI",  "or" : "ORI",  "om" : "ORM",  "os" : "OSS",  "pa" : "PAN",  "fa" : "PER",  "pi" : "PLI",  "pl" : "POL",  "pt" : "POR",  "ps" : "PUS",  "qu" : "QUE",  "rm" : "ROH",  "ro" : "RUM",  "rn" : "RUN",  "ru" : "RUS",  "sg" : "SAG",  "sa" : "SAN",  "si" : "SIN",  "sk" : "SLO",  "sl" : "SLV",  "se" : "SME",  "sm" : "SMO",  "sn" : "SNA",  "sd" : "SND",  "so" : "SOM",  "st" : "SOT",  "es" : "SPA",  "sc" : "SRD",  "sr" : "SRP",  "ss" : "SSW",  "su" : "SUN",  "sw" : "SWA",  "sv" : "SWE",  "ty" : "TAH",  "ta" : "TAM",  "tt" : "TAT",  "te" : "TEL",  "tg" : "TGK",  "tl" : "TGL",  "th" : "THA",  "bo" : "TIB",  "ti" : "TIR",  "to" : "TON",  "tn" : "TSN",  "ts" : "TSO",  "tk" : "TUK",  "tr" : "TUR",  "tw" : "TWI",  "ug" : "UIG",  "uk" : "UKR",  "ur" : "URD",  "uz" : "UZB",  "ve" : "VEN",  "vi" : "VIE",  "vo" : "VOL",  "cy" : "WEL",  "wa" : "WLN",  "wo" : "WOL",  "xh" : "XHO",  "yi" : "YID",  "yo" : "YOR",  "za" : "ZHA",  "zu" : "ZUL" }

UMLS_CUI = UMLS_CUI()
UMLS_AUI = UMLS_AUI()

UMLS_SRC = UMLS_AUI.extract_terminology("SRC", 0)

CUI_AUI_Mapping(UMLS_CUI, UMLS_AUI).register()
CUI_AUI_Mapping(UMLS_AUI, UMLS_CUI).register()

      
# SELECT * FROM MRSAT a, MRSAT b WHERE a.ATN = "FROMRSAB" AND a.ATV = "ICD10" AND b.ATN = "TORSAB" AND b.ATV="ICPC2EENG" AND a.METAUI = b.METAUI
