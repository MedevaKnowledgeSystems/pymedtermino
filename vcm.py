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
pymedtermino.vcm
****************

PyMedtermino module for VCM icons.
   
.. class:: VCM
   
   The VCM icons terminology. See :class:`pymedtermino.Terminology` for common terminology members; only VCM-specific members are described here.

.. class:: VCM_CONCEPT
   
   The VCM medical concept terminology. It is used to describe the medical concept represented by VCM icons. See :class:`pymedtermino.Terminology` for common terminology members; only VCM-specific members are described here.

.. class:: VCM_CONCEPT_MONOAXIAL
   
   A mono-axial (=single inheritance) version of :class:`pymedtermino.vcm.VCM_CONCEPT`. All anatomical structures have been associated to a single parents. See :class:`pymedtermino.Terminology` for common terminology members; only VCM-specific members are described here.
   
.. class:: VCM_LEXICON
   
   The VCM lexicon terminology. It describes the colors, shapes and pictograms used by VCM icons. See :class:`pymedtermino.Terminology` for common terminology members; only VCM-specific members are described here.
   
"""

from __future__ import print_function
from functools import reduce


__all__ = ["VCM_CONCEPT", "VCM_CONCEPT_MONOAXIAL", "VCM_LEXICON", "VCM", "VCMIcon",
           "vcm_concept_monoaxial_2_vcm_lexicon", "vcm_lexicon_2_vcm_concept_monoaxial",
           "generalize_icons", "simplify_icons", "remove_duplicate_icons",
           "keep_most_graphically_specific_icons", "keep_most_graphically_generic_icons"]

import sys, os, os.path, weakref, operator, sqlite3 as sql_module
import pymedtermino

class _BaseVCMTerminology(pymedtermino.Terminology):
  def get_relation_translation(self, relation, lang):
    self.db_cursor.execute("SELECT code FROM Concept WHERE term=?", (relation,))
    code = self.db_cursor.fetchone()[0]
    self.db_cursor.execute("SELECT term FROM Concept WHERE lang=? AND code=?", (lang, code,))
    return self.db_cursor.fetchone()[0]
  
  def search(self, text):
    self.db_cursor.execute("SELECT DISTINCT code FROM Concept WHERE term LIKE ?", ("%%%s%%" % text,))
    r1 = self.db_cursor.fetchall()
    r = [self[code] for (code,) in r1]
    root = self.first_levels()[0]
    return [concept for concept in r if concept.is_a(root)]
  
  
class _BaseVCMConcept(pymedtermino.MultiaxialConcept, pymedtermino._IntCodeConcept):
  def __init__(self, code):
    self.db_cursor.execute("SELECT term FROM Concept WHERE lang=? AND code=?", (pymedtermino.LANGUAGE, code))
    r = self.db_cursor.fetchone()
    if not r:
      self.db_cursor.execute("SELECT term FROM Concept WHERE code=?", (code,))
      r = self.db_cursor.fetchone()
      if not r: raise ValueError()
    pymedtermino.MultiaxialConcept.__init__(self, code, r[0])
    
  def __getattr__(self, attr):
    if   attr == "parents":
      self.db_cursor.execute("SELECT destination FROM Relation WHERE source=? AND relation='is_a'", (self.code,))
      self.parents = [self.terminology[code] for (code,) in self.db_cursor.fetchall()]
      return self.parents
    
    elif attr == "children":
      self.db_cursor.execute("SELECT source FROM Relation WHERE destination=? AND relation='is_a'", (self.code,))
      self.children = [self.terminology[code] for (code,) in self.db_cursor.fetchall()]
      return self.children
    
    elif attr == "relations":
      self.db_cursor.execute("SELECT DISTINCT relation FROM Relation WHERE source=?", (self.code,))
      self.relations = set(rel for (rel,) in self.db_cursor.fetchall() if rel != u"is_a")
      self.db_cursor.execute("SELECT DISTINCT relation FROM Relation WHERE destination=?", (self.code,))
      for (rel,) in self.db_cursor.fetchall():
        if rel != u"is_a": self.relations.add(u"INVERSE_%s" % rel)
      return self.relations
    
    elif attr.startswith(u"INVERSE_"):
      self.db_cursor.execute("SELECT DISTINCT source FROM Relation WHERE destination=? AND relation=?", (self.code, attr[8:]))
      l = [self.terminology[code] for (code,) in self.db_cursor.fetchall()]
      if not l: raise AttributeError(attr)
      setattr(self, attr, l)
      return l
    
    else:
      self.db_cursor.execute("SELECT DISTINCT destination FROM Relation WHERE source=? AND relation=?", (self.code, attr))
      l = [self.terminology[code] for (code,) in self.db_cursor.fetchall()]
      if not l: raise AttributeError(attr)
      setattr(self, attr, l)
      return l
    
    raise AttributeError(attr)
  
  def get_translation(self, lang):
    self.db_cursor.execute("SELECT term FROM Concept WHERE lang=? AND code=?", (lang, self.code,))
    return self.db_cursor.fetchone()[0]
  
  def get_annotation(self, annotation, lang):
    self.db_cursor.execute("SELECT %s FROM Concept WHERE lang=? AND code=?" % annotation, (lang, self.code,))
    return self.db_cursor.fetchone()[0]
  

class VCM_CONCEPT(_BaseVCMTerminology):
  _use_weakref = 0
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "VCM_CONCEPT")
    self.db        = pymedtermino.connect_sqlite3("vcm_concept")
    self.db_cursor = self.db.cursor()
    self.Concept.db_cursor = self.db_cursor
    
  def _create_Concept(self): return VCMConceptConcept
  def first_levels(self): return [self[54]]

class VCMConceptConcept(_BaseVCMConcept):
  def __getattr__(self, attr):
    if   attr == "comment": return self.get_annotation("comment", pymedtermino.LANGUAGE)
    
    return _BaseVCMConcept.__getattr__(self, attr)

VCM_CONCEPT = VCM_CONCEPT()


class VCM_CONCEPT_MONOAXIAL(_BaseVCMTerminology):
  _use_weakref = 0
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "VCM_CONCEPT_MONOAXIAL")
    self.db        = pymedtermino.connect_sqlite3("vcm_concept_monoaxial")
    self.db_cursor = self.db.cursor()
    self.Concept.db_cursor = self.db_cursor
    
  def _create_Concept(self): return VCMConceptConceptMonoaxial
  def first_levels(self): return [self[54]]

class VCMConceptConceptMonoaxial(_BaseVCMConcept):
  pass

VCM_CONCEPT_MONOAXIAL = VCM_CONCEPT_MONOAXIAL()

vcm_concept_2_vcm_concept_monoaxial = pymedtermino.SameCodeMapping(VCM_CONCEPT, VCM_CONCEPT_MONOAXIAL)
vcm_concept_2_vcm_concept_monoaxial.register()
vcm_concept_monoaxial_2_vcm_concept = vcm_concept_2_vcm_concept_monoaxial._create_reverse_mapping()
vcm_concept_monoaxial_2_vcm_concept.register()



class VCM_LEXICON(_BaseVCMTerminology):
  _use_weakref = 0
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "VCM_LEXICON")
    # read_only=False because import_vcm.py update the database.
    self.db        = pymedtermino.connect_sqlite3("vcm_lexicon", read_only=False)
    self.db_cursor = self.db.cursor()
    self.Concept.db_cursor = self.db_cursor
    
  def _create_Concept(self): return VCMLexiconConcept
  def first_levels(self): return [self[490]]

  
class VCMLexiconConcept(_BaseVCMConcept):
  """A VCM lexicon concept. See :class:`pymedtermino.Concept` for common terminology members; only VCM-specific members are described here.

