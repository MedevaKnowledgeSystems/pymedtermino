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

from __future__ import print_function

import sys, os, os.path, csv
from collections import defaultdict

from pymedtermino     import *
from pymedtermino.vcm import *

class Label(object):
  def __init__(self, **langs):
    self.langs = langs
    
  def __repr__(self): return "Label(%s)" % ", ".join('%s = "%s"' % (lang, self.langs[lang]) for lang in self.langs)
  def __getitem__(self, lang): return self.langs[lang]
  def __setitem__(self, lang, v): self.langs[lang] = v
  
class LabelPart(object):
  def __init__(self, **parts):
    self.parts   = parts
    self.genres  = {}
    self.langs   = {}
    self.methods = {}
    for key, val in parts.items():
      splitted = key.split("_")
      if len(splitted) == 2: lang, method = splitted; genre = ""
      else:                  lang, method, genre = splitted
      if not lang in self.methods: self.methods[lang] = set()
      self.methods[lang].add(method)
      if method == "base":
        self.langs [lang, method] = val
        self.genres[lang] = genre
      else:
        if genre: self.langs[lang, method, genre] = val
        else:
          self.langs[lang, method] = val
          
  def __repr__(self): return "LabelPart(%s)" % ", ".join('%s = "%s"' % (key, val) for key, val in self.parts.items())
  
  def to_label(self): return Label(**self.langs)
  
  def __getitem__(self, index):
    lang, method, genre = index
    r = self.langs.get((lang, method, genre))
    if not r: r = self.langs[lang, method]
    return r
    
def combine(parts, orig_concepts):
  r = Label()
  for lang in ["en", "fr"]:
    bases = [part for part in parts if "base"   in part.methods[lang]]
    if (not orig_concepts.find(VCM_CONCEPT[251])) and (orig_concepts.find(VCM_CONCEPT[94])) and (bases[-1] is data[cons("Pathological_alteration")]): # Anatomical_structure, Biologic_function
      bases[-1] = LabelPart(en_base = "disorder", fr_base_m = "trouble")
    genre = bases[0].genres[lang]
    ppres = [part for part in parts if "preprefix" in part.methods[lang]]
    pres  = [part for part in parts if "prefix"    in part.methods[lang]]
    adjs  = [part for part in parts if "adj"       in part.methods[lang]]
    comps = [part for part in parts if "comp"      in part.methods[lang]]
    sufs  = [part for part in parts if "suffix"    in part.methods[lang]]
    bases = [base[lang, "base",      genre] for base in bases]
    ppres = [ppre[lang, "preprefix", genre] for ppre in ppres]
    pres  = [pre [lang, "prefix",    genre] for pre  in pres]
    adjs  = [adj [lang, "adj",       genre] for adj  in adjs]
    comps = [comp[lang, "comp",      genre] for comp in comps]
    sufs  = [suf [lang, "suffix",    genre] for suf  in sufs]
    comps.reverse()
    if   lang == "en": r[lang] = " ".join(ppres + pres + adjs + bases + comps + sufs)
    elif lang == "fr": r[lang] = " ".join(ppres + pres + bases + adjs + comps + sufs)
  return r


#CONCEPTS = { concept.get_translation("en") : concept for concept in VCM_CONCEPT.all_concepts() }
CONCEPTS = dict((concept.get_translation("en"), concept) for concept in VCM_CONCEPT.all_concepts() )
def cons(*ss): return frozenset(CONCEPTS[s] for s in ss)

