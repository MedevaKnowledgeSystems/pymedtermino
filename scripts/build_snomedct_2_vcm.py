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

# (Re)build SNOMED CT => VCM mapping.

from __future__ import print_function

import sys, os, os.path, re
from collections        import defaultdict

import pymedtermino
pymedtermino.REMOVE_SUPPRESSED_CONCEPTS  = 0
pymedtermino.REMOVE_SUPPRESSED_TERMS     = 1
pymedtermino.REMOVE_SUPPRESSED_RELATIONS = 1

from pymedtermino       import *
from pymedtermino.vcm   import *
from pymedtermino.utils.mapping_db import *
from pymedtermino.snomedct         import *
from pymedtermino.snomedct         import MAIN_CLINICAL_FINDING_RELATIONS
from pymedtermino.snomedct_2_vcm   import *


class MultiConcepts(list):
  def find(self, terme):
    for termes in self:
      t = termes.find(terme)
      if t: return t
      
  def __str__(self): return "MultiConcepts(\n  %s,\n)" % ",\n  ".join([repr(i) for i in self])
  
  def keep_most_specific(self):
    for termes in self: termes.keep_most_specific()


def joindre_groupe_de_meme_localisation(groupes):
  groupes2 = []
  loca_2_groupes = defaultdict(list)
  for groupe in groupes:
    if "finding_site" in groupe.relations:
      for loca in groupe.finding_site:
        loca_2_groupes[loca].append(groupe)
    else:
      groupes2.append(groupe)
      
  for loca, groupes in loca_2_groupes.items():
    if len(groupes) == 1: groupes2.append(groupes[0])
    else:
      nouveau = Group()
      for groupe in groupes:
        for relation in groupe.relations:
          nouveau.add_relation(relation, getattr(groupe, relation))
      groupes2.append(nouveau)
  return groupes2