VCM lexicon defines "graphical is a" relation in addition to standard "is a". A concept A is considered as "graphically being" a concept B if (and only if) the pictogram associated to A include the pictogram associated to B.

.. attribute:: category
   
   The category of lexicon (0: central color, 1: modifier, etc).

.. attribute:: graphical_parents
   
   The list of concepts that are graphically more general than this one.

.. attribute:: graphical_children
   
   The list of concepts that are graphically more specific than this one.

.. attribute:: abstract
   
   True if this concept is a lexicon category, rather than a concrete color, shape or pictogram.

.. attribute:: empty
   
   True if this concept is an 'empty' lexicon, such as "no pictogram".

.. attribute:: priority
   
   The priority of this lexicon concept, for icon sorting.

.. attribute:: second_priority
   
   The second priority of this lexicon concept, for icon sorting. Only used (non-zero) for some transverse modifiers ; these modifiers use a different priority if they are used along with a central pictogram or not.

Additional attributes can be available, listed in the :attr:`relations <pymedtermino.Concept.relations>` attribute.
"""
  @staticmethod
  def canonize_code(code):
    if isinstance(code, tuple): return code
    else:                       return int(code)
    
  def __init__(self, code):
    if isinstance(code, tuple): raise ValueError("No such VCM lexicon element: %s!" % (code,))
    
    self.db_cursor.execute("SELECT term, category, text_code, priority, second_priority FROM Concept WHERE lang=? AND code=?", (pymedtermino.LANGUAGE, code))
    r = self.db_cursor.fetchone()
    if not r:
      self.db_cursor.execute("SELECT term, category, text_code FROM Concept WHERE code=?", (code,))
      r = self.db_cursor.fetchone()
      if not r: raise ValueError()
    self.code = code
    self.term, self.category, self.text_code, self.priority, self.second_priority = r
    
    VCM_LEXICON.dict[self.code] = self
    
    self.db_cursor.execute("SELECT text_code FROM Concept WHERE code=? AND lang='en'", (code,))
    self.english_text_code = self.db_cursor.fetchone()[0]
    
    self.db_cursor.execute("SELECT text_code FROM Concept WHERE code=?", (code,))
    self.text_codes = [text_code for (text_code,) in self.db_cursor.fetchall()]
    for text_code in self.text_codes:
      VCM_LEXICON.dict[self.category, text_code] = self
      
  def __getattr__(self, attr):
    if   attr == "graphical_parents":
      if "graphical_is_a" in self.relations: self.graphical_parents = self.graphical_is_a
      else:                                  self.graphical_parents = []
      return self.graphical_parents
    
    elif attr == "graphical_children":
      if "INVERSE_graphical_is_a" in self.relations: self.graphical_children = self.INVERSE_graphical_is_a
      else:                                          self.graphical_children = []
      return self.graphical_children
    
    elif attr == "abstract": return (not self.text_code) or self.text_code.startswith(u"_")
    
    elif attr == "empty": return (self.text_code == u"empty") or (self.text_code == u"rien")
    
    return _BaseVCMConcept.__getattr__(self, attr)
  
  def is_graphically_a(self, concept):
    """Same as :func:`pymedtermino.Concept.is_a` but using "graphically is a" relation rather than standard "is a"."""
    if self is concept: return True
    for parent in self.graphical_parents:
      if parent.is_graphically_a(concept): return True
    return False
  
  def graphical_ancestors(self):
    """Same as :func:`pymedtermino.Concept.ancestors` but using "graphically is a" relation rather than standard "is a"."""
    for parent in self.graphical_parents:
      yield parent
      for concept in parent.graphical_ancestors():
        yield concept
        
  def graphical_descendants(self):
    """Same as :func:`pymedtermino.Concept.descendants` but using "graphically is a" relation rather than standard "is a"."""
    for child in self.graphical_children:
      yield child
      for concept in child.graphical_descendants():
        yield concept
        
  def self_and_graphical_ancestors(self):
    """Same as :func:`pymedtermino.Concept.self_and_ancestors` but using "graphically is a" relation rather than standard "is a"."""
    yield self
    for concept in self.graphical_ancestors(): yield concept
    
  def self_and_graphical_ancestors_no_double(self):
    """Same as :func:`pymedtermino.Concept.self_and_ancestors_no_double` but using "graphically is a" relation rather than standard "is a"."""
    yield self
    for concept in self.graphical_ancestors_no_double(): yield concept
    
  def self_and_graphical_descendants(self):
    """Same as :func:`pymedtermino.Concept.self_and_descendants` but using "graphically is a" relation rather than standard "is a"."""
    yield self
    for concept in self.graphical_descendants(): yield concept
    
  def self_and_graphical_descendants_no_double(self):
    """Same as :func:`pymedtermino.Concept.self_and_descendants_no_double` but using "graphically is a" relation rather than standard "is a"."""
    yield self
    for concept in self.graphical_descendants_no_double(): yield concept

  def graphical_ancestors_no_double(self, already = None):
    """Same as :func:`pymedtermino.Concept.ancestors_no_double` but using "graphically is a" relation rather than standard "is a"."""
    if already is None: already = set()
    for parent in self.graphical_parents:
      if not parent in already:
        already.add(parent)
        yield parent
        for concept in parent.graphical_ancestors_no_double(already):
          yield concept
          
  def graphical_descendants_no_double(self, already = None):
    """Same as :func:`pymedtermino.Concept.descendants_no_double` but using "graphically is a" relation rather than standard "is a"."""
    if already is None: already = set()
    for child in self.graphical_children:
      if not child in already:
        already.add(child)
        yield child
        for concept in child.graphical_descendants_no_double(already):
          yield concept
  
  def _non_abstract_graphical_children(lex):
    if lex.empty:
      for lex2 in lex.parents[0]._non_abstract_graphical_children():
        if not lex2 is lex: yield lex2
    else:
      for child in lex.graphical_children:
        if child.abstract:
          for child_child in child._non_abstract_graphical_children(): yield child_child
        else: yield child

  def _non_abstract_graphical_parents(lex):
    if not lex.empty:
      parent_found = 0
      for parent in lex.graphical_parents:
        if parent.abstract:
          for parent_parent in parent._non_abstract_graphical_parents():
            yield parent_parent
            parent_found = 1
        else:
          yield parent
          parent_found = 1
      if not parent_found: yield VCM_LEXICON[lex.category, u"empty"]
  
VCM_LEXICON = VCM_LEXICON()
VCM_LEXICON.CENTRAL_COLOR              = VCM_LEXICON[494]
VCM_LEXICON.TOP_RIGHT_COLOR            = VCM_LEXICON[688]
VCM_LEXICON.MODIFIER                   = VCM_LEXICON[501]
VCM_LEXICON.PHYSIO_MODIFIER            = VCM_LEXICON[503]
VCM_LEXICON.PATHO_MODIFIER             = VCM_LEXICON[504]
VCM_LEXICON.ETIOLOGY_MODIFIER          = VCM_LEXICON[511]
VCM_LEXICON.PROCESSUS_MODIFIER         = VCM_LEXICON[528]
VCM_LEXICON.QUANTITATIVE_MODIFIER      = VCM_LEXICON[505]
VCM_LEXICON.TRANSVERSE_MODIFIER        = VCM_LEXICON[535]
VCM_LEXICON.CENTRAL_PICTOGRAM          = VCM_LEXICON[543]
VCM_LEXICON.TOP_RIGHT_PICTOGRAM        = VCM_LEXICON[694]
VCM_LEXICON.SECOND_TOP_RIGHT_PICTOGRAM = VCM_LEXICON[717]
VCM_LEXICON.SHADOW                     = VCM_LEXICON[721]
VCM_LEXICON.EMPTY_CENTRAL_COLOR        = VCM_LEXICON[499]
VCM_LEXICON.EMPTY_CENTRAL_PICTOGRAM    = VCM_LEXICON[544]
VCM_LEXICON.EMPTY_TOP_RIGHT_COLOR      = VCM_LEXICON[689]
VCM_LEXICON.EMPTY_MODIFIER             = VCM_LEXICON[502]

for i in VCM_LEXICON.all_concepts(): pass

#vcm_concept_2_vcm_lexicon = pymedtermino.SQLMapping(VCM_CONCEPT, VCM_LEXICON, os.path.join(pymedtermino.DATA_DIR, "vcm_concept_2_vcm_lexicon.sqlite3"), has_and = 1)
#vcm_concept_2_vcm_lexicon.register()
#vcm_lexicon_2_vcm_concept = vcm_concept_2_vcm_lexicon._create_reverse_mapping()
#vcm_lexicon_2_vcm_concept.register()

vcm_concept_monoaxial_2_vcm_lexicon = pymedtermino.SQLMapping(VCM_CONCEPT_MONOAXIAL, VCM_LEXICON, os.path.join(pymedtermino.DATA_DIR, "vcm_concept_monoaxial_2_vcm_lexicon.sqlite3"), has_and = 1)
vcm_concept_monoaxial_2_vcm_lexicon.register()
vcm_lexicon_2_vcm_concept_monoaxial = vcm_concept_monoaxial_2_vcm_lexicon._create_reverse_mapping()
vcm_lexicon_2_vcm_concept_monoaxial.register()

(VCM_LEXICON >> VCM_CONCEPT_MONOAXIAL >> VCM_CONCEPT).register()
(VCM_CONCEPT >> VCM_CONCEPT_MONOAXIAL >> VCM_LEXICON).register()


_EMPTY_TEXT_CODES                  = set(VCM_LEXICON[502].text_codes) # No modifier
_PATHOLOGICAL_MODIFIER_TEXT_CODES  = set()
_PHYSIOLOGICAL_MODIFIER_TEXT_CODES = set()

for modifier in VCM_LEXICON.MODIFIER.self_and_descendants():
  if   modifier.is_a(VCM_LEXICON.PHYSIO_MODIFIER): _PHYSIOLOGICAL_MODIFIER_TEXT_CODES.update(modifier.text_codes)
  elif modifier.is_a(VCM_LEXICON.PATHO_MODIFIER ): _PATHOLOGICAL_MODIFIER_TEXT_CODES .update(modifier.text_codes)




class VCM(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "VCM")
    
  def _create_Concept(self): return VCMIcon
  
  def first_levels(self): return [] # XXX

  def icon_from_lexs(self, lexs):
    return self[u"empty--empty--empty"].derive_lexs(lexs)
  
  def icons_from_lexs(self, lexs, debug = 0):
    enlever_quantitatif = 0
    
    lexs = pymedtermino.Concepts(lexs)
    lexs.keep_most_specific()
    
    # Infection or Allergie imply inflammation
    if lexs.find(VCM_LEXICON[1, u"infection"]) or lexs.find(VCM_LEXICON[1, u"allergy"]):
      lexs = lexs.subtract(VCM_LEXICON[1, u"inflammation"])
      
    couleurs_centrales = lexs.extract(VCM_LEXICON.CENTRAL_COLOR)
    if not couleurs_centrales: couleurs_centrales = set([VCM_LEXICON[0, u"empty"]])
    
    pictogrammes_centraux = lexs.extract(VCM_LEXICON.CENTRAL_PICTOGRAM)
    pictogrammes_centraux.add(VCM_LEXICON[2, u"empty"])
    if len(pictogrammes_centraux) > 1:
      lex = [p for p in pictogrammes_centraux.lowest_common_ancestors() if not p.abstract]
      if lex:
        pictogrammes_centraux = pymedtermino.Concepts([lex[0]])
        enlever_quantitatif = 1
        
    if debug:
      print()
      print("LEXS =", lexs)
      print()
      print("pictos centraux :", pictogrammes_centraux)
      
    modificateurs_physio                    = lexs.extract(VCM_LEXICON.PHYSIO_MODIFIER)
    modificateurs_patho                     = lexs.extract(VCM_LEXICON.PATHO_MODIFIER)
    modificateurs_etiologies                = lexs.extract(VCM_LEXICON.ETIOLOGY_MODIFIER)
    modificateurs_processus                 = lexs.extract(VCM_LEXICON.PROCESSUS_MODIFIER)
    modificateurs_localisations_secondaires = lexs.extract(VCM_LEXICON.TRANSVERSE_MODIFIER)

    if enlever_quantitatif:
      modificateurs_quantitatifs            = pymedtermino.Concepts()
      if debug and lexs.extract(VCM_LEXICON.QUANTITATIVE_MODIFIER): print("On enlève les modificateurs qualitatifs")
    else:
      modificateurs_quantitatifs            = lexs.extract(VCM_LEXICON.QUANTITATIVE_MODIFIER)
      

    modificateurss = (modificateurs_etiologies | modificateurs_processus | modificateurs_localisations_secondaires | modificateurs_quantitatifs).all_subsets()
    if   modificateurs_physio and not modificateurs_patho:
      for modificateurs in modificateurss: modificateurs.add(VCM_LEXICON.PHYSIO_MODIFIER)
    elif modificateurs_patho:
      for modificateurs in modificateurss: modificateurs.add(VCM_LEXICON.PATHO_MODIFIER)
    else:
      for modificateurs in modificateurss: modificateurs.add(VCM_LEXICON[1, u"empty"])
      
    if debug:
      print()
      print("modificateurss :")
      for i in modificateurss: print("  ", i)
      
    exposants_traitements = lexs.extract(VCM_LEXICON[4, u"traitement"])
    if len(exposants_traitements) > 1:
      lex = exposants_traitements.lowest_common_ancestors()
      lex = lex.pop()
      if not lex.abstract: exposants_traitements = pymedtermino.Concepts([lex])
      
    exposants_examens = lexs.extract(VCM_LEXICON[4, u"_surveillance"])
    if len(exposants_examens) > 1:
      lex = exposants_examens.lowest_common_ancestors()
      lex = lex.pop()
      if not lex.abstract: exposants_examens = pymedtermino.Concepts([lex])
      
    exposants = exposants_traitements | exposants_examens
    if not exposants: exposants = pymedtermino.Concepts([VCM_LEXICON[4, u"empty"]])
    
    seconds_exposants = lexs.extract(VCM_LEXICON.SECOND_TOP_RIGHT_PICTOGRAM)
    if not seconds_exposants: seconds_exposants = pymedtermino.Concepts([VCM_LEXICON[5, u"empty"]])
    
    icones = []
    for couleur_centrale in couleurs_centrales:
      for modificateurs in modificateurss:
        for pictogramme_central in pictogrammes_centraux:
          for exposant in exposants:
            if   exposant.is_a(VCM_LEXICON[4, u"traitement"   ]): couleur_en_exposant = VCM_LEXICON[3, u"traitement"]
            elif exposant.is_a(VCM_LEXICON[4, u"_surveillance"]): couleur_en_exposant = VCM_LEXICON[3, u"surveillance"]
            else:                                                 couleur_en_exposant = VCM_LEXICON[3, u"empty"]
            for second_exposant in seconds_exposants:
              icones.append(VCM[u"empty--empty--empty"].derive(couleur_centrale, pymedtermino.Concepts(modificateurs), pictogramme_central, couleur_en_exposant, exposant, second_exposant))
    if debug:
      print()
      print("toutes les icônes :", len(icones))
      for i in icones: print("  ", i, end = u"")
      
    # Retirer les icônes incohérentes
    #icones = [icone for icone in icones if (icone.consistent) or icone.code.startswith("rien--")]
    icones = [icone for icone in icones if icone.consistent]
    
    if debug:
      print()
      print("retirer les icônes incohérentes :", len(icones))
      for i in icones: print("  ", i, end = u"")
    
    icones = pymedtermino.Concepts(icones)
    icones.keep_most_specific()
    
    if debug:
      print()
      print("retirer les icônes plus générales que d'autres :", len(icones))
      for i in icones: print("  ", i, end = u"")
      
    return icones


class VCMIcon(pymedtermino.MultiaxialConcept, pymedtermino._StringCodeConcept):
  """A VCM icon (=a concept in the VCM terminology). See :class:`pymedtermino.Concept` for common terminology members; only VCM-specific members are described here.

