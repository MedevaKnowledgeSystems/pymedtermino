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
pymedtermino
************

PyMedTermino (Medical Terminologies for Python) is a Python module for easy access to the main medical terminologies in Python, including SNOMED CT, ICD10, MedDRA, UMLS and VCM icons.

PyMedTermino is available under the GNU LGPL licence, and it has been created by Jean-Baptiste Lamy,
LIMICS, Paris 13 University, Sorbonne Paris Cité, INSERM UMRS 1142, Paris 6 University
74 rue Marcel Cachin
93017 Bobigny, France

This module includes Pymedtermino's global parameters, the base classes for terminology-specific modules, and utility classes.

Global parameters
-----------------

.. autodata:: pymedtermino.DATA_DIR
.. autodata:: pymedtermino.LANGUAGE 
.. autodata:: pymedtermino.REMOVE_SUPPRESSED_CONCEPTS 
.. autodata:: pymedtermino.REMOVE_SUPPRESSED_TERMS 
.. autodata:: pymedtermino.REMOVE_SUPPRESSED_RELATIONS 


General functions
-----------------

The following function can get any concept from a "terminology:code" string:

.. autofunction:: get_concept


Bases classes
-------------

This module also defined the :class:`Terminology`, :class:`Concept`, :class:`Mapping`
classes that are used as base classes for the various terminologies.

.. autoclass:: Terminology
   :members:

.. autoclass:: Concept

.. autoclass:: Mapping
   :members:


Utility classes
---------------

.. autoclass:: Concepts
   :members:
"""

import sys, os, os.path, atexit, operator, weakref, sqlite3 as sql_module
from functools   import reduce
from collections import defaultdict

if sys.version[0] != "2": unicode = str

def _get_env(var, default):
    return os.environ.get("PYMEDTERMINO_" + var, default)


def _get_bool_env(var, default=True):
    val = _get_env(var, default)
    if val is not default:
        if not val or val == "0":
            return False
        return True

#: the default language used for terms, when several translations are available. If the desired language is not available, it defaults to English.
#:
#: .. warning:: this parameter must be set BEFORE loading terminologies. Default : "en" (English).
LANGUAGE                      = _get_env("LANGUAGE", "en")
DATA_DIR                      = _get_env("DATA_DIR", os.path.dirname(__file__)) #: the directory where SQLite3 database files containing terminologies are located. Default : PyMedTermino directory.
REMOVE_SUPPRESSED_CONCEPTS    = _get_bool_env("REMOVE_SUPPRESSED_CONCEPTS", True) #: if True, concepts tagged as suppressed or depreciated in terminologies are skipped.
REMOVE_SUPPRESSED_TERMS       = _get_bool_env("REMOVE_SUPPRESSED_TERMS", True) #: if True, terms (=translations) tagged as suppressed or depreciated in terminologies are skipped.
REMOVE_SUPPRESSED_RELATIONS   = _get_bool_env("REMOVE_SUPPRESSED_RELATIONS", True) #: if True, relations tagged as suppressed or depreciated in terminologies are skipped.
READ_ONLY_DATABASE            = _get_bool_env("READ_ONLY_DATABASE", True)

TERMINOLOGIES                 = {}
MISSING_CONCEPTS              = set()
SHOW_MISSING_CONCEPTS_AT_EXIT = True

def print_missing_concepts():
  if SHOW_MISSING_CONCEPTS_AT_EXIT and MISSING_CONCEPTS:
    sys.stderr.write("\n")
    sys.stderr.write("Missing concepts:\n")
    for i in MISSING_CONCEPTS:
      sys.stderr.write(i)
      sys.stderr.write("\n")
atexit.register(print_missing_concepts)

class UnknownTerminologyError(Exception): pass
class UnknownConceptError    (Exception): pass



class Terminology(object):
  """Base class for all terminologies.

.. attribute:: name
   
   name of the terminology

.. method:: first_levels()

   Returns the root concepts in the terminology (=concepts without parents).

.. method:: search(text)

   Searches for concepts whose terms match the given text (free-text search).
   
   :returns: a list of concept.
   

