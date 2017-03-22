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

import sys, os, os.path, stat, sqlite3

if sys.version[0] == "2":
  from StringIO import StringIO
else:
  from io import StringIO
  def unicode(s):
    if isinstance(s, str): return s
    return repr(s)

from pymedtermino.utils.db import *

class MappingAnd(list):
  if sys.version[0] == "2":
    def __unicode__(self): return u"MappingAnd(%s)" % list.__repr__(self)
    def __repr__   (self): return unicode(self).encode("utf8")
  else:
    def __repr__   (self): return u"MappingAnd(%s)" % list.__repr__(self)

def parse_mapping(mapping_txt, reverse = 0):
  lines            = mapping_txt.split(u"\n")
  mappings         = []
  line_n           = 0
  for line in lines:
    line_n += 1
    if u"#" in line: line = line.split(u"#")[0]
    if not line.strip(): continue
    for match_type in [u"==", u"~=", u"=~", u"~~"]:
      if match_type in line:
        codes1, codes2 = line.split(match_type)
        break
    else: raise ValueError("No match at line %s: '%s'!" % (line_n, repr(line)))
    
    if reverse:
      codes1, codes2 = codes2, codes1
      match_type = match_type[::-1]
    codes1 = codes1.split()
    codes2 = codes2.split()
    for code1 in codes1:
      for code2 in codes2:
        and1 = MappingAnd(i.strip() for i in code1.split(u"+"))
        and2 = MappingAnd(i.strip() for i in code2.split(u"+"))
        mappings.append((and1, match_type, and2))
  return mappings


def Txt_2_SQLMapping(txt_filename, db, code1_type = "INTEGER", code2_type = "INTEGER", reverse = 0, txt = None):
  db_cursor = db.cursor()
  
  if txt_filename: txt = read_file(txt_filename, "utf8")
  mappings = parse_mapping(txt, reverse = reverse)
  HAS_AND  = 0
  for left, match_type, right in mappings:
    if (len(left) > 1) or (len(right) > 1):
      HAS_AND = 1
      break
    
  do_sql(db_cursor, u"""
CREATE TABLE Mapping (
  id         INTEGER PRIMARY KEY,
  code1      %s,
  match_type TEXT,
  code2      %s
);""" % (code1_type, code2_type))
  
  if HAS_AND:
    do_sql(db_cursor, u"""
CREATE TABLE MappingAnd1 (
  id         INTEGER PRIMARY KEY,
  mapping_id INTEGER,
  match_type TEXT,
  code       %s
);""" % (code1_type))
    do_sql(db_cursor, u"""
CREATE TABLE MappingAnd2 (
  id         INTEGER PRIMARY KEY,
  mapping_id INTEGER,
  match_type TEXT,
  code       %s
);""" % (code2_type))
    AND_ID = 1
    
  for left, match_type, right in mappings:
    if (len(left) > 1) or (len(right) > 1):
      for left_ in left:
        do_sql(db_cursor, u"""INSERT INTO MappingAnd1 VALUES (NULL, ?, ?, ?)""", (AND_ID, match_type[0], left_))
      for right_ in right:
        do_sql(db_cursor, u"""INSERT INTO MappingAnd2 VALUES (NULL, ?, ?, ?)""", (AND_ID, match_type[1], right_))
      AND_ID += 1
    else:
      do_sql(db_cursor, u"""INSERT INTO Mapping VALUES (NULL, ?, ?, ?)""", (left[0], match_type, right[0]))
      
  do_sql(db_cursor, u"""CREATE INDEX Mapping_code1_index ON Mapping(code1)""")
  do_sql(db_cursor, u"""CREATE INDEX Mapping_code2_index ON Mapping(code2)""")
  
  if HAS_AND:
    do_sql(db_cursor, u"""CREATE INDEX MappingAnd1_code_index ON MappingAnd1(code)""")
    do_sql(db_cursor, u"""CREATE INDEX MappingAnd2_code_index ON MappingAnd2(code)""")
    do_sql(db_cursor, u"""CREATE INDEX MappingAnd1_mapping_id_index ON MappingAnd1(mapping_id)""")
    do_sql(db_cursor, u"""CREATE INDEX MappingAnd2_mapping_id_index ON MappingAnd2(mapping_id)""")
    



  
