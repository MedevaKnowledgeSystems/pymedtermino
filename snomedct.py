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
pymedtermino.snomedct
*********************

PyMedtermino module for SNOMEDCT.

.. class:: SNOMEDCT
   
   The SNOMED CT terminology. See :class:`pymedtermino.Terminology` for common terminology members; only SNOMED CT-specific members are described here.
   
   .. automethod:: CORE_problem_list

"""

__all__ = ["SNOMEDCT", "Group"]

import sys, os, os.path
import pymedtermino


db        = pymedtermino.connect_sqlite3("snomedct")
db_cursor = db.cursor()
db_cursor.execute("PRAGMA synchronous  = OFF;")
db_cursor.execute("PRAGMA journal_mode = OFF;")

import atexit
atexit.register(db.close)

class SNOMEDCT(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "SNOMEDCT")
    
  def _create_Concept(self): return SNOMEDCTConcept
  
  def first_levels(self):
    return [self[code] for code in [u"123037004", u"404684003", u"308916002", u"272379006", u"106237007", u"363787002", u"410607006", u"373873005", u"78621006", u"260787004", u"71388002", u"362981000", u"419891008", u"243796009", u"48176007", u"370115009", u"123038009", u"254291000", u"105590001"]]
  
  def search(self, text):
    #db_cursor.execute("SELECT DISTINCT conceptId FROM Description WHERE term LIKE ?", ("%%%s%%" % text,))
    if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
      db_cursor.execute("SELECT DISTINCT Description.conceptId FROM Concept, Description, Description_fts WHERE (Description_fts.term MATCH ?) AND (Description.id = Description_fts.docid) AND (Concept.id = Description.conceptId) AND (Concept.active = 1)", (text,))
    else:
      db_cursor.execute("SELECT DISTINCT Description.conceptId FROM Description, Description_fts WHERE (Description_fts.term MATCH ?) AND (Description.id = Description_fts.docid)", (text,))
      
    r = db_cursor.fetchall()
    l = []
    for (code,) in r:
      try: l.append(self[code])
      except ValueError: pass
    return l
  
  def CORE_problem_list(self):
    """Returns a generator iterating over all SNOMED CT concepts that are included in the CORE problem list."""
    pymedtermino.snomedct.db_cursor.execute("SELECT Id FROM Concept WHERE is_in_core = 1")
    for (code,) in pymedtermino.snomedct.db_cursor.fetchall():
      yield self[code]
      
      
class Group(object):
  """A group, grouping several SNOMED CT relation together in the definition of a Concept."""
  
  def __init__(self): self.relations = set()

  def add_relation(self, rel, concept):
    if isinstance(concept, pymedtermino.Concept):
      if rel in self.relations:
        getattr(self, rel).add(concept)
      else:
        self.relations.add(rel)
        setattr(self, rel, pymedtermino.Concepts([concept]))
    else:
      if rel in self.relations:
        getattr(self, rel).update(concept)
      else:
        self.relations.add(rel)
        setattr(self, rel, pymedtermino.Concepts(concept))
      
  def imply(a, b):
    if not b.relations.issubset(a.relations): return 0
    for relation in b.relations:
      if not getattr(a, relation).imply(getattr(b, relation)): return 0
    return 1
    
  def __repr__(self):
    return "<Group %s>" % "; ".join(["%s %s" % (rel, ", ".join([concept.term for concept in getattr(self, rel)])) for rel in self.relations])
  

if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS: _parent_class = pymedtermino.MultiaxialConcept
else:                                       _parent_class = pymedtermino.CycleSafeMultiaxialConcept

class SNOMEDCTConcept(_parent_class, pymedtermino._IntCodeConcept):
  """A SNOMED CT concept. See :class:`pymedtermino.Concept` for common terminology members; only SNOMED CT-specific members are described here.

.. attribute:: is_in_core
   
   True if this concept belongs to the SNOMED CT CORE problem list.

.. attribute:: groups
   
   A list of the groups in the concept's definition. Each group include one or more relations, grouped together.

.. attribute:: out_of_group
   
   A special group that includes all relations that do *not* belongs to a group.

.. attribute:: active
   
   True if this concept is still active in SNOMED CT; False if it has been removed.

.. attribute:: definition_status
   
.. attribute:: module

