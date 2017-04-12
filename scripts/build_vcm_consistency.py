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

import random, time

import pymedtermino
pymedtermino.READ_ONLY_DATABASE = False

from pymedtermino          import *
from pymedtermino.vcm      import *
from pymedtermino.utils.db import *
from pymedtermino.utils.owl_file_reasoner import *

if sys.version[0] == "2":
  from StringIO import StringIO
  def encode(s): return s.encode("utf8")
  def decode(s): return s.decode("utf8")
else:
  from io import StringIO
  def encode(s): return s
  def decode(s): return s


command = "cp -f ./pymedtermino/vcm_onto/*.owl /home/jiba/public_html/vcm_onto/"
print(command)
os.system(command)

OWL_FILE = u""

LOCAL              = u"#"
VCM_ICON           = u"http://localhost/~jiba/vcm_onto/vcm_icon.owl#"
VCM_SEARCH_CONCEPT = u"http://localhost/~jiba/vcm_onto/vcm_search_concept.owl#"
VCM_ICON_CONCEPT   = u"http://localhost/~jiba/vcm_onto/vcm_icon_concept.owl#"


from pymedtermino.vcm import db_consistency_cursor

def lex_pair_consistent(a, b):
  if a.code > b.code: a, b = b, a
  db_consistency_cursor.execute(u"SELECT lex1 FROM InconsistentPairs WHERE lex1=? AND lex2=?;", (a.code, b.code))
  if db_consistency_cursor.fetchone(): return 0
  return 1

def picto_modifiers_consistent(picto, modifiers):
  modifiers = [modifier.code for modifier in modifiers]
  modifiers.sort()
  while len(modifiers) < 3: modifiers.append(0)
  
  db_consistency_cursor.execute(u"SELECT picto FROM ConsistentPictoMods WHERE picto=? AND mod1=? AND mod2=? AND mod3=?;", (picto.code, modifiers[0], modifiers[1], modifiers[2]))
  if len(db_consistency_cursor.fetchall()) > 0: return 1
  return 0