data = {
  cons("Therapy") : LabelPart(en_preprefix = "treatment of", fr_preprefix = "traitement de"),
  cons("Drug_therapy") : LabelPart(en_preprefix = "drug for", fr_preprefix = "médicament de"),
  cons("Topical_drug_therapy") : LabelPart(en_preprefix = "topic drug for", fr_preprefix = "médicament topique de"),
  cons("Injectable_systemic_drug_therapy") : LabelPart(en_preprefix = "injectable drug for", fr_preprefix = "médicament injectable de"),
  cons("Oral_systemic_drug_therapy") : LabelPart(en_preprefix = "oral drug for", fr_preprefix = "médicament oral de"),
  
  cons("Procedure") : LabelPart(en_preprefix = "procedure for", fr_preprefix = "procédure pour"),
  cons("Radiotherapy") : LabelPart(en_preprefix = "radiotherapy for", fr_preprefix = "radiothérapie de"),
  cons("Surgical_procedure") : LabelPart(en_preprefix = "surgery treatment for", fr_preprefix = "traitement chirurgical de"),
  cons("Implant") : LabelPart(en_preprefix = "implant for", fr_preprefix = "implant de"),
  cons("Implant", "Pathological_alteration") : LabelPart(en_base = "implant", fr_base_m = "implant"),
  cons("Graft") : LabelPart(en_preprefix = "graft treatment for", fr_preprefix = "traitement par greffe de"),
  cons("Graft", "Pathological_alteration") : LabelPart(en_base = "graft", fr_base_f = "greffe"),
  cons("Ectomy") : LabelPart(en_preprefix = "ablation surgery for", fr_preprefix = "chirurgie ablative de"),
  cons("Ectomy", "Pathological_alteration") : LabelPart(en_base = "(total or partial) ablation", fr_base_f = "ablation (totale ou partielle)"),
  cons("Retraining_therapy") : LabelPart(en_preprefix = "retraining therapy for", fr_preprefix = "traitement par rééducation de"),
  cons("Lifestyle_and_dietary_therapy") : LabelPart(en_preprefix = "lifestyle and dietary therapy for", fr_preprefix = "règles hygiéno-diététiques pour"),
  
  #cons("Medical_test") : LabelPart(en_preprefix = "monitoring of", fr_preprefix = "surveillance de"),
  #cons("Medical_test", "Pathological_alteration") : LabelPart(en_base = "monitoring", fr_base_f = "surveillance"),
  cons("Clinical_test", "Future") : LabelPart(en_preprefix = "clinical test for", fr_preprefix = "examen clinique de"),
  cons("Clinical_test", "Pathological_alteration", "Future") : LabelPart(en_base = "clinical test", fr_base_m = "examen clinique"),
  cons("Biological_test", "Future") : LabelPart(en_preprefix = "biological test for", fr_preprefix = "test biologique de"),
  cons("Biological_test", "Pathological_alteration", "Future") : LabelPart(en_base = "biological test", fr_base_m = "test biologique"),
  cons("Anormal_biological_examination", "Future") : LabelPart(en_preprefix = "biological test for", en_suffix = "with abnormal result", fr_preprefix = "test biologique de", fr_suffix = "avec résultats anormaux"),
  cons("Anormal_biological_examination", "Pathological_alteration", "Future") : LabelPart(en_base = "biological test", en_suffix = "with abnormal result", fr_base_m = "test biologique", fr_suffix = "avec résultats anormaux"),
  cons("Imaging_test", "Future") : LabelPart(en_preprefix = "imaging for", fr_preprefix = "imagerie de"),
  cons("Imaging_test", "Pathological_alteration", "Future") : LabelPart(en_base = "imaging", fr_base_f = "imagerie"),
  cons("Functional_test", "Future") : LabelPart(en_preprefix = "functional test for", fr_preprefix = "examen fonctionnel de"),
  cons("Functional_test", "Pathological_alteration", "Future") : LabelPart(en_base = "functional test", fr_base_m = "examen fonctionnel"),
  cons("Biopsy", "Future") : LabelPart(en_preprefix = "biopsy for", fr_preprefix = "biopsie pour"),
  cons("Biopsy", "Pathological_alteration", "Future") : LabelPart(en_base = "biopsy", fr_base_f = "biopsie"),
  cons("Diagnostic", "Future") : LabelPart(en_preprefix = "diagnosis of", fr_preprefix = "diagnostic de"),
  
  cons("Medical_document") : LabelPart(en_preprefix = "document related to", fr_preprefix = "compte-rendu sur"),
  cons("Health_professional", "Pathological_alteration") : LabelPart(en_base = "physician", fr_base_m = "médecin"),
  cons("Health_professional", "Cardiac_function", "Cardiac_structure", "Pathological_alteration") : LabelPart(en_base = "cardiologist", fr_base_m = "cardiologue"),
  cons("Health_professional", "Infection", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "infectiologist", fr_base_m = "infectiologue"),
  cons("Health_professional", "Bacterial_infection", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "bacteriologist", fr_base_m = "bacteriologue"),
  cons("Health_professional", "Viral_infection", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "virologist", fr_base_m = "virologue"),
  cons("Health_professional", "Parasitic_infection", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "parasitologist", fr_base_m = "parasitologue"),
  cons("Health_professional", "Tumor", "Pathological_alteration") : LabelPart(en_base = "cancerologist", fr_base_m = "cancérologue"),
  cons("Health_professional", "Peripheric_nervous_structure", "Peripheric_nervous_function", "Pathological_alteration") : LabelPart(en_base = "neurologist", fr_base_m = "neurologue"),
  cons("Health_professional", "Alimentation", "Pathological_alteration") : LabelPart(en_base = "nutritionist", fr_base_m = "nutritionniste"),
  cons("Health_professional", "Bone_structure", "Pathological_alteration") : LabelPart(en_base = "orthopedic surgeon", fr_base_m = "chirurgien orthopédiste"),
  cons("Health_professional", "Articular_function", "Pathological_alteration") : LabelPart(en_base = "rheumatologist", fr_base_m = "rhumatologue"),
  cons("Health_professional", "Behavioral_function", "Pathological_alteration") : LabelPart(en_base = "psychologist", fr_base_m = "psychologue"),
  cons("Health_professional", "Odontologic_structure", "Pathological_alteration") : LabelPart(en_base = "dentist", fr_base_m = "dentiste"),
  cons("Health_professional", "Visual_function", "Visual_structure", "Pathological_alteration") : LabelPart(en_base = "opthtalmologist", fr_base_m = "opthtalmologue"),
  cons("Health_professional", "Integumentary_structure", "Pathological_alteration") : LabelPart(en_base = "dermatologist", fr_base_m = "dermatologue"),
  cons("Health_professional", "Female_reproductive_function", "Female_genital_structure", "Pathological_alteration") : LabelPart(en_base = "gynécologist", fr_base_m = "gynécoloque"),
  cons("Health_professional", "Hormonal_regulation_function", "Endocrine_structure", "Pathological_alteration") : LabelPart(en_base = "endocrinologist", fr_base_m = "endocrinologue"),
  cons("Health_professional", "Respiratory_function", "Respiratory_structure", "Pathological_alteration") : LabelPart(en_base = "pneumologist", fr_base_m = "pneumologue"),
  cons("Health_professional", "Upper_respiratory_tract_structure", "Pathological_alteration") : LabelPart(en_base = "otolaryngologist", fr_base_m = "oto-rhino-laryngologue (ORL)"),
  cons("Health_professional", "Renal_excretion_function", "Urinary_structure", "Pathological_alteration") : LabelPart(en_base = "nephrologist", fr_base_m = "néphrologue"),
  cons("Health_professional", "Diabetes", "Pathological_alteration") : LabelPart(en_base = "diabetologist", fr_base_m = "diabétologue"),
  cons("Health_professional", "Pregnancy", "Absence_of_pathological_alteration") : LabelPart(en_base = "midwife", fr_base_f = "sage-femme"),
  cons("Health_professional", "Drug_therapy", "Pathological_alteration") : LabelPart(en_base = "pharmacist", fr_base_m = "pharmacien"),
  cons("Health_professional", "Surgical_procedure", "Pathological_alteration") : LabelPart(en_base = "surgeon", fr_base_m = "chirurgien"),
  cons("Health_professional", "Retraining_therapy", "Pathological_alteration") : LabelPart(en_base = "physical therapist", fr_base_m = "kinésitherapeute"),
  cons("Health_professional", "Lifestyle_and_dietary_therapy", "Pathological_alteration") : LabelPart(en_base = "dietician", fr_base_m = "diététicien"),
  cons("Health_professional", "Biological_test", "Future", "Pathological_alteration") : LabelPart(en_base = "biologist", fr_base_m = "biologiste"),
  cons("Health_professional", "Imaging_test", "Future", "Pathological_alteration") : LabelPart(en_base = "radiologist", fr_base_m = "radiologue"),
  
  cons("Property_of_a_drug_treatment") : LabelPart(en_base = "property of the drug treatment", fr_base_f = "propriété du traitement médicamenteux"),
  cons("Low_dose") : LabelPart(en_base = "low dose", fr_base_f = "faible dose"),
  cons("High_dose") : LabelPart(en_base = "high dose", fr_base_f = "forte dose"),
  cons("Current_dose") : LabelPart(en_base = "dose", fr_base_f = "dose"),
  cons("Current_dose", "Decrease_of_a_property_of_a_drug_treatment") : LabelPart(en_base = "dose decrease", fr_base_f = "diminution de la dose"),
  cons("Current_dose", "Increase_of_a_property_of_a_drug_treatment") : LabelPart(en_base = "dose increase", fr_base_f = "augmentation de la dose"),
  cons("Withdrawal") : LabelPart(en_base = "withdrawal", fr_base_m = "sevrage"),
  cons("Treatment_discontinuation") : LabelPart(en_base = "stop the treatment", fr_base_f = "arrêt du traitement"),
  cons("Dose_schedule") : LabelPart(en_base = "dose shedule", fr_base_m = "plan de prise"),
  
  
  cons("Past")    : LabelPart(en_prefix = "history of", fr_prefix = "antécédent de"),
  cons("Future")  : LabelPart(en_prefix = "risk of", fr_prefix = "risque de"),
  
  cons("Absence_of_pathological_alteration") : LabelPart(en_base = "physiologic state", fr_base_f = "état physiologique"),
  cons("Pathological_alteration") : LabelPart(en_base = "disorder", fr_base_f = "maladie"),
  cons("Allergy") : LabelPart(en_adj = "allergic", fr_adj = "allergique"),
  cons("Inflammation") : LabelPart(en_adj = "inflammatory", fr_adj = "inflammatoire"),
  cons("Inflammation", "Pathological_alteration") : LabelPart(en_base = "inflammation", fr_base_f = "inflammation"),
  cons("Obstruction") : LabelPart(en_suffix = "with obstruction", fr_suffix = "avec obstruction"),
  cons("Obstruction", "Pathological_alteration") : LabelPart(en_base = "obstruction", fr_base_f = "obstruction"),
  cons("Stop", "Pathological_alteration") : LabelPart(en_base = "arrest", fr_base_m = "arrêt"),
  cons("Autoimmune") : LabelPart(en_adj = "autoimmune", fr_adj_f = "autoimmune", fr_adj_m = "autoimmun"),
  
  cons("Infection", "Pathological_alteration") : LabelPart(en_base = "infection", fr_base_f = "infection"),
  cons("Infection", "Pathological_alteration", "Inflammation") : LabelPart(en_base = "infection", fr_base_f = "infection"),
  cons("Infection") : LabelPart(en_adj = "infectious", fr_adj_f = "infectieuse", fr_adj_m = "infectieux"),
  cons("Infection", "Inflammation") : LabelPart(en_adj = "infectious", fr_adj_f = "infectieuse", fr_adj_m = "infectieux"),
  cons("Bacterial_infection", "Pathological_alteration") : LabelPart(en_base = "bacterial infection", fr_base_f = "infection bactérienne"),
  cons("Bacterial_infection", "Pathological_alteration", "Inflammation") : LabelPart(en_base = "bacterial infection", fr_base_f = "infection bactérienne"),
  cons("Bacterial_infection") : LabelPart(en_adj = "bacterial", fr_adj_f = "bactérienne", fr_adj_m = "bactérien"),
  cons("Bacterial_infection", "Inflammation") : LabelPart(en_adj = "bacterial", fr_adj_f = "bactérienne", fr_adj_m = "bactérien"),
  cons("Viral_infection", "Pathological_alteration") : LabelPart(en_base = "viral infection", fr_base_f = "infection virale"),
  cons("Viral_infection", "Pathological_alteration", "Inflammation") : LabelPart(en_base = "viral infection", fr_base_f = "infection virale"),
  cons("Viral_infection") : LabelPart(en_adj = "viral", fr_adj_f = "virale", fr_adj_m = "viral"),
  cons("Viral_infection", "Inflammation") : LabelPart(en_adj = "viral", fr_adj_f = "virale", fr_adj_m = "viral"),
  cons("Viral_infection", "Inflammation") : LabelPart(en_adj = "viral", fr_adj_f = "virale", fr_adj_m = "viral"),
  cons("Fungal_infection", "Pathological_alteration") : LabelPart(en_base = "mycosis", fr_base_f = "mycose"),
  cons("Fungal_infection", "Pathological_alteration", "Inflammation") : LabelPart(en_base = "mycosis", fr_base_f = "mycose"),
  cons("Fungal_infection") : LabelPart(en_adj = "fungal", fr_adj_f = "fongique", fr_adj_m = "fongique"),
  cons("Fungal_infection", "Inflammation") : LabelPart(en_adj = "fungal", fr_adj_f = "fongique", fr_adj_m = "fongique"),
  cons("Parasitic_infection", "Pathological_alteration") : LabelPart(en_base = "parasite", fr_base_m = "parasite"),
  cons("Parasitic_infection", "Pathological_alteration", "Inflammation") : LabelPart(en_base = "parasite", fr_base_m = "parasite"),
  cons("Parasitic_infection") : LabelPart(en_adj = "parasitic", fr_adj_f = "parasitaire", fr_adj_m = "parasitaire"),
  cons("Parasitic_infection", "Inflammation") : LabelPart(en_adj = "parasitic", fr_adj_f = "parasitaire", fr_adj_m = "parasitaire"),
  
  cons("Caused_by_a_substance", "Pathological_alteration") : LabelPart(en_base = "poisoning", fr_base_f = "intoxication"),
  cons("Caused_by_a_substance") : LabelPart(en_suffix = "due to poisoning", fr_suffix = "suite à une intoxication"),
  cons("Dependency", "Pathological_alteration") : LabelPart(en_base = "dependence", fr_base_f = "dépendance"),
  cons("Dependency") : LabelPart(en_comp = "related to dependence", fr_comp = "liée à une dépendance"),
  cons("Caused_by_drug_treatment") : LabelPart(en_adj = "drug-induced", fr_suffix = "de cause médicamenteuse"),
  cons("Caused_by_graft", "Pathological_alteration") : LabelPart(en_base = "graft complication", fr_base_f = "complication", fr_suffix = "suite à une greffe"),
  cons("Caused_by_graft") : LabelPart(en_suffix = "due to a graft", fr_suffix = "suite à une greffe"),
  cons("Caused_by_radiation", "Pathological_alteration") : LabelPart(en_base = "complication", en_suffix = "due to radiation", fr_base_f = "complication", fr_suffix = "suite à une irradiation"),
  cons("Caused_by_radiation") : LabelPart(en_suffix = "due to radiation", fr_suffix = "suite à une irradiation"),
  cons("Caused_by_treatment") : LabelPart(en_adj = "iatrogenic", fr_adj = "iatrogénique"),
  cons("Oedema", "Liquid_penetration", "Pathological_alteration") : LabelPart(en_base = "edema", fr_base_m = "oedème"),
  cons("Oedema", "Liquid_penetration") : LabelPart(en_suffix = "with edema", fr_suffix = "avec oedème"),
  cons("Oedema", "Pathological_alteration") : LabelPart(en_base = "edema", fr_base_m = "oedème"),
  cons("Oedema") : LabelPart(en_suffix = "with edema", fr_suffix = "avec oedème"),
  cons("Enlargement", "Pathological_alteration") : LabelPart(en_base = "hypertrophy", fr_base_f = "hypertrophie"),
  cons("Enlargement") : LabelPart(en_adj = "hypertrophic", fr_adj = "hypertrophique"),
  cons("Genetic") : LabelPart(en_adj = "genetic", fr_adj = "génétique"),
  cons("Hemorrhage", "Pathological_alteration") : LabelPart(en_base = "hemorrhage", fr_base_f = "hémorragie"),
  cons("Hemorrhage") : LabelPart(en_adj = "hemorrhagic", fr_adj = "hémorragique"),
  cons("Lesion", "Pathological_alteration") : LabelPart(en_base = "ulcer", fr_base_f = "ulcère"),
  cons("Lesion") : LabelPart(en_suffix = "with ulcer", fr_suffix = "avec ulcère"),
  cons("Malformation", "Pathological_alteration") : LabelPart(en_base = "congenital anomaly", fr_base_f = "anomalie congénitale"),
  cons("Malformation") : LabelPart(en_adj = "congenital", fr_adj_f = "congénitale", fr_adj_m = "congénital"),
  cons("Pain", "Pathological_alteration") : LabelPart(en_base = "pain", fr_base_f = "douleur"),
  cons("Pain") : LabelPart(en_adj = "painful", fr_adj_f = "douloureuse", fr_adj_m = "douloureux"),
  cons("Tumor", "Pathological_alteration") : LabelPart(en_base = "neoplasm", fr_base_f = "tumeur"),
  cons("Tumor") : LabelPart(en_adj = "malignant", fr_adj_f = "maligne", fr_adj_m = "malin"),
  cons("Cyst", "Benign_tumor", "Pathological_alteration") : LabelPart(en_base = "benign neoplasm", fr_base_f = "tumeur bénine"),
  cons("Cyst", "Benign_tumor") : LabelPart(en_adj = "malignant", fr_adj_f = "bénine", fr_adj_m = "bénin"),
  cons("Benign_tumor", "Pathological_alteration") : LabelPart(en_base = "benign neoplasm", fr_base_f = "tumeur bénine"),
  cons("Benign_tumor") : LabelPart(en_adj = "malignant", fr_adj_f = "bénine", fr_adj_m = "bénin"),
  
  cons("Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperfunctionning", fr_base_f = "hyperfonction"),
  cons("Hyperfunctionning") : LabelPart(en_suffix = "with hyperfunctionning", fr_suffix = "avec hyperfonction"),
  cons("Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "insufficiency", fr_base_f = "insuffisance"),
  cons("Hypofunctionning") : LabelPart(en_suffix = "with insufficiency", fr_suffix = "avec insuffisance"),
  cons("Increase_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "increase", fr_base_f = "augmentation"),
  cons("Increase_of_an_anatomical_structure") : LabelPart(en_suffix = "with increase", fr_suffix = "avec augmentation"),
  cons("Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "decrease", fr_base_f = "diminution"),
  cons("Decrease_of_an_anatomical_structure") : LabelPart(en_suffix = "with decrease", fr_suffix = "avec diminution"),
  
  # Loca secondaire
  cons("Metabolic_function", "Metabolic_etiology") : LabelPart(en_adj = "metabolic", fr_adj = "métabolique"),
  cons("Metabolic_function") : LabelPart(en_adj = "metabolic", fr_adj = "métabolique"),
  cons("Metabolic_etiology") : LabelPart(en_adj = "metabolic", fr_adj = "métabolique"),
  cons("Vascular_structure") : LabelPart(en_adj = "vascular", fr_adj = "vasculaire"),
  cons("Vascular_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "vasculitis", fr_base_f = "vascularite"),
  cons("Vascular_structure", "Obstruction", "Pathological_alteration") : LabelPart(en_base = "thrombosis", fr_base_f = "thrombose"),
  cons("Vascular_structure", "Inflammation", "Obstruction", "Pathological_alteration") : LabelPart(en_base = "thrombophlebitis", fr_base_f = "thrombophlébite"),
  cons("Blood_pressure_regulation_function", "Pathological_alteration") : LabelPart(en_base = "abnormal blood pressure", fr_base_f = "pression artérielle anormale"),
  cons("Blood_pressure_regulation_function", "Absence_of_pathological_alteration") : LabelPart(en_base = "normal blood pressure", fr_base_f = "pression artérielle normale"),
  cons("Blood_pressure_regulation_function") : LabelPart(en_comp = "of blood pressure", fr_comp = "de la pression artérielle"),
  cons("Blood_pressure_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypotension", fr_base_f = "hypotension"),
  cons("Blood_pressure_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hypertension", fr_base_f = "hypertension"),
  cons("Blood_pressure_regulation_function", "Hypofunctionning") : LabelPart(en_suffix = "with hypotension", fr_suffix = "avec hypotension"),
  cons("Blood_pressure_regulation_function", "Hyperfunctionning") : LabelPart(en_suffix = "with hypertension", fr_suffix = "avec hypertension"),
  cons("Peripheric_nervous_structure", "Peripheric_nervous_function", "Pathological_alteration") : LabelPart(en_base = "neuropathy", fr_base_f = "neuropathie"),
  cons("Peripheric_nervous_structure", "Pathological_alteration") : LabelPart(en_base = "neuropathy", fr_base_f = "neuropathie"),
  cons("Peripheric_nervous_function", "Pathological_alteration") : LabelPart(en_base = "neuropathy", fr_base_f = "neuropathie"),
  cons("Peripheric_nervous_structure", "Peripheric_nervous_function") : LabelPart(en_comp = "of peripheric nervous system", fr_comp = "du système nerveux périphérique"),
  cons("Peripheric_nervous_structure") : LabelPart(en_comp = "of peripheric nerve", fr_comp = "des nerfs périphériques"),
  cons("Peripheric_nervous_function") : LabelPart(en_comp = "of peripheric nervous system", fr_comp = "du système nerveux périphérique"),
  cons("Peripheric_nervous_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "neuritis", fr_base_f = "névrite"),
  cons("Peripheric_nervous_structure", "Pain", "Pathological_alteration") : LabelPart(en_base = "neuralgia", fr_base_f = "neuralgie"),
  
  # Caractéristiques patient
  cons("Living_conditions", "Pathological_alteration") : LabelPart(en_base = "unsatisfactory living conditions", fr_base_f = "conditions de vie non satisfaisante"),
  cons("Living_conditions") : LabelPart(en_comp = "of living conditions", fr_comp = "des conditions de vie"),
  cons("Alimentation") : LabelPart(en_adj = "nutritional", fr_adj_f = "nutritionnelle", fr_adj_m = "nutritionnel"),
  cons("Alimentation", "Decrease_of_a_patient_characteristic", "Pathological_alteration") : LabelPart(en_base = "nutritional déficiency", fr_base_f = "carence nutritionnelle"),
  cons("Alimentation", "Increase_of_a_patient_characteristic", "Pathological_alteration") : LabelPart(en_base = "nutritional excess", fr_base_m = "excès nutritionnel"),
  cons("Alimentation", "Allergy", "Pathological_alteration") : LabelPart(en_base = "allergic reaction to food", fr_base_f = "réaction allergique alimentaire"),
  cons("Alimentation", "Inflammation", "Bacterial_infection", "Pathological_alteration") : LabelPart(en_base = "bacterial food poisoning", fr_base_f = "intoxication alimentaire due à une bactérie"),
  cons("Alimentation", "Inflammation", "Viral_infection", "Pathological_alteration") : LabelPart(en_base = "viral food poisoning", fr_base_f = "intoxication alimentaire due à un virus"),
  cons("Alimentation", "Inflammation", "Fungal_infection", "Pathological_alteration") : LabelPart(en_base = "fungal food poisoning", fr_base_f = "intoxication alimentaire due à un champignon"),
  cons("Alimentation", "Inflammation", "Parasitic_infection", "Pathological_alteration") : LabelPart(en_base = "parasitic food poisoning", fr_base_f = "intoxication alimentaire due à un parasite"),
  cons("Surroundings", "Pathological_alteration") : LabelPart(en_base = "Problem related to surroundings", fr_base_m = "Problème lié à l'entourage"),
  cons("Surroundings") : LabelPart(en_comp = "related to surroundings", fr_comp = "lié à l'entourage"),
  cons("Family", "Pathological_alteration") : LabelPart(en_base = "Family problem", fr_base_m = "Problème de famille"),
  cons("Family") : LabelPart(en_comp = "related to family", fr_comp = "lié à la famille"),
  cons("Height") : LabelPart(en_comp = "of stature", fr_comp = "de la stature"),
  cons("Height", "Decrease_of_a_patient_characteristic", "Pathological_alteration") : LabelPart(en_base = "short stature disorder", fr_base_f = "nanisme"),
  cons("Height", "Increase_of_a_patient_characteristic", "Pathological_alteration") : LabelPart(en_base = "gigantism", fr_base_f = "gigantisme"),
  cons("Weight") : LabelPart(en_comp = "of weight", fr_comp = "du poids"),
  cons("Weight", "Decrease_of_a_patient_characteristic", "Pathological_alteration") : LabelPart(en_base = "underweight", fr_base_f = "insuffisance pondérale"),
  cons("Weight", "Increase_of_a_patient_characteristic", "Pathological_alteration") : LabelPart(en_base = "obesity", fr_base_f = "obésité"),
  cons("Car_driving", "Machine_use") : LabelPart(en_comp = "of car driving and machine use", fr_comp = "de la conduite automobile et de l'utilisation de machine"),
  cons("Car_driving", "Machine_use", "Pathological_alteration") : LabelPart(en_base = "problem during car driving and machine use", fr_base_m = "problème lors de la conduite automobile et de l'utilisation de machine"),
  cons("Car_driving", "Machine_use", "Absence_of_pathological_alteration") : LabelPart(en_base = "driving and machine use", fr_base_m = "conduite automobile et de l'utilisation de machine"),
  cons("Travel") : LabelPart(en_comp = "of travel", fr_comp = "des voyages"),
  cons("Travel", "Pathological_alteration") : LabelPart(en_base = "problem related to travel", fr_base_m = "problème lié aux voyages"),
  cons("Travel", "Absence_of_pathological_alteration") : LabelPart(en_base = "travel", fr_base_m = "voyage"),
  cons("Tobacco_consumption") : LabelPart(en_comp = "related to tobacco", fr_comp = "lié au tabac"),
  cons("Tobacco_consumption", "Pathological_alteration") : LabelPart(en_base = "tobacco consumption", fr_base_m = "tabagisme"),
  cons("Alcohol_consumption") : LabelPart(en_comp = "related to alcohol", fr_comp = "liée à la consommation d'alcool"),
  cons("Alcohol_consumption", "Pathological_alteration") : LabelPart(en_base = "alcoholism", fr_base_m = "alcoolisme"),
  cons("Alcohol_consumption", "Absence_of_pathological_alteration") : LabelPart(en_base = "alcohol consumption", fr_base_m = "consommation d'alcool"),
  cons("Drug_consumption") : LabelPart(en_suffix = "related to drug consumption", fr_suffix = "liée à la consommation de drogue"),
  cons("Drug_consumption", "Pathological_alteration") : LabelPart(en_base = "drug consumption", fr_base_f = "consommation de drogue"),
  cons("Physical_activity") : LabelPart(en_suffix = "related to physical activity", fr_suffix = "liée à l'activité physique"),
  cons("Physical_activity", "Absence_of_pathological_alteration") : LabelPart(en_base = "physical activity", fr_base_f = "activité physique"),
  cons("Temperature_regulation_function") : LabelPart(en_comp = "of temperature", fr_comp = "de la température"),
  cons("Temperature_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "fever", fr_base_f = "fièvre"),
  cons("Temperature_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_suffix = "hypothermia", fr_suffix = "hypothermie"),
  
  # Régions du corps
  cons("Head_region") : LabelPart(en_comp = "of head", fr_comp = "de la tête"),
  
  cons("Abdomen_region") : LabelPart(en_adj = "abdominal", fr_adj_f = "abdominale", fr_adj_m = "abdominal"),
  
  cons("Thorax_region") : LabelPart(en_adj = "thoracic", fr_adj = "thoracique"),
  
  cons("Back_region") : LabelPart(en_comp = "of back", fr_comp = "du dos"),
  cons("Back_region", "Pain", "Pathological_alteration") : LabelPart(en_base = "backhache", fr_base_f = "mal de dos"),
  
  cons("Arm_region") : LabelPart(en_comp = "of arm", fr_comp = "du bras"),
  cons("Hand_region") : LabelPart(en_comp = "of hand", fr_comp = "de la main"),
  cons("Arm_region", "Hand_region") : LabelPart(en_comp = "of upper extremity", fr_comp = "des membres supérieurs"),
  
  cons("Leg_region") : LabelPart(en_comp = "of leg", fr_comp = "de la jambe"),
  cons("Foot_region") : LabelPart(en_comp = "of foot", fr_comp = "du pied"),
  cons("Leg_region", "Foot_region") : LabelPart(en_comp = "of lower extremity", fr_comp = "des membres inférieurs"),
  
  # Sytèmes anatomo-fonctionnels
  cons("Blood_structure") : LabelPart(en_comp = "of blood", fr_comp = "du sang"),
  
  cons("Coagulation_function", "Platelet") : LabelPart(en_comp = "of hemostatic system", fr_comp = "du système hémostatique"),
  cons("Coagulation_function") : LabelPart(en_comp = "of coagulation", fr_comp = "de la coagulation"),
  cons("Platelet") : LabelPart(en_comp = "of platelets", fr_comp = "des plaquettes"),
  cons("Coagulation_function", "Hypofunctionning", "Platelet", "Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "thombopenia and/or coagulation deficiency", fr_base_f = "thrombopénie et/ou déficit de la coagulation"),
  cons("Platelet", "Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "thombopenia and/or coagulation deficiency", fr_base_f = "thrombopénie et/ou déficit de la coagulation"),
  cons("Coagulation_function", "Hyperfunctionning", "Platelet", "Increase_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "thombocytosis and/or excess of coagulation", fr_base_f = "thrombocytose et/ou excès de la coagulation"),
  
  cons("Red_cell") : LabelPart(en_comp = "of red cells", fr_comp = "des globules rouges"),
  cons("Red_cell", "Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "anemia", fr_base_f = "anémie"),
  cons("Red_cell", "Increase_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "erythrocytosis", fr_base_f = "érythrocytose"),
  
  cons("Immune_function", "White_cell", "Immune_structure", "Thymus_gland_structure") : LabelPart(en_comp = "of immune system", fr_comp = "du système immunitaire"),
  cons("Immune_function") : LabelPart(en_comp = "of immunity", fr_comp = "de l'immunité"),
  cons("White_cell", "Immune_structure", "Thymus_gland_structure") : LabelPart(en_comp = "of immune structure", fr_comp = "de structures immunitaires"),
  cons("Immune_structure", "Thymus_gland_structure") : LabelPart(en_comp = "of immune structure", fr_comp = "de structures immunitaires"),
  cons("White_cell", "Immune_function") : LabelPart(en_comp = "of immune system", fr_comp = "du système immunitaire"),
  cons("White_cell") : LabelPart(en_comp = "of immune structure", fr_comp = "de structures immunitaires"),
  cons("Immune_function", "Hypofunctionning", "White_cell", "Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "immunodeficiency", fr_base_f = "immodéficience"),
  cons("White_cell", "Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "immunodeficiency", fr_base_f = "immodéficience"),
  cons("Immune_function", "Hyperfunctionning", "White_cell", "Increase_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "increased white cells number or excessive immunity", fr_base_f = "augmentation des globules blancs ou excès de l'immunité"),
  cons("White_cell", "Increase_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "increased white cells number or excessive immunity", fr_base_f = "augmentation des globules blancs ou excès de l'immunité"),
  
  cons("Blood_parameter_regulation_function", "Serum") : LabelPart(en_comp = "of blood serum", fr_comp = "du plasma"),
  cons("Blood_parameter_regulation_function") : LabelPart(en_comp = "of blood serum", fr_comp = "du plasma"),
  cons("Serum") : LabelPart(en_comp = "of blood serum", fr_comp = "du plasma"),
  cons("Blood_parameter_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "electrolyte imbalance", fr_base_m = "trouble hydroélectrolytique"),
  cons("Blood_parameter_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "electrolyte imbalance", fr_base_m = "trouble hydroélectrolytique"),

  cons("Active_principle_concentration_regulation_function") : LabelPart(en_comp = "of active principle concentration", fr_comp = "de la concentration en principe actif"),

  cons("Natremia_regulation_function") : LabelPart(en_comp = "of natremia", fr_comp = "de la natrémie"),
  cons("Phosphoremia_regulation_function") : LabelPart(en_comp = "of phosphoremia", fr_comp = "de la phosphorémie"),
  cons("Kaliemia_regulation_function") : LabelPart(en_comp = "of kaliemia", fr_comp = "de la kaliémie"),
  cons("Magnesemia_regulation_function") : LabelPart(en_comp = "of magnesemia", fr_comp = "de la magnésémie"),
  cons("Lithiemia_regulation_function") : LabelPart(en_comp = "of lithiemia", fr_comp = "de la lithiémie"),
  cons("Glycemia_regulation_function") : LabelPart(en_comp = "of glycemia", fr_comp = "de la glycémie"),
  cons("Lipidemia_regulation_function") : LabelPart(en_comp = "of lipidemia", fr_comp = "de la lipidémie"),
  
  cons("Natremia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hyponatremia", fr_base_f = "hyponatrémie"),
  cons("Phosphoremia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypophosphoremia", fr_base_f = "hypophosphorémie"),
  cons("Kaliemia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypokaliemia", fr_base_f = "hypokaliémie"),
  cons("Magnesemia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypomagnesemia", fr_base_f = "hypomagnésémie"),
  cons("Lithiemia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypolithiemia", fr_base_f = "hypolithiémie"),
  cons("Glycemia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypoglycemia", fr_base_f = "hypoglycémie"),
  cons("Lipidemia_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypolipidemia", fr_base_f = "hypolipidémie"),
  
  cons("Natremia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hypernatremia", fr_base_f = "hypernatrémie"),
  cons("Phosphoremia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperphosphoremia", fr_base_f = "hyperphosphorémie"),
  cons("Kaliemia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperkaliemia", fr_base_f = "hyperkaliémie"),
  cons("Magnesemia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hypermagnesemia", fr_base_f = "hypermagnésémie"),
  cons("Lithiemia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperlithiemia", fr_base_f = "hyperlithiémie"),
  cons("Glycemia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperglycemia", fr_base_f = "hyperglycémie"),
  cons("Lipidemia_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperlipidemia", fr_base_f = "hyperlipidémie"),
  
  cons("Bone_structure") : LabelPart(en_comp = "of bone", fr_adj_f = "osseuse", fr_adj_m = "osseux"),
  cons("Bone_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "osteitis", fr_base_f = "ostéite"),
  
  cons("Articular_function", "Articular_structure") : LabelPart(en_comp = "of articular system", fr_comp = "du système articulaires"),
  cons("Articular_function") : LabelPart(en_comp = "articular", fr_comp = "articulaire"),
  cons("Articular_structure") : LabelPart(en_comp = "of joints", fr_comp = "des articulations"),
  cons("Articular_function", "Articular_structure", "Pathological_alteration") : LabelPart(en_base = "arthropathy", fr_base_f = "arthropathie"),
  cons("Articular_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "arthritis", fr_base_f = "arthrite"),
  cons("Articular_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "arthrosis", fr_base_f = "arthrose"),
  
  cons("Hematopoietic_structure") : LabelPart(en_comp = "of hematopoietic structure", fr_comp = "de structures hématopoiétiques"),
  
  cons("Spinal_cord_structure") : LabelPart(en_comp = "of spinal cord", fr_comp = "de la moelle épinière"),
  cons("Spinal_cord_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "myelitis", fr_base_f = "myélite"),
  
  cons("Muscular_function", "Skeletal_muscular_structure") : LabelPart(en_comp = "of muscles", fr_comp = "des muscles"),
  cons("Muscular_function") : LabelPart(en_comp = "muscular", fr_comp = "musculaire"),
  cons("Skeletal_muscular_structure") : LabelPart(en_comp = "of muscles", fr_comp = "des muscles"),
  cons("Skeletal_muscular_structure", "Pain", "Pathological_alteration") : LabelPart(en_base = "myalgia", fr_base_f = "myalgie"),
  cons("Muscular_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "myasthenia", fr_base_f = "myasthénie"),
  
  cons("Blood_cell_destruction_function", "Splenic_structure") : LabelPart(en_comp = "of spleen", fr_comp = "de la rate"),
  cons("Blood_cell_destruction_function") : LabelPart(en_comp = "of spleen", fr_comp = "de la rate"),
  cons("Splenic_structure") : LabelPart(en_comp = "of spleen", fr_comp = "de la rate"),
  cons("Splenic_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "splenitis", fr_base_f = "splénite"),
  
  cons("Central_nervous_structure") : LabelPart(en_comp = "of the central nervous system", fr_comp = "du système nerveux central"),
  cons("Nervous_structure") : LabelPart(en_comp = "of the central nervous system", fr_comp = "du système nerveux central"),
  cons("Central_nervous_function") : LabelPart(en_adj = "cerebral", fr_adj_f = "cérébrale", fr_adj_m = "cérébral"),
  cons("Central_nervous_structure", "Pain", "Pathological_alteration") : LabelPart(en_base = "headhache", fr_base_f = "céphalée"),
  
  cons("Cerebral_function") : LabelPart(en_comp = "of cerebral function", fr_comp = "des fonctions cérébrales"),
  cons("Motor_function") : LabelPart(en_comp = "of motor functions", fr_comp = "des fonctions motrices"),
  cons("Motor_function", "Stop", "Pathological_alteration") : LabelPart(en_base = "paralysis", fr_base_f = "paralysie"),
  cons("Sensory_function") : LabelPart(en_comp = "of sensory functions", fr_comp = "des fonctions sensorielles"),
  cons("Central_sensory_function") : LabelPart(en_comp = "of central sensory functions", fr_comp = "des fonctions sensorielles centrales"),
  cons("Sleep_function") : LabelPart(en_comp = "of sleep", fr_comp = "du sommeil"),
  cons("Sleep_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "insomnia", fr_base_m = "insomnie"),
  cons("Sleep_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hypersomnia", fr_base_m = "hypersomnie"),
  
  cons("Behavioral_function") : LabelPart(en_adj = "behavioral", fr_comp = "du comportement"),
  
  cons("Mood_function") : LabelPart(en_adj = "mood", fr_comp = "de l'humeur"),
  cons("Mood_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "depression", fr_base_m = "dépression"),
  cons("Mood_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "maniac disorder", fr_base_m = "troubles maniaques"),
  
  cons("Alimentary_behavioral_function") : LabelPart(en_comp = "of alimentary behavior", fr_comp = "du comportement alimentaire"),
  cons("Alimentary_behavioral_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "loss of appetite", fr_base_f = "perte d'appétit"),
  cons("Alimentary_behavioral_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "excess of appetite", fr_base_m = "appétit excessif"),
  
  cons("Sexual_behavioral_function") : LabelPart(en_comp = "of sexual behavior", fr_comp = "du comportement sexuel"),
  cons("Sexual_behavioral_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "sexual inhibition", fr_base_f = "inhibition sexuelle"),
  cons("Sexual_behavioral_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "sexual deinhibition", fr_base_m = "désinhibition sexuelle"),
  
  cons("Language_function", "Communication_function") : LabelPart(en_comp = "of language and communication", fr_comp = "du langage et de la communication"),
  
  cons("Breast_structure") : LabelPart(en_comp = "of breast", fr_comp = "du sein"),
  cons("Lactation_function") : LabelPart(en_comp = "of lactation", fr_comp = "de la lactation"),
  
  cons("Cardiac_structure", "Cardiac_function") : LabelPart(en_comp = "of heart or pericardia", fr_comp = "du coeur ou du péricarde"),
  cons("Cardiac_structure") : LabelPart(en_comp = "of heart or pericardia", fr_comp = "du coeur ou du péricarde"),
  cons("Cardiac_function") : LabelPart(en_adj = "cardiac", fr_adj = "cardiaque"),
  cons("Cardiac_structure", "Vascular_structure") : LabelPart(en_comp = "of coronary vessels", fr_comp = "des coronaires"),
  cons("Cardiac_structure", "Vascular_structure", "Pathological_alteration") : LabelPart(en_base = "coronary disease", fr_base_f = "maladie coronaire"),
  
  cons("Cardiac_rhythm_regulation_function") : LabelPart(en_comp = "of cardiac rhythm", fr_comp = "du rythme cardiaque"),
  cons("Cardiac_rhythm_regulation_function", "Pathological_alteration") : LabelPart(en_base = "heart rhythm disorder", fr_base_m = "trouble du rythme"),
  cons("Cardiac_rhythm_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "bradycardia", fr_base_m = "bradycardie"),
  cons("Cardiac_rhythm_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "tachycardia", fr_base_m = "tachycardie"),
  
  cons("Delivery") : LabelPart(en_suffix = "during delivery", fr_suffix = "lors de l'accouchement"),
  
  cons("Odontologic_structure") : LabelPart(en_comp = "of tooth", fr_comp = "des dents"),
  
  cons("Dental_structure") : LabelPart(en_comp = "of tooth", fr_comp = "des dents"),
  cons("Dental_structure", "Bacterial_infection", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "dental carie", fr_base_f = "carie dentaire"),
  
  cons("Dental_pulp_structure") : LabelPart(en_comp = "of pulp of tooth", fr_comp = "de la pulpe dentaire"),
  cons("Dental_pulp_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "pulpitis", fr_base_f = "pulpite dentaire"),
  cons("Dental_pulp_structure", "Pain", "Pathological_alteration") : LabelPart(en_base = "pulpalgia", fr_base_f = "pulpalgie"),
  
  cons("Digestive_structure", "Digestive_function") : LabelPart(en_comp = "of digestive system", fr_comp = "du système digestif"),
  cons("Digestive_structure") : LabelPart(en_comp = "of digestive tract", fr_comp = "du tube digestif"),
  cons("Digestive_function") : LabelPart(en_adj = "digestive", fr_adj_f = "digestive", fr_adj_m = "digestif"),
  
  cons("Buccal_structure") : LabelPart(en_adj = "oral", fr_adj_f = "orale", fr_adj_m = "oral"),
  
  cons("Oesophageal_structure") : LabelPart(en_adj = "oesophageal", fr_comp = "de l'oesophage"),
  cons("Oesophageal_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "esophagitis", fr_base_f = "oesophagite"),
  
  cons("Stomacal_structure") : LabelPart(en_comp = "of stomach", fr_comp = "de l'estomac"),
  cons("Stomacal_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "gastritis", fr_base_f = "gastrite"),

  cons("Hepatic_degradation_function", "Hepatic_structure") : LabelPart(en_adj = "hepatic", fr_adj = "hépatique"),
  cons("Hepatic_structure") : LabelPart(en_comp = "of liver", fr_comp = "du foie"),
  cons("Hepatic_degradation_function") : LabelPart(en_adj = "hepatic", fr_adj = "hépatique"),
  cons("Hepatic_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "hepatitis", fr_base_f = "hépatite"),
  
  cons("Pancreatic_production_function", "Pancreatic_structure") : LabelPart(en_adj = "pancreatic", fr_adj = "pancréatique"),
  cons("Pancreatic_structure") : LabelPart(en_comp = "of pancreas", fr_comp = "du pancréas"),
  cons("Pancreatic_production_function") : LabelPart(en_adj = "pancreatic", fr_adj = "pancréatique"),
  cons("Pancreatic_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "pancreatitis", fr_base_f = "pancréatite"),
  
  cons("Prostatic_structure") : LabelPart(en_comp = "of prostate", fr_comp = "de la prostate"),
  cons("Prostatic_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "prostatitis", fr_base_f = "prostatite"),
  
  cons("Intestinal_transit_function", "Intestinal_structure") : LabelPart(en_comp = "of intestine", fr_comp = "de l'intestin"),
  cons("Intestinal_structure") : LabelPart(en_comp = "of intestine", fr_comp = "de l'intestin"),
  cons("Intestinal_transit_function") : LabelPart(en_adj = "of intestinal transit", fr_adj = "du transit intestinal"),
  cons("Intestinal_transit_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "constipation", fr_base_f = "constipation"),
  cons("Intestinal_transit_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "diarrhea", fr_base_f = "diarrhée"),
  
  cons("Large_intestine_transit_function", "Large_intestinal_structure") : LabelPart(en_comp = "of large intestine", fr_comp = "du côlon"),
  cons("Large_intestinal_structure") : LabelPart(en_comp = "of large intestine", fr_comp = "du côlon"),
  cons("Large_intestine_transit_function") : LabelPart(en_adj = "of transit of large intestine", fr_adj = "du transit du côlon"),
  
  cons("Auditory_function", "Auditive_structure") : LabelPart(en_comp = "of auditory system", fr_comp = "du système auditif"),
  cons("Auditive_structure") : LabelPart(en_comp = "of ear", fr_comp = "de l'oreille"),
  cons("Auditory_function") : LabelPart(en_adj = "auditory", fr_adj_f = "auditive", fr_adj_m = "auditif"),
  cons("Auditive_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base_f = "otitis", fr_base_f = "otite"),
  cons("Auditory_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hearing loss", fr_base_f = "perte d'audition"),
  cons("Auditory_function", "Stop", "Pathological_alteration") : LabelPart(en_base = "total deafness", fr_base_f = "surdité totale"),
  cons("Auditory_nervous_structure") : LabelPart(en_comp = "of auditory nerve", fr_comp = "du nerf auditif"),
  
  cons("Visual_function", "Visual_structure") : LabelPart(en_comp = "of visual system", fr_comp = "du système visuel"),
  cons("Visual_structure") : LabelPart(en_comp = "of eye", fr_comp = "de l'oeil"),
  cons("Visual_function") : LabelPart(en_adj = "visual", fr_adj_f = "visuelle", fr_adj_m = "visuel"),
  cons("Visual_nervous_structure") : LabelPart(en_comp = "of optical nerve", fr_comp = "du nerf optique"),
  cons("Visual_function", "Stop", "Pathological_alteration") : LabelPart(en_base = "blindness", fr_base_f = "cécité"),
  cons("Visual_structure", "Blood_pressure_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "ocular hypertension", fr_base_f = "hypertension oculaire"),
  
  cons("Fat_storage_function", "Adipose_structure") : LabelPart(en_comp = "of adipose tissue", fr_comp = "du tissus adipeux"),
  cons("Adipose_structure") : LabelPart(en_comp = "of adipose tissue", fr_comp = "du tissus adipeux"),
  cons("Fat_storage_function") : LabelPart(en_comp = "of fat regulation", fr_comp = "de la régulation des graisses"),
  cons("Adipose_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "panniculitis", fr_base_f = "panniculite"),
  
  cons("Integumentary_structure") : LabelPart(en_comp = "of skin", fr_comp = "de la peau"),
  cons("Integumentary_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "dermatitis", fr_base_f = "dermatite"),
  cons("Integumentary_structure", "Allergy", "Pathological_alteration") : LabelPart(en_base = "cutaneous allergy", fr_base_f = "allergie cutanée"),
  cons("Integumentary_structure", "Oedema", "Allergy", "Pathological_alteration") : LabelPart(en_base = "allergic urticaria", fr_base_f = "urticaire allergique"),
  
  cons("Mucous_structure") : LabelPart(en_comp = "of mucosa", fr_comp = "des muqueuses"),
  
  cons("Nail_structure") : LabelPart(en_comp = "of fingernail", fr_comp = "des ongles"),
  
  cons("Hair_structure") : LabelPart(en_comp = "of hair", fr_comp = "des poils et cheveux"),
  cons("Hair_structure", "Decrease_of_an_anatomical_structure", "Pathological_alteration") : LabelPart(en_base = "alopecia", fr_base_f = "alopécie"),
  
  cons("Gall_production_function", "Gallbladder_structure") : LabelPart(en_comp = "of biliary tract", fr_comp = "des voies biliaires"),
  cons("Gallbladder_structure") : LabelPart(en_comp = "of gallbladder", fr_comp = "de la vésicule"),
  cons("Gall_production_function") : LabelPart(en_adj = "biliary", fr_adj = "biliaire"),
  cons("Gallbladder_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "cholangitis", fr_base_f = "cholangite"),
  
  cons("Reproductive_function", "Genital_structure") : LabelPart(en_comp = "of reproductive system", fr_comp = "du système reproductif"),
  cons("Genital_structure") : LabelPart(en_comp = "of reproductive organs", fr_comp = "des organes reproductifs"),
  cons("Reproductive_function") : LabelPart(en_comp = "of reproduction", fr_comp = "de la reproduction"),
  
  cons("Male_reproductive_function", "Erectile_function", "Male_genital_structure") : LabelPart(en_comp = "of male reproductive system", fr_comp = "du système reproductif mâle"),
  cons("Male_genital_structure") : LabelPart(en_comp = "of male sexual organs", fr_comp = "des organes sexuels mâles"),
  cons("Erectile_function", "Male_reproductive_function") : LabelPart(en_comp = "of male reproduction", fr_comp = "de la reproduction mâle"),
  cons("Erectile_function") : LabelPart(en_comp = "of erectile function", fr_comp = "de la fonction érectile"),
  cons("Erectile_function", "Male_reproductive_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "impotence", fr_base_f = "impuissance"),
  
  cons("Female_reproductive_function", "Female_genital_structure") : LabelPart(en_comp = "of female genital tract", fr_comp = "du système reproductif femelle"),
  cons("Female_genital_structure") : LabelPart(en_comp = "of female reproductive organs", fr_comp = "des organes reproductifs femelles"),
  cons("Female_reproductive_function") : LabelPart(en_comp = "of female reproduction", fr_comp = "de la reproduction femelle"),
  
  cons("Uterine_structure") : LabelPart(en_comp = "of uterus", fr_comp = "de l'utérus"),
  cons("Placental_structure") : LabelPart(en_comp = "of placenta", fr_comp = "du placenta"),
  cons("Uterine_structure", "Placental_structure") : LabelPart(en_comp = "of uterus", fr_comp = "de l'utérus"),
  
  cons("Gengival_structure") : LabelPart(en_adj = "gingival", fr_comp = "des gencives"),
  cons("Gengival_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "gingivitis", fr_base_f = "gingivite"),
  
  cons("Hormonal_regulation_function", "Endocrine_structure") : LabelPart(en_comp = "of endocrine system", fr_comp = "du système endocrine"),
  cons("Hormonal_regulation_function") : LabelPart(en_comp = "of endocrine system", fr_comp = "du système endocrine"),
  cons("Endocrine_structure") : LabelPart(en_comp = "of endocrine structure", fr_comp = "de structures endocrines"),
  
  cons("Thyroid_regulation_function", "Thyroid_structure") : LabelPart(en_comp = "of thyroid", fr_comp = "de la thyroïde"),
  cons("Thyroid_regulation_function") : LabelPart(en_adj = "thyroidic", fr_comp = "thyroïdienne"),
  cons("Thyroid_structure") : LabelPart(en_comp = "of thyroid", fr_comp = "de la thyroïde"),
  cons("Thyroid_structure", "Enlargement", "Pathological_alteration") : LabelPart(en_base = "goiter", fr_base_m = "goître"),
  cons("Thyroid_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "thyroiditis", fr_base_f = "thyroïdite"),
  cons("Thyroid_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "hyperthyroidism", fr_base_f = "hyperthyroïdie"),
  cons("Thyroid_regulation_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "hypothyroidism", fr_base_f = "hypothyroïdie"),
  
  cons("Respiratory_function", "Respiratory_structure") : LabelPart(en_comp = "of respiratory system", fr_comp = "du système respiratoire"),
  cons("Respiratory_structure") : LabelPart(en_comp = "of respiratory tract", fr_comp = "des voies respiratoires"),
  cons("Respiratory_function") : LabelPart(en_adj = "respiratory", fr_adj = "respiratoire"),
  cons("Respiratory_function", "Respiratory_structure", "Allergy", "Pathological_alteration") : LabelPart(en_base = "respiratory system allergy", fr_base_f = "allergie respiratoire"),
  cons("Respiratory_structure", "Blood_pressure_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "pulmonary hypertension", fr_base_f = "hypertension pulmonaire"),
  
  cons("Upper_respiratory_tract_structure") : LabelPart(en_comp = "of upper respiratory tract", fr_comp = "des voies respiratoires suppérieures"),
  cons("Upper_respiratory_tract_structure", "Allergy", "Pathological_alteration") : LabelPart(en_base = "upper respiratory tract allergy", fr_base_f = "allergie respiratoire suppérieure"),
  
  cons("Lower_respiratory_tract_structure", "Bronchial_function") : LabelPart(en_comp = "of bronchus", fr_comp = "des bronches"),
  cons("Lower_respiratory_tract_structure") : LabelPart(en_comp = "of bronchus", fr_comp = "des bronches"),
  cons("Bronchial_function") : LabelPart(en_adj = "bronchial", fr_adj = "bronchique"),
  cons("Lower_respiratory_tract_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "bronchitis", fr_base_f = "bronchite"),
  
  cons("Renal_excretion_function", "Urinary_structure") : LabelPart(en_comp = "of urinary system", fr_comp = "du système urinaire"),
  cons("Urinary_structure") : LabelPart(en_comp = "of urinary tract", fr_comp = "des voies urinaires"),
  cons("Renal_excretion_function") : LabelPart(en_comp = "of urinary system", fr_comp = "du système urinaire"),
  cons("Renal_excretion_function", "Hypofunctionning", "Pathological_alteration") : LabelPart(en_base = "renal failure", fr_base = "insuffisance rénale"),
  cons("Renal_excretion_function", "Stop", "Pathological_alteration") : LabelPart(en_base = "end-stage renal failure", fr_base = "insuffisance rénale terminale"),
  cons("Urinary_structure", "Blood_pressure_regulation_function", "Hyperfunctionning", "Pathological_alteration") : LabelPart(en_base = "renal hypertension", fr_base_f = "hypertension rénale"),
  
  cons("Ionic_renal_excretion_function") : LabelPart(en_comp = "of renal excretion", fr_comp = "de l'excrétion rénale"),
  
  cons("Hematuria", "Pathological_alteration") : LabelPart(en_base = "hematuria", fr_base_f = "hématurie"),
  cons("Hematuria") : LabelPart(en_suffix = "with hematuria", fr_suffix = "avec hématurie"),
  
  cons("Leucocyturia", "Pathological_alteration") : LabelPart(en_base = "leucocyturia", fr_base_f = "leucocyturie"),
  cons("Leucocyturia") : LabelPart(en_suffix = "with leucocyturia", fr_suffix = "avec leucocyturie"),
  
  cons("Ureteric_structure") : LabelPart(en_comp = "of ureter", fr_comp = "de l'uretère"),
  cons("Ureteric_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "ureteritis", fr_base_f = "urétérite"),
  
  cons("Micturition_function", "Urinary_bladder_structure", "Uretral_structure") : LabelPart(en_comp = "of lower urinary tract", fr_comp = "des voies urinaires basses"),
  cons("Micturition_function", "Urinary_bladder_structure") : LabelPart(en_comp = "of urinary bladder", fr_comp = "de la vessie"),
  cons("Micturition_function", "Uretral_structure") : LabelPart(en_comp = "of urethra", fr_comp = "de l'urètre"),
  cons("Micturition_function") : LabelPart(en_comp = "of micturition", fr_comp = "de la miction"),
  cons("Urinary_bladder_structure", "Uretral_structure") : LabelPart(en_comp = "of lower urinary tract", fr_comp = "des voies urinaires basses"),
  cons("Urinary_bladder_structure") : LabelPart(en_comp = "of urinary bladder", fr_comp = "de la vessie"),
  cons("Uretral_structure") : LabelPart(en_comp = "of urethra", fr_comp = "de l'urètre"),
  cons("Urinary_bladder_structure", "Uretral_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "cystitis", fr_base_f = "cystite"),
  cons("Urinary_bladder_structure", "Inflammation", "Pathological_alteration") : LabelPart(en_base = "cystitis", fr_base_f = "cystite"),
  
  # Pathos spécifiques
  cons("Acnea", "Pathological_alteration") : LabelPart(en_base = "acnea", fr_base_f = "acnée"),
  #cons("Acnea") : LabelPart(en_base = "acnea", fr_base_f = "acnée"),
  cons("Asthenia", "Pathological_alteration") : LabelPart(en_base = "fatigue", fr_base_f = "asthénie"),
  cons("Bone_destructuration", "Pathological_alteration") : LabelPart(en_base = "osteoporosis", fr_base_f = "ostéoporose"),
  #cons("Bone_destructuration") : LabelPart(en_base = "osteoporotic", fr_base_f = "ostéoporotique"),
  cons("Bone_remodeling", "Pathological_alteration") : LabelPart(en_base = "osteitis deformans", fr_base_f = "ostéite déformante"),
  cons("Cerebral_degeneration", "Pathological_alteration") : LabelPart(en_base = "cerebral degeneration", fr_base_f = "dégénération cérébrale"),
  cons("Cough", "Pathological_alteration") : LabelPart(en_base = "cough", fr_base_f = "toux"),
  cons("Parkinsonian_syndrome", "Pathological_alteration") : LabelPart(en_base = "extrapyramidal disease", fr_base_f = "syndrome Parkinsonien"),
  cons("Anxiety", "Pathological_alteration") : LabelPart(en_base = "anxiety", fr_base_f = "anxiété"),
  cons("Fracture", "Pathological_alteration") : LabelPart(en_base = "bone fracture", fr_base_f = "fracture osseuse"),
  cons("Gastroesophageal_reflux", "Pathological_alteration") : LabelPart(en_base = "Gastroesophageal reflux disease", fr_base_f = "Reflux gastro-oesophagien"),
  cons("Photosensibilization", "Pathological_alteration") : LabelPart(en_base = "photosensibilization", fr_base_f = "photo-sensibilisation"),
  cons("Photosensibilization", "Allergy") : LabelPart(en_base = "photoallergic dermatitis", fr_base_f = "dermatite photoallergique"),
  cons("Photosensibilization") : LabelPart(en_suffix = "with photosensibilization", fr_suffix = "avec photo-sensibilisation"),
  cons("Diabetes", "Pathological_alteration") : LabelPart(en_base = "diabetes", fr_base_m = "diabète"),
  cons("Glaucoma", "Pathological_alteration") : LabelPart(en_base = "glaucoma", fr_base_m = "glaucome"),
  cons("Psoriasis", "Pathological_alteration") : LabelPart(en_base = "psoriasis", fr_base_m = "psoriasis"),
  cons("Vertigo", "Pathological_alteration") : LabelPart(en_base = "vertigo", fr_base_m = "vertiges"),
  cons("Vomitting", "Pathological_alteration") : LabelPart(en_base = "vomitting", fr_base_m = "vomissement"),
  cons("Menopause", "Absence_of_pathological_alteration") : LabelPart(en_base = "menopause", fr_base_f = "ménopause"),
  cons("Menopause", "Pathological_alteration") : LabelPart(en_base = "menopause-related disorder", fr_base_f = "maladie liée à la ménopause"),
  cons("Overdosage") : LabelPart(en_suffix = "with overdosage", fr_suffix = "avec overdose"),
  cons("Overdosage", "Pathological_alteration") : LabelPart(en_base = "overdosage", fr_base_f = "overdose"),
  
  cons("Pregnancy") : LabelPart(en_suffix = "related to pregnancy", fr_suffix = "lié à la grossesse"),
  cons("Pregnancy", "Absence_of_pathological_alteration") : LabelPart(en_base = "pregnancy", fr_base = "grossesse"),
  cons("Pregnancy", "Pathological_alteration") : LabelPart(en_base = "disorder of pregnancy", fr_base = "grossesse pathologique"),
  cons("Pregnancy", "Stop", "Pathological_alteration") : LabelPart(en_base = "spontaneous abortion", fr_base_m = "avortement spontané"),
  cons("Pregnancy", "Drug_therapy", "Absence_of_pathological_alteration", "Future") : LabelPart(en_base = "contraceptive drug", fr_base_m = "médicament contraceptif"),
  cons("Pregnancy", "Ectomy", "Absence_of_pathological_alteration") : LabelPart(en_base = "elective abortion", fr_base_m = "interruption volontaire de grossesse"),
  cons("Pregnancy", "Ectomy", "Pathological_alteration") : LabelPart(en_base = "elective abortion", fr_base_m = "interruption volontaire de grossesse"),
  
  cons("Age_class") : LabelPart(en_base = "age class", fr_base_m = "classe d'âge"),
}
#print(len(data), "labels prédéfinis.")

splits = ([
  # These are useless since they dupplicate other concepts (e.g. Female_genital_structure)
  cons("Sex"),
  cons("Male"),
  cons("Female"),
  cons("Embryonic_structure"),
  cons("Foetal_structure"),
  cons("Modification_of_a_property_of_a_drug_treatment"),
#  cons("Absence_dinformation"),
  frozenset([VCM_CONCEPT[17]]),
  
  cons("Property_of_a_drug_treatment", "Pathological_alteration"),
  cons("Property_of_a_drug_treatment"),
  cons("Low_dose"),
  cons("Withdrawal"),
  cons("High_dose"),
  cons("Current_dose", "Decrease_of_a_property_of_a_drug_treatment"),
  cons("Current_dose", "Increase_of_a_property_of_a_drug_treatment"),
  cons("Current_dose"),
  cons("Treatment_discontinuation"),
  cons("Dose_schedule"),
  
  cons("Current"),
  
  cons("Acnea", "Pathological_alteration"),
  cons("Asthenia", "Pathological_alteration"),
  cons("Bone_destructuration", "Pathological_alteration"),
  cons("Bone_remodeling", "Pathological_alteration"),
  cons("Cerebral_degeneration", "Pathological_alteration"),
  cons("Cough", "Pathological_alteration"),
  cons("Parkinsonian_syndrome", "Pathological_alteration"),
  cons("Anxiety", "Pathological_alteration"),
  cons("Fracture", "Pathological_alteration"),
  cons("Gastroesophageal_reflux", "Pathological_alteration"),
  cons("Photosensibilization", "Pathological_alteration"),
  cons("Photosensibilization", "Allergy"),
  cons("Photosensibilization"),
  cons("Diabetes", "Pathological_alteration"),
  cons("Glaucoma", "Pathological_alteration"),
  cons("Psoriasis", "Pathological_alteration"),
  cons("Vertigo", "Pathological_alteration"),
  cons("Vomitting", "Pathological_alteration"),
  cons("Menopause", "Pathological_alteration"),
  cons("Overdosage"),
  cons("Overdosage", "Pathological_alteration"),
  
  cons("Tumor", "Pathological_alteration"),
  cons("Tumor"),
  cons("Cyst", "Benign_tumor", "Pathological_alteration"),
  cons("Cyst", "Benign_tumor"),
  cons("Benign_tumor", "Pathological_alteration"),
  cons("Benign_tumor"),
  
  cons("Peripheric_nervous_structure", "Peripheric_nervous_function", "Pathological_alteration"),
  cons("Peripheric_nervous_structure", "Pain", "Pathological_alteration"),
  cons("Peripheric_nervous_structure", "Pathological_alteration"),
  cons("Peripheric_nervous_function", "Pathological_alteration"),
  
  cons("Allergy"),
  
  # These ones must be defined BEFORE the other ones!
  cons("Vascular_structure", "Inflammation", "Obstruction", "Pathological_alteration"),
  cons("Vascular_structure", "Inflammation", "Pathological_alteration"),
  cons("Peripheric_nervous_structure", "Inflammation", "Pathological_alteration"),
  ] 
  + [key for key in sorted(data.keys(), key = lambda k: -len(k)) if (len(key) > 1) and ((VCM_CONCEPT[192] in key) or (VCM_CONCEPT[78] in key)) and (Concepts(key).find(VCM_CONCEPT[251]))] # Inflammation, Pain, Anatomical_structure
  + [key for key in sorted(data.keys(), key = lambda k: -len(k)) if (len(key) > 1) and ((VCM_CONCEPT[72] in key) or (VCM_CONCEPT[33] in key)) and (Concepts(key).find(VCM_CONCEPT[251]))] # Decrease_of_an_anatomical_structure, Increase_of_an_anatomical_structure, Anatomical_structure
          + [key for key in sorted(data.keys(), key = lambda k: -len(k)) if (len(key) > 1) and ((VCM_CONCEPT[70] in key) or (VCM_CONCEPT[31] in key)) and (Concepts(key).find(VCM_CONCEPT[38]))] # Decrease_of_a_patient_characteristic, Increase_of_a_patient_characteristic, Patient_characteristic
  + [key for key in sorted(data.keys(), key = lambda k: -len(k)) if (len(key) > 1) and ((VCM_CONCEPT[180] in key) or (VCM_CONCEPT[177] in key) or (VCM_CONCEPT[29] in key)) and (Concepts(key).find(VCM_CONCEPT[94]))] # Hypofunctionning, Hyperfunctionning, Stop, Biologic_function
  + [
  cons("Auditive_structure", "Inflammation", "Pathological_alteration"),
  
  cons("Alimentation", "Inflammation", "Bacterial_infection", "Pathological_alteration"),
  cons("Alimentation", "Inflammation", "Viral_infection", "Pathological_alteration"),
  cons("Alimentation", "Inflammation", "Fungal_infection", "Pathological_alteration"),
  cons("Alimentation", "Inflammation", "Parasitic_infection", "Pathological_alteration"),
    
  cons("Infection", "Pathological_alteration", "Inflammation"),
  cons("Bacterial_infection", "Pathological_alteration", "Inflammation"),
  cons("Viral_infection", "Pathological_alteration", "Inflammation"),
  cons("Fungal_infection", "Pathological_alteration", "Inflammation"),
  cons("Parasitic_infection", "Pathological_alteration", "Inflammation"),
  cons("Infection", "Inflammation"),
  cons("Bacterial_infection", "Inflammation"),
  cons("Viral_infection", "Inflammation"),
  cons("Fungal_infection", "Inflammation"),
  cons("Parasitic_infection", "Inflammation"),
  
  cons("Inflammation", "Pathological_alteration"),
  cons("Inflammation"),
  
  cons("Autoimmune"),
  cons("Stop", "Pathological_alteration"),
  cons("Hyperfunctionning", "Pathological_alteration"),
  cons("Hyperfunctionning"),
  cons("Hypofunctionning", "Pathological_alteration"),
  cons("Hypofunctionning"),
  cons("Increase_of_an_anatomical_structure", "Pathological_alteration"),
  cons("Increase_of_an_anatomical_structure"),
  cons("Decrease_of_an_anatomical_structure", "Pathological_alteration"),
  cons("Decrease_of_an_anatomical_structure"),
  
  cons("Oedema", "Pathological_alteration", "Liquid_penetration"),
  cons("Oedema", "Liquid_penetration"),
  cons("Oedema", "Pathological_alteration"),
  cons("Oedema"),
  
  cons("Enlargement", "Pathological_alteration"),
  cons("Enlargement"),
  cons("Lesion", "Pathological_alteration"),
  cons("Lesion"),
  
  cons("Infection", "Pathological_alteration"),
  cons("Infection"),
  cons("Bacterial_infection", "Pathological_alteration"),
  cons("Bacterial_infection"),
  cons("Viral_infection", "Pathological_alteration"),
  cons("Viral_infection"),
  cons("Fungal_infection", "Pathological_alteration"),
  cons("Fungal_infection"),
  cons("Parasitic_infection", "Pathological_alteration"),
  cons("Parasitic_infection"),

  cons("Dependency", "Pathological_alteration"),

  cons("Hemorrhage", "Pathological_alteration"),
  cons("Hemorrhage"),
  
  cons("Genetic"),
  cons("Metabolic_function", "Metabolic_etiology"),
  cons("Metabolic_function"),
  cons("Metabolic_etiology"),
  
  cons("Pain", "Pathological_alteration"),
  cons("Pain"),
  
  cons("Caused_by_a_substance", "Pathological_alteration"),
  cons("Caused_by_a_substance"),
  cons("Caused_by_drug_treatment"),
  cons("Caused_by_graft", "Pathological_alteration"),
  cons("Caused_by_graft"),
  cons("Caused_by_radiation", "Pathological_alteration"),
  cons("Caused_by_radiation"),
  cons("Caused_by_treatment"),
  
  cons("Blood_pressure_regulation_function", "Pathological_alteration"),
  cons("Blood_pressure_regulation_function", "Absence_of_pathological_alteration"),
  cons("Blood_pressure_regulation_function"),
  
  cons("Obstruction", "Pathological_alteration"),
  cons("Obstruction"),
  
  cons("Malformation", "Pathological_alteration"),
  cons("Malformation"),
    
  cons("Health_professional"),
  cons("Medical_document"),


  cons("Therapy"),
  cons("Drug_therapy"),
  cons("Topical_drug_therapy"),
  cons("Injectable_systemic_drug_therapy"),
  cons("Oral_systemic_drug_therapy"),
  cons("Procedure"),
  cons("Radiotherapy"),
  cons("Surgical_procedure"),
  cons("Implant", "Pathological_alteration"),
  cons("Implant"),
  cons("Graft", "Pathological_alteration"),
  cons("Graft"),
  cons("Ectomy", "Pathological_alteration"),
  cons("Ectomy"),
  cons("Retraining_therapy"),
  cons("Lifestyle_and_dietary_therapy"),
  
  cons("Clinical_test", "Pathological_alteration", "Future"),
  cons("Clinical_test", "Future"),
  cons("Biological_test", "Pathological_alteration", "Future"),
  cons("Biological_test", "Future"),
  cons("Imaging_test", "Pathological_alteration", "Future"),
  cons("Imaging_test", "Future"),
  cons("Functional_test", "Pathological_alteration", "Future"),
  cons("Functional_test", "Future"),
  cons("Anormal_biological_examination", "Pathological_alteration", "Future"),
  cons("Anormal_biological_examination", "Future"),
  cons("Biopsy", "Pathological_alteration", "Future"),
  cons("Biopsy", "Future"),
  cons("Diagnostic", "Future"),
  
  cons("Past"),
  cons("Future"),
  
  cons("Pathological_alteration"),
  cons("Absence_of_pathological_alteration"),
  
  cons("Vascular_structure"),
  cons("Peripheric_nervous_structure"),
  cons("Peripheric_nervous_function"),
])

def concepts_2_parts(concepts, orig = None):
  #print("  ", ", ".join(c.term for c in concepts))
  if not orig: orig = concepts
  if concepts in data: return [data[concepts]]
    
  for split in splits:
    if split.issubset(concepts):
      #print("  ", ", ".join(c.term for c in split))
      new_concepts = concepts.difference(split)
      if split == cons("Allergy"):
        new_concepts = Concepts(new_concepts)
        if new_concepts.find(VCM_CONCEPT[251]): # Anatomical_structure
          new_concepts.subtract_update(VCM_CONCEPT[94]) # Biologic_function
        new_concepts.update(cons("Inflammation"))
        new_concepts = frozenset(new_concepts)
        
      parts = concepts_2_parts(new_concepts, orig)
      split_part = data.get(split)
      if (split == cons("Inflammation")) and (cons("Allergy").issubset(orig)):
        return parts # Do not say "allergic inflammatory disorder"
      if split_part and parts: return [split_part] + parts
      return parts
    
  #raise ValueError(concepts)
  print("* PyMedTermino * Warning: no label for VCM concept set %s." % list(concepts))

def concepts_2_label(concepts):
  try:
    if not concepts: return Label(fr = "(pas de libellé)", en = "(no label)")
    if concepts.find(VCM_CONCEPT[182]):  # Violent_hypofunctionning
      concepts.remove(VCM_CONCEPT[182])  # Violent_hypofunctionning
      concepts.add(VCM_CONCEPT[180])  # Hypofunctionning
    if concepts.find(VCM_CONCEPT[179]):  # Violent_hyperfunctionning
      concepts.remove(VCM_CONCEPT[179])  # Violent_hyperfunctionning
      concepts.add(VCM_CONCEPT[177])  # Hyperfunctionning
    if concepts.find(VCM_CONCEPT[187]):  # Infection
      concepts.add(VCM_CONCEPT[192])  # Inflammation
    #print("  ", ", ".join(c.term for c in concepts))
    parts = concepts_2_parts(frozenset(concepts))
    if parts is None: return Label(en = "xxx", fr = "xxx")
    return combine(parts, concepts)
  except:
    sys.excepthook(*sys.exc_info())
    return Label(en = "xxx", fr = "xxx")
  
def icon_2_label(icon): return concepts_2_label(icon.concepts)


if __name__ == "__main__":
  print()
  print(icon_2_label(VCM["current--inflammation--oreille"]))
  print(icon_2_label(VCM["current--allergy--oreille"]))
  print(icon_2_label(VCM["current--infection--oreille"]))
  print(icon_2_label(VCM["current--bacterie--oreille"]))
  print()
  print(icon_2_label(VCM["current--inflammation--gorge_nez"]))
  print(icon_2_label(VCM["current--allergy--gorge_nez"]))
  print(icon_2_label(VCM["current--infection--gorge_nez"]))
  print(icon_2_label(VCM["current--bacterie--gorge_nez"]))
  print()
  print(icon_2_label(VCM["current--inflammation--foie"]))
  print(icon_2_label(VCM["current--allergy--foie"]))
  print(icon_2_label(VCM["current--infection--foie"]))
  print(icon_2_label(VCM["current--virus--foie"]))
  print(icon_2_label(VCM["current--tumeur--foie"]))
  print(icon_2_label(VCM["current--tumeurb--foie"]))
  print()
  print(icon_2_label(VCM["current--allergie--peau"]))
  print()
  print(icon_2_label(VCM["current--douleur"]))
  print(icon_2_label(VCM["current--douleur--peau"]))
  print(icon_2_label(VCM["current--douleur--abdomen"]))
  print(icon_2_label(VCM["current--douleur--cerveau"]))
  print(icon_2_label(VCM["current--douleur--dos"]))
  print(icon_2_label(VCM["current--douleur--os"]))
  print(icon_2_label(VCM["current--douleur--dental_pulp"]))
  print(icon_2_label(VCM["current--douleur--tube_digestif"]))
  print(icon_2_label(VCM["current--douleur--genital"]))
  print(icon_2_label(VCM["current--douleur--ivory"]))
  print(icon_2_label(VCM["current--douleur--large_intestine"]))
  print(icon_2_label(VCM["current--douleur--small_intestine"]))
  print()

  print(icon_2_label(VCM["current--malformation-nerve--eye"]))
  print(icon_2_label(VCM["current--malformation-vaisseau--eye"]))
  print(icon_2_label(VCM["current--patho-vaisseau--coeur"]))
  print(icon_2_label(VCM["current--malformation-vaisseau--coeur"]))
  print(icon_2_label(VCM["current--arret--cerveau_eeg"]))
  print(icon_2_label(VCM["current--arret--coeur"]))
  print(icon_2_label(VCM["current--arret--grossesse"]))
  print(icon_2_label(VCM["current--arret--oreille"]))
  print(icon_2_label(VCM["current--arret--oeil"]))
  print(icon_2_label(VCM["current--arret--rein"]))
  print(icon_2_label(VCM["current--arret--poumon"]))
  print()

  print(icon_2_label(VCM["current--haemorrhage-patho--petit_intestin"]))
  print()

  print(icon_2_label(VCM["current--malformation--obstructed_bronchial"]))
  print(icon_2_label(VCM["current--nerve-tumor--tete"]))
  print(icon_2_label(VCM["current--parasite--alimentation"]))
  print(icon_2_label(VCM["current--patho--poumon--traitement--comprime"]))
  print(icon_2_label(VCM["current--patho--poumon--traitement--ectomie"]))
  print(icon_2_label(VCM["current--patho-inflammation--rate--traitement--ectomie"]))

  print(icon_2_label(VCM["risque--patho--poumon--surveillance--diagnostic"]))
  print(icon_2_label(VCM["risque--hypo--coeur--surveillance--diagnostic"]))
  print(icon_2_label(VCM["risque--hyper-vaisseau_pa--rien--surveillance--diagnostic--prof"]))
  print(icon_2_label(VCM["en_cours--patho--coeur--rien--rien--prof"]))
  print(icon_2_label(VCM["en_cours--bacterie--rien--rien--rien--prof"]))
  print(icon_2_label(VCM["en_cours--patho--rien--traitement--medicament--prof"]))
  print(icon_2_label(VCM["en_cours--hypo--thyroide"]))
  print(icon_2_label(VCM["en_cours--lesion--estomac"]))
  print(icon_2_label(VCM["current--nerve--rien"]))
  print(icon_2_label(VCM["en_cours--patho--glande_diabete"]))
  print()
  print(icon_2_label(VCM["en_cours--physio--grossesse"]))
  print(icon_2_label(VCM["risque--physio--grossesse"]))
  print(icon_2_label(VCM["risque--physio--grossesse--traitement--medicament"]))
  print(icon_2_label(VCM["antecedent--physio--grossesse"]))
  print(icon_2_label(VCM["en_cours--patho--grossesse"]))
  print(icon_2_label(VCM["en_cours--physio--grossesse--traitement--ectomie"]))
  print(icon_2_label(VCM["en_cours--patho--grossesse--traitement--ectomie"]))
  print()

  print(icon_2_label(VCM["en_cours--due_to_radiation-hypo--alimentation"]))
  
  print(cons("Decrease_of_a_patient_characteristic", "Alimentation", "Pathological_alteration") in splits)
  # XXX tumeur + malformation congénitale ?
