
import sys, os, os.path
from collections import defaultdict

import pymedtermino
from pymedtermino.all import *

NB = 0
NB_MEANINGFUL_ICONS = 0
NB_WITH_X_ICONS = defaultdict(lambda: 0)

NON_ALIGNED = Concepts()

ICONS = Concepts()

for t in SNOMEDCT[404684003].descendants_no_double():
  NB += 1
  icons = t >> VCM
  ICONS.update(icons)
  for icon in icons:
    if (not icon.central_pictogram.empty) or ((icon.modifiers != Concepts([VCM_LEXICON[503]])) and (icon.modifiers != Concepts([VCM_LEXICON[504]]))):
      NB_MEANINGFUL_ICONS += 1
      NB_WITH_X_ICONS[len(icons)] += 1
      break
  else:
    NON_ALIGNED.add(t)
  
print("%s SNOMED CT clinical findings mapped to %s VCM icons" % (NB, len(ICONS)))
print("%s SNOMED CT clinical findings with meaningful icons (%s %%)" % (NB_MEANINGFUL_ICONS, float(NB_MEANINGFUL_ICONS) / NB))
for x in sorted(NB_WITH_X_ICONS.keys()):
  print("%s SNOMED CT clinical findings with %s icons (%s %%)" % (NB_WITH_X_ICONS[x], x, float(NB_WITH_X_ICONS[x]) / NB))
print("%s SNOMED CT clinical findings without meaningful icons (%s %%)" % (NB - NB_MEANINGFUL_ICONS, float(NB - NB_MEANINGFUL_ICONS) / NB))

NON_ALIGNED.discard(SNOMEDCT[64572001])
NON_ALIGNED.discard(SNOMEDCT[118234003])
NON_ALIGNED.discard(SNOMEDCT[118240005])
NON_ALIGNED.discard(SNOMEDCT[418799008])

print()
for t in NON_ALIGNED:
  for t2 in NON_ALIGNED:
    if (not t is t2) and t.is_a(t2): break
  else:
    print(t)