def start(search_concept = 0):
  global OWL_FILE
  if not search_concept:
    OWL_FILE = "/home/jiba/public_html/tmp_onto/vcm_icon.owl"
    sys.stdout  = open(OWL_FILE, "w")
    print(encode(u"""<?xml version="1.0" ?>

<!DOCTYPE rdf:RDF [
    <!ENTITY owl 'http://www.w3.org/2002/07/owl#' >
    <!ENTITY xsd 'http://www.w3.org/2001/XMLSchema#' >
    <!ENTITY owl2xml 'http://www.w3.org/2006/12/owl2-xml#' >
    <!ENTITY rdfs 'http://www.w3.org/2000/01/rdf-schema#' >
    <!ENTITY rdf 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' >
    <!ENTITY vcm_concept_monoaxial 'http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#' >
    <!ENTITY vcm_lexique 'http://localhost/~jiba/vcm_onto/vcm_lexique.owl#' >
    <!ENTITY vcm_graphique 'http://localhost/~jiba/vcm_onto/vcm_graphique.owl#' >
    <!ENTITY vcm_repr 'http://localhost/~jiba/vcm_onto/vcm_repr.owl#' >
    <!ENTITY vcm_icon 'http://localhost/~jiba/tmp_onto/vcm_icon.owl#' >
]>

<rdf:RDF xmlns='&vcm_icon;'
         xml:base='http://localhost/~jiba/tmp_onto/vcm_icon.owl'
         xmlns:rdfs='http://www.w3.org/2000/01/rdf-schema#'
         xmlns:owl2xml='http://www.w3.org/2006/12/owl2-xml#'
         xmlns:owl='http://www.w3.org/2002/07/owl#'
         xmlns:xsd='http://www.w3.org/2001/XMLSchema#'
         xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
         xmlns:vcm_lexique='&vcm_lexique;'
         xmlns:vcm_concept_monoaxial='&vcm_concept_monoaxial;'
         xmlns:vcm_graphique='&vcm_graphique;'
         xmlns:vcm_repr='&vcm_repr;'
>

  <owl:Ontology rdf:about="">
        <owl:imports rdf:resource='http://localhost/~jiba/vcm_onto/vcm_repr.owl'/>
  </owl:Ontology>
"""))
    
  else:
    OWL_FILE = "/home/jiba/public_html/tmp_onto/vcm_icon_concept.owl"
    sys.stdout  = open(OWL_FILE, "w")
    
    print(encode(u"""<?xml version="1.0" ?>

<!DOCTYPE rdf:RDF [
    <!ENTITY owl 'http://www.w3.org/2002/07/owl#' >
    <!ENTITY xsd 'http://www.w3.org/2001/XMLSchema#' >
    <!ENTITY owl2xml 'http://www.w3.org/2006/12/owl2-xml#' >
    <!ENTITY rdfs 'http://www.w3.org/2000/01/rdf-schema#' >
    <!ENTITY rdf 'http://www.w3.org/1999/02/22-rdf-syntax-ns#' >
    <!ENTITY vcm_concept_monoaxial 'http://localhost/~jiba/vcm_onto/vcm_concept_monoaxial.owl#' >
    <!ENTITY vcm_lexique 'http://localhost/~jiba/vcm_onto/vcm_lexique.owl#' >
    <!ENTITY vcm_graphique 'http://localhost/~jiba/vcm_onto/vcm_graphique.owl#' >
    <!ENTITY vcm_repr 'http://localhost/~jiba/vcm_onto/vcm_repr.owl#' >
    <!ENTITY vcm_search_concept 'http://localhost/~jiba/vcm_onto/vcm_search_concept.owl#' >
    <!ENTITY vcm_icon_concept 'http://localhost/~jiba/tmp_onto/vcm_icon_concept.owl#' >
]>

<rdf:RDF xmlns='&vcm_icon_concept;'
         xml:base='http://localhost/~jiba/tmp_onto/vcm_icon_concept.owl'
         xmlns:rdfs='http://www.w3.org/2000/01/rdf-schema#'
         xmlns:owl2xml='http://www.w3.org/2006/12/owl2-xml#'
         xmlns:owl='http://www.w3.org/2002/07/owl#'
         xmlns:xsd='http://www.w3.org/2001/XMLSchema#'
         xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
         xmlns:vcm_lexique='&vcm_lexique;'
         xmlns:vcm_concept_monoaxial='&vcm_concept_monoaxial;'
         xmlns:vcm_graphique='&vcm_graphique;'
         xmlns:vcm_repr='&vcm_repr;'
         xmlns:vcm_search_concept='&vcm_search_concept;'
>

  <owl:Ontology rdf:about="">
        <owl:imports rdf:resource='http://localhost/~jiba/vcm_onto/vcm_search_concept.owl'/>
  </owl:Ontology>
"""))


def icon_2_owl(icon):
  name = icon.code
  lexs_2_owl(icon.lexs, name)
  return name

def lexs_2_owl(lexs, name = u"", no_other_modifier = 1):
  if not name: name = u"__".join([u"%s" % lex.code for lex in lexs])
  owl_clazz = Clazz(LOCAL, u"TESTSAT_%s" % name)
  owl_clazz.add_restriction(Isa(Clazz(VCM_GRAPHIQUE, u"Icône")))
  
  def is_a_lexs(lex):
    for parent in lexs:
      if lex.is_a(parent): return 1
    return 0
  
  modifiers = []
  for lex in lexs:
    if lex.category == 1: modifiers.append(lex)
    rel = category2relation_irepr[lex.category]
    
    owl_clazz.add_restriction(And(
      [Some(rel, Clazz(VCM_LEXICON, lex.code))]
    + [Not(Clazz(VCM_LEXICON, child.code)) for child in lex.children if not is_a_lexs(child)]
    ))
    
  if no_other_modifier:
    owl_clazz.add_restriction(Only(has_modifier, Or([Clazz(VCM_LEXICON, modifier.code) for modifier in modifiers])))
    
  print(encode(owl_clazz.owl()))
  return name