def snomedct_2_multi_snomedcts(terme, multi_snomedcts = None, debug = 0, avec_icones_mineures = 0):
  if multi_snomedcts is None:
    multi_snomedcts = MultiConcepts()
    multi_snomedcts.terme_2_relations = defaultdict(set)
    
  definitional_manifestations = set()
  associated_withs            = set()
  
  def ajouter_termes(multi_snomedcts, termes):
    multi_snomedcts.append(termes)
    termes.in_groups = set()
    
  def ajouter_terme(snomedcts, relation, terme2):
    snomedcts.add(terme2)
    multi_snomedcts.terme_2_relations[terme2].add(relation)
    if "has_definitional_manifestation" in terme2.relations:
      definitional_manifestations.update(terme2.has_definitional_manifestation)
      
  snomedcts_hors_groupe = set()
  ajouter_terme(snomedcts_hors_groupe, "isa", terme)
  
  for relation in terme.out_of_group.relations & MAIN_CLINICAL_FINDING_RELATIONS:
    for terme2 in getattr(terme.out_of_group, relation):
      if   relation == "has_definitional_manifestation":
        definitional_manifestations.add(terme2)
        continue
      elif relation == "associated_with":
        if terme2.is_a(SNOMEDCT[404684003]): # Pour les 'associated with', on ne retient que les 'clinical finding' et pas les procédures, etc
          associated_withs.add(terme2)
        continue
      elif relation == "part_of": # Already taken into account when mapping SNOMEDCT to VCM_CONCEPT
        continue
      ajouter_terme(snomedcts_hors_groupe, relation, terme2)
      
  #print("HORS GROUPE :", snomedcts_hors_groupe)
  
  if terme.groups:
    for groupe in joindre_groupe_de_meme_localisation(terme.groups):
      termes_du_groupe = Concepts(terme2 for relation in groupe.relations & MAIN_CLINICAL_FINDING_RELATIONS for terme2 in getattr(groupe, relation))
      
      if termes_du_groupe.find(SNOMEDCT[123037004]): # Body structure (body structure)
        ajouter_termes(multi_snomedcts, Concepts(i for i in snomedcts_hors_groupe if not i.is_a(SNOMEDCT[123037004]))) # Body structure (body structure)
      else:
        ajouter_termes(multi_snomedcts, Concepts(snomedcts_hors_groupe))
      for relation in groupe.relations & MAIN_CLINICAL_FINDING_RELATIONS:
        for terme2 in getattr(groupe, relation):
          ajouter_terme(multi_snomedcts[-1], relation, terme2)
          multi_snomedcts[-1].in_groups.add(terme2)
  else:
    ajouter_termes(multi_snomedcts, Concepts(snomedcts_hors_groupe))
    
  # REGLE : les relations s'appliquant sur le terme définissant la manifestation, sont considérées comme s'appliquant directement sur le terme qui est défini
  if definitional_manifestations:
    precedents = list(multi_snomedcts)
    for definition in definitional_manifestations:
      # REGLE : les maladies autoimmunes ne sont pas considérées comme des maladies du système immunitaire en VCM.
      if (terme.is_a(SNOMEDCT[85828009])) and (definition is SNOMEDCT[106182000]): continue
      
      snomedct_2_multi_snomedcts(definition, multi_snomedcts, debug = debug)
      
    for concepts in multi_snomedcts:
      if not concepts in precedents:
        concepts.update(snomedcts_hors_groupe)
        
  # REGLE : les termes "associés à" sont traités comme des paquets de concept en plus, mais ne se combine pas aux autres concepts
  if associated_withs:
    for associated_with in associated_withs:
      snomedct_2_multi_snomedcts(associated_with, multi_snomedcts, debug = debug)
      
      
  # REGLE : les malformations des chromosomes sont considérés comme des maladies génétiques et non comme des malformations,
  # sauf si une localisation (= "finding site") est associée.
  if terme.is_a(SNOMEDCT[74345006]):
    for termes in multi_snomedcts:
      if SNOMEDCT[107656002] in termes:
        relations = set()
        for terme2 in termes:
          relations.update(multi_snomedcts.terme_2_relations[terme2])
        if not "finding_site" in relations:
          termes.remove(SNOMEDCT[107656002])
          
  # REGLE : en cas de "Multiple congenital malformations", on élimine les localisations anatomiques.
  for termes in multi_snomedcts:
    if SNOMEDCT[116022009] in termes:
      relations = set()
      for terme2 in list(termes):
        if multi_snomedcts.terme_2_relations[terme2] == set(["finding_site"]):
          termes.remove(terme2)
          
  # REGLE : si oedème, on élimine les agrandissements (swelling). La SNOMEDCT considère l'oedème comme un type d'agrandissement, pas VCM.
  if multi_snomedcts.find(SNOMEDCT[79654002]): # Edema (morphologic abnormality)
    for termes in multi_snomedcts:
      termes.subtract_update(SNOMEDCT[442672001]) # Swelling (morphologic abnormality)

  # REGLE : les abcès sont par défaut considérés comme bactérien ;
  # si une étiologie d'infection (bactérien ou autre) est présente on retire donc l'abcès.
  for termes in multi_snomedcts:
    if termes.find(SNOMEDCT[44132006]) and termes.find(SNOMEDCT[441862004]): # Abscess ; Infectious process
      termes.subtract_update(SNOMEDCT[44132006]) # Abscess
      
  return multi_snomedcts


