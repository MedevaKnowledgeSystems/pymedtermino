#! /usr/bin/env python
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


# Get SNOMED CT from (RF2 release):
# http://www.nlm.nih.gov/research/umls/licensedcontent/snomedctfiles.html

# Example: SNOMEDCT_DIR = "/home/jiba/telechargements/base_med/SnomedCT_RF2Release_INT_20150131"
# Example ( ** OLD ** 2014 release): SNOMEDCT_DIR = "/home/jiba/telechargements/base_med/SnomedCT_Release_INT_20140731/RF2Release"
SNOMEDCT_DIR = ""

# Get SNOMED CT CORE Problem list from:
# http://www.nlm.nih.gov/research/umls/Snomed/core_subset.html

# Example: SNOMEDCT_CORE_FILE = "/home/jiba/telechargements/base_med/SNOMEDCT_CORE_SUBSET_201502.txt"
SNOMEDCT_CORE_FILE = ""

# Get ICD10 from (NB choose "ClaML" format):
# http://apps.who.int/classifications/apps/icd/ClassificationDownload/DLArea/Download.aspx

# Example: ICD10_DIR = "/home/jiba/telechargements/base_med/icd10"
ICD10_DIR = ""

# Get ICD10 French translation from ATIH:
# http://www.atih.sante.fr/plateformes-de-transmission-et-logiciels/logiciels-espace-de-telechargement/id_lot/456

# Example: CIM10_DIR = "/home/jiba/telechargements/base_med/cim10"
CIM10_DIR = ""

# Get MedDRA from (available in several languages):
# https://www.meddra.org/software-packages

# Example:
# MEDDRA_DIRS = {
#  "en" : "/home/jiba/telechargements/base_med/meddra/en/MedAscii",
#  "fr" : "/home/jiba/telechargements/base_med/meddra/fr/ascii-171",
# }
MEDDRA_DIRS = {
  # "lang" : "path",
}

# Set to False if you don't want to build VCM terminologies.
#
# VCM is pre-built in release source distribution, so it has no impact it in this case.
#
# However, VCM is *not* pre-built in Mercurial sources. You may want to disable it if you build
# from Mercurial repository and you don't need VCM.

BUILD_VCM = False

# NB The build_vcm_consistency script requires about one day to run, has plenty of dependency,
# and is Linux-only. Therefore, it is *not* run when building PyMedTermino!
# Instead, the VCM icon consistency database is pre-built and compressed in the source release.


import os, os.path, sys, glob

HERE = os.path.dirname(sys.argv[0]) or "."

i = 0
while i < len(sys.argv):
  if   sys.argv[i] == "--snomedct":          del sys.argv[i]; SNOMEDCT_DIR       = sys.argv[i]; del sys.argv[i]
  elif sys.argv[i] == "--snomedct-core":     del sys.argv[i]; SNOMEDCT_CORE_FILE = sys.argv[i]; del sys.argv[i]
  elif sys.argv[i] == "--icd10":             del sys.argv[i]; ICD10_DIR          = sys.argv[i]; del sys.argv[i]
  elif sys.argv[i] == "--icd10-translation": del sys.argv[i]; CIM10_DIR          = sys.argv[i]; del sys.argv[i]
  elif sys.argv[i] == "--meddra":
    del sys.argv[i]
    lang, path = sys.argv[i].split("_", 1)
    MEDDRA_DIRS[lang] = path
    del sys.argv[i]
  else: i += 1


if len(sys.argv) <= 1: sys.argv.append("install")