.. attribute:: lexs

   The list of lexicon concept in this icon.

.. attribute:: physio

.. attribute:: patho

.. attribute:: etiology
   
.. attribute:: quantitative
   
.. attribute:: process
   
.. attribute:: transverse

   All these attributes returns the shape modifier of the corresponding category (or None if no such modifiers).

.. attribute:: short_code

   The short icon code, compressed.
   
.. attribute:: long_code
   
   The entire icon code, including optional component.
   
.. attribute:: consistent
   
   True if the icon is consistent, according to the VCM ontology.
   
.. attribute:: concepts
   
   The set of VCM medical concepts associated to this icon.

.. attribute:: priority
   
   The priority of this icon (for sorting purpose).

"""
  relations = ["central_color", "modifiers", "central_pictogram", "top_right_color", "top_right_pictogram", "second_top_right_pictogram", "shadow", "physio", "patho", "etiology", "quantitative", "process", "transverse"]
  @staticmethod
  def canonize_code(code):
    if code: code = code.split(u"--")
    else:    code = []
    for i in range(len(code)):
      if i == 1: continue
      code[i] = VCM_LEXICON[i, code[i]].text_code
    if len(code) > 1:
      modifiers = set([VCM_LEXICON[1, text_code].text_code for text_code in code[1].split(u"-")])
      if modifiers.isdisjoint(_PATHOLOGICAL_MODIFIER_TEXT_CODES):
        if modifiers.isdisjoint(_PHYSIOLOGICAL_MODIFIER_TEXT_CODES) and modifiers.isdisjoint(_EMPTY_TEXT_CODES):
          modifiers.add(VCM_LEXICON.PATHO_MODIFIER.text_code)
      else:
        modifiers2 = modifiers.copy()
        for text_code in VCM_LEXICON.PATHO_MODIFIER.text_codes: modifiers2.discard(text_code)
        if not modifiers2.isdisjoint(_PATHOLOGICAL_MODIFIER_TEXT_CODES): modifiers = modifiers2
        
      if not modifiers.isdisjoint(_EMPTY_TEXT_CODES):
        modifiers2 = modifiers.copy()
        for text_code in _EMPTY_TEXT_CODES: modifiers2.discard(text_code)
        if modifiers2 and ((not modifiers2.isdisjoint(_PATHOLOGICAL_MODIFIER_TEXT_CODES)) or (not modifiers2.isdisjoint(_PHYSIOLOGICAL_MODIFIER_TEXT_CODES))): modifiers = modifiers2
        
      code[1] = u"-".join(sorted(modifiers))
    #else:             modifiers = set([u"empty"])
    
    #while len(code) < 7: code.append(VCM_LEXICON[6, u"empty"].text_code)
    while code and (code[-1] in _EMPTY_TEXT_CODES): del code[-1]
    if not code: return VCM_LEXICON[0, u"empty"].text_code
    return u"--".join(code)
  
  def __init__(self, code):
    ids  = code  .split(u"--")
    while len(ids) < 7: ids.append(u"empty")
    id2s = ids[1].split(u"-")
    
    self.code                       = code
    self.central_color              = VCM_LEXICON[0, ids[0]]
    self.modifiers                  = pymedtermino.Concepts(VCM_LEXICON[1, id2] for id2 in id2s)
    self.central_pictogram          = VCM_LEXICON[2, ids[2]]
    self.top_right_color            = VCM_LEXICON[3, ids[3]]
    self.top_right_pictogram        = VCM_LEXICON[4, ids[4]]
    self.second_top_right_pictogram = VCM_LEXICON[5, ids[5]]
    self.shadow                     = VCM_LEXICON[6, ids[6]]
    
    self.lexs = pymedtermino.Concepts([self.central_color, self.central_pictogram, self.top_right_color, self.top_right_pictogram, self.second_top_right_pictogram, self.shadow])
    self.lexs.update(self.modifiers)
    
    VCM.dict[code] = self
    pymedtermino.cache(self)
    
  def __getattr__(self, attr):
    if   attr == "physio":
      self.physio = self.modifiers.find(VCM_LEXICON.PHYSIO_MODIFIER)
      return self.physio
    
    elif attr == "patho":
      self.patho = self.modifiers.find(VCM_LEXICON.PATHO_MODIFIER)
      return self.patho

    elif attr == "etiology":
      self.etiology = self.modifiers.find(VCM_LEXICON.ETIOLOGY_MODIFIER)
      return self.etiology

    elif attr == "quantitative":
      self.quantitative = self.modifiers.find(VCM_LEXICON.QUANTITATIVE_MODIFIER)
      return self.quantitative
    
    elif attr == "process":
      self.process = self.modifiers.find(VCM_LEXICON.PROCESSUS_MODIFIER)
      return self.process

    elif attr == "transverse":
      self.transverse = self.modifiers.find(VCM_LEXICON.TRANSVERSE_MODIFIER)
      return self.transverse
      
    elif attr == "label":
      db_label_cursor.execute("SELECT term_en, term_fr FROM Label WHERE code=?", (self.code,))
      r = db_label_cursor.fetchall()
      if r:
        self.label = { "en" : r[0][0], "fr" : r[0][1] }
      else:
        import pymedtermino.vcm_label as vcm_label
        self.label = vcm_label.icon_2_label(self).langs
      return self.label

    elif attr == "term":
      self.term = self.label.get(pymedtermino.LANGUAGE, "") or self.label["en"]
      return self.term
      
    elif attr == "parents":
      self.parents = []
      for lex in self.lexs:
        for parent_lex in lex._non_abstract_graphical_parents():
          #if self.quantitative and (lex.category == 2) and (not lex.is_a(parent_lex)): continue
          if self.quantitative and (lex.category == 2): continue
          lexs = [None] * 7
          if lex.category == 1:
            modifiers = list(self.modifiers)
            modifiers.remove(lex)
            modifiers.append(parent_lex)
            lexs[1] = modifiers
          else:
            lexs[lex.category] = parent_lex
            if parent_lex is VCM_LEXICON[3, u"empty"]:
              lexs[4] = VCM_LEXICON[4, u"empty"]
            if parent_lex is VCM_LEXICON[4, u"empty"]:
              continue
          
          parent_icon = self.derive(*lexs)
          if parent_icon.consistent: self.parents.append(parent_icon)
      return self.parents
    
    elif attr == "children":
      self.children = []
      for lex in self.lexs:
        if (lex is VCM_LEXICON[4, u"empty"]) and self.top_right_color.empty: continue
        for child_lex in lex._non_abstract_graphical_children():
          if child_lex.text_code:
            if self.quantitative and (lex.category == 2): continue
            lexs = [None] * 7
            if lex.category == 1:
              modifiers = list(self.modifiers)
              modifiers.remove(lex)
              modifiers.append(child_lex)
              lexs[1] = modifiers
            else:
              lexs[lex.category] = child_lex
              if   ((child_lex is VCM_LEXICON[3, u"traitement"]) or (child_lex is VCM_LEXICON[3, u"antecedent_traitement"])) and (self.top_right_pictogram is VCM_LEXICON[4, u"empty"]):
                lexs[4] = VCM_LEXICON[4, u"traitement"]
              elif ((child_lex is VCM_LEXICON[3, u"surveillance"]) or (child_lex is VCM_LEXICON[3, u"antecedent_surveillance"])) and (self.top_right_pictogram is VCM_LEXICON[4, u"empty"]):
                lexs[4] = VCM_LEXICON[4, u"diagnostic"]
                
            child_icon = self.derive(*lexs)
            if child_icon.consistent: self.children.append(child_icon)
      return self.children
    
    #elif attr == "short_code": return u"-".join(sorted(u"%s" % lex.code for lex in self.lexs if not lex.empty))
    #elif attr == "short_code": return u"".join(sorted( struct.pack("!H", lex.code) for lex in self.lexs if not lex.empty)
    
    elif attr == "short_code":
      import struct
      codes = [lex.code for lex in self.lexs if not lex.empty]
      codes.sort()
      return struct.pack("!" + "H" * len(codes), *codes).decode("latin")
    
    elif attr == "long_code":
      long_code = self.code.split(u"--")
      while len(long_code) < 7: long_code.append(u"empty")
      return u"--".join(long_code)
    
    elif attr == "consistent":
      if self.central_color.empty: return 1
      if VCM_LEXICON[1, u"empty"] in self.modifiers: return 1
      
      return len(self.concepts) > 0
      
    elif attr == "concepts":
      self.concepts = pymedtermino.Concepts()
      
      # Step 1 : check consistency of lex pairs
      for lex1 in self.lexs:
        for lex2 in self.lexs:
          if (lex1.code < lex2.code):
            db_consistency_cursor.execute(u"SELECT lex1 FROM InconsistentPairs WHERE lex1=? AND lex2=?;", (lex1.code, lex2.code))
            if db_consistency_cursor.fetchone(): return self.concepts
            
      # Step 2 : get the concepts associated to central picto + mods, and check their consistency (no concept => inconsistent)
      modifiers = [modifier.code for modifier in self.modifiers]
      modifiers.sort()
      while len(modifiers) < 3: modifiers.append(0)
      db_consistency_cursor.execute(u"SELECT concept FROM PictoModsSens WHERE picto=? AND mod1=? AND mod2=? AND mod3=?;", (self.central_pictogram.code, modifiers[0], modifiers[1], modifiers[2]))
      picto_mods_concepts = db_consistency_cursor.fetchall()
      if not picto_mods_concepts: return self.concepts
      
      # Step 3 : check consistency with regard to the list of inconsistent icons
      db_consistency_cursor.execute(u"SELECT codes FROM InconsistentIcon WHERE codes=? LIMIT 1;", (self.short_code,))
      if db_consistency_cursor.fetchone(): return self.concepts
      
      # Step 2 : get the concepts associated to the rest of the icon
      self.concepts =      (VCM_LEXICON >> VCM_CONCEPT)(self.top_right_color)
      self.concepts.update((VCM_LEXICON >> VCM_CONCEPT)(self.top_right_pictogram))
      self.concepts.keep_most_specific()
      self.concepts.update((VCM_LEXICON >> VCM_CONCEPT)(self.central_color))
      self.concepts.update((VCM_LEXICON >> VCM_CONCEPT)(self.second_top_right_pictogram))
      self.concepts.update([VCM_CONCEPT[code] for (code,) in picto_mods_concepts])
      if not (VCM_CONCEPT[15] in self.concepts): self.concepts.add(VCM_CONCEPT[450]) # Absence_de_trouble_pathologique, Trouble_pathologique
      return self.concepts
    
    elif attr == "priority":
      self.priority = 0
      for lex in self.lexs:
        if (not self.central_pictogram.is_a(VCM_LEXICON.EMPTY_CENTRAL_PICTOGRAM)) and lex.is_a(VCM_LEXICON.TRANSVERSE_MODIFIER) and lex.second_priority:
          self.priority += lex.second_priority
          continue
        if self.transverse and self.transverse.second_priority and lex.is_a(VCM_LEXICON.EMPTY_CENTRAL_PICTOGRAM): continue
        #print(lex.term, lex.priority)
        self.priority += lex.priority
      return self.priority
    
    raise AttributeError(attr)
  
  def __lt__(self, other): return self.priority < other.priority
  def __gt__(self, other): return self.priority > other.priority
    
  
  def get_translation(self, lang): return self.label[lang]
    
  def get_english_code(self):
    english_code = self.code.split(u"--")
    for i in range(len(english_code)):
      if i == 1:
        english_code[1] = u"-".join(VCM_LEXICON[1, j].english_text_code for j in english_code[1].split(u"-"))
      else:
        english_code[i] = VCM_LEXICON[i, english_code[i]].english_text_code
    return u"--".join(english_code)
  english_code = property(get_english_code)
  
  def derive(self, central_color = None, modifiers = None, central_pictogram = None, top_right_color = None, top_right_pictogram = None, second_top_right_pictogram = None, shadow = None):
    """Creates and returns a new VCM icon, using this icon as a string point, and adding the given VCM lexicon concepts."""
    codes = self.long_code.split(u"--")
    while len(codes) < 7: codes.append(u"empty")
    if central_color             : codes[0] = central_color             .text_code
    if modifiers                 : codes[1] = u"-".join(modifier.text_code for modifier in modifiers)
    if central_pictogram         : codes[2] = central_pictogram         .text_code
    if top_right_color           : codes[3] = top_right_color           .text_code
    if top_right_pictogram       : codes[4] = top_right_pictogram       .text_code
    if second_top_right_pictogram: codes[5] = second_top_right_pictogram.text_code
    if shadow                    : codes[6] = shadow                    .text_code
    return VCM[u"--".join(codes)]
    
  def derive_lexs(self, lexs):
    """Creates and returns a new VCM icon, using this icon as a string point, and adding the given VCM lexicon concepts, as a list."""
    codes = self.code.split(u"--")
    while len(codes) < 7: codes.append(u"empty")
    modifiers = pymedtermino.Concepts()
    
    for lex in lexs:
      if lex.category == 1: modifiers.add(lex)
      else:                 codes[lex.category] = lex.text_code
      
    if modifiers:
      etiology     = modifiers.find(VCM_LEXICON.ETIOLOGY_MODIFIER)     or self.etiology
      quantitative = modifiers.find(VCM_LEXICON.QUANTITATIVE_MODIFIER) or self.quantitative
      process      = modifiers.find(VCM_LEXICON.PROCESSUS_MODIFIER)    or self.process
      transverse   = modifiers.find(VCM_LEXICON.TRANSVERSE_MODIFIER)   or self.transverse
      physio       = modifiers.find(VCM_LEXICON.PHYSIO_MODIFIER)
      patho        = modifiers.find(VCM_LEXICON.PATHO_MODIFIER)
      
      if   physio:
        modifiers2 = set(filter(None, [etiology, quantitative, process, transverse]))
        modifiers2.discard(VCM_LEXICON.PATHO_MODIFIER)
        modifiers2.add(physio)
      elif patho :
        modifiers2 = set(filter(None, [etiology, quantitative, process, transverse]))
        modifiers2.discard(VCM_LEXICON.PHYSIO_MODIFIER)
        modifiers2.add(patho)
      else:
        modifiers2 = set(filter(None, [self.patho, self.physio, etiology, quantitative, process, transverse]))
        
      codes[1] = u"-".join(modifier.text_code for modifier in modifiers2)
      
    return VCM[u"--".join(codes)]
    
  def is_a(self, concept):
    if self is concept: return True
    if not self.is_graphically_a(concept): return False
    
    if concept.quantitative: # Le quantitatif se rapporte à certains autres éléments, qui doivent donc être les mêmes !
      if (not self.central_pictogram is concept.central_pictogram) and (not concept.central_pictogram is VCM_LEXICON[2, u"empty"]): return False
      if  not self.process           is concept.process: return False
      
    return True
  
  def is_graphically_a(self, concept):
    """Same as :func:`pymedtermino.Concept.is_a` but using "graphically is a" relation rather than standard "is a"."""
    if self is concept: return True
    if not isinstance(concept, VCMIcon): return False
    
    if (not concept.central_color              is VCM_LEXICON[0, u"empty"]) and (not self.central_color             .is_graphically_a(concept.central_color             )): return False
    if (not concept.central_pictogram          is VCM_LEXICON[2, u"empty"]) and (not self.central_pictogram         .is_graphically_a(concept.central_pictogram         )): return False
    if (not concept.top_right_color            is VCM_LEXICON[3, u"empty"]) and (not self.top_right_color           .is_graphically_a(concept.top_right_color           )): return False
    if (not concept.top_right_pictogram        is VCM_LEXICON[4, u"empty"]) and (not self.top_right_pictogram       .is_graphically_a(concept.top_right_pictogram       )): return False
    if (not concept.second_top_right_pictogram is VCM_LEXICON[5, u"empty"]) and (not self.second_top_right_pictogram.is_graphically_a(concept.second_top_right_pictogram)): return False
    if (not concept.shadow                     is VCM_LEXICON[6, u"empty"]) and (not self.shadow                    .is_graphically_a(concept.shadow                    )): return False
    
    if concept.physio != self.physio: return False
    
    if concept.etiology     and ((not self.etiology    ) or (not self.etiology    .is_graphically_a(concept.etiology    ))): return False
    if concept.process      and ((not self.process     ) or (not self.process     .is_graphically_a(concept.process     ))): return False
    if concept.transverse   and ((not self.transverse  ) or (not self.transverse  .is_graphically_a(concept.transverse  ))): return False
    if concept.quantitative and ((not self.quantitative) or (not self.quantitative.is_graphically_a(concept.quantitative))): return False
    
    return True
  
VCM = VCM()


db_consistency        = pymedtermino.connect_sqlite3("vcm_consistency")
db_consistency_cursor = db_consistency.cursor()

db_label              = pymedtermino.connect_sqlite3("vcm_label")
db_label_cursor       = db_label.cursor()

class VCM_LEXICON_2_VCMMapping(pymedtermino.Mapping):
  def __init__(self): pymedtermino.Mapping.__init__(self, VCM_LEXICON, VCM)
  def map_concepts(self, lexs, debug = 0): return VCM.icons_from_lexs(lexs, debug = debug)

vcm_lexicon_2_vcm = VCM_LEXICON_2_VCMMapping()
vcm_lexicon_2_vcm.register()


class VCMLexiconIndex(object):
  def __init__(self, terminology, db_filename):
    self.terminology = terminology
    if isinstance(db_filename, str):
      if not os.path.isfile(db_filename):
        raise IOError('File not found: %s' % db_filename)
      self.db                 = sql_module.connect(db_filename)
      self.db_cursor          = self.db.cursor()
    else:
      self.db_cursor          = db_filename
    self.db_cursor.execute("PRAGMA query_only = TRUE;")
    
  def _get_concept_by_lex(self, lex):
    self.db_cursor.execute(u"SELECT code FROM VCMLexiconIndex WHERE lex=?", (lex.code,))
    return [code for (code,) in self.db_cursor.fetchall()]
  
  def __getitem__(self, lex):
    if isinstance(lex, VCMLexiconConcept):
      codes = []
      for sublex in lex.self_and_graphical_descendants():
        codes.extend(self._get_concept_by_lex(sublex))
    else:
      lexs  = lex
      codes = None
      for lex in lexs:
        nouveaux_codes = []
        for sublex in lex.self_and_graphical_descendants(): nouveaux_codes.extend(self._get_concept_by_lex(sublex))
        if codes is None: codes = set(nouveaux_codes)
        else:             codes.intersection_update(set(nouveaux_codes))
    return [self.terminology[code] for code in codes]
    
  
def keep_most_graphically_specific_icons(self, on_del = None):
  """keeps only the most specific icons, i.e. remove all concepts that are more general that another concept in the set, using "graphical is a" relations.