"""
  _use_weakref = 1
  def __init__(self, name):
    self.name = name
    if self._use_weakref:
      self.dict = weakref.WeakValueDictionary()
    else:
      self.dict = {}
    self.Concept = self._create_Concept()
    self.Concept.terminology = self
    self.canonize_code = self.Concept.canonize_code
    TERMINOLOGIES[name] = self
    
  if sys.version[0] == "2":
    def __unicode__(self): return u"<Terminology %s>" % self.name
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u"<Terminology %s>" % self.name
    
  def __rshift__(origin, destination):
    mapping = _MAPPINGS.get((origin, destination))
    if mapping is None: raise ValueError("No mapping available or loaded between %s and %s!" % (origin, destination))
    return mapping
    
  def all_concepts(self, *args):
    """Retuns a generator for iterating over *all* concepts in the terminology."""
    for root in self.first_levels(*args):
      yield root
      for concept in root.descendants():
        yield concept
        
  def all_concepts_no_double(self):
    """Retuns a generator for iterating over *all* concepts in the terminology, each concept being iterated only once (for multiaxial terminologies)."""
    already = set()
    for root in self.first_levels():
      if not root in already:
        already.add(root)
        yield root
      for concept in root.descendants():
        if not concept in already:
          already.add(concept)
          yield concept
          
  def get(self, code):
    """Retuns the concept of the given code, or None if no such concept."""
    code = self.canonize_code(code)
    concept = self.dict.get(code)
    if not concept:
      try:                            concept = self.Concept(code)
      except (ValueError, TypeError): return None
    return concept
  
  def has_concept(self, code):
    """Retuns True if the terminology has a concept of the given code."""
    try: concept = self[self.canonize_code(code)]
    except ValueError: return False
    return True
  
  def concept(self, code):
    """Retuns the concept of the given code; raise ValueError if it does not exist.
Also available as Terminology[code] (i.e. Terminology.__getitem__)."""
    code = self.canonize_code(code)
    concept = self.dict.get(code)
    if concept: return concept
      #if self._use_weakref:
      #  concept = concept()
      #  if concept: return concept
      #else: return concept
      
    try: concept = self.Concept(code)
    except ValueError:
      MISSING_CONCEPTS.add("%s:%s" % (self.name, code))
      raise ValueError(u"Missing concept %s:%s !" % (self.name, code))
    return concept
  __getitem__ = concept
  __call__    = concept
  

_CACHES = [None] * 500
_NEXT_CACHE_ID = 0
def cache(o):
  global _NEXT_CACHE_ID
  _CACHES[_NEXT_CACHE_ID] = o
  _NEXT_CACHE_ID += 1
  if _NEXT_CACHE_ID >= len(_CACHES): _NEXT_CACHE_ID = 0
  

class Concept(object):
  """Base class for all concepts, in any terminology.

.. attribute:: terminology

   the terminology this concept is extracted from.

.. autoinstanceattribute:: code
.. autoinstanceattribute:: term

.. attribute:: terms

   the list of terms for this concept.

.. attribute:: parents

   the list of parent concepts.

   .. note:: Concept.parents is *always* a list, even for terminologies with single inheritance (like ICD10). This allows to write terminology-independent code.

.. attribute:: children

   the list of children concepts.

.. attribute:: relations

   the list of the available relations for this concept. The available relations depend of the terminology, and is-a relations are not included (use parents and children attributes). Each relation corresponds to an attribute of the concept.

.. automethod:: full_code
.. automethod:: get_translation
.. automethod:: get_translations
.. automethod:: is_a
.. automethod:: __rshift__
.. automethod:: ancestors

.. method:: ancestors_no_double

   Returns a generator for iterating over all ancestors of this concept. Each concept is only yielded once (useful for multiaxial terminologies).
   
.. automethod:: self_and_ancestors
.. automethod:: self_and_ancestors_no_double

.. automethod:: descendants

.. method:: descendants_no_double

   Returns a generator for iterating over all descendants of this concept. Each concept is only yielded once (useful for multiaxial terminologies).