def OWL_2_SQL(owl_filenames, db, code_type = u"INTEGER", annotations = []):
  db_cursor = db.cursor()
  
  OWL_CONCEPTS = {}
  from collections import defaultdict
  class OWLConcept(object):
    def __init__(self, code):
      self.code        = code
      self.terms       = {}
      self.relations   = defaultdict(set)
      self.annotations = defaultdict(u"".__class__)
      OWL_CONCEPTS[self.code] = self

    def get_annotation_with_type(self, lang, name, type):
      a = self.get_annotation(lang, name)
      if   type == "INTEGER"  :
        if a == u"": a = 0
        else:        a = int(a)
      elif type == "FLOAT":
        if a == u"": a = 0.0
        else:        a = float(a)
      return a
    def get_annotation(self, lang, name):
      a = self.annotations.get((lang, name), None)
      if not a is None: return a
      a = self.annotations.get((u"", name), None)
      if not a is None: return a
      a = self.annotations.get((u"en", name), None)
      if not a is None: return a
      return u""
      
  def get_concept(uri):
    fichier, code = unicode(uri).split(u"#")
    return OWL_CONCEPTS.get(code) or OWLConcept(code)

  do_sql(db_cursor, u"""
CREATE TABLE Concept (
  id     INTEGER PRIMARY KEY,
  code   %s,
  lang   TEXT,
  term   TEXT %s
);""" % (code_type, u"".join(",\n  %s %s" % annotation for annotation in annotations)))
  do_sql(db_cursor, u"""
CREATE TABLE Relation (
  id          INTEGER PRIMARY KEY,
  source      %s,
  relation    TEXT,
  destination %s
);
""" % (code_type, code_type))
  
  is_a = OWLConcept(u"0")
  is_a.terms["fr"] = u"est_un"
  is_a.terms["en"] = u"is_a"
  
  import xml.sax as sax, xml.sax.handler as handler
  class Parser(handler.ContentHandler):
    def __init__(self):
      self.classes = []
      self.balises = []
      self.on_prop = u""
      
    def startElement(self, balise, attrs):
      self.balises.append(balise)
      self.current_content = u""
      
      if   (balise == u"owl:Class") or (balise == u"owl:ObjectProperty"):
        if (u"rdf:about" in attrs) and (attrs[u"rdf:about"] != u"Thing"):
          concept = get_concept(attrs[u"rdf:about"])
          self.classes.append(concept)
        else:
          self.classes.append(None)
          
      elif balise == u"rdfs:label":
        self.lang = attrs[u"xml:lang"]
          
      elif balise == u"rdfs:subClassOf":
        if u"rdf:resource" in attrs:
          self.classes[-1].relations[is_a].add(get_concept(attrs[u"rdf:resource"]))
        
      elif balise == u"owl:onProperty":
        if u"rdf:resource" in attrs:
          self.on_prop = get_concept(attrs[u"rdf:resource"])
          
      elif balise == u"owl:someValuesFrom":
        if u"rdf:resource" in attrs:
          if (self.balises[-2] == u"owl:Restriction") and (self.balises[-3] == u"rdfs:subClassOf") and (self.balises[-4] == u"owl:Class"): 
            self.classes[-1].relations[self.on_prop].add(get_concept(attrs[u"rdf:resource"]))
            
      else:
        self.on_prop = u""
        self.lang = attrs.get(u"xml:lang", u"")
        
    def characters(self, content):
      self.current_content += content
      
    def characters2(self, content):
      if self.balises[-1] == u"rdfs:label":
        if self.classes:
          self.classes[-1].terms[self.lang] = self.classes[-1].terms.get(self.lang, u"") + content
      else:
        balise = self.balises[-1]
        if u":" in balise: balise = balise.split(u":")[-1]
        for annotation_name, annotation_type in annotations:
          if balise == annotation_name:
            self.classes[-1].annotations[self.lang, annotation_name] += content
            break
          
    def endElement(self, balise):
      self.characters2(self.current_content)
      
      del self.balises[-1]
      if balise == u"owl:Class":
        del self.classes[-1]
        
  parser = Parser()
  for filename in owl_filenames:
    sax.parseString(read_file(filename, encoding = None), parser)

  for concept in OWL_CONCEPTS.values():
    for lang, term in concept.terms.items():
      do_sql(db_cursor, u"""INSERT INTO Concept VALUES(NULL, ?, ?, ?%s);""" % (u", ?" * len(annotations)),
             [concept.code, lang, term] + [concept.get_annotation_with_type(lang, annotation_name, annotation_type) for annotation_name, annotation_type in annotations])
      
  for concept in OWL_CONCEPTS.values():
    for relation, destinations in concept.relations.items():
      for destination in destinations:
        do_sql(db_cursor, u"""INSERT INTO Relation VALUES(NULL, ?, ?, ?)""",
               (concept.code, relation.terms["en"], destination.code))
        
  do_sql(db_cursor, u"""CREATE INDEX Concept_code_lang_index ON Concept(code, lang)""")
  do_sql(db_cursor, u"""CREATE INDEX Relation_source_relation_index ON Relation(source, relation)""")
  do_sql(db_cursor, u"""CREATE INDEX Relation_destination_relation_index ON Relation(destination, relation)""")



def index_terminology_by_vcm_lexicon(terminology, db, code_type = "INTEGER"):
  from collections import defaultdict
  from pymedtermino.vcm import VCM
  
  db_cursor = db.cursor()
  do_sql(db_cursor, u"""
CREATE TABLE VCMLexiconIndex (
  id     INTEGER PRIMARY KEY,
  code   %s,
  lex    INTEGER
);""" % code_type)

  for concept in terminology.all_concepts_no_double():
    icons = concept >> VCM
    lexs = set(lex for icon in icons for lex in icon.lexs if (not lex.empty) and (not lex.abstract))
    for lex in lexs:
      do_sql(db_cursor, u"""INSERT INTO VCMLexiconIndex VALUES (NULL, ?, ?)""", (concept.code, lex.code))
      
  do_sql(db_cursor, u"""CREATE INDEX VCMLexiconIndex_lex_index ON VCMLexiconIndex(lex)""")
  
  