:param self: the list of icons.
:param on_del: an optional callable, called for each icon removed.
:returns: the new list of icons.
"""
  clone = list(self)
  for t1 in clone:
    for t2 in clone:
      if (not t1 is t2) and t1.is_graphically_a(t2): # t2 is more generic than t1 => we keep t1
        self.discard(t2)
        if on_del: on_del(t1, t2)
  return self

def keep_most_graphically_generic_icons(self, on_del = None, add_shadow = 1):
  """keeps only the most generic icons, i.e. remove all concepts that are more general that another concept in the set, using "graphical is a" relations.

:param self: the list of icons.
:param on_del: an optional callable, called for each icon removed.
:param add_shadow: if True, automatically adds shadow below icons that are present several times.
:returns: the new list of icons.
"""
  clone  = list(self)
  clone2 = list(self)
  #if add_shadow: shadowed = { t : t for t in self if t.shadow == VCM_LEXICON[6, u"shadow"] }
  if add_shadow:
    shadowed = {}
    for t in self:
      if t.shadow == VCM_LEXICON[6, u"shadow"]: shadowed[t] = t
      
  for t1 in clone:
    for t2 in clone2:
      if (not t1 is t2) and t1.is_graphically_a(t2): # t2 is more generic than t1 => we keep t2
        self  .discard(t1)
        clone2.remove(t1)
        if add_shadow:
          if shadowed.get(t2):
            if on_del: on_del(shadowed[t2], t1)
          else:
            shadowed[t2] = t2.derive(shadow = VCM_LEXICON[6, u"shadow"])
            if on_del:
              on_del(shadowed[t2], t2)
              on_del(shadowed[t2], t1)
        else:
          if on_del: on_del(t2, t1)
        break
      
  if add_shadow:
    for t in shadowed:
      if not shadowed[t] is t:
        self.discard(t)
        self.add(shadowed[t])
  return self


def generalize_lexs(lexs):
  """Generalizes the given list of lexicon concepts, using the lowest common ancestor on "graphical is a" relations."""
  r = lexs_lowest_common_ancestor(lexs)
  if (not r) or (r.abstract): return VCM_LEXICON[tuple(lexs)[0].category, "empty"]
  return r

def lexs_lowest_common_ancestor(lexs):
  """Returns the lowest common ancestor, using "graphical is a" relations."""
  if len(lexs) == 0: return None
  if len(lexs) == 1: return tuple(lexs)[0]
  l1 = [set([lex]) for lex in lexs]
  l2 = [set([lex]) for lex in lexs]
  while 1:
    intersection = reduce(operator.and_, l2)
    if intersection: return tuple(intersection)[0]
    
    l1_new = []
    for i in l1:
      s = set()
      l1_new.append(s)
      for j in i: s.update(j.graphical_parents)
    if l1 == l1_new: return None
    
    l1 = l1_new
    for i in range(len(l1)): l2[i].update(l1[i])
    
      
def generalize_icons(icons, on_del = None, fail_if_too_much_information_is_lost = 0):
  """Generalizes the given list of icons, and returns the lowest common ancestor icon.