Additional attributes are available for relations, and are listed in the :attr:`relations <pymedtermino.Concept.relations>` attribute.
"""
  
  def __init__(self, code):
    if pymedtermino.REMOVE_SUPPRESSED_CONCEPTS:
      db_cursor.execute("SELECT active FROM Concept WHERE id=?", (code,))
      if db_cursor.fetchone()[0] != 1: raise ValueError()
      
      db_cursor.execute("SELECT term FROM Description WHERE conceptId=? AND typeId=900000000000003001 AND active=1", (code,))
      self.active = 1
      
    else:
      db_cursor.execute("SELECT term FROM Description WHERE conceptId=? AND typeId=900000000000003001", (code,))
      
    r = db_cursor.fetchone()
    if not r: raise ValueError()
    pymedtermino.MultiaxialConcept.__init__(self, code, r[0])
    
  def __getattr__(self, attr):
    if   attr == "parents":
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT destinationId FROM Relationship WHERE sourceId=? AND typeId=116680003 AND active=1", (self.code,)) # 116680003 = is_a
      else:
        db_cursor.execute("SELECT DISTINCT destinationId FROM Relationship WHERE sourceId=? AND typeId=116680003", (self.code,)) # 116680003 = is_a
        
      self.parents = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      return self.parents
    
    elif attr == "children":
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT sourceId FROM Relationship WHERE destinationId=? AND typeId=116680003 AND active=1", (self.code,)) # 116680003 = is_a
      else:
        db_cursor.execute("SELECT DISTINCT sourceId FROM Relationship WHERE destinationId=? AND typeId=116680003", (self.code,)) # 116680003 = is_a
        
      self.children = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      return self.children
    
    elif attr == "relations":
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT typeId FROM Relationship WHERE sourceId=? AND active=1", (self.code,))
      else:
        db_cursor.execute("SELECT DISTINCT typeId FROM Relationship WHERE sourceId=?", (self.code,))
        
      self.relations = set(code_2_relation[rel] for (rel,) in db_cursor.fetchall() if rel != 116680003) # 116680003 = is_a
      
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT typeId FROM Relationship WHERE destinationId=? AND active=1", (self.code,))
      else:
        db_cursor.execute("SELECT DISTINCT typeId FROM Relationship WHERE destinationId=?", (self.code,))
        
      for (rel,) in db_cursor.fetchall():
        if rel != 116680003:
          self.relations.add("INVERSE_%s" % code_2_relation[rel])
      return self.relations
    
    elif (attr == "groups") or (attr == "out_of_group"):
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT relationshipGroup, typeId, destinationId FROM Relationship WHERE sourceId=? AND active=1", (self.code,))
      else:
        db_cursor.execute("SELECT DISTINCT relationshipGroup, typeId, destinationId FROM Relationship WHERE sourceId=?", (self.code,))
        
      data = db_cursor.fetchall()
      groups = [Group() for i in range(1 + max([0] + [group_id for (group_id, rel, code) in data]))]
      for (group_id, rel, code) in data:
        if rel == 116680003: continue # 116680003 = is_a
        group = groups[group_id]
        group.add_relation(code_2_relation[rel], self.terminology[code])
      self.groups       = [group for group in groups[1:] if group.relations] # Pourquoi y a-t-il des groupes vides dans la SNOMED CT ???
      self.out_of_group = groups[0]
      if attr == "groups": return self.groups
      else:                return self.out_of_group
      
    elif attr in relation_2_code:
      relation_code = relation_2_code[attr]
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT destinationId FROM Relationship WHERE sourceId=? AND typeId=? AND active=1", (self.code, relation_code))
      else:
        db_cursor.execute("SELECT DISTINCT destinationId FROM Relationship WHERE sourceId=? AND typeId=?", (self.code, relation_code))
        
      l = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      setattr(self, attr, l)
      return l
    
    elif attr.startswith(u"INVERSE_"):
      relation_code = relation_2_code[attr[8:]]
      if pymedtermino.REMOVE_SUPPRESSED_RELATIONS and self.active:
        db_cursor.execute("SELECT DISTINCT sourceId FROM Relationship WHERE destinationId=? AND typeId=? AND active=1", (self.code, relation_code))
      else:
        db_cursor.execute("SELECT DISTINCT sourceId FROM Relationship WHERE destinationId=? AND typeId=?", (self.code, relation_code))
        
      l = [self.terminology[code] for (code,) in db_cursor.fetchall()]
      setattr(self, attr, l)
      return l
    
    elif attr == "active":
      db_cursor.execute("SELECT active FROM Concept WHERE id=?", (self.code,))
      self.active = db_cursor.fetchone()[0]
      return self.active
    
    elif attr == "terms":
      if pymedtermino.REMOVE_SUPPRESSED_TERMS and self.active:
        db_cursor.execute("SELECT term FROM Description WHERE conceptId=? AND active=1", (self.code,))
      else:
        db_cursor.execute("SELECT term FROM Description WHERE conceptId=?", (self.code,))
      self.terms = [l[0] for l in db_cursor.fetchall()]
      return self.terms
    
    elif attr == "definition_status":
      db_cursor.execute("SELECT definitionStatusId FROM Concept WHERE id=?", (self.code,))
      self.definition_status = SNOMEDCT[db_cursor.fetchone()[0]]
      return self.definition_status
    
    elif attr == "module":
      db_cursor.execute("SELECT moduleId FROM Concept WHERE id=?", (self.code,))
      self.module = SNOMEDCT[db_cursor.fetchone()[0]]
      return self.module
    
    elif attr == "is_in_core":
      db_cursor.execute("SELECT is_in_core FROM Concept WHERE id=?", (self.code,))
      self.is_in_core = int(db_cursor.fetchone()[0])
      return self.is_in_core
    
    raise AttributeError(attr)
  
  def is_part_of(self, concept, already = None):
    if self is concept: return True
    if already is None: already = set([self])
    if u"part_of" in self.relations: parents = set(self.parents + self.part_of)
    else:                           parents =     self.parents
    for parent in parents:
      if not parent in already:
        already.add(parent)
        if parent.is_part_of(concept, already): return True
    return False
  
  def descendant_parts(self):
    """Returns the sub-parts of this concept, recursively."""
    if u"INVERSE_part_of" in self.relations:
      for child in self.INVERSE_part_of:
        yield child
        for concept in child.descendant_parts():
          yield concept
          
  def ancestor_parts(self):
    """Returns the super-part of this concept, recursively."""
    if u"part_of" in self.relations:
      for parent in self.part_of:
        yield parent
        for concept in parent.ancestor_parts():
          yield concept
          
  def associated_clinical_findings(self):
    """Return the clinical finding concepts associated to this concept (which is expected to be a anatomical structure, a morphology, etc)."""
    r = pymedtermino.Concepts()
    for i in set(self.self_and_descendants()) | set(self.descendant_parts()):
      for relation in MAIN_CLINICAL_FINDING_RELATIONS:
        relation = "INVERSE_%s" % relation
        if relation in i.relations:
          for j in getattr(i, relation):
            if j.is_a(SNOMEDCT[404684003]): r.add(j)
    return r

SNOMEDCT = SNOMEDCT()


MAIN_CLINICAL_FINDING_RELATIONS = set([
  "part_of",
  "temporal_context",
  "finding_site",
  "associated_morphology",
  "has_interpretation",
  "interprets",
  "has_definitional_manifestation",
  "pathological_process",
  "has_focus",
  "causative_agent",
  
  "associated_with", # Discutable...
  "due_to",
  ])
 
code_2_relation = {
  131195008 : u"subject_of_information",
  42752001  : u"due_to",
  309824003 : u"instrumentation",
  246112005 : u"severity",
  367346004 : u"measures",
  363589002 : u"associated_procedure",
  272741003 : u"laterality",
  363701004 : u"direct_substance",
  405813007 : u"procedure_site_direct",
  370133003 : u"specimen_substance",
  370134009 : u"time_aspect",
  408730004 : u"procedure_context",
  260858005 : u"extent",
  419066007 : u"finding_informer",
  263535000 : u"communication_with_wound",
  425391005 : u"using_access_device",
  370127007 : u"access_instrument",
  118170007 : u"specimen_source_identity",
  363700003 : u"direct_morphology",
  370132008 : u"scale_type",
  246100006 : u"onset",
  363713009 : u"has_interpretation",
  116676008 : u"associated_morphology",
  116683001 : u"associated_function",
  118168003 : u"specimen_source_morphology",
  308489006 : u"pathological_process",
  424361007 : u"using_substance",
  363705008 : u"has_definitional_manifestation",
  408729009 : u"finding_context",
  260686004 : u"method",
  263502005 : u"clinical_course",
  246267002 : u"location",
  363710007 : u"indirect_device",
  116686009 : u"has_specimen",
  363715002 : u"associated_etiologic_finding",
  261583007 : u"using",
  363699004 : u"direct_device",
  363709002 : u"indirect_morphology",
  246456000 : u"episodicity",
  260870009 : u"priority",
  116680003 : u"is_a",
  405816004 : u"procedure_morphology",
  363704007 : u"procedure_site",
  123005000 : u"part_of",
  246093002 : u"component",
  260669005 : u"approach",
  370130000 : u"property",
  408731000 : u"temporal_context",
  255234002 : u"after",
  363714003 : u"interprets",
  424226004 : u"using_device",
  363698007 : u"finding_site",
  405815000 : u"procedure_device",
  363703001 : u"has_intent",
  47429007  : u"associated_with",
  246090004 : u"associated_finding",
  370135005 : u"pathological_process",
  424876005 : u"surgical_approach",
  418775008 : u"finding_method",
  411116001 : u"has_dose_form",
  260908002 : u"course",
  363708005 : u"temporally_follows",
  408732007 : u"subject_relationship_context",
  127489000 : u"has_active_ingredient",
  258214002 : u"stage",
  424244007 : u"using_energy",
  410675002 : u"route_of_administration",
  370129005 : u"measurement_method",
  246513007 : u"revision_status",
  405814001 : u"procedure_site_indirect",
  246454002 : u"occurrence",
  118171006 : u"specimen_procedure",
  363702006 : u"has_focus",
  260507000 : u"access",
  116678009 : u"has_measured_component",
  370131001 : u"recipient_category",
  246075003 : u"causative_agent",
  118169006 : u"specimen_source_topography",
}
relation_2_code = dict((relation, code) for (code, relation) in code_2_relation.items())


#if __name__ == "__main__":
#  relation_codes = {}
#  db_cursor.execute("select distinct typeId from Relationship")
#  codes = db_cursor.fetchall()
#  for code, in codes:
#    db_cursor.execute("select term from Description where conceptId=? and typeId=900000000000013009", (code,))
#    relation_codes[code] = db_cursor.fetchone()[0].lower().replace(" ", "_").replace("_-_", "_")
#  print "code_2_relation = {"
#  for code in relation_codes: print '''  %s : u"%s",''' % (code, relation_codes[code])
#  print "}"