_search_concepts = []
def search_concept_2_owl(name, cons = None, avec_not = 0):
  global _search_concepts
  
  if not cons:
    if not _search_concepts:
      for con in vcm_concept.recursive():
        lexs = (VCM_CONCEPT >> VCM_LEXICON)(con)
        if not lexs: continue
        if con.is_a(VCM_CONCEPT[426]): continue # Temporality
        if con.is_a(VCM_CONCEPT[214]): continue # Medical_care
        if con.is_a(VCM_CONCEPT[ 85]): continue # Medical_context
        _search_concepts.append(con)
    cons = _search_concepts
    
  for con in cons:
    print((encode(u"""
    <owl:Class rdf:about='#TESTSAT_%s_SEARCH_icon_repr_%s'>
        <rdfs:subClassOf rdf:resource='#TESTSAT_%s'/>
        <rdfs:subClassOf rdf:resource='&vcm_search_concept;SEARCH_icon_repr_%s'/>
    </owl:Class>
""" % (name, con.code, name, con.code))))
    if avec_not: print((encode(u"""
    <owl:Class rdf:about='#TESTSAT_%s_SEARCH_icon_not_repr_%s'>
        <rdfs:subClassOf rdf:resource='#TESTSAT_%s'/>
        <rdfs:subClassOf rdf:resource='&vcm_search_concept;SEARCH_icon_not_repr_%s'/>
    </owl:Class>
""" % (name, con.code, name, con.code))))

  #assert_all_disjoint([u"%s_CHERCHE_icône_repr_%s" % (name, con.code) for con in cons])

  
def assert_all_disjoint(names):
  print((encode(u"""
    <rdf:Description>
        <rdf:type rdf:resource='&owl;AllDisjointClasses'/>
        <owl:members rdf:parseType='Collection'>""")))
  for name in names:
    print((encode(u"""            <rdf:Description rdf:about='#TESTSAT_%s'/>""" % name)))
  print((encode(u"""
        </owl:members>
    </rdf:Description>""")))
  
  
def check_consistency_hermit():
  import ontopy.owl
  
  inconsistents = set()
  t = time.time()
  #cl = "hermit.sh -U -N %s" % OWL_FILE
  cl = "java -Xmx2000M -cp %s org.semanticweb.HermiT.cli.CommandLine -U -N %s" % (ontopy.owl._HERMIT_CLASSPATH, OWL_FILE)
  print(cl, file = sys.stderr)
  s = os.popen(cl).read()
  t = time.time() - t
  print("Hermit : %ss" % t, file = sys.stderr)
  
  s = decode(s)
  for ligne in s.split(u"\n")[1:]:
    if u"#"in ligne:
      inconsistent = ligne.split(u"#")[1].replace(u">", u"")
      if u"TESTSAT_" in inconsistent:
        inconsistent = inconsistent.replace(u"TESTSAT_", u"")
        inconsistents.add(inconsistent)
        #print("INCONSISTENT :", inconsistent)
  return inconsistents

check_consistency = check_consistency_hermit


def end():
  print(u"""
  <owl:Class rdf:about="&owl;Thing"/>

</rdf:RDF>
""")
  sys.stdout.close()
  sys.stdout = sys.__stdout__


def possible_modifierss():
  modss = set()
  modss.add(frozenset([VCM_LEXICON[1, u"physio"]]))
  modss.add(frozenset([VCM_LEXICON[1, u"patho" ]]))
  etiologies                = set(VCM_LEXICON[1, u"_etiologie"].descendants())
  processus                 = set(VCM_LEXICON[1, u"_processus"].descendants())
  localisations_secondaires = set(VCM_LEXICON[1, u"_localisation_secondaire"].descendants())
  quantitatifs              = set(VCM_LEXICON[1, u"_quantitatif"].descendants())
  
  mods_non_transverse = etiologies | processus | quantitatifs
  
  for mod in VCM_LEXICON.MODIFIER.descendants(): mod.mod_category = 0
  for mod in etiologies                        : mod.mod_category = 1
  for mod in processus                         : mod.mod_category = 2
  for mod in localisations_secondaires         : mod.mod_category = 3
  for mod in quantitatifs                      : mod.mod_category = 4
  
  for mod in mods_non_transverse:
    if mod.abstract: continue
    modss.add(frozenset([mod]))
    
  for mod1 in mods_non_transverse:
    if mod1.abstract: continue
    if mod1.empty: continue
    for mod2 in mods_non_transverse:
      if mod2.abstract: continue
      if mod2.empty: continue
      if (mod2 is mod1): continue
      if mod2.text_code < mod1.text_code: continue
      if mod1.mod_category == mod2.mod_category: continue
      if not lex_pair_consistent(mod2, mod1): continue
      modss.add(frozenset([mod1, mod2]))
      
  modss2 = set(modss)
  for loca in localisations_secondaires:
    if loca.abstract: continue
    for mods in modss2:
      if len(mods) > 1:
        if not loca in (VCM_LEXICON[1, u"vaisseau"], VCM_LEXICON[1, u"vaisseau_pa"], VCM_LEXICON[1, u"nerf"], VCM_LEXICON[1, u"hemorragie"], VCM_LEXICON[1, u"oedeme"], VCM_LEXICON[1, u"metab"]): continue
      ok = 1
      for mod in mods:
        if not lex_pair_consistent(mod, loca): ok = 0
      if not ok: continue
      modss.add(mods | frozenset([loca]))
  
  # Hypo / hypertension due à un médicament
  #modss.add(frozenset([VCM_LEXICON[1, u"vaisseau_pa"], VCM_LEXICON[1, u"hypo"], VCM_LEXICON[1, u"etio_medicament"]]))
  
  print(len(modss), "ensembles de modificateurs possibles.")
  
  return modss
  