if ("build" in sys.argv) or ("install" in sys.argv):
  def do(s):
    print(s)
    r = os.system(s)
    return r
  def failed(filename):
    if os.path.exists(filename): os.unlink(filename)
    sys.exit()
      
  if SNOMEDCT_DIR and (not os.path.exists(os.path.join(HERE, "snomedct.sqlite3"))):
    cmd = sys.executable + ' %s%sscripts%simport_snomedct.py "%s" "%s"' % (HERE, os.sep, os.sep, SNOMEDCT_DIR, SNOMEDCT_CORE_FILE)
    if do(cmd) != 0: failed(os.path.join(HERE, "snomedct.sqlite3"))
    
  if ICD10_DIR and (not os.path.exists(os.path.join(HERE, "icd10.sqlite3"))):
    cmd = sys.executable + ' %s%sscripts%simport_icd10.py "%s" "%s"' % (HERE, os.sep, os.sep, ICD10_DIR, CIM10_DIR)
    if do(cmd) != 0: failed(os.path.join(HERE, "icd10.sqlite3"))
    
  if MEDDRA_DIRS and (not os.path.exists(os.path.join(HERE, "meddra.sqlite3"))):
    cmd = sys.executable + ' %s%sscripts%simport_meddra.py %s' % (HERE, os.sep, os.sep, " ".join('"%s_%s"' % (lang, MEDDRA_DIRS[lang]) for lang in MEDDRA_DIRS))
    if do(cmd) != 0: failed(os.path.join(HERE, "meddra.sqlite3"))
    
  if BUILD_VCM and (not os.path.exists(os.path.join(HERE, "vcm_concept.sqlite3"))):
    """
    python ./pymedtermino/scripts/import_vcm_concept.py 
    python ./pymedtermino/scripts/import_vcm_lexicon.py 
    python ./pymedtermino/scripts/build_vcm_concept_monoaxial.py 
    python ./pymedtermino/scripts/import_vcm_concept_monoaxial.py 
    python ./pymedtermino/scripts/import_vcm_mappings.py 
    python ./pymedtermino/scripts/build_vcm_search_concept.py 
    python ./pymedtermino/scripts/build_vcm_repr.py 

    python ./pymedtermino/scripts/build_vcm_consistency.py --pairs
    python ./pymedtermino/scripts/build_vcm_consistency.py --picto-mods
    python ./pymedtermino/scripts/build_vcm_consistency.py --icons
    python ./pymedtermino/scripts/build_vcm_consistency.py --sens
    python ./pymedtermino/scripts/build_vcm_consistency.py --picto-mods
    """
    
    cmd = sys.executable + ' %s%sscripts%simport_vcm_concept.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    cmd = sys.executable + ' %s%sscripts%simport_vcm_lexicon.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    cmd = sys.executable + ' %s%sscripts%sbuild_vcm_concept_monoaxial.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    cmd = sys.executable + ' %s%sscripts%simport_vcm_concept_monoaxial.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    cmd = sys.executable + ' %s%sscripts%simport_vcm_mappings.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    cmd = sys.executable + ' %s%sscripts%sbuild_vcm_search_concept.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    cmd = sys.executable + ' %s%sscripts%sbuild_vcm_repr.py' % (HERE, os.sep, os.sep)
    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_concept.sqlite3"))
    
#  if BUILD_VCM_CONCISTENCY and (not os.path.exists(os.path.join(HERE, "vcm_consistency.sqlite3"))):
#    cmd = sys.executable + ' %s%sscripts%sbuild_vcm_consistency.py' % (HERE, os.sep, os.sep)
#    if do(cmd) != 0: failed(os.path.join(HERE, "vcm_consistency.sqlite3"))

  if not os.path.exists(os.path.join(HERE, "vcm_consistency.sqlite3")):
    print("Uncompressing VCM consistency database...")
    import bz2, shutil
    comp = bz2.open(os.path.join(HERE, "vcm_consistency.sqlite3.bz2"))
    shutil.copyfileobj(comp, open(os.path.join(HERE, "vcm_consistency.sqlite3"), "wb"))

import distutils.core, distutils.sysconfig
if ("upload_docs" in sys.argv) or ("build_sphinx" in sys.argv): import setuptools


distutils.core.setup(
  name         = "PyMedTermino",
  version      = "0.3.3",
  license      = "LGPLv3+",
  description  = "Medical Terminologies for Python: SNOMED CT, ICD10, MedDRA, CDF, UMLS and VCM icons",
  long_description = open(os.path.join(HERE, "README.rst")).read(),
  
  zip_safe = False,

  author       = "Lamy Jean-Baptiste (Jiba)",
  author_email = "<jean-baptiste.lamy *@* univ-paris13 *.* fr>",
  url          = "http://www.lesfleursdunormal.fr/static/informatique/pymedtermino/index_en.html",
  classifiers  = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Healthcare Industry",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Topic :: Scientific/Engineering :: Medical Science Apps.",
    "Topic :: Software Development :: Libraries :: Python Modules",
    ],
  
  package_dir  = {"pymedtermino" : "."},
  packages     = ["pymedtermino", "pymedtermino.utils"],
  #package_data = {"pymedtermino" : ["%s" % file for file in os.listdir(HERE) if file.endswith(".sqlite3")]}
  package_data = {"pymedtermino" : ["*.sqlite3"]}
  )


if "clean" in sys.argv:
  try: os.unlink(os.path.join(HERE, "snomedct.sqlite3"))
  except: pass
  try: os.unlink(os.path.join(HERE, "icd10.sqlite3"))
  except: pass
  try: os.unlink(os.path.join(HERE, "meddra.sqlite3"))
  except: pass

