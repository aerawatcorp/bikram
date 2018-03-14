===============================
Python Bikram Samwat
===============================


.. image:: https://img.shields.io/pypi/v/bikram.svg
        :target: https://pypi.python.org/pypi/bikram

.. image:: https://img.shields.io/travis/poudel/bikram.svg
        :target: https://travis-ci.org/poudel/bikram

.. image:: https://readthedocs.org/projects/bikram/badge/?version=latest
        :target: https://bikram.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Utilities to work with Bikram/Vikram Samwat dates. Documentation: https://bikram.readthedocs.io.


Features
--------

* Convert Bikram Samwat dates to AD and vice versa.
  Intended to be useful for Nepali software developers.
* Well tested and readable source code.
* Date operations, i.e. addition/subtraction,
  supported with :code:`datetime.date` and :code:`datetime.timedelta` within range.
* Supports comparison with :code:`datetime.date` and :code:`datetime.timedelta` objects.


Caveats
-------

* Is not very helpful if the date falls outside the map of BS years to days in month.


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

