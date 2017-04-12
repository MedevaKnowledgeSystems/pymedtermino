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

import unittest

import pymedtermino
pymedtermino.LANGUAGE = "fr"
from pymedtermino          import *
from pymedtermino.icd10    import *
from pymedtermino.snomedct import *
from pymedtermino.vcm      import *
from pymedtermino.snomedct_2_vcm import *
from pymedtermino.scripts.build_snomedct_2_vcm import snomedct_2_icons


class TestVCM(unittest.TestCase):
  def setUp(self): pass
  
  def test_icd10(self):
    pymedtermino.LANGUAGE = "fr"
    assert ICD10["I10"].parents == [ICD10[u"I10-I15"]  # Hypertensive diseases
    ]
    print()
    print(ICD10.search("portal hypertension"))
    print()
    assert ICD10.search("portal hypertension") == [ICD10[u"K76.6"]  # Portal hypertension
    ]
    pymedtermino.LANGUAGE = "fr"
    

  
  def test_1(self): assert VCM.canonize_code(u"en_cours--patho--coeur--rien--rien--rien--rien") == u"en_cours--patho--coeur"
  def test_2(self): assert VCM.canonize_code(u"en_cours--patho--coeur--rien--rien--rien") == u"en_cours--patho--coeur"
  def test_3(self): assert VCM.canonize_code(u"en_cours--hypo--coeur--rien--rien--rien") == u"en_cours--hypo--coeur"
  def test_4(self): assert VCM.canonize_code(u"en_cours--patho-hypo--coeur--rien--rien--rien") == u"en_cours--hypo--coeur"
  def test_5(self): assert VCM.canonize_code(u"en_cours--patho-vaisseau--coeur--rien--rien--rien") == u"en_cours--patho-vaisseau--coeur"
  def test_6(self): assert VCM.canonize_code(u"en_cours--vaisseau-patho--coeur--rien--rien--rien") == u"en_cours--patho-vaisseau--coeur"
  def test_7(self): assert VCM.canonize_code(u"en_cours--vaisseau--coeur--rien--rien--rien") == u"en_cours--patho-vaisseau--coeur"
  def test_8(self): assert VCM.canonize_code(u"en_cours--physio--coeur--rien--rien--rien") == u"en_cours--physio--coeur"
  def test_9(self): assert VCM.canonize_code(u"en_cours--physio-vaisseau--coeur--rien--rien--rien") == u"en_cours--physio-vaisseau--coeur"

  def test_10(self): assert VCM[u"en_cours--patho--coeur"].is_a(VCM[u"en_cours--patho--coeur"])
  def test_11(self):
    def test_is_a(a, b):
      assert a.is_a(b)
      assert not b.is_a(a)
    test_is_a(VCM[u"en_cours--patho--coeur"], VCM[u"en_cours--patho--rien"])
    test_is_a(VCM[u"en_cours--bacterie--coeur"], VCM[u"en_cours--patho--coeur"])
    test_is_a(VCM[u"en_cours--bacterie--coeur"], VCM[u"en_cours--patho--rien"])
    test_is_a(VCM[u"en_cours--bacterie--coeur"], VCM[u"en_cours--patho--rien"])
    test_is_a(VCM[u"en_cours--hypo--coeur"], VCM[u"en_cours--patho--coeur"])
    test_is_a(VCM[u"en_cours--hypo--coeur"], VCM[u"en_cours--patho--rien"])
    test_is_a(VCM[u"en_cours--hypo--coeur"], VCM[u"en_cours--hypo--rien"])
  def test_12(self):
    assert VCM[u"en_cours--hypo--coeur_rythme"].is_a(VCM[u"en_cours--patho--coeur"])
  def test_13(self):
    assert VCM[u"en_cours--hypo--coeur_rythme"].is_a(VCM[u"en_cours--patho--coeur_rythme"])
  def test_14(self):
    assert not VCM[u"en_cours--hypo--coeur_rythme"].is_a(VCM[u"en_cours--hypo--coeur"])

  def compare_icons(self, icons1, icons2): assert set(icons1) == set(icons2)
    
  def test_15(self):
    self.compare_icons(VCM[u"en_cours--hypo--coeur--rien--rien--rien"].parents, [
      VCM[u"rien--hypo--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--patho--coeur--rien--rien--rien--rien"]  #
      ])
  def test_16(self):
    self.compare_icons(VCM[u"en_cours--patho--coeur--rien--rien--rien"].parents, [
      VCM[u"rien--patho--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--rien--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--patho--rien--rien--rien--rien--rien"]  # 
      ])
  def test_17(self):
    self.compare_icons(VCM[u"en_cours--patho--coeur_rythme--rien--rien--rien"].parents, [
      VCM[u"rien--patho--coeur_rythme--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--patho--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--rien--coeur_rythme--rien--rien--rien--rien"]  # 
      ])
  def test_18(self):
    self.compare_icons(VCM[u"en_cours--hypo--coeur_rythme--rien--rien--rien"].parents, [
      VCM[u"en_cours--patho--coeur_rythme--rien--rien--rien--rien"]  # 
    , VCM[u"rien--hypo--coeur_rythme--rien--rien--rien--rien"]  # 
      ])
  def test_19(self):
    self.compare_icons(VCM[u"en_cours--patho-vaisseau--coeur--rien--rien--rien"].parents, [
      VCM[u"en_cours--patho--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"rien--patho-vaisseau--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--rien-vaisseau--coeur--rien--rien--rien--rien"]  # 
    , VCM[u"en_cours--patho-vaisseau--rien--rien--rien--rien--rien"]  # 
      ])
  def test_20(self):
    self.compare_icons(VCM[u"en_cours--hypo--coeur_rythme--traitement--medicament--rien"].parents, [
      VCM[u"en_cours--patho--coeur_rythme--traitement--medicament--rien--rien"]  # 
    , VCM[u"rien--hypo--coeur_rythme--traitement--medicament--rien--rien"]  # 
    , VCM[u"en_cours--hypo--coeur_rythme--traitement--traitement--rien--rien"]  # 
    , VCM[u"en_cours--hypo--coeur_rythme--rien--rien--rien--rien"]  # 
      ])
  def test_21(self):
    self.compare_icons(VCM[u"risque--hypo--coeur--surveillance--diagnostic--rien"].parents, [
      VCM[u"rien--hypo--coeur--surveillance--diagnostic--rien--rien"]  # 
    , VCM[u"risque--patho--coeur--surveillance--diagnostic--rien--rien"]  # 
    , VCM[u"risque--hypo--coeur--rien--rien--rien--rien"]  # 
      ])

  def test_31(self):
    self.compare_icons(VCM[u"en_cours--patho--coeur--rien--rien--rien"].children, [
        VCM[u"en_cours--patho--coeur--antecedent_traitement--traitement--rien--rien"]  # 
      , VCM[u"en_cours--patho--coeur--traitement--traitement--rien--rien"]  # 
      , VCM[u"en_cours--patho--coeur_rythme--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--patho--coeur--rien--rien--rien--ombre"]  # 
      , VCM[u"en_cours--patho--coeur--rien--rien--prof--rien"]  # 
      , VCM[u"en_cours--patho--coeur--rien--rien--doc--rien"]  # 
      , VCM[u"en_cours--agrandissement--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--malformation--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--lesion--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--douleur--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--inflammation--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--substance--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--genetique--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--autoimmune--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--etio_traitement--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--allergie--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--infectieux--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--tumeur--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--hypo--coeur--rien--rien--rien--rien"]  # 
      , VCM[u"en_cours--hyper--coeur--rien--rien--rien--rien"]  # 
      ])
  def test_32(self):
    self.compare_icons(VCM[u"risque--hypo--coeur--surveillance--diagnostic--rien"].children, [
      VCM[u"risque--hypo--coeur--surveillance--diagnostic--rien--ombre"]  # 
    , VCM[u"risque--hypo2--coeur--surveillance--diagnostic--rien--rien"]  # 
    , VCM[u"risque--arret--coeur--surveillance--diagnostic--rien--rien"]  # 
    , VCM[u"risque--hypo--coeur--surveillance--diagnostic--prof--rien"]  # 
    , VCM[u"risque--hypo--coeur--surveillance--diagnostic--doc--rien"]  #
    , VCM[u"risque--hypo--coeur--surveillance--radio--rien"]  # 
    , VCM[u"risque--hypo--coeur--surveillance--bio--rien"]  # 
    , VCM[u"risque--hypo--coeur--surveillance--fonctionnel--rien"]  # 
    , VCM[u"risque--hypo--coeur--surveillance--clinique--rien"]  # 
      ])
    
  def test_41(self):
    assert (VCM_CONCEPT >> VCM_LEXICON)([VCM_CONCEPT[206], VCM_CONCEPT[346]]) == Concepts([
  VCM_LEXICON[504]  # Modificateur_patho
, VCM_LEXICON[609]  # Pictogramme_petit_intestin_bouché
, VCM_LEXICON[608]  # Pictogramme_petit_intestin
      ])
  def test_42(self):
    assert (VCM_LEXICON >> VCM_CONCEPT)([VCM_LEXICON[609]]) == Concepts([
      VCM_CONCEPT[308]
    , VCM_CONCEPT[346]
    , VCM_CONCEPT[300]
    , VCM_CONCEPT[206]
      ])

  def test_52(self):
    assert VCM[u"en_cours--patho--coeur"].consistent == 1
    assert VCM[u"en_cours--tumeur--peau"].consistent == 1
    assert VCM[u"en_cours--tumeur--sommeil"].consistent == 0


class TestSNOMEDCT_2_VCM(unittest.TestCase):
  TESTS = {
    SNOMEDCT[312132001] : set([u"en_cours--virus--oeil--rien--rien--rien--rien"]), # Viral eye infection
    SNOMEDCT[444819004] : set([u"en_cours--inflammation-vaisseau--rein--rien--rien--rien--rien"]), # Polyarteritis of kidney
    SNOMEDCT[38822007] : set([u"en_cours--inflammation--vessie--rien--rien--rien--rien"]), # Cystitis
    SNOMEDCT[57190000] : set([u"en_cours--hypo--oeil--rien--rien--rien--rien"]), # Myopia
    SNOMEDCT[415116008] : set([u"en_cours--hypo--plaquette--rien--rien--rien--rien"]), # Platelet count below reference range
    SNOMEDCT[410429000] : set([u"en_cours--arret--coeur--rien--rien--rien--rien"]), # Cardiac arrest
    SNOMEDCT[111583006] : set([u"en_cours--hyper--globule_blanc--rien--rien--rien--rien"]), # Leukocytosis
    SNOMEDCT[414478003] : set([u"en_cours--hyper--globule_blanc--rien--rien--rien--rien"]), # Leukocytosis
    SNOMEDCT[421869004] : set([u"en_cours--hypo--coeur_rythme--rien--rien--rien--rien"]), # Bradyarrhythmia
    SNOMEDCT[84828003] : set([u"en_cours--hypo--globule_blanc--rien--rien--rien--rien"]), # Leukopenia
    SNOMEDCT[123777002] : set([u"en_cours--autoimmune-hypo--globule_blanc--rien--rien--rien--rien"]), # Autoimmune leukopenia
    SNOMEDCT[300959008] : set([u"en_cours--allergie--toux--rien--rien--rien--rien"]), # Allergic cough
    SNOMEDCT[64572001] : set([u"en_cours--patho--rien--rien--rien--rien--rien"]), # Disease
    SNOMEDCT[91927006] : set([u"en_cours--allergie--gorge_nez--rien--rien--rien--rien"]), # Allergic rhinitis due to tree pollens
    SNOMEDCT[38689004] : set([u"en_cours--hypo-infectieux--globule_rouge--rien--rien--rien--rien"]), # :Hemolytic anemia due to infection
    SNOMEDCT[16932000] : set([u"en_cours--patho--nausee--rien--rien--rien--rien"]), # :Nausea and vomiting
    SNOMEDCT[69825009] : set([u"en_cours--tumeurb--bouche--rien--rien--rien--rien"]), # :Mucocele of salivary gland
    SNOMEDCT[17234001] : set([u"en_cours--malformation-tumeurb--grossesse", u"en_cours--malformation-tumeurb--vessie--rien--rien--rien--rien"]), # :Allantoic cyst
    SNOMEDCT[109553005] : set([u"en_cours--malformation-tumeurb--bouche--rien--rien--rien--rien"]), # :Palatal cyst of the newborn
    SNOMEDCT[93432008] : set([u"en_cours--etio_medicament-hypo--bronches--rien--rien--rien--rien"]), # :Drug-induced asthma
    SNOMEDCT[407674008] : set([u"en_cours--etio_medicament-hypo--bronches--rien--rien--rien--rien"]), # :Aspirin-induced asthma
    SNOMEDCT[24620004] : set([u"en_cours--hypo-parasite--globule_rouge--rien--rien--rien--rien"]), # :Hemolytic anemia due to babesiosis
    SNOMEDCT[4237001] : set([u"en_cours--infectieux--dent_pulpe--rien--rien--rien--rien"]), # :Suppurative pulpitis
    
    SNOMEDCT[253823009] : set([u"en_cours--tumeurb--genital_femelle--rien--rien--rien--rien"]), # :Embryonic cyst of ovary
    SNOMEDCT[410074002] : set([u"en_cours--patho--oeil--rien--rien--rien--rien"]), # :Atrophy of orbital fat
    SNOMEDCT[43742007] : set([u"en_cours--inflammation--coeur--rien--rien--rien--rien", u"en_cours--hypo--globule_rouge--rien--rien--rien--rien"]), # :Pericarditis associated with severe chronic anemia
    SNOMEDCT[28119000] : set([u"en_cours--patho--rein--rien--rien--rien--rien", u"en_cours--hyper-vaisseau_pa--rien--rien--rien--rien--rien"]), # :Renal hypertension
    SNOMEDCT[68267002] : set([u"en_cours--hyper-vaisseau_pa--cerveau--rien--rien--rien--rien"]), # :Benign intracranial hypertension
    SNOMEDCT[232266005] : set([u"en_cours--patho--oreille--rien--rien--rien--rien"]), # :Total loss of ossicle
    SNOMEDCT[200861004] : set([u"en_cours--etio_radio--peau--rien--rien--rien--rien"]), # :Skin changes due to chronic exposure to non-ionizing radiation
    SNOMEDCT[70385007] : set([u"en_cours--virus--oeil--rien--rien--rien--rien", u"en_cours--virus--gorge_nez--rien--rien--rien--rien"]), # :Adenoviral pharyngoconjunctivitis
    SNOMEDCT[236104004] : set([u"en_cours--patho--tube_digestif--rien--rien--rien--rien"]), # Gastrointestinal anastomotic stricture
    SNOMEDCT[20342001] : set([u"en_cours--patho--vessie_bouche--rien--rien--rien--rien"]), # Calculus in urethra
    SNOMEDCT[432504007] : set([u"en_cours--patho-vaisseau_bouche--cerveau--rien--rien--rien--rien"]), # Cerebral infarction
    SNOMEDCT[408512008] : set([u"en_cours--hyper--poids--rien--rien--rien--rien"]), # Body mass index 40+ - severely obese
    
    SNOMEDCT[225569001] : set([u"current--pain--eye--empty--empty--empty--empty", u"current--arrest--eye--empty--empty--empty--empty"]), # Painful blind eye
    SNOMEDCT[85828009] : set([u"current--autoimmune--empty--empty--empty--empty--empty"]), # Autoimmune disease
    SNOMEDCT[268240006] : set([u"current--malformation--muscle--empty--empty--empty--empty"]), # Congenital torticollis
    SNOMEDCT[262704003] : set([u"current--edema-patho--spinal_cord--empty--empty--empty--empty"]), # Edema of sacral cord
    SNOMEDCT[64775002] : set([u"current--obstructed_vessel-patho--brain--empty--empty--empty--empty"]), # Vertebral artery thrombosis
    SNOMEDCT[127909008] : set([u"empty--empty--white_cell--empty--empty--empty--empty"]), # Dendritic cell system structure
    SNOMEDCT[48499001] : set([u"current--hyper--weight--empty--empty--empty--empty"]), # Increased body mass index

    SNOMEDCT[5984000] : set([u"current--patho--delivery"]), # Fetus OR newborn affected by malpresentation, malposition AND/OR disproportion during labor AND/OR delivery (disorder)
    SNOMEDCT[443371007] : set([u"current--hypo--cerebral_function"]), # Decreased level of consciousness (finding)
    SNOMEDCT[398665005] : set([u"current--hypo--cerebral_function"]), # Vasovagal syncope (disorder)
    SNOMEDCT[299698007] : set([u"current--patho--alimentation"]), # Feeding poor (finding)
    SNOMEDCT[54016002] : set([u"current--patho--heart_rhythm"]), # Mobitz type I incomplete atrioventricular block (disorder)
    SNOMEDCT[80394007] : set([u"current--hyper--glycemia"]), # Hyperglycemia (disorder)
    SNOMEDCT[271327008] : set([u"current--hypo--glycemia"]), # Hypoglycemic syndrome (disorder)
    SNOMEDCT[14900002] : set([u"current--due_to_radiation-hypo--gland"]), # Radiotherapy-induced hypopituitarism (disorder)
    SNOMEDCT[49650001] : set([u"current--pain--urinary_bladder"]), # Dysuria (finding)
    SNOMEDCT[423341008] : set([u"en_cours--nerf-patho--oeil", u"en_cours--oedeme-patho--oeil"]), # Optic disc edema (disorder)
    SNOMEDCT[6400008] : set([u"current--patho--eye", u"current--patho--lipidemia"]), # Xanthoma of eyelid (disorder)
    SNOMEDCT[66628005] : set([u"current--autoimmune--eye", u"current--enlargement--thyroid", u"current--autoimmune-hyper--thyroid"]), # Toxic diffuse goiter with exophthalmos AND with thyrotoxic storm (disorder)

    SNOMEDCT[414545008] : set([u"current--patho-vessel--heart"]), # Ischemic heart disease (disorder)
    SNOMEDCT[41256004] : set([u"current--hypo--eye"]), # Presbyopia (disorder)
    SNOMEDCT[72866009] : set([u"current--patho-vessel--leg"]), # Varicose veins of lower extremity (disorder)
    SNOMEDCT[70153002] : set([u"current--patho-vessel--large_intestine"]), # Hemorrhoids (disorder)

    SNOMEDCT[20656007] : set([u"current--patho-vessel--mouth"]), # Sublingual varices (disorder)
    SNOMEDCT[28670008] : set([u"current--patho-vessel--oesophagia"]), # Esophageal varices (disorder)

    SNOMEDCT[75119003] : set([u"current--parasite--liver"]), # Amebic liver abscess (disorder)

#    SNOMEDCT[] : set([u""]), # 
    }
  
  @classmethod
  def create_test(clazz):
    for snomedct, icons in clazz.TESTS.items():
      def f(self, snomedct = snomedct, icons = icons):
        icons  = Concepts([VCM[code] for code in icons])
        icons2 = snomedct_2_icons(snomedct)
        if icons != icons2:
          print("Error for :", snomedct)
          print(icons)
          print(icons2)
        assert icons == icons2
      setattr(clazz, "test_%s" % snomedct.code, f)
  
TestSNOMEDCT_2_VCM.create_test()

class TestVCM_consistency(unittest.TestCase):
  TESTS = {
    VCM[u"en_cours--patho--coeur"] : Concepts([
      VCM_CONCEPT[266]  # Structure_cardiaque
    , VCM_CONCEPT[102]  # Fonction_cardiaque
    , VCM_CONCEPT[450]  # Trouble_pathologique
    , VCM_CONCEPT[23]  # Actuel
    ]),
    VCM[u"antecedent--patho--coeur"] : Concepts([
      VCM_CONCEPT[208]  # Passé
    , VCM_CONCEPT[266]  # Structure_cardiaque
    , VCM_CONCEPT[102]  # Fonction_cardiaque
    , VCM_CONCEPT[450]  # Trouble_pathologique
    ]),
    VCM[u"risque--bacterie--coeur"] : Concepts([
      VCM_CONCEPT[166]  # Futur
    , VCM_CONCEPT[266]  # Structure_cardiaque
    , VCM_CONCEPT[188]  # Infection_bactérienne
    , VCM_CONCEPT[450]  # Trouble_pathologique
    ]),
    VCM[u"risque--hypo--coeur_rythme"] : Concepts([
      VCM_CONCEPT[132]  # Fonction_de_régulation_du_rythme_cardiaque
    , VCM_CONCEPT[180]  # Hypofonctionnement
    , VCM_CONCEPT[450]  # Trouble_pathologique
    , VCM_CONCEPT[166]  # Futur
    ]),
    VCM[u"risque--arret--grossesse"] : Concepts([
      VCM_CONCEPT[29]  # Arrêt
    , VCM_CONCEPT[172]  # Grossesse
    , VCM_CONCEPT[166]  # Futur
    , VCM_CONCEPT[450]  # Trouble_pathologique
    ]),
    VCM[u"en_cours--hypo-vaisseau_pa--coeur"] : Concepts([
      VCM_CONCEPT[266]  # Structure_cardiaque
    , VCM_CONCEPT[180]  # Hypofonctionnement
    , VCM_CONCEPT[130]  # Fonction_de_régulation_de_la_tension
    , VCM_CONCEPT[23]  # Actuel
    , VCM_CONCEPT[450]  # Trouble_pathologique
    ]),
    VCM[u"en_cours--bacterie--coeur_rythme"] : Concepts(),
    VCM[u"en_cours--hypo--coeur--traitement--medicament"] : Concepts([
      VCM_CONCEPT[430]  # Traitement_médicamenteux
    , VCM_CONCEPT[180]  # Hypofonctionnement
    , VCM_CONCEPT[102]  # Fonction_cardiaque
    , VCM_CONCEPT[450]  # Trouble_pathologique
    , VCM_CONCEPT[23]  # Actuel
    ])
    }
  
  @classmethod
  def create_test(clazz):
    for icon, concepts in clazz.TESTS.items():
      def f(self, icon = icon, concepts = concepts):
        assert icon.concepts == concepts
        if concepts: assert     icon.consistent
        else:        assert not icon.consistent
      setattr(clazz, "test_%s" % icon.code, f)

TestVCM_consistency.create_test()


if __name__ == '__main__':
  unittest.main()
  
  #import cProfile; cProfile.run("unittest.main()")