def multi_snomedcts_2_multi_concepts(terme_de_depart, multi_snomedcts, debug = 0, avec_icones_mineures = 0):
  multi_concepts = MultiConcepts()
  
  in_groups     = Concepts()
  quantitatives = Concepts()
  
  for termes in multi_snomedcts:
    multi_concepts.append(Concepts())
    multi_concepts[-1].in_groups = set()
    
    for terme in termes:
      corresps = (SNOMEDCT >> VCM_CONCEPT)(terme)
      for concept in corresps:
        if multi_snomedcts.terme_2_relations[terme] == set(["causative_agent"]):
          if   concept.is_a(VCM_CONCEPT[171]): concept = VCM_CONCEPT[48] # Graft, Caused_by_graft
          elif concept.is_a(VCM_CONCEPT[221]): concept = VCM_CONCEPT[45] # Radiotherapy, Caused_by_radiation
          elif concept.is_a(VCM_CONCEPT[215]): concept = VCM_CONCEPT[49] # Procedure, Caused_by_a_medical_procedure
          elif concept.is_a(VCM_CONCEPT[430]): concept = VCM_CONCEPT[47] # Drug_therapy, Caused_by_drug_treatment
          elif concept.is_a(VCM_CONCEPT[428]): concept = VCM_CONCEPT[46] # Therapy, Caused_by_treatment

        if concept.is_a(VCM_CONCEPT[447]): quantitatives.add(concept) # Trouble_fonctionnelle_quantitatif
          
        # REGLE : Si la relation est "interprets", on ne prend pas en compte les exposants (examen, traitement, etc) associé au terme SNOMED CT
        # ex : pour une leucocytose (finding), il s'agit d'une interprétation d'une numération des globule blanc, mais ce n'est pas un examen !
        if multi_snomedcts.terme_2_relations[terme] == set(["interprets"]) and concept.is_a(VCM_CONCEPT[214]): continue # Medical_care
        
        if debug: print("  ", unicode(terme).replace(u"\n", u" "), " => ", unicode(concept).replace(u"\n", u" "))
        multi_concepts[-1].add(concept)
        
        if terme in termes.in_groups:
          multi_concepts[-1].in_groups.add(concept)
          in_groups.add(concept)
          

  
  if debug:
    print ("CONCEPTS IN GROUPS =", in_groups)
  anatomical_structure = VCM_CONCEPT[251]
  biologic_function    = VCM_CONCEPT[94]
  alteration           = VCM_CONCEPT[436]
  patho                = VCM_CONCEPT[450]
  for concept_in_group in in_groups:
    if concept_in_group.is_a(anatomical_structure) or concept_in_group.is_a(biologic_function) or concept_in_group.is_a(alteration):
      concepts_to_remove = set([concept_in_group])
      if "INVERSE_is_achieved_by" in concept_in_group.relations:
        concepts_to_remove.update(concept_in_group.INVERSE_is_achieved_by)
      for concepts in multi_concepts:
        if (concepts_to_remove & concepts) and not(concepts_to_remove & concepts.in_groups):
          concepts.difference_update(concepts_to_remove)
          if concept_in_group.is_a(patho): concepts.add(patho)
          
  
  for quantitative in quantitatives:
    if debug:
      print()
      print("QUANTITATIVE =", quantitative)
    concepts_of_ancestors = []
    for ancestor in terme_de_depart.ancestors_no_double():
      concepts_of_ancestor = ancestor >> VCM_CONCEPT
      concepts_of_ancestor.ancestor = ancestor
      if concepts_of_ancestor.find(quantitative):
        concepts_of_ancestors.append(concepts_of_ancestor)

    for cs1 in concepts_of_ancestors[:]:
      for cs2 in concepts_of_ancestors:
        if cs1 is cs2: continue
        
        if cs1.imply(cs2):
          concepts_of_ancestors.remove(cs1)
          break

    if debug:
      print("CONCEPTS_OF_ANCESTORS =", concepts_of_ancestors)
      print()
      
    matching_concepts = list()
    for concepts in multi_concepts:
      for concepts_of_ancestor in concepts_of_ancestors:
        if concepts.imply(concepts_of_ancestor): 
          matching_concepts.append(concepts)
          break
    if matching_concepts:
      for concepts in multi_concepts:
        if not concepts in matching_concepts:
          concepts.discard(quantitative)
          
      
  if avec_icones_mineures:
    for concepts in multi_concepts:
      concepts.subtract_update(VCM_CONCEPT[55]) # Multi_hierarchical_concept
      
  multi_concepts.keep_most_specific()
  
  if terme_de_depart.is_a(SNOMEDCT[404684003]): # Clinical finding
    for concepts in multi_concepts:
      if not concepts.find(VCM_CONCEPT[450]): # Pathological_alteration
        concepts.add(VCM_CONCEPT[15]) # Absence_of_pathological_alteration
        
      
  # REGLE : si aucune temporalité n'est précisée, on ajoute "Actuel" pour les clinical findings
  for concepts in multi_concepts:
    #if concepts.find(VCM_CONCEPT[15]) or concepts.find(VCM_CONCEPT[450]): # Absence_of_pathological_alteration, Pathological_alteration
    if terme_de_depart.is_a(SNOMEDCT[404684003]): # Clinical finding
      if not concepts.find(VCM_CONCEPT[426]): concepts.add(VCM_CONCEPT[23]) # Temporality, Current
      
  # REGLE : la grossesse est traité comme une icône "isolée"
  for concepts in multi_concepts[:]:
    if concepts.find(VCM_CONCEPT[172]): # Pregnancy
      concepts.discard(VCM_CONCEPT[172]) # Pregnancy
      multi_concepts.append(Concepts([VCM_CONCEPT[172]])) # Pregnancy
      multi_concepts[-1].update(concepts.extract(VCM_CONCEPT[426])) # Temporality
      multi_concepts[-1].update(concepts.extract(VCM_CONCEPT[29])) # Stop
      if concepts.find(VCM_CONCEPT[450]): multi_concepts[-1].add(VCM_CONCEPT[450]) # Pathological_alteration, Pathological_alteration
      if concepts.find(VCM_CONCEPT[ 15]): multi_concepts[-1].add(VCM_CONCEPT[ 15]) # Absence_of_pathological_alteration, Absence_of_pathological_alteration
      
      
  # Retire les groupes doublons
  for concepts1 in multi_concepts[:]:
    for concepts2 in multi_concepts[:]:
      if concepts1 is concepts2: continue
      if concepts1 == concepts2: continue
      if concepts1.imply(concepts2):
        multi_concepts.remove(concepts2)
        
  return multi_concepts



