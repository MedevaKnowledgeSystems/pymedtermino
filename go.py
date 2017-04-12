# -*- coding: utf-8 -*-
# PyMedTermino
# Copyright (C) 2016 Coralie CAPRON
# Copyright (C) 2016 Jean-Baptiste LAMY
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
pymedtermino.go
******************

PyMedtermino module for GeneOntology.
.. class:: GO
.. class:: Taxons
.. class:: GeneProduct
   
   The GeneOntology terminology. See :class:`pymedtermino.Terminology` for common terminology members; only GeneOntology-specific members are described here.
"""
#__all__ represents the Terminologies the user can access with the python shell. Must be used like >>> "Terminology["ID"]"
__all__ = ["GO", "Taxons", "GeneProduct", "get_gene_products", "Terms", "get_annotation_terms"]

import pymedtermino
import os, os.path, cymysql as sql_module


# Connexion in command-line :
# mysql -h mysql.ebi.ac.uk -u go_select -pamigo -P 4085 -D go_latest

db        = sql_module.connect(host="mysql.ebi.ac.uk", user="go_select",db="go_latest", passwd="amigo", port=4085)
db_cursor = db.cursor()


  
class GO(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "GO")

  def _create_Concept(self): return GeneOntologyConcept 
  
  def first_levels(self):
    return [self[code] for code in ['GO:0008150','GO:0003674','GO:0005575']] #Here are the three elemental processes: the "highest" ancestors.


class GeneOntologyConcept(pymedtermino.MultiaxialConcept, pymedtermino._StringCodeConcept):
  """A GeneOntology concept where the parents/children relations are found. See :class:`pymedtermino.Concept` for common terminology members; only GeneOntology-specific members are described here.

.. attribute:: children

.. attribute:: parents


"""
  def __init__(self, code):
#    db_cursor.execute("SELECT child.acc AS child_acc,  child.name AS child_name,  parent.acc AS parent_acc,  parent.name AS parent_name FROM  term AS child  INNER JOIN term2term ON (child.id=term2_id)  INNER JOIN term AS parent ON (parent.id=term1_id) WHERE parent.acc=%s or child.acc=%s", (code, code))
    db_cursor.execute("SELECT name FROM term WHERE acc=%s", (code,))
    r = db_cursor.fetchone()
    if not r: raise ValueError(code)
    pymedtermino.MultiaxialConcept.__init__(self, code, r[0])
    
  def __getattr__(self, attr):
    if (attr == "children"): 
      db_cursor.execute("SELECT child.acc FROM  term AS child  INNER JOIN term2term ON (child.id=term2_id)  INNER JOIN term AS parent ON (parent.id=term1_id) WHERE parent.acc=%s", (self.code))
      self.children = [GO[code_tuple[0]] for code_tuple in db_cursor.fetchall()]
      return self.children 
    
    elif attr == "parents":  #ParentsAccession
      db_cursor.execute("SELECT parent.acc FROM  term AS child  INNER JOIN term2term ON (child.id=term2_id)  INNER JOIN term AS parent ON (parent.id=term1_id) WHERE child.acc=%s", (self.code))
      self.parents = [GO[code_tuple[0]] for code_tuple in db_cursor.fetchall()]
      return self.parents

    else: raise AttributeError(attr)


GO = GO()


class Taxons(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self, "Taxons")

  def _create_Concept(self): return TaxonsConcept 
  
  def first_levels(self):
     return [self[523005]] #523005 is the root ID
  

class TaxonsConcept(pymedtermino.MonoaxialConcept, pymedtermino._IntCodeConcept): 
  """A GeneOntology concept where the species parents and children are found. 
  See :class:`pymedtermino.Concept` for common terminology members; only GeneOntology-specific members are described here.

.. attribute:: parents

.. attribute:: children