:param icons: the list of icons.
:param on_del: an optional callable, called for each icon removed.
:param fail_if_too_much_information_is_lost: if True, returns None when too much information is lost (i.e. central pictogram).
:returns: the new list of icons.
"""
  if len(icons) == 1: return icons[0]
  
  if fail_if_too_much_information_is_lost and (len(set(icon.central_color for icon in icons)) > 1): return None
  
  central_colors = pymedtermino.Concepts(icon.central_color   for icon in icons)
  if len(central_colors) == 1: central_color = tuple(central_colors)[0]
  else:                        central_color = VCM_LEXICON[0, u"current"]
  
  top_right_color = generalize_lexs(pymedtermino.Concepts(icon.top_right_color for icon in icons))
  if not top_right_color is VCM_LEXICON.EMPTY_TOP_RIGHT_COLOR:
    top_right_pictogram = generalize_lexs(pymedtermino.Concepts(icon.top_right_pictogram for icon in icons))
  else:
    top_right_pictogram = VCM_LEXICON[4, u"empty"]
    
  second_top_right_pictogram = generalize_lexs(pymedtermino.Concepts(icon.second_top_right_pictogram for icon in icons))
  central_pictogram          = generalize_lexs(pymedtermino.Concepts(icon.central_pictogram for icon in icons))
  
  etiologies     = [icon.etiology     for icon in icons]
  quantitatives  = [icon.quantitative for icon in icons]
  processes      = [icon.process      for icon in icons]
  transverses    = [icon.transverse   for icon in icons]
  physio         = 0
  for icon in icons:
    if icon.physio: physio = 1
    
  if None in etiologies: etiology = None
  else:
    etiology = generalize_lexs([i for i in etiologies if i])
    if etiology.code is VCM_LEXICON.PATHO_MODIFIER: etiology = None
    
  if None in quantitatives: quantitative = None
  else:
    quantitative = generalize_lexs([i for i in quantitatives if i])
    if quantitative.code is VCM_LEXICON.PATHO_MODIFIER: quantitative = None
    
  if None in processes: process = None
  else:
    process = generalize_lexs([i for i in processes if i])
    if process.code is VCM_LEXICON.PATHO_MODIFIER: process = None
    
  if None in transverses: transverse = None
  else:
    transverse = generalize_lexs([i for i in transverses if i])
    if (transverse is VCM_LEXICON.PATHO_MODIFIER) or (transverse is VCM_LEXICON.EMPTY_MODIFIER): transverse = None

  # Le quantitatif porte sur le pictogramme central, donc perdre le pictogramme central => perdre le quantitatif
  if set([icon.central_pictogram for icon in icons]) != set([central_pictogram]):
    quantitative = None
    
  # Le quantitatif porte sur l'étiologie / le processus / la localisation
  # secondaire, donc perdre l'étiologie / le processus / la loca II
  # => perdre le quantitatif
  if [i for i in etiologies if i] and not etiology: quantitative = None
  if [i for i in processes  if i] and not process : quantitative = None
  
  modifiers = [i for i in [etiology, quantitative, process, transverse] if i]
  if not modifiers:
    if physio: modifiers = [VCM_LEXICON.PHYSIO_MODIFIER]
    else:      modifiers = [VCM_LEXICON.PATHO_MODIFIER ]
    
  gen_icon = VCM[u"%s--%s--%s--%s--%s--%s--%s" %
    (central_color.text_code,
     u"-".join(modifier.text_code for modifier in modifiers) or u"empty",
     central_pictogram.text_code,
     top_right_color.text_code,
     top_right_pictogram.text_code,
     second_top_right_pictogram.text_code,
     VCM_LEXICON[6, u"shadow"].text_code,
    )]
  
  # Vérifie s'il n'y a pas une perte d'information exessive
  if fail_if_too_much_information_is_lost and (gen_icon.central_pictogram is VCM_LEXICON.EMPTY_CENTRAL_PICTOGRAM):
    if (gen_icon.modifiers == pymedtermino.Concepts([VCM_LEXICON.PHYSIO_MODIFIER])) or (gen_icon.modifiers == pymedtermino.Concepts([VCM_LEXICON.PATHO_MODIFIER])):
      for icon in icons:
        if not icon.central_pictogram is VCM_LEXICON.EMPTY_CENTRAL_PICTOGRAM:
          return None
        if (icon.modifiers != pymedtermino.Concepts([VCM_LEXICON.PHYSIO_MODIFIER])) and (icon.modifiers != pymedtermino.Concepts([VCM_LEXICON.PATHO_MODIFIER])):
          return None
        
  return gen_icon

def simplify_icons(icons, on_del = None):
  """Simplifies the given list of icons, and returns a new list.