def masques_recursive(concept):
  masques = set()
  for c in concept.self_and_ancestors_no_double():
    if "mask" in c.relations:
      for masque in c.mask: masques.add(masque)
  return masques

def multi_concepts_masquage(multi_concepts, debug = 0, avec_icones_mineures = 0):
  for concepts in multi_concepts:
    for concept in list(concepts):
      for masque in masques_recursive(concept):
        concepts.discard(masque)

  # REGLE : si un organe est présent, on ne prend pas en compte les régions anatomiques
  # (ex : si "poumon" est présent, on ne garde pas la localisation "thorax")
  # (NB il faut le faire APRES le masquage car une région peut masquer une structure tissulaire)
  for concepts in multi_concepts:
    for tissus in concepts.extract(VCM_CONCEPT[414]): # Tissular_structure
      if tissus.is_a(VCM_CONCEPT[256]): # Non_transversal_anatomical_structure
        concepts.subtract_update(VCM_CONCEPT[224]) # Anatomical_region
        break
      


def multi_concepts_2_multi_lexiques(multi_concepts, debug = 0):
  multi_lexiques = MultiConcepts()
  
  for concepts in multi_concepts: multi_lexiques.append((VCM_CONCEPT >> VCM_LEXICON)(concepts))
  
  return multi_lexiques

def multi_lexiques_2_icones(multi_lexiques, debug = 0):
  icones = Concepts()
  for lexs in multi_lexiques: icones.update((VCM_LEXICON >> VCM).map_concepts(lexs, debug = debug))      
  return keep_most_graphically_specific_icons(icones)