def possible_colors_and_top_rights():
  couleurs_exposants = set()
  
  for couleur_centrale in [VCM_LEXICON[0, u"en_cours"], VCM_LEXICON[0, u"antecedent"], VCM_LEXICON[0, u"risque"], VCM_LEXICON[0, u"traitement"]]:
    for exposant in VCM_LEXICON.TOP_RIGHT_PICTOGRAM.descendants():
      if exposant.abstract: continue
      if not lex_pair_consistent(couleur_centrale, exposant): continue
      if   exposant.is_a(VCM_LEXICON[4, u"traitement"   ]): couleur_en_exposant = VCM_LEXICON[3, u"traitement"]
      elif exposant.is_a(VCM_LEXICON[4, u"_surveillance"]): couleur_en_exposant = VCM_LEXICON[3, u"surveillance"]
      else:                                                 couleur_en_exposant = VCM_LEXICON[3, u"rien"]
      
      for exposant2 in VCM_LEXICON.SECOND_TOP_RIGHT_PICTOGRAM.descendants():
        if not lex_pair_consistent(exposant2, couleur_centrale   ): continue
        if not lex_pair_consistent(exposant2, couleur_en_exposant): continue
        if not lex_pair_consistent(exposant2, exposant           ): continue
        couleurs_exposants.add(frozenset([couleur_centrale, couleur_en_exposant, exposant, exposant2]))
        
  print(len(couleurs_exposants), "ensembles de couleurs et d'exposants possibles.")
  
  return couleurs_exposants


if "--possible-modifierss" in sys.argv:
  modss = possible_modifierss()
  for mods in modss:
    print(len(mods), u", ".join([mod.term for mod in mods]))
    
if "--test" in sys.argv:
  print(lex_pair_consistent(VCM_LEXICON[631], VCM_LEXICON[704]))
  print(lex_pair_consistent(VCM_LEXICON[1, u"tumeur"], VCM_LEXICON[2, u"sommeil"]))
  print(lex_pair_consistent(VCM_LEXICON[1, u"tumeur"], VCM_LEXICON[2, u"foie"]))
  print()
  print(picto_modifiers_consistent(VCM_LEXICON[2, u"foie"], [VCM_LEXICON[1, u"inflammation"]]))
  