The list is simplified by keeping the lowest common ancestor icons, whenever possible without loosing any central pictograms.

:param icons: the list of icons.
:param on_del: an optional callable, called for each icon removed.
:returns: the new list of icons.
"""
  icons = list(icons)
  for _i in range(len(icons)):
    for _j in range(len(icons)):
      if _i < _j:
        i = icons[_i]
        j = icons[_j]
        ij = generalize_icons([i, j], fail_if_too_much_information_is_lost = 1)
        if ij:
          icons = list(icons)
          if on_del:
            on_del(ij, i)
            on_del(ij, j)
          icons.remove(i)
          icons.remove(j)
          icons.append(ij)
          return simplify_icons(icons, on_del)
  return icons


def remove_duplicate_icons(icons, on_del = None, add_shadow = 1):
  """Removes dupplicated icons in the given list, and returns a new list.

:param icons: the list of icons.
:param on_del: an optional callable, called for each icon removed.
:param add_shadow: if True, automatically adds shadow below icons that are present several times.
:returns: the new list of icons.
"""
  icons  = list(icons)
  
  for i in range(len(icons)):
    iconA = icons[i]
    for j in range(len(icons)):
      if (i != j):
        iconB = icons[j]
        if iconB and iconA and (
          (iconA.central_color              == iconB.central_color             ) and
          (iconA.central_pictogram          == iconB.central_pictogram         ) and
          (iconA.modifiers                  == iconB.modifiers                 ) and
          (iconA.top_right_color            == iconB.top_right_color           ) and
          (iconA.top_right_pictogram        == iconB.top_right_pictogram       ) and
          (iconA.second_top_right_pictogram == iconB.second_top_right_pictogram) and
         ((iconA.shadow == iconB.shadow) or (iconA.shadow == VCM_LEXICON[6, u"shadow"]))
          ):
          if iconA.shadow == VCM_LEXICON[6, u"shadow"]: # Déjà fait
            if on_del: on_del(iconA, iconB)
            icons[j] = None
          elif add_shadow:
            iconA_avec_ombre = iconA.derive(shadow = VCM_LEXICON[6, u"shadow"])
            if on_del:
              on_del(iconA_avec_ombre, iconA)
              on_del(iconA_avec_ombre, iconB)
            icons[i] = iconA_avec_ombre
            icons[j] = None
          else:
            icons[j] = None
            
            
  return [i for i in icons if i]