def snomedct_2_icons(t, debug = 0, avec_icones_mineures = 0):
  if debug:
    print()
    print(t)
    print()
    
  multi_snomedcts = snomedct_2_multi_snomedcts(t, debug = debug, avec_icones_mineures = avec_icones_mineures)
  
  if debug:
    print()
    print("SNOMEDCTS =", multi_snomedcts)
    
  multi_concepts = multi_snomedcts_2_multi_concepts(t, multi_snomedcts, debug = debug, avec_icones_mineures = avec_icones_mineures)
  
  if debug:
    print()
    print("CONCEPTS =", multi_concepts)
    
  multi_concepts_masquage(multi_concepts, debug = debug, avec_icones_mineures = avec_icones_mineures)
  
  if debug:
    print()
    print("CONCEPTS APRES MASQUAGE =", multi_concepts)
    
  multi_lexiques = multi_concepts_2_multi_lexiques(multi_concepts, debug = debug)
  
  if debug:
    print()
    print("LEXIQUES =", multi_lexiques)
    
  icones = multi_lexiques_2_icones(multi_lexiques, debug = debug)
  
  icones_corrected = manual_correction(t, icones)
  if not icones_corrected is None:
    icones = icones_corrected
    if debug:
      print()
      print("MANUAL CORRECTION!!!")
      print()
      
  if debug:
    print()
    for i in icones:
      print("=>", i, end = u"")
      
  return icones

def manual_correction(t, icones):
  if t.code == 194779001:
    return [VCM[u"en_cours--hypo--coeur"], VCM[u"en_cours--patho--rein"], VCM[u"en_cours--hyper-vaisseau_pa"]]
  if t.code == 194780003:
    return [VCM[u"en_cours--patho--coeur"], VCM[u"en_cours--hypo--rein"], VCM[u"en_cours--hyper-vaisseau_pa"]]
  return None


if __name__ == "__main__":
  if "--all" in sys.argv:
    snomedct2vcm = {}
    all_icons    = set()
    nb = 0
    for t in SNOMEDCT[404684003].self_and_descendants_no_double():
      nb += 1
      snomedct2vcm[t] = snomedct_2_icons(t)
      if (nb % 1000) == 0:
        print("%s..." % nb)
    def shortify_code(code):
      while code.endswith("--empty"): code = code[:-7]
      return code
    #f = open("/tmp/snomedct_2_vcm.txt", "w")
    s = u""
    nb = 0
    for t in SNOMEDCT[404684003].self_and_descendants_no_double():
      nb += 1
      for parent in t.parents:
        if snomedct2vcm[t] != snomedct2vcm.get(parent):
          for icon in snomedct2vcm[t]: all_icons.add(icon)
          #f.write("%s == %s\n" % (t.code, " ".join(shortify_code(icon.code) for icon in snomedct2vcm[t])))
          s += u"%s == %s\n" % (t.code, " ".join(shortify_code(icon.code) for icon in snomedct2vcm[t]))
          break
      if (nb % 1000) == 0:
        print("%s..." % nb)
        #f.flush()
    write_file("/tmp/snomedct_2_vcm.txt", s, "utf8")
    print("%s different icons." % len(all_icons))
    
    HERE        = os.path.dirname(sys.argv[0])
    SQLITE_FILE = os.path.join(HERE, "..", "snomedct_2_vcm.sqlite3")
    db = create_db(SQLITE_FILE)
    Txt_2_SQLMapping("/tmp/snomedct_2_vcm.txt", db, "INTEGER", "TEXT")
    close_db(db, SQLITE_FILE)
    
  else:
    #t = SNOMEDCT[95851007]
    #t = SNOMEDCT[430621000]
    
    #t = SNOMEDCT[41553006] 
    
    #t = SNOMEDCT[792004] # Creutzfeldt-Jakob
    
    t = SNOMEDCT[60442001]
    
    #t = SNOMEDCT[87666009]
    
    icones = snomedct_2_icons(t, debug = 1)
    
    print(t)
    print(icones)
    