if "--pairs" in sys.argv:
  pymedtermino.vcm.db_consistency_cursor.execute(u"DROP TABLE IF EXISTS InconsistentPairs;")
  pymedtermino.vcm.db_consistency_cursor.execute(u"""
CREATE TABLE InconsistentPairs(
  lex1 INTEGER,
  lex2 INTEGER
);""")
  
  start()
  
  pairs = set()
  all_lexs = set(lex for lex in VCM_LEXICON.all_concepts() if (not lex.abstract) and (not lex.is_a(VCM_LEXICON.SHADOW)))
  for lex1 in all_lexs:
    for lex2 in all_lexs:
      if lex1 is lex2: continue
      if (lex1.category == lex2.category) and (lex1.category != 1): continue
      pair = frozenset([lex1, lex2])
      if pair in pairs: continue # Déjà fait
      
      pairs.add(pair)
      lexs_2_owl(pair, no_other_modifier = 0)
      
  end()
  
  print(len(pairs), "paires d'éléments du lexique.", file = sys.stderr)
  
  inconsistents = check_consistency()
  inconsistents = set([frozenset(map(VCM_LEXICON.__getitem__, inconsistent.split(u"__"))) for inconsistent in inconsistents])
  
  print(len(inconsistents), "paires incohérentes.", file = sys.stderr)
  
  write_file("/tmp/vcm_lexique_paires_inconsistentes.txt", u"\n".join([u" ".join([u"%s" % lex.code for lex in inconsistent]) for inconsistent in inconsistents]), "utf8")

  for a, b in inconsistents:
    if a.code > b.code: a, b = b, a
    pymedtermino.vcm.db_consistency_cursor.execute(u"""INSERT INTO InconsistentPairs VALUES (?, ?);""", (a.code, b.code))
    
  pymedtermino.vcm.db_consistency_cursor.execute(u"""CREATE INDEX pair_InconsistentPairs on InconsistentPairs(lex1, lex2);""")
  close_db(pymedtermino.vcm.db_consistency, set_readonly = 0)
  

def lexs_2_picto_mods(lexs):
  picto = None
  mods  = []
  for lex in lexs:
    if   lex.category == 2: picto = lex.code
    elif lex.category == 1: mods.append(lex.code)
    else: raise ValueError
  mods.sort()
  while len(mods) < 3: mods.append(0)
  return [picto] + mods


if "--picto-mods" in sys.argv:
  modss               = possible_modifierss()
  nb                  = 0
  nb_consistent       = 0
  nb_inconsistent     = 0
  
  pymedtermino.vcm.db_consistency_cursor.execute(u"DROP TABLE IF EXISTS ConsistentPictoMods;")
  pymedtermino.vcm.db_consistency_cursor.execute(u"""
CREATE TABLE ConsistentPictoMods(
  picto INTEGER,
  mod1 INTEGER,
  mod2 INTEGER,
  mod3 INTEGER
);""")
  
  
  def combinaisons():
    for pictogramme_central in VCM_LEXICON.CENTRAL_PICTOGRAM.descendants():
      if pictogramme_central.abstract: continue
      
      for mods in modss:
        ok = 1
        for mod in mods:
          if not lex_pair_consistent(mod, pictogramme_central):
            ok = 0
            break
        if not ok: continue
        
        lexs = mods | frozenset([pictogramme_central])
        yield lexs
        
  combinaisons = combinaisons()
  
  def creer_nouveau_fichier():
    global nb
    owl_file = OWLFile(u"picto_mods")
    owl_file.picto_mods = set()
    sys.stdout = owl_file.file
    for i in range(10000):
      try: lexs = next(combinaisons)
      except StopIteration: break
      lexs_2_owl(lexs)
      owl_file.picto_mods.add(frozenset([lex.code for lex in lexs]))
      nb += 1
    sys.stdout = sys.__stdout__
    print(nb, "picto central + modificateurs possibles...", file = sys.stderr)
    if owl_file.picto_mods: return owl_file
    return None
  
  def analyser_incoherences(owl_file, inconsistents):
    global nb, nb_consistent, nb_inconsistent
    print(len(inconsistents), "picto central + modificateurs incohérents dans ce paquet.", file = sys.stderr)
    
    inconsistents = set([frozenset(int(i) for i in inconsistent.split(u"__")) for inconsistent in inconsistents])
    consistents = owl_file.picto_mods - inconsistents
    nb_inconsistent += len(inconsistents)
    nb_consistent   += len(consistents)
    print(nb_consistent, "picto central + modificateurs cohérentes.", file = sys.stderr)
    
    for consistent in consistents:
      lexs = [VCM_LEXICON[code] for code in consistent]
      picto_mod = lexs_2_picto_mods(lexs)
      
      pymedtermino.vcm.db_consistency_cursor.execute(u"""INSERT INTO ConsistentPictoMods VALUES (?, ?, ?, ?);""", picto_mod)
    
  main_loop(creer_nouveau_fichier, analyser_incoherences)
  
  print("", file = sys.stderr)
  print(nb             , "picto central + modificateurs.", file = sys.stderr)
  print(nb_inconsistent, "picto central + modificateurs incohérentes.", file = sys.stderr)
  print(nb_consistent  , "picto central + modificateurs cohérentes.", file = sys.stderr)
  
  pymedtermino.vcm.db_consistency_cursor.execute(u"""CREATE INDEX index_ConsistentPictoMods on ConsistentPictoMods(picto, mod1, mod2, mod3);""")
  close_db(pymedtermino.vcm.db_consistency, set_readonly = 0)
  

