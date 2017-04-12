PyMedTermino
============

PyMedTermino (Medical Terminologies for Python) is a Python module for
easy access to the main medical terminologies in Python.
The following terminologies are supported: SNOMED CT, ICD10, MedDRA, CDF, UMLS and VCM
icons (an iconic terminology developped at Paris 13 University).
PyMedTermino facilitates the access to terminologies, but does not include terminology
contents (excepted for VCM); terminology contents should be obtained separately
(e.g. downloaded from UMLS).

PyMedTermino has been created at the LIMICS reseach lab,
University Paris 13, Sorbonne Paris Cité, INSERM UMRS 1142, Paris 6 University, by
Jean-Baptiste Lamy. PyMedTermino is available under the GNU LGPL licence and has been
described in the following scientific article (please cite it if you use PyMedTermino !):

Lamy JB, Venot A, Duclos C.
`PyMedTermino: an open-source generic API for advanced terminology services. <http://ebooks.iospress.nl/volumearticle/39485>`_
Stud Health Technol Inform 2015;210:924-928


In case of trouble, please contact Jean-Baptiste Lamy <jean-baptiste.lamy *@* univ-paris13 *.* fr>

::

  LIMICS
  University Paris 13, Sorbonne Paris Cité
  Bureau 149
  74 rue Marcel Cachin
  93017 BOBIGNY
  FRANCE


What can I do with PyMedTermino?
--------------------------------

  >>> ICD10.search("tachycardia")
  [ ICD10[u"I49.5"]  # Sick sinus syndrome
  , ICD10[u"I47.2"]  # Ventricular tachycardia
  , ICD10[u"F43.0"]  # Acute stress reaction
  , ICD10[u"I47"]  # Paroxysmal tachycardia
  , ICD10[u"I47.1"]  # Supraventricular tachycardia
  , ICD10[u"I47.9"]  # Paroxysmal tachycardia, unspecified
  , ICD10[u"R00.0"]  # Tachycardia, unspecified
  , ICD10[u"O68.0"]  # Labour and delivery complicated by fetal heart rate anomaly
  ]
  >>> ICD10[u"I47"].parents
  [ICD10[u"I30-I52"]  # Other forms of heart disease
  ]
  >>> ICD10[u"I47"].children
  [ ICD10[u"I47.0"]  # Re-entry ventricular arrhythmia
  , ICD10[u"I47.2"]  # Ventricular tachycardia
  , ICD10[u"I47.1"]  # Supraventricular tachycardia
  , ICD10[u"I47.9"]  # Paroxysmal tachycardia, unspecified
  ]
  >>> list(ICD10[u"I47"].ancestors_no_double())
  [ ICD10[u"I30-I52"]  # Other forms of heart disease
  , ICD10[u"IX"]  # Diseases of the circulatory system
  ]
  >>> ICD10[u"I47"] >> VCM   # Maps the ICD10 concept to VCM icon
  Concepts([
    VCM[u"current--hyper--heart_rhythm"]  # tachycardia
  ])

PyMedTermino can also be used without Python, just for converting terminology contents into Sqlite3 databases.


Links
-----

PyMedTermino on BitBucket (development repository): https://bitbucket.org/jibalamy/pymedtermino

PyMedTermino on PyPI (Python Package Index, stable release): https://pypi.python.org/pypi/PyMedTermino

Documentation: http://pythonhosted.org/PyMedTermino
