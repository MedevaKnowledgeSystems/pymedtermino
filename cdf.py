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
pymedtermino.cdf
*******************

PyMedtermino module for CDF (Thériaque French drug database).

.. class:: CDF
   
   The CDF terminology. See :class:`pymedtermino.Terminology` for common terminology members; only CDF-specific members are described here.

   A CDF to ICD10 mapping (from Thériaque) is also provided.
"""

__all__ = ["CDF", "CCH", "CPH", "SAC", "SAU", "GSAC", "connect_to_theriaque_db"]

import sys, os, os.path, psycopg2
import pymedtermino

db = db_cursor = None
def connect_to_theriaque_db(host = "", port = "", user = "theriaque", password = "", db_name = "theriaque", encoding = "latin1"):
  """Connects to a Thériaque PostgreSQL database.
This function **must** be called before using CDF. Default values should be OK for a local Theriaque installation with PostgresQL."""
  global db, db_cursor
  db        = psycopg2.connect(host = host, port = port, database = db_name, user = user, password = password)
  db_cursor = db.cursor()
  
  import atexit
  atexit.register(db.close)
  
  
class CDF(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "CDF")
    
  def _create_Concept(self): return CDFConcept
  
  def first_levels(self, numero = None):
    if numero:
      db_cursor.execute("SELECT cdf_numero_pk, cdf_code_pk FROM cdf_codif WHERE cdf_numero_pk = %s", (numero,))
      for (numero, code) in db_cursor.fetchall():
        concept = self["%s_%s" % (numero, code)]
        for p in concept.parents:
          if p.code.startswith(numero): break
        else: yield concept
    else:
      db_cursor.execute("SELECT cdf_numero_pk, cdf_code_pk FROM cdf_codif")
      for (numero, code) in db_cursor.fetchall():
        concept = self["%s_%s" % (numero, code)]
        if not concept.parents: yield concept
        
  def all_concepts(self, *args):
    """Retuns a generator for iterating over *all* concepts in the terminology."""
    for root in self.first_levels(*args):
      yield root
      for concept in root.descendants():
        yield concept
        
  def search(self, text):
    text = text.upper().replace("*", "%")
    #db_cursor.execute("SELECT DISTINCT conceptId FROM Description WHERE term LIKE ?", ("%%%s%%" % text,))
    db_cursor.execute("SELECT cdf_numero_pk, cdf_code_pk FROM cdf_codif WHERE cdf_nom LIKE %s", (text,))
    r = db_cursor.fetchall()
    l = []
    for (numero, code) in r:
      try: l.append(self["%s_%s" % (numero, code)])
      except ValueError: pass
    return l

_HIERARCHICAL_CDF_CLASSIFICATONS = { "CS" }

class CDFConcept(pymedtermino.MultiaxialConcept, pymedtermino._StringCodeConcept):
  """A CDF concept. See :class:`pymedtermino.Concept` for common terminology members; only CDF-specific members are described here.

Additional attributes are available for relations, and are listed in the :attr:`relations <pymedtermino.Concept.relations>` attribute.

.. attribute:: cdf_numero

   The original CDF "numero" code.

.. attribute:: cdf_code

   The original CDF "code".