def picto_mods_consistents_gen():
  pymedtermino.vcm.db_consistency_cursor.execute(u"""SELECT picto, mod1, mod2, mod3 FROM ConsistentPictoMods;""")
  for picto, mod1, mod2, mod3 in pymedtermino.vcm.db_consistency_cursor.fetchall():
    picto_mods = set([VCM_LEXICON[picto], VCM_LEXICON[mod1]])
    if mod2 != 0: picto_mods.add(VCM_LEXICON[mod2])
    if mod3 != 0: picto_mods.add(VCM_LEXICON[mod3])
    yield picto_mods
    
#list(picto_mods_consistents_gen())


if "--icons" in sys.argv:
  couleurs_exposants = possible_colors_and_top_rights()
  
  start()
  
  nb_icon        = 0
  fichier        = open("/tmp/vcm_icons_inconsistentes.txt", "w")
  nb_consistent  = 0
  
  pymedtermino.vcm.db_consistency_cursor.execute(u"DROP TABLE IF EXISTS InconsistentIcon;")
  pymedtermino.vcm.db_consistency_cursor.execute(u"""
CREATE TABLE InconsistentIcon(
  codes TEXT
);""")
  
  picto_mods_consistents = list(picto_mods_consistents_gen())
  print(len(picto_mods_consistents), "picto mods possibles...", file = sys.stderr)
  
  def combinaisons():
    for couleur_exposant in couleurs_exposants:
      for picto_mod in picto_mods_consistents:
        ok = 1
        for i in couleur_exposant:
          for j in picto_mod:
            if (i.code < j.code) and (not lex_pair_consistent(i, j)):
              ok = 0
              break
          if ok == 0: break
        if ok == 0: continue
        
        yield couleur_exposant | picto_mod
  combinaisons = combinaisons()
  
  def creer_nouveau_fichier():
    global nb_icon
    owl_file = OWLFile(u"icon")
    owl_file.icons_codes = set()
    sys.stdout = owl_file.file
    for i in range(7500):
      try: combinaison = next(combinaisons)
      except StopIteration: break
      icon_code = lexs_2_owl(combinaison)
      owl_file.icons_codes.add(icon_code)
      nb_icon += 1
      
    sys.stdout = sys.__stdout__
    print(nb_icon, "icônes possibles...", file = sys.stderr)
    if owl_file.icons_codes: return owl_file
    return None
  
  def analyser_incoherences(owl_file, inconsistents):
    global nb_icon, icons_codes, nb_consistent
    print(len(inconsistents), "icônes incohérentes dans ce paquet.", file = sys.stderr)
    
    inconsistents = set([VCM.icon_from_lexs([VCM_LEXICON[code] for code in inconsistent.split(u"__")]) for inconsistent in inconsistents])
    nb_consistent += len(owl_file.icons_codes) - len(inconsistents)
    print(nb_consistent, "icônes cohérentes...", file = sys.stderr)
    
    for inconsistent in inconsistents:
      fichier.write(encode((u"%s\n" % inconsistent.short_code)))
      pymedtermino.vcm.db_consistency_cursor.execute(u"""INSERT INTO InconsistentIcon VALUES (?);""", (inconsistent.short_code,))
    fichier.flush()
    
    
  main_loop(creer_nouveau_fichier, analyser_incoherences)
  print(nb_icon   , "icônes possibles.", file = sys.stderr)
  print(nb_consistent, "icônes cohérentes.", file = sys.stderr)
  
  pymedtermino.vcm.db_consistency_cursor.execute(u"""CREATE INDEX index_InconsistentIcon on InconsistentIcon(codes);""")
  close_db(pymedtermino.vcm.db_consistency, set_readonly = 0)