.. automethod:: self_and_descendants
.. automethod:: self_and_descendants_no_double
"""
  def __init__(self, code, term):
    self.code = code #: the code of the concept
    if not term is None: self.term = term #: the preferred term (i.e. label) of the concept
    #if self.terminology._use_weakref: self.terminology.dict[code] = weakref.ref(self)
    #else:                             self.terminology.dict[code] = self
    self.terminology.dict[code] = self
    cache(self)
    
  def full_code(self):
    """Returns the 'full code' for this concept, including both terminology name and concept code (for example "icd10:I10")."""
    return u"%s:%s" % (self.terminology.name, self.code)
    
  def pair(self): return [self.terminology.name, self.code]
  
  def __rshift__(self, destination_terminology):
    """Maps the concept to the destination_terminology. See :doc:`tuto_en` for more info."""
    if destination_terminology is self.terminology: return Concepts([self])
    return (self.terminology >> destination_terminology)(self)
    
  def is_a(self, concept):
    """Returns True if this concept is a child of the given concept (or if both concepts are the same)."""
    if self is concept: return True
    for parent in self.parents:
      if parent.is_a(concept): return True
    return False
  imply = is_a
  
  def copy(self): return self # Immutable
  __copy__ = __deepcopy__ = copy
  
  def ancestors(self):
    """Returns a generator for iterating over all ancestors of this concept."""
    for parent in self.parents:
      yield parent
      for concept in parent.ancestors():
        yield concept
        
  def descendants(self):
    """Returns a generator for iterating over all descendants of this concept."""
    for child in self.children:
      yield child
      for concept in child.descendants():
        yield concept
        
  def self_and_ancestors(self):
    """Returns a generator for iterating over all ancestors of this concept, including the concept itself."""
    yield self
    for concept in self.ancestors(): yield concept
    
  def self_and_ancestors_no_double(self):
    """Returns a generator for iterating over all ancestors of this concept, including the concept itself. Each concept is only yielded once (useful for multiaxial terminologies)."""
    yield self
    for concept in self.ancestors_no_double(): yield concept
    
  def self_and_descendants(self):
    """Returns a generator for iterating over all descendants of this concept, including the concept itself."""
    yield self
    for concept in self.descendants(): yield concept
    
  def self_and_descendants_no_double(self):
    """Returns a generator for iterating over all descendants of this concept, including the concept itself. Each concept is only yielded once (useful for multiaxial terminologies)."""
    yield self
    for concept in self.descendants_no_double(): yield concept
    
  def get_english_code(self): return self.code
  english_code = property(get_english_code)
    
  def get_translation(self, language):
    """Returns the preferred term for this concept, in the given language. Not supported by all terminology."""
    return self.term # No translation available in default implementation
    
  def get_translations(self, language):
    """Returns all concept's terms, in the given language. Not supported by all terminology."""
    return self.terms # No translation available in default implementation
  
class MonoaxialConcept(Concept):
  ancestors_no_double   = Concept.ancestors
  descendants_no_double = Concept.descendants
  
class MultiaxialConcept(Concept):
  def ancestors_no_double(self, already = None):
    if already is None: already = set()
    for parent in self.parents:
      if not parent in already:
        already.add(parent)
        yield parent
        for concept in parent.ancestors_no_double(already):
          yield concept
          
  def descendants_no_double(self, already = None):
    if already is None: already = set()
    for child in self.children:
      if not child in already:
        already.add(child)
        yield child
        for concept in child.descendants_no_double(already):
          yield concept
          
class CycleSafeMultiaxialConcept(MultiaxialConcept):
  def is_a(self, concept, already = None):
    if self is concept: return True
    if already is None: already = set([self])
    for parent in self.parents:
      if not parent in already:
        already.add(parent)
        if parent.is_a(concept, already): return True
    return False
  
class _StringCodeConcept(Concept):
  if sys.version[0] == "2":
    def __unicode__  (self): return u'%s[u"%s"]  # %s\n' % (self.terminology.name, self.code, self.term.replace(u"\n", u" "))
    def __repr__     (self): return unicode(self).encode("utf8")
    @staticmethod
    def canonize_code(code): return unicode(code)
  else:
    def __repr__     (self): return u'%s[u"%s"]  # %s\n' % (self.terminology.name, self.code, self.term.replace(u"\n", u" "))  
    @staticmethod
    def canonize_code(code): return str(code)
    
