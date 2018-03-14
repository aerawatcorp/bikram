=====
Usage
=====

This package contains a class named :code:`samwat`. This is our BS date object,
similar to python's native :code:`datetime.date` object. It supports
date operations with the python's native date objects.

More often than not, there is a need to work with BS and AD date at the same time.
Converting back and forth to do calculation and representation becomes very tedious
and results in a spagetti codebase. The :code:`samwat` object tries to make this a bit cleaner
and intuitive. Here are some examples:


samwat
----------------

Let's get today's date in Bikram Samwat.

>>> from datetime import date
>>> from bikram import samwat
>>> bs_date = samwat.from_ad(date.today())
>>> bs_date
samwat(2074, 11, 30)

Now, let's convert the :code:`bs_date` into AD.

>>> bs_date.ad
datetime.date(2018, 3, 14)

That's it. The :code:`samwat` instance has a property called :code:`ad` that
returns a corresponding :code:`datetime.date` instance.


Out of range dates
~~~~~~~~~~~~~~~~~~~
A :code:`ValueError` is thrown if the date you are trying to convert falls
out of the range. If you are using this library to convert user-submitted dates
then you need to handle this exception accordingly to avoid runtime errors.

>>> samwat.from_ad(date(2100, 1,1))
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/danse/projects/k/bikram/bikram/bikram.py", line 113, in from_ad
    return convert_ad_to_bs(ad_date)
  File "/home/danse/projects/k/bikram/bikram/bikram.py", line 126, in convert_ad_to_bs
    raise ValueError('A.D. year is out of range...')
ValueError: A.D. year is out of range...

More
~~~~

For in-depth usage and examples, go to the next page.