_NON_INFORMATIVE = set([
  VCM_CONCEPT[446], # Trouble_fonctionnel
  VCM_CONCEPT[437], # Trouble_anatomique
  VCM_CONCEPT[442], # Trouble_anatomique_quantitatif
  VCM_CONCEPT[447], # Trouble_fonctionnelle_quantitatif
  VCM_CONCEPT[444], # Trouble_dune_caractéristique_patient
  VCM_CONCEPT[445], # Trouble_dune_caractéristique_patient_quantitatif
  VCM_CONCEPT[487], # Étiologie
  VCM_CONCEPT[ 14], # Absence_de_modification_dune_propriété_du_traitement_médicamenteux
  VCM_CONCEPT[218], # Propriété_du_traitement_médicamenteux
  ])

def simplify_concepts(cons):
  if VCM_CONCEPT[451] in cons: # Trouble_pathologique_non_précisé
    cons = cons.subtract(VCM_CONCEPT[450]) # Trouble_pathologique
    cons.add(VCM_CONCEPT[450]) # Trouble_pathologique
    
  if VCM_CONCEPT[489] in cons: # Étiologie_non_précisée
    cons = cons.subtract(VCM_CONCEPT[487]) # Étiologie
    
  cons.keep_most_specific()
  cons.remove_complete_families()
  cons.difference_update(_NON_INFORMATIVE)
  return cons
  
  
if "--sens" in sys.argv:
  pymedtermino.vcm.db_consistency_cursor.execute(u"DROP TABLE IF EXISTS PictoModsSens;")
  pymedtermino.vcm.db_consistency_cursor.execute(u"""
CREATE TABLE PictoModsSens(
  picto   INTEGER,
  mod1    INTEGER,
  mod2    INTEGER,
  mod3    INTEGER,
  concept INTEGER
);""")
  


  #def picto_mods_consistents_gen():
  #  yield set([VCM_LEXICON[2, "glande_diabete"], VCM_LEXICON[1, "patho"]])
    
    
  combinaisons = picto_mods_consistents_gen()
  
  nb  = 0
  def creer_nouveau_fichier():
    global nb
    owl_file = OWLFile(u"sens0", import_ontos = [u"vcm_search_concept"])
    owl_file.names = {}
    sys.stdout = owl_file.file
    for i in range(1000):
      try: picto_mod = next(combinaisons)
      except StopIteration: break
      
      picto_mod_cons = Concepts()
      for lex in picto_mod:
        lex_cons = lex >> VCM_CONCEPT
        lex_cons.keep_most_generic()
        picto_mod_cons.update(lex_cons)
      #picto_mod_cons = (VCM_LEXICON >> VCM_CONCEPT)(picto_mod)
      #picto_mod_cons.keep_most_generic()
      
      name = lexs_2_owl(picto_mod)
      owl_file.names[name] = picto_mod, picto_mod_cons
      search_concept_2_owl(name, cons = picto_mod_cons)
      nb += 1
    sys.stdout = sys.__stdout__
    print("    %s..." % nb, file = sys.stderr)
    
    if owl_file.names: return owl_file
    return None
  
  def analyser_incoherences(owl_file, inconsistents):
    if not inconsistents: raise ValueError()
    
    for name in owl_file.names:
      lexs, picto_mod_cons = owl_file.names[name]
      picto_mods = lexs_2_picto_mods(lexs)
      cons = Concepts()
      for con in picto_mod_cons:
        if ("%s_SEARCH_icon_repr_%s" % (name, con.code)) in inconsistents: continue
        cons.add(con)
        
      cons  = cons.subtract(VCM_CONCEPT[426]) # Temporality
      cons  = cons.subtract(VCM_CONCEPT[214]) # Medical_care
      cons  = cons.subtract(VCM_CONCEPT[ 85]) # Medical_context
      cons  = simplify_concepts(cons)
      for con in cons:
        pymedtermino.vcm.db_consistency_cursor.execute(u"""INSERT INTO PictoModsSens VALUES (?, ?, ?, ?, ?);""", picto_mods + [con.code])
        
  main_loop(creer_nouveau_fichier, analyser_incoherences)
  print(nb, file = sys.stderr)

  pymedtermino.vcm.db_consistency_cursor.execute(u"""CREATE INDEX index_PictoModsSens on PictoModsSens(picto, mod1, mod2, mod3);""")
  close_db(pymedtermino.vcm.db_consistency, set_readonly = 0)