class _IntCodeConcept(Concept):
  @staticmethod
  def canonize_code(code): return int(code)
  if sys.version[0] == "2":
    def __unicode__(self): return u'%s[%s]  # %s\n' % (self.terminology.name, self.code, self.term.replace(u"\n", u" "))
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u'%s[%s]  # %s\n' % (self.terminology.name, self.code, self.term.replace(u"\n", u" "))
  


class Concepts(set):
  """A set of concepts. The set can contain each concept only once, and it
inherits from Python's :class:`set` the methods for computing intersection, union, difference, ..., of two sets.

.. automethod:: __rshift__
"""
  if sys.version[0] == "2":
    def __unicode__(self): return u"%s([\n  %s])" % (self.__class__.__name__, u", ".join([unicode(t) for t in self]))
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u"%s([\n  %s])" % (self.__class__.__name__, u", ".join([unicode(t) for t in self]))
  
  def __rshift__(self, destination_terminology):
    """Maps the set of concepts to the destination_terminology. See :doc:`tuto_en` for more info."""
    terminology_2_concepts = defaultdict(list)
    for concept in self: terminology_2_concepts[concept.terminology].append(concept)
    r = Concepts()
    for terminology, concepts in terminology_2_concepts.items():
      r.update((terminology >> destination_terminology).map_concepts(concepts))
    return r
  
  def find(self, parent_concept):
    """returns the first concept of the set that is a descendant of parent_concept (including parent_concept itself)."""
    for c in self:
      if c.is_a(parent_concept): return c

  def find_graphically(self, concept):
    for c in self:
      if hasattr(c, "is_graphically_a"):
        if c.is_graphically_a(concept): return c
      else:
        if c.is_a(concept): return c
        
  def imply(self, other):
    """returns true if all concepts in the OTHER set are descendants of (at least) one of the concept in this set."""
    for cb in other:
      for ca in self:
        if ca.imply(cb): break
      else:
        return False
    return True
  
  def is_semantic_subset(self, other):
    """returns true if all concepts in this set are descendants of (at least) one of the concept in the OTHER set."""
    for c1 in self:
      for c2 in other:
        if c1.is_a(c2): break
      else:
        return False
    return True
  
  def is_semantic_disjoint(self, other):
    """returns true if all concepts in this set are disjoint from all concepts in the OTHER set."""
    for c1 in self:
      for c2 in other:
        if c1.is_a(c2): return False
        if c2.is_a(c1): return False
    return True
  
  def keep_most_specific(self, more_specific_than = None):
    """keeps only the most specific concepts, i.e. remove all concepts that are more general that another concept in the set."""
    clone = self.copy()
    for t1 in clone:
      for t2 in more_specific_than or clone:
        if (not t1 is t2) and t1.is_a(t2): # t2 is more generic than t1 => we keep t1
          self.discard(t2)
          
  def keep_most_generic(self, more_generic_than = None):
    """keeps only the most general concepts, i.e. remove all concepts that are more specific that another concept in the set."""
    clone  = self.copy()
    clone2 = self.copy()
    for t1 in clone:
      for t2 in more_generic_than or clone2:
        if (not t1 is t2) and t1.is_a(t2): # t2 is more generic than t1 => we keep t2
          self  .discard(t1)
          clone2.discard(t1)
          break
          
  def extract(self, parent_concept):
    """returns all concepts of the set that are descendant of parent_concept (including parent_concept itself)."""
    return Concepts([c for c in self if c.is_a(parent_concept)])
  
  def subtract(self, parent_concept):
    """returns a new set after removing all concepts that are descendant of parent_concept (including parent_concept itself)."""
    return Concepts([c for c in self if not c.is_a(parent_concept)])
    
  def subtract_update(self, parent_concept):
    """same as `func`:subtract, but modify the set *in place*."""
    for c in set(self):
      if c.is_a(parent_concept): self.discard(c)
      
  def remove_complete_families(self, only_family_with_more_than_one_child = 1):
    modified = 1
    while modified:
      modified = 0
      clone = self.copy()
      if only_family_with_more_than_one_child:
        parents = set([p for i in self for p in i.parents if len(p.children) > 1])
      else:
        parents = set([p for i in self for p in i.parents])
        
      while parents:
        t = parents.pop()
        children = set(t.children)
        if children.issubset(clone):
          modified = 1
          for i in self.copy():
            if i.is_a(t): self.remove(i)
          for i in parents.copy():
            if i.is_a(t): parents.remove(i)
          self.add(t)
  
          
  def lowest_common_ancestors(self):
    """returns the lowest common ancestors between this set of concepts."""
    if len(self) == 0: return None
    if len(self) == 1: return Concepts(self)
    
    ancestors = [set(concept.self_and_ancestors_no_double()) for concept in self]
    common_ancestors = Concepts(reduce(operator.and_, ancestors))
    r = Concepts()
    common_ancestors.keep_most_specific()
    return common_ancestors

  def all_subsets(self):
    """returns all the subsets included in this set."""
    l = [Concepts()]
    for concept in self:
      for concepts in l[:]:
        l.append(concepts | set([concept]))
    return l
  
  def __and__             (s1, s2): return s1.__class__(set.__and__(s1, s2))
  def __or__              (s1, s2): return s1.__class__(set.__or__(s1, s2))
  def __sub__             (s1, s2): return s1.__class__(set.__sub__(s1, s2))
  def __xor__             (s1, s2): return s1.__class__(set.__xor__(s1, s2))
  def difference          (s1, s2): return s1.__class__(set.difference(s1, s2))
  def intersection        (s1, s2): return s1.__class__(set.intersection(s1, s2))
  def symmetric_difference(s1, s2): return s1.__class__(set.symmetric_difference(s1, s2))
  def union               (s1, s2): return s1.__class__(set.union(s1, s2))
  def copy                (s1):     return s1.__class__(s1)