"""
  
  def __init__(self, code):
    self.cdf_numero, self.cdf_code = code.split("_")
    #db_cursor.execute("SELECT cdf_nom FROM cdf_codif WHERE (cdf_numero_pk = ?) AND (cdf_code_pk = ?)", (self.cdf_numero, self.cdf_code))
    db_cursor.execute("SELECT cdf_nom FROM cdf_codif WHERE cdf_numero_pk = %s AND cdf_code_pk = %s", (self.cdf_numero, self.cdf_code))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    
    pymedtermino.MultiaxialConcept.__init__(self, code, r[0])
    
  def __getattr__(self, attr):
    if   attr == "parents":
      db_cursor.execute("SELECT cdfpf_numerop_fk_pk, cdfpf_codep_fk_pk FROM cdfpf_lien_cdf_pere_fils WHERE (cdfpf_numerof_fk_pk = %s) AND (cdfpf_codef_fk_pk = %s)", (self.cdf_numero, self.cdf_code))
      self.parents = [self.terminology["%s_%s" % (numero, code)] for (numero, code) in db_cursor.fetchall()]
      if (self.cdf_numero in _HIERARCHICAL_CDF_CLASSIFICATONS) and (len(self.cdf_code) > 1):
        self.parents.insert(0, self.terminology[self.code[:-1]])
      return self.parents
      
    elif attr == "children":
      db_cursor.execute("SELECT cdfpf_numerof_fk_pk, cdfpf_codef_fk_pk FROM cdfpf_lien_cdf_pere_fils WHERE (cdfpf_numerop_fk_pk = %s) AND (cdfpf_codep_fk_pk = %s) ORDER BY cdfpf_numord", (self.cdf_numero, self.cdf_code))
      self.children = [self.terminology["%s_%s" % (numero, code)] for (numero, code) in db_cursor.fetchall()]
      if (self.cdf_numero in _HIERARCHICAL_CDF_CLASSIFICATONS):
        db_cursor.execute("SELECT cdf_code_pk FROM cdf_codif WHERE (cdf_numero_pk = %s) AND (cdf_code_pk LIKE %s)", (self.cdf_numero, "%s_" % self.cdf_code))
        self.children = [self.terminology["%s_%s" % (self.cdf_numero, code)] for (code,) in db_cursor.fetchall()] + self.children
      return self.children
    
    elif attr == "relations": return []
      
    elif attr == "terms": return [self.term]
      
    raise AttributeError(attr)

CDF = CDF()


try:    from pymedtermino.icd10 import ICD10
except: ICD10 = None

if ICD10:
  class CDF_2_ICD10_Mapping(pymedtermino.Mapping):
    def __init__(self):
      pymedtermino.Mapping.__init__(self, CDF, ICD10)
      
    def _create_reverse_mapping(self): return ICD10_2_CDF_Mapping()
    
    def map_concepts(self, concepts):
      r = pymedtermino.Concepts()
      for concept in concepts:
        db_cursor.execute("SELECT cimcdf_cim_code_fk_pk FROM cimcdf_cim10_codif WHERE (cimcdf_cdf_numero_fk_pk = %s) AND (cimcdf_cdf_code_fk_pk = %s)", (concept.cdf_numero, concept.cdf_code))
        for (code,) in db_cursor.fetchall():
          if (not "-" in code) and (len(code) > 3): code = "%s.%s" % (code[:3], code[3:])
          c = self.terminology2.get(code)
          if c: r.add(c)
      return r

  class ICD10_2_CDF_Mapping(pymedtermino.Mapping):
    def __init__(self):
      pymedtermino.Mapping.__init__(self, ICD10, CDF)
      
    def _create_reverse_mapping(self): return CDF_2_ICD10_Mapping()
    
    def map_concepts(self, concepts):
      r = pymedtermino.Concepts()
      for concept in concepts:
        code = concept.code.replace(".", "")
        db_cursor.execute("SELECT cimcdf_cdf_numero_fk_pk, cimcdf_cdf_code_fk_pk FROM cimcdf_cim10_codif WHERE cimcdf_cim_code_fk_pk = %s", (code,))
        for (numero, code) in db_cursor.fetchall():
          c = self.terminology2.get("%s_%s" % (numero, code))
          if c: r.add(c)
      return r
      
  cdf_2_icd10 = CDF_2_ICD10_Mapping()
  cdf_2_icd10.register()
  icd10_2_cdf = ICD10_2_CDF_Mapping()
  icd10_2_cdf.register()

  

class CCH(pymedtermino.Terminology):
  def __init__(self): pymedtermino.Terminology.__init__(self, "CCH")
    
  def _create_Concept(self): return CCHConcept
  
  def first_levels(self):
    db_cursor.execute("SELECT cch_code_pk FROM cch_classechimique WHERE length(cch_code_pk) = 1")
    for (code,) in db_cursor.fetchall(): yield self[code]
    
  def search(self, text):
    text = text.upper().replace("*", "%")
    db_cursor.execute("SELECT cch_code_pk FROM cch_classechimique WHERE cch_nom LIKE %s", (text,))
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l

class CCHConcept(pymedtermino.MonoaxialConcept, pymedtermino._StringCodeConcept):
  """A CCH (chemical class) concept. See :class:`pymedtermino.Concept` for common terminology members; only CDF-specific members are described here."""
  
  def __init__(self, code):
    db_cursor.execute("SELECT cch_nom, cch_cch_code_fk FROM cch_classechimique WHERE cch_code_pk = %s", (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    pymedtermino.MonoaxialConcept.__init__(self, code, r[0])
    self.parent_code = r[1]
    
  def __getattr__(self, attr):
    if   attr == "parents":
      if self.parent_code: self.parents = [self.terminology[self.parent_code]]
      else:                self.parents = []
      return self.parents
      
    elif attr == "children":
      db_cursor.execute("SELECT cch_code_pk FROM cch_classechimique WHERE cch_cch_code_fk = %s", (self.code,))
      self.children = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      return self.children
    
    elif attr == "relations": return []
    elif attr == "terms":     return [self.term]
      
    raise AttributeError(attr)

CCH = CCH()
  


class CPH(pymedtermino.Terminology):
  def __init__(self): pymedtermino.Terminology.__init__(self, "CPH")
    
  def _create_Concept(self): return CPHConcept
  
  def first_levels(self):
    db_cursor.execute("SELECT cph_code_pk FROM cph_classepharmther WHERE length(cph_code_pk) = 1")
    for (code,) in db_cursor.fetchall(): yield self[code]
    
  def search(self, text):
    text = text.upper().replace("*", "%")
    db_cursor.execute("SELECT cph_code_pk FROM cph_classepharmther WHERE cph_nom LIKE %s", (text,))
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l

class CPHConcept(pymedtermino.MonoaxialConcept, pymedtermino._StringCodeConcept):
  """A CPH (pharmacotherapeutical class) concept. See :class:`pymedtermino.Concept` for common terminology members; only CDF-specific members are described here."""
  
  def __init__(self, code):
    db_cursor.execute("SELECT cph_nom, cph_cph_code_fk FROM cph_classepharmther WHERE cph_code_pk = %s", (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    pymedtermino.MonoaxialConcept.__init__(self, code, r[0])
    self.parent_code = r[1]
    
  def __getattr__(self, attr):
    if   attr == "parents":
      if self.parent_code: self.parents = [self.terminology[self.parent_code]]
      else:                self.parents = []
      return self.parents
      
    elif attr == "children":
      db_cursor.execute("SELECT cph_code_pk FROM cph_classepharmther WHERE cph_cph_code_fk = %s", (self.code,))
      self.children = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      return self.children
    
    elif attr == "relations": return []
    elif attr == "terms":     return [self.term]
      
    raise AttributeError(attr)

CPH = CPH()
  


class FlatlistConcept(pymedtermino.MonoaxialConcept):
  def __getattr__(self, attr):
    if   attr == "parents":   return []
    elif attr == "children":  return []
    elif attr == "relations": return []
    elif attr == "terms":     return [self.term]
    raise AttributeError(attr)

  
class SAC(pymedtermino.Terminology):
  def __init__(self): pymedtermino.Terminology.__init__(self, "SAC")
    
  def _create_Concept(self): return SACConcept
  
  def first_levels(self):
    db_cursor.execute("SELECT sac_code_sq_pk FROM sac_subactive")
    for (code,) in db_cursor.fetchall(): yield self[code]
  all_concepts = first_levels
    
  def search(self, text):
    text = text.upper().replace("*", "%")
    db_cursor.execute("SELECT sac_code_sq_pk FROM sac_subactive WHERE sac_nom LIKE %s", (text,))
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l

class SACConcept(FlatlistConcept, pymedtermino._IntCodeConcept):
  """A SAC (active substance) concept. See :class:`pymedtermino.Concept` for common terminology members; only CDF-specific members are described here."""
  
  def __init__(self, code):
    db_cursor.execute("SELECT sac_nom FROM sac_subactive WHERE sac_code_sq_pk = %s", (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    pymedtermino.MonoaxialConcept.__init__(self, code, r[0])

SAC = SAC()



class SAU(pymedtermino.Terminology):
  def __init__(self): pymedtermino.Terminology.__init__(self, "SAU")
    
  def _create_Concept(self): return SAUConcept
  
  def first_levels(self):
    db_cursor.execute("SELECT sau_code_sq_pk FROM sau_subauxiliaire")
    for (code,) in db_cursor.fetchall(): yield self[code]
  all_concepts = first_levels
    
  def search(self, text):
    text = text.upper().replace("*", "%")
    db_cursor.execute("SELECT sau_code_sq_pk FROM sau_subauxiliaire WHERE sau_nom LIKE %s", (text,))
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l

class SAUConcept(FlatlistConcept, pymedtermino._IntCodeConcept):
  """A SAU (auxiliary substance) concept. See :class:`pymedtermino.Concept` for common terminology members; only CDF-specific members are described here."""
  
  def __init__(self, code):
    db_cursor.execute("SELECT sau_nom FROM sau_subauxiliaire WHERE sau_code_sq_pk = %s", (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    pymedtermino.MonoaxialConcept.__init__(self, code, r[0])

SAU = SAU()



class GSAC(pymedtermino.Terminology):
  def __init__(self): pymedtermino.Terminology.__init__(self, "GSAC")
    
  def _create_Concept(self): return GSACConcept
  
  def first_levels(self):
    db_cursor.execute("SELECT gsac_code_sq_pk FROM gsac_pere_subact")
    for (code,) in db_cursor.fetchall(): yield self[code]
  all_concepts = first_levels
    
  def search(self, text):
    text = text.upper().replace("*", "%")
    db_cursor.execute("SELECT gsac_code_sq_pk FROM gsac_pere_subact WHERE gsac_nom LIKE %s", (text,))
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l

class GSACConcept(FlatlistConcept, pymedtermino._IntCodeConcept):
  """A GSAC (father active substance) concept. See :class:`pymedtermino.Concept` for common terminology members; only CDF-specific members are described here."""
  
  def __init__(self, code):
    db_cursor.execute("SELECT gsac_nom FROM gsac_pere_subact WHERE gsac_code_sq_pk = %s", (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    pymedtermino.MonoaxialConcept.__init__(self, code, r[0])

GSAC = GSAC()



def _create_mapping(table, terminology1, attr1, terminology2, attr2):
  class _Mapping(pymedtermino.Mapping):
    def __init__(self): pymedtermino.Mapping.__init__(self, terminology1, terminology2)

    def _create_reverse_mapping(self): return CCH_2_SAC_Mapping()

    def map_concepts(self, concepts):
      r = pymedtermino.Concepts()
      for concept in concepts:
        db_cursor.execute("SELECT cimcdf_cim_code_fk_pk FROM  WHERE (cimcdf_cdf_numero_fk_pk = %s) AND (cimcdf_cdf_code_fk_pk = %s)", (concept.cdf_numero, concept.cdf_code))
        for (code,) in db_cursor.fetchall():
          if (not "-" in code) and (len(code) > 3): code = "%s.%s" % (code[:3], code[3:])
          c = self.terminology2.get(code)
          if c: r.add(c)
      return r
  


class Theriaque_Mapping(pymedtermino.Mapping):
  def __init__(self, table, terminology1, attr1, terminology2, attr2):
    pymedtermino.Mapping.__init__(self, terminology1, terminology2)
    self.table   = table
    self.attr1   = attr1
    self.attr2   = attr2
    self.request = "SELECT %s FROM %s WHERE %s = %%s" % (attr2, table, attr1)
    
  def _create_reverse_mapping(self): return Theriaque_Mapping(self.table, self.terminology2, self.attr2, self.terminology1, self.attr1)
  
  def map_concepts(self, concepts):
    r = pymedtermino.Concepts()
    for concept in concepts:
      db_cursor.execute(self.request, (concept.code,))
      for (code,) in db_cursor.fetchall():
        c = self.terminology2.get(code)
        if c: r.add(c)
    return r
  
Theriaque_Mapping("saccch_subact_classech", SAC , "saccch_sac_code_fk_pk", CCH , "saccch_cch_code_fk_pk").register()
Theriaque_Mapping("saccch_subact_classech", CCH , "saccch_cch_code_fk_pk", SAC , "saccch_sac_code_fk_pk").register()
Theriaque_Mapping("saccph_subact_classeph", SAC , "saccph_sac_code_fk_pk", CPH , "saccph_cph_code_fk_pk").register()
Theriaque_Mapping("saccph_subact_classeph", CPH , "saccph_cph_code_fk_pk", SAC , "saccph_sac_code_fk_pk").register()
Theriaque_Mapping("saucch_subaux_classech", SAU , "saucch_sau_code_fk_pk", CCH , "saucch_cch_code_fk_pk").register()
Theriaque_Mapping("saucch_subaux_classech", CCH , "saucch_cch_code_fk_pk", SAU , "saucch_sau_code_fk_pk").register()
Theriaque_Mapping("sac_subactive"         , SAC , "sac_code_sq_pk"       , GSAC, "sac_gsac_code_fk"     ).register()
Theriaque_Mapping("sac_subactive"         , GSAC, "sac_gsac_code_fk"     , SAC , "sac_code_sq_pk"       ).register()