"""
  def __init__ (self,code):
    db_cursor.execute("SELECT genus, species, parent_id from species where id=%s", (code))
    r=db_cursor.fetchone()
    if not r:
      raise ValueError(code)
    self.genus       = r[0]
    self.species     = r[1]
    self.parent_id   = r[2]
    if self.species: name = "%s %s" % (self.genus, self.species)
    else:            name = self.genus
    pymedtermino.MonoaxialConcept.__init__(self, code, name)

  def __getattr__(self,attr):
    if (attr == "parents"):
      if self.parent_id is None: self.parents = []
      else:                      self.parents = [self.terminology[self.parent_id]]
      return self.parents

    elif (attr == "children"):
      db_cursor.execute("SELECT id from species where parent_id=%s", (self.code,))
      self.children = [self.terminology[id_tuple[0]] for id_tuple in db_cursor.fetchall()]
      return self.children


Taxons = Taxons()

class GeneProduct(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self,"GeneProduct")

  def _create_Concept(self): return GPConcept

  def first_levels(self):
    raise ValueError

class GPConcept(pymedtermino.MultiaxialConcept, pymedtermino._StringCodeConcept):
  """A GeneOntology concept where the gene_products are found. 
  See :class:`pymedtermino.Concept` for common terminology members; only GeneOntology-specific members are described here.

.. attribute:: species

.. attribute:: parents

.. attribute:: children
  """
  def __init__(self,code):
    db_cursor.execute("SELECT full_name, species_id from gene_product where id=%s", (code)) #ID of the gene_product
    r=db_cursor.fetchone()  
    if not r:
      raise ValueError(code)
    name                           = r[0]
    self.species_id                = r[1]
    pymedtermino.MultiaxialConcept.__init__(self, code, name)

  def __getattr__(self,attr):
    if(attr == "species"):
      self.species = Taxons[self.species_id] #Will give automatically the name with the species ID thanks to the Taxons terminology
      return self.species
    
    elif(attr == "parents"):
       self.parents = []
       return self.parents
    
    elif(attr == "children"):
       self.children = []
       return self.children

GeneProduct = GeneProduct()

class Terms(pymedtermino.Terminology):
  def __init__(self):
    pymedtermino.Terminology.__init__(self,"Terms")

  def _create_Concept(self): return TermsConcept

  def first_levels(self):
    raise ValueError

class TermsConcept(pymedtermino.MultiaxialConcept, pymedtermino._StringCodeConcept):
  """A GeneOntology concept where the terms of gene_products are found. See :class:`pymedtermino.Concept` 
  for common terminology members; only GeneOntology-specific members are described here.

.. attribute:: termName

.. attribute:: parents

.. attribute:: children
  """
  def __init__(self,code):
    db_cursor.execute("SELECT full_name FROM gene_product INNER JOIN association ON (gene_product.id=association.gene_product_id) INNER JOIN term ON (association.term_id=term.id) WHERE gene_product_id =%s", (code)) 
    r = db_cursor.fetchone()  
    if not r:
      raise ValueError(code)
    name                           = r[0]
    pymedtermino.MultiaxialConcept.__init__(self, code, name)

  def __getattr__(self,attr):
    if(attr == "termName"):
      db_cursor.execute("SELECT acc FROM gene_product INNER JOIN association ON (gene_product.id=association.gene_product_id) INNER JOIN term ON (association.term_id=term.id) WHERE gene_product_id =%s", (self.code)) 
      self.termName = [GO[term[0]] for term in db_cursor.fetchall()] 
      return self.termName
    

    elif(attr == "parents"):
       self.parents = []
       return self.parents
    
    elif(attr == "children"):
       self.children = []
       return self.children

Terms = Terms()

#get_gene_products returns a list of gene products for a given list of metabolic pathways

def get_gene_products(species, go):
    listgp =[]
    gos = list(go.self_and_descendants_no_double())
    for go in gos: 
      go = go.code
      listgp.append(go)   
    gosJoin =",".join("'%s'"% id for id in listgp)  
    
    db_cursor.execute("SELECT distinct gene_product_id FROM gene_product INNER JOIN species ON (gene_product.species_id=species.id)INNER JOIN association ON (gene_product.id=association.gene_product_id) INNER JOIN term ON (association.term_id=term.id) WHERE acc in (%s) and species.id=%s "%(gosJoin,species.code))
    r = [GeneProduct[tuple[0]]for tuple in db_cursor.fetchall()]
    listgo =[]
    for go in r:
      listgo.append(go)
    return listgo

#get_annotation_terms returns a list of terms for a given gene product ID 
def get_annotation_terms(geneProductId):
    db_cursor.execute("SELECT acc FROM gene_product INNER JOIN association ON (gene_product.id=association.gene_product_id) INNER JOIN term ON (association.term_id=term.id) WHERE gene_product_id =%s", (geneProductId.code)) 
    r = [GO[tuple[0]]for tuple in db_cursor.fetchall()]
    listTerm =[]
    for term in r:
      listTerm.append(term)
    return listTerm