class ModifiedConcept(Concept):
  def __init__(self, origin, modifiers, term = None):
    term = term or origin.term
    self.code        = "%s:%s" % (origin.code, u":".join(modifier.code for modifier in modifiers))
    self.origin      = origin
    self.modifiers   = modifiers
    self.term        = term or origin.term
    self.terminology = origin.terminology
    if term != origin.term: self.terms = [term]
    
  def __rshift__(self, destination_terminology):
    if destination_terminology is self.terminology: return Concepts([self])
    if destination_terminology.name == u"VCM":
      mappeds = (self.terminology >> destination_terminology)(self.origin)
      #vcm_modifiers = [modifier for modifier in self.modifiers if modifier.terminology.name == u"VCM"]
      vcm_lexs      = [lex for modifier in self.modifiers if modifier.terminology.name == u"VCM" for lex in modifier.lexs if not lex.empty]
      return Concepts(mapped.derive_lexs(vcm_lexs) for mapped in mappeds)
        
    return Concepts(ModifiedConcept(mapped, self.modifiers) for mapped in (self.terminology >> destination_terminology)(self.origin))
  
  def __hash__(self): return hash((self.origin, frozenset(self.modifiers), self.term))
  
  def __eq__(self, other):
    if not isinstance(other, ModifiedConcept): return False
    return (self.origin == other.origin) and (self.modifiers == other.modifiers)
  
  def is_a(self, other):
    if not isinstance(other, ModifiedConcept): return None
    if not self.origin.est_un(other.origin): return None
    for modificateur_o in other.modificateurs:
      for modificateur_s in self.modificateurs:
        if modificateur_s.est_un(modificateur_o): break
      else: return None
    return 1
  imply = is_a
  
  if sys.version[0] == "2":
    def __unicode__(self): return u'get_concept("%s")'% self.full_code()
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u'get_concept("%s")'% self.full_code()
    
  def full_code(self):
    if self.term != self.origin.term: return u":".join([self.origin.full_code()] + [modifier.full_code() for modifier in self.modifiers] + [self.term])
    return u":".join([self.origin.full_code()] + [modifier.full_code() for modifier in self.modifiers])
  
  def tuple(self):
    tuple = [self.origin.terminology.name, self.origin.code]
    for modifier in self.modifiers:
      tuple.append(modifier.terminology.name)
      tuple.append(modifier.code)
    if self.term != self.origin.term: tuple.append(self.term)
    return tuple
  
  #def get_icones(self):
  #  icones = self.origin.get_icones()
  #  for modificateur in self.modificateurs:
  #    icones = [icone.applique_modificateur(modificateur) for icone in icones]
  #  return set(icones)
  
  #def get_icones_codes(self):
  #  return set(icone.code for icone in self.get_icones())

