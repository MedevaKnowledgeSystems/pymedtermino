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

from __future__ import print_function

import sys, os, fcntl, time, subprocess
try:
  import ontopy
except ImportError:
  import owlready as ontopy

from pymedtermino.utils.db import *

if sys.version[0] == "2":
  from StringIO import StringIO
  def encode(s): return s.encode("utf8")
  def decode(s): return s.decode("utf8")
else:
  from io import StringIO
  def encode(s): return s
  def decode(s):
    if isinstance(s, bytes): return s.decode("utf8")
    return s


NB_PROCESSORS = 3

OWL_FILES = {}

class OWLFile(object):
  def __init__(self, prefix = u"", import_ontos = [u"vcm_repr"], reasoner = u"hermit"):
    self.prefix     = prefix
    self.reasoner   = reasoner
    self.popen      = None
    self.output     = u""
    self.id         = 0
    while self.id in OWL_FILES: self.id += 1
    
    OWL_FILES[self.id] = self
    
    self.name     = "/home/jiba/public_html/tmp_onto/tmp_onto_%s_%s.owl" % (self.prefix, self.id)
    self.file = open(self.name, "w")
    self.file.write(encode((u"""<?xml version="1.0" ?>

<!DOCTYPE rdf:RDF [
    <!ENTITY owl 'http://www.w3.org/2002/07/owl#' >
    <!ENTITY xsd 'http://www.w3.org/2001/XMLSchema#' >
    <!ENTITY owl2xml 'http://www.w3.org/2006/12/owl2-xml#' >
    <!ENTITY rdfs 'http://www.w3.org/2000/01/rdf-schema#' >
    <!ENTITY rdf 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' >
    <!ENTITY vcm_concept 'http://localhost/~jiba/vcm_onto/vcm_concept.owl#' >
    <!ENTITY vcm_concept_monoaxial 'http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#' >
    <!ENTITY vcm_lexique 'http://localhost/~jiba/vcm_onto/vcm_lexique.owl#' >
    <!ENTITY vcm_graphique 'http://localhost/~jiba/vcm_onto/vcm_graphique.owl#' >
    <!ENTITY vcm_repr 'http://localhost/~jiba/vcm_onto/vcm_repr.owl#' >
    <!ENTITY vcm_search_concept 'http://localhost/~jiba/vcm_onto/vcm_search_concept.owl#' > <!-- ok -->
    <!ENTITY tmp_onto_%s_%s 'http://localhost/~jiba/tmp_onto/tmp_onto_%s_%s.owl#' >
]>
<rdf:RDF xmlns='&tmp_onto_%s_%s;'
         xml:base='http://localhost/~jiba/tmp_onto/tmp_onto_%s_%s.owl'
         xmlns:rdfs='http://www.w3.org/2000/01/rdf-schema#'
         xmlns:owl2xml='http://www.w3.org/2006/12/owl2-xml#'
         xmlns:owl='http://www.w3.org/2002/07/owl#'
         xmlns:xsd='http://www.w3.org/2001/XMLSchema#'
         xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
         xmlns:vcm_lexique='&vcm_lexique;'
         xmlns:vcm_concept='&vcm_concept;'
         xmlns:vcm_graphique='&vcm_graphique;'
         xmlns:vcm_repr='&vcm_repr;'
         xmlns:vcm_search_concept='&vcm_search_concept;'
>
""" % (self.prefix, self.id, self.prefix, self.id, self.prefix, self.id, self.prefix, self.id))))

    self.file.write(encode(u"""
  <owl:Ontology rdf:about="">
"""))
    for onto in import_ontos:
      self.file.write(encode((u"""
        <owl:imports rdf:resource='http://localhost/~jiba/vcm_onto/%s.owl'/>
""" % onto)))
    self.file.write(encode(u"""
  </owl:Ontology>
"""))
    
  def close(self):
    del OWL_FILES[self.id]
     
  def start_reasoner_hermit(self, on_ended = None):
    self.file.write(u"""
  <owl:Class rdf:about="&owl;Thing"/>

</rdf:RDF>
""")
    self.file.flush()
    self.file.close()
    self.on_ended   = on_ended
    self.start_time = time.time()
    #cl = "hermit.sh -U -N %s" % self.name
    cl = "java -Xmx2000M -cp %s org.semanticweb.HermiT.cli.CommandLine -U -N %s" % (ontopy._HERMIT_CLASSPATH, self.name)
    print(cl, file = sys.stderr)
    self.popen = subprocess.Popen(cl, shell = 1, stdout = subprocess.PIPE)
    fcntl.fcntl(self.popen.stdout, fcntl.F_SETFL, fcntl.fcntl(self.popen.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
    
  def verify_reasoner_hermit(self):
    if self.popen:
      poll = self.popen.poll()
      if poll is None:
        try:    s = decode(self.popen.stdout.read())
        except: s = u""
        if s:
          self.output += s
          print("  ", self.name, len(s), file = sys.stderr)
          
      else:
        print("END of reasoning for", self.name, file = sys.stderr)
        t = time.time() - self.start_time
        print("Hermit : %ss" % t, file = sys.stderr)
        fcntl.fcntl(self.popen.stdout, fcntl.F_SETFL, fcntl.fcntl(self.popen.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
        s = self.output + decode(self.popen.stdout.read())
        
        write_file("/tmp/log2", s)
        
        incoherents = set()
        for ligne in s.split(u"\n")[1:]:
          if u"#"in ligne:
            incoherent = ligne.split(u"#")[1].replace(u">", u"")
            if u"TESTSAT_" in incoherent:
              incoherent = incoherent.replace(u"TESTSAT_", u"")
              incoherents.add(incoherent)
              #print("INCOHERENT :", incoherent, file = sys.stderr)
              
        if self.on_ended: self.on_ended(self, incoherents)
        self.popen = None
        self.close()
      
  def start_reasoner(self, on_ended = None):
    getattr(self, u"start_reasoner_%s" % self.reasoner)(on_ended)
    
  def verify_reasoner(self):
    getattr(self, u"verify_reasoner_%s" % self.reasoner)()


def verify_reasoners():
  for owl_file in list(OWL_FILES.values()): owl_file.verify_reasoner()

def nb_active_reasoners():
  return len([owl_file for owl_file in OWL_FILES.values() if owl_file.popen])


def main_loop(new_file_func, analyse_inconsistencies):
  ended = 0
  while 1:
    if nb_active_reasoners() < NB_PROCESSORS:
      if ended:
        time.sleep(0.5)
      else:
        file = new_file_func()
        if file: file.start_reasoner(on_ended = analyse_inconsistencies)
        else:    ended = 1
      if ended and (nb_active_reasoners() == 0): break
    else:
      time.sleep(0.5)
    verify_reasoners()





from pymedtermino       import *
from pymedtermino.vcm   import *

# OWL generation stuff

def shift(s, nb_space = 2): return (u" " * nb_space) + ("\n" + u" " * nb_space).join(s.split("\n"))

class LogicalOperatorList(list):
  def owl(self):
    owls = []
    for i in self:
      if isinstance(i, Clazz): owls.append(u"<rdf:Description rdf:about='%s'/>" % i.owl_ref())
      else:                    owls.append(i.owl())
    if len(owls) == 1: return owls[0]
    return u"""
<owl:Class>
  <owl:%s rdf:parseType='Collection'>
%s
  </owl:%s>
</owl:Class>
""" % (self._owl_operand_type, shift(u"\n".join(owls), 2), self._owl_operand_type)
  
  def owl_subclass(self):
    return u"""
<rdfs:subClassOf>
%s
</rdfs:subClassOf>
""" % shift(self.owl())
    

class Or (LogicalOperatorList): _owl_operand_type = u"unionOf"
class And(LogicalOperatorList): _owl_operand_type = u"intersectionOf"

class Not(object):
  def __init__(self, clazz):
    self.clazz = clazz
    
  def owl(self):
    if isinstance(self.clazz, Clazz): return u"""<owl:complementOf rdf:resource='%s'/>""" % self.clazz.owl_ref()
    else:
      return u"""
<owl:complementOf>
%s
</owl:complementOf>
""" % shift(self.clazz)
      
  def owl_subclass(self):
    return u"""
<rdfs:subClassOf>
%s
</rdfs:subClassOf>
""" % shift(self.owl())


class Restriction(object):
  def __init__(self, prop, clazz):
    self.prop          = prop
    self.clazz         = clazz
    
  def owl(self):
    if isinstance(self.clazz, Clazz):
      owl_clazz = u"<owl:%s rdf:resource='%s'/>" % (self._owl_restriction_type, self.clazz.owl_ref())
    else:
      owl_clazz = u"""
<owl:%s>
%s
</owl:%s>
""" % (self._owl_restriction_type, shift(self.clazz.owl()), self._owl_restriction_type)
    return u"""
<owl:Restriction>
  <owl:onProperty rdf:resource='%s'/>
%s
</owl:Restriction>""" % (self.prop.owl_ref(), shift(owl_clazz, 2))

  def owl_subclass(self):
    return u"""
<rdfs:subClassOf>
%s
</rdfs:subClassOf>
""" % shift(self.owl())
    
  
class Only(Restriction): _owl_restriction_type = u"allValuesFrom"
class Some(Restriction): _owl_restriction_type = u"someValuesFrom"


def terminology_2_owl(terminology):
  if   terminology is VCM_CONCEPT_MONOAXIAL: return u"http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#"
  elif terminology is VCM_LEXICON:           return u"http://localhost/~jiba/vcm_onto/vcm_lexique.owl#"
  
class Property(object):
  def __init__(self, concept):
    self.concept = concept
    
  def owl_ref(self): return u"%s%s" % (terminology_2_owl(self.concept.terminology), self.concept.code)

class Property(Property):
  def __init__(self, terminology, code):
    if isinstance(terminology, Terminology): self.terminology = terminology_2_owl(terminology)
    else:                                    self.terminology = terminology
    self.code = code
      
  def owl_ref(self): return u"%s%s" % (self.terminology, self.code)

class Isa(object):
  def __init__(self, clazz):
    self.clazz = clazz
    
  def owl_subclass(self): return u"""<rdfs:subClassOf rdf:resource='%s'/>""" % self.clazz.owl_ref()

class Clazz(object):
  def __init__(self, terminology, code):
    if isinstance(terminology, Terminology): self.terminology = terminology_2_owl(terminology)
    else:                                    self.terminology = terminology
    self.code = code
    self.restrictions = []
    
  def add_restriction(self, restriction): self.restrictions.append(restriction)
  
  def owl_ref(self): return u"%s%s" % (self.terminology, self.code)
  
  def owl(self):
    if not self.restrictions: return u""
    return u"""
<owl:Class rdf:about='%s'>
%s
</owl:Class>
""" % (self.owl_ref(), shift(u"\n".join(restriction.owl_subclass() for restriction in self.restrictions)))

VCM_GRAPHIQUE = u"http://localhost/~jiba/vcm_onto/vcm_graphique.owl#"
VCM_REPR      = u"http://localhost/~jiba/vcm_onto/vcm_repr.owl#"

represent                        = Property(VCM_REPR, 751)
is_represented_by                = Property(VCM_REPR, 750)
related_to_state                 = Property(VCM_CONCEPT_MONOAXIAL, 5)
state_related_to                 = Property(VCM_CONCEPT_MONOAXIAL, 13)

is_central_color_of              = Property(VCM_GRAPHIQUE, 736)
is_central_pictogram_of          = Property(VCM_GRAPHIQUE, 740)
is_modifier_of                   = Property(VCM_GRAPHIQUE, 739)
is_top_right_color_of            = Property(VCM_GRAPHIQUE, 738)
is_top_right_pictogram_of        = Property(VCM_GRAPHIQUE, 742)
is_second_top_right_pictogram_of = Property(VCM_GRAPHIQUE, 743)

has_central_color                = Property(VCM_GRAPHIQUE, 725)
has_central_pictogram            = Property(VCM_GRAPHIQUE, 733)
has_modifier                     = Property(VCM_GRAPHIQUE, 727)
has_top_right_color              = Property(VCM_GRAPHIQUE, 726)
has_top_right_pictogram          = Property(VCM_GRAPHIQUE, 734)
has_second_top_right_pictogram   = Property(VCM_GRAPHIQUE, 735)

category2relation_repr = {
  0 : is_central_color_of,
  1 : is_modifier_of,
  2 : is_central_pictogram_of,
  3 : is_top_right_color_of,
  4 : is_top_right_pictogram_of,
  5 : is_second_top_right_pictogram_of,
  }
category2relation_irepr = {
  0 : has_central_color,
  1 : has_modifier,
  2 : has_central_pictogram,
  3 : has_top_right_color,
  4 : has_top_right_pictogram,
  5 : has_second_top_right_pictogram,
  }