def is_one_of(concept, *parents):
  for parent in parents:
    if concept.is_a(parent): return parent


def _pair_2_concept(classif, code):
  terminology = TERMINOLOGIES.get(classif.upper())
  if not terminology: raise UnknownTerminologyError(classif)
  concept = terminology.get(code)
  if not concept: raise UnknownConceptError(classif, code)
  return concept

def _tuple_2_concept(tuple):
  nb = len(tuple)
  if nb < 2: raise ValueError(tuple)
  origin = _pair_2_concept(tuple[0], tuple[1])
  if nb == 2: return origin
  
  mods = [_pair_2_concept(tuple[i], tuple[i + 1]) for i in range(2, nb - 1, 2)]
  if (nb // 2) != (nb / 2.0): term = tuple[-1]
  else:                       term = None
  if (not mods) and (term == origin.term): return origin
  return ModifiedConcept(origin, mods, term)

def get_concept(full_code):
  """Return a concept from a 'full code' including both terminology name and concept code (for example "icd10:I10")."""
  return _tuple_2_concept(full_code.split(":"))


_MAPPINGS = {}

class Mapping(object):
  """Base class for a mapping between two terminologies.

.. automethod:: __call__
"""
  def __init__(self, terminology1, terminology2):
    self.terminology1 = terminology1 #: origin terminology for the mapping
    self.terminology2 = terminology2 #: destination terminology for the mapping
    
  def register(self):
    """Registers the mapping as the default mapping between its origin and destination terminologies."""
    _MAPPINGS[self.terminology1, self.terminology2] = self
    
  def __rshift__(self, other):
    """Chains this mapping with another mapping, and returns the resulting mapping. See :doc:`tuto_en` for more info."""
    if   isinstance(self, ChainMapping):  mappings  = list(self.mappings)
    else:                                 mappings  = [self]
    if   isinstance(other, ChainMapping): mappings +=  other.mappings
    elif isinstance(other, Mapping):      mappings += [other.mappings]
    else:                                 mappings += [mappings[-1].terminology2 >> other]
    return ChainMapping(mappings)
  
  if sys.version[0] == "2":
    def __unicode__(self): return u"<Mapping from %s to %s>" % (self.terminology1, self.terminology2)
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u"<Mapping from %s to %s>" % (self.terminology1, self.terminology2)
    
  def map_concepts(self, concepts, use_ancestors = True): pass
  
  def __call__(self, concepts):
    """Maps the given concept(s) using this mapping.

.. note:: You only need this method if you have several mappings with the same origin and destination terminologies.
   In other situations, you should rather use ``concept(s) >> destination_terminology``.
"""
    if isinstance(concepts, Concept):  concepts = [concepts]
    return self.map_concepts(concepts)
  
class ChainMapping(Mapping):
  def __init__(self, mappings):
    self.mappings = mappings
    Mapping.__init__(self, mappings[0].terminology1, mappings[-1].terminology2)
    
  def map_concepts(self, concepts, use_ancestors = True):
    for mapping in self.mappings: concepts = mapping.map_concepts(concepts)
    return concepts

  
class SQLMapping(Mapping):
  def __init__(self, terminology1, terminology2, db_filename, has_and = 1, reversed = 0, get_concept_parents = None):
    Mapping.__init__(self, terminology1, terminology2)
    if isinstance(db_filename, str):
      self.db                 = sql_module.connect(db_filename)
      self.db_cursor          = self.db.cursor()
    else:
      self.db_cursor          = db_filename
    self.db_cursor.execute("PRAGMA query_only = TRUE;")
    
    self._has_and             = has_and
    self.reversed             = reversed
    if not reversed:
      self._SQL_MAP_CONCEPT = u"SELECT match_type, code2 FROM Mapping WHERE code1=?"
      self._SQL_MAP_AND     = u"SELECT mapping_id FROM MappingAnd1 WHERE code=?"
      self._SQL_MAP_AND1    = u"SELECT match_type, code FROM MappingAnd1 WHERE mapping_id=?"
      self._SQL_MAP_AND2    = u"SELECT code FROM MappingAnd2 WHERE mapping_id=?"
    else:
      self._SQL_MAP_CONCEPT = u"SELECT match_type, code1 FROM Mapping WHERE code2=?"
      self._SQL_MAP_AND     = u"SELECT mapping_id FROM MappingAnd2 WHERE code=?"
      self._SQL_MAP_AND1    = u"SELECT match_type, code FROM MappingAnd2 WHERE mapping_id=?"
      self._SQL_MAP_AND2    = u"SELECT code FROM MappingAnd1 WHERE mapping_id=?"
      
    if get_concept_parents: self._get_concept_parents = get_concept_parents
    
  def _create_reverse_mapping(self):
    return SQLMapping(self.terminology2, self.terminology1, self.db_cursor, has_and = self._has_and, reversed = not self.reversed)
  
  def _get_concept_parents(self, concept): return concept.parents
      
  def map_concepts(self, concepts, use_ancestors = True, cumulated_concepts = None):
    r                          = Concepts()
    cumulated_concepts         = cumulated_concepts or set(concepts)
    concepts_partially_matched = Concepts(concepts)
    
    if self._has_and:
      mapping_ids = set()
      for concept in concepts:
        self.db_cursor.execute(self._SQL_MAP_AND, (concept.english_code,))
        for (mapping_id,) in self.db_cursor.fetchall(): mapping_ids.add(mapping_id)
        
      for mapping_id in mapping_ids:
        concepts_in_and = Concepts()
        self.db_cursor.execute(self._SQL_MAP_AND1, (mapping_id,))
        for (match_type, code1) in self.db_cursor.fetchall():
          concept = self.terminology1[code1]
          concepts_in_and.add(concept)
          if not concept in cumulated_concepts: break
        else:
          self.db_cursor.execute(self._SQL_MAP_AND2, (mapping_id,))
          for (code2,) in self.db_cursor.fetchall():
            r.add(self.terminology2[code2])
          if match_type == u"=":
            concepts_partially_matched.difference_update(concepts_in_and)
          
    for concept in tuple(concepts_partially_matched):
      exact_matches   = Concepts()
      partial_matches = Concepts()
      self.db_cursor.execute(self._SQL_MAP_CONCEPT, (concept.english_code,))
      for (match_type, code2) in self.db_cursor.fetchall():
        if not self.reversed: match_type = match_type[0]
        else:                 match_type = match_type[1]
        if   match_type == u"=": exact_matches  .add(self.terminology2[code2])
        elif match_type == u"~": partial_matches.add(self.terminology2[code2])
        #print unicode(concept).replace("\n", ""), match_type, unicode(self.terminology2[code2]).replace("\n", "")
        
      if exact_matches:
        r.update(exact_matches)
        concepts_partially_matched.discard(concept)
      else:
        r.update(partial_matches)
        
    if concepts_partially_matched and use_ancestors:
      concepts = Concepts(sum([self._get_concept_parents(concept) for concept in concepts_partially_matched], []))
      if concepts and not concepts.issubset(cumulated_concepts):
        cumulated_concepts.update(concepts)
        r.update(self.map_concepts(concepts, use_ancestors, cumulated_concepts))
    return r
        

class SameCodeMapping(Mapping):
  def _create_reverse_mapping(self): return SameCodeMapping(self.terminology2, self.terminology1)
  def map_concepts(self, concepts):
    #return Concepts([self.terminology2[concept.english_code] for concept in concepts])
    r = Concepts()
    for concept in concepts:
      try:
        c = self.terminology2[concept.english_code]
        r.add(c)
      except ValueError: pass
    return r

  
def connect_sqlite3(base_filename, read_only=True):
    """Open existing DB in DATA_DIR as sqlite3 DB
    Connection will be read-only if read_only and READ_ONLY_DATABASE
    """
    path = '%s.sqlite3' % os.path.join(DATA_DIR, base_filename)
    if not os.path.exists(path):
      raise IOError('Database %s not available. Please build, or set pymedtermino.DATA_DIR correctly' % path)
    db = sql_module.connect(path)
    if READ_ONLY_DATABASE and read_only:
      db.cursor().execute("PRAGMA query_only = TRUE;")
    return db
