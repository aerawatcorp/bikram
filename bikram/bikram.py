"""
This module contains the :code:`samwat`, a container class for Bikram Samwat dates.

To run the examples in this page, import :code:`samwat` like this:

>>> from bikram import samwat

Some examples require the :code:`datetime.date`, and :code:`datetime.timedelta`
objects. Please import them as follows:

>>> from datetime import date, timedelta

"""
from functools import total_ordering
from datetime import date, timedelta
from .constants import BS_YEAR_TO_MONTHS


__all__ = ['samwat', 'convert_ad_to_bs', 'convert_bs_to_ad']


@total_ordering
class samwat:
    '''
    This class represents a Bikram Samwat date. It can be used as an independent
    container, without using the date conversion part.

    >>> samwat(2074, 11, 30)
    samwat(2074, 11, 30)

    If you have the equivalent :code:`datetime.date` instance, then you can pass it
    as :code:`_ad` argument to the constructor like this:

    >>> samwat(2074, 11, 30, date(2018, 3, 14))

    Doing so will cache the AD equivalent of the :code:`samwat` instance and provide
    a faster access through the :code:`ad` property for future access.

    :code:`samwat` also supports date operations, comparison etc. with other :code:`samwat`
    objects and :code:`datetime.date` objects. It also supports arithmetic operations with
    :code:`datetime.timedelta` objects.

    Compare two :code:`samwat` date:

    >>> samwat(2074, 10, 30) < samwat(2074, 11, 30)
    True

    Comparison with :code:`datetime.date` object:

    >>> samwat(2074, 10, 30) == date(2018, 3, 14)
    True

    Subtract 10 days from a :code:`samwat` using :code:`datetime.timedelta` object.

    >>> samwat(2074, 10, 30) - timedelta(days=10)
    samwat(2074, 10, 20)

    Subtract two :code:`samwat` dates and get :code:`datetime.timedelta` representation.

    >>> samwat(2074, 10, 11) - samwat(2070, 10, 11)
    datetime.timedelta(1461)

    Please note that the above operations require that the date be in the range of years
    specified in the :code:`constants.py` file. As warned in the usage guide, you will
    need to handle :code:`ValueError` exception if the date falls outside the range.
    '''
    __slots__ = ('year', 'month', 'day', '_ad')

    def __init__(self, year, month, day, ad=None):
        self.year = year
        self.month = month
        self.day = day
        self._ad = ad

    @property
    def ad(self):
        """
        Return a :code:`datetime.date` instance, that is, this date converted to AD.
        Accessing the :code:`ad` property automatically tries to calculate the AD date.

        It caches the :code:`datetiem.date` object as :code:`_ad` to avoid expensive
        calculation for the next time.

        >>> samwat(2074, 11, 30).ad
        datetime.date(2018, 3, 14)

        """
        if self._ad is None:
            self._ad = convert_bs_to_ad(self)
        return self._ad

    def as_tuple(self):
        """
        Return a :code:`samwat` instance as a tuple of year, month, and day.

        >>> samwat(2074, 11, 30).as_tuple()
        (2074, 11, 30)

        """
        return self.year, self.month, self.day

    def replace(self, year=None, month=None, day=None):
        '''
        Return a new copy of :code:`samwat` by replacing one or more provided attributes
        of this date. For example, to replace the year:

        >>> samwat(2074, 11, 30).replace(year=2073)
        samwat(2073, 11, 30)

        To replace the month:

        >>> samwat(2074, 11, 30).replace(month=12)
        samwat(2074, 12, 30)

        '''
        args = [year or self.year, month or self.month, day or self.day]
        return samwat(*args)

    def __repr__(self):
        return 'samwat({self.year}, {self.month}, {self.day})'.format(self=self)

    def __str__(self):
        return '{self.year}-{self.month}-{self.day}'.format(self=self)

    def __add__(self, other):
        if isinstance(other, timedelta):
            return convert_ad_to_bs(self.ad + other)
        raise TypeError(
            'Addition only supported for datetime.timedelta type, not {}'
            .format(type(other)))

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return convert_ad_to_bs(self.ad - other)
        elif isinstance(other, samwat):
            return self.ad - other.ad
        elif isinstance(other, date):
            return self.ad - other
        raise TypeError(
            'Subtraction only supported for datetime.timedelta, datetime.date '
            'and bikram.samwat types, not {}'.format(type(other).__name__))

    def __rsub__(self, other):
        if isinstance(other, samwat):
            return other - self
        elif isinstance(other, date):
            return other - self.ad
        raise TypeError('Unsupported operand types {} - bikram.samwat'.format(type(other)))

    def __isub__(self, other):
        return self.__sub__(other)

    def __hash__(self):
        return hash((self.year, self.month, self.day))

    def __eq__(self, other):
        if isinstance(other, date):
            return self.ad == other
        elif isinstance(other, samwat):
            return self.as_tuple() == other.as_tuple()
        raise TypeError('Cannot compare bikram.samwat with {}'
                        .format(type(other).__name__))

    def __lt__(self, other):
        if isinstance(other, date):
            return self.ad <= other
        elif isinstance(other, samwat):
            return self.as_tuple() < other.as_tuple()
        raise TypeError('Cannot compare bikram.samwat with {}'
                        .format(type(other).__name__))

    @staticmethod
    def today():
        '''
        Returns a :code:`samwat` instance for today.
        '''
        return convert_ad_to_bs(date.today())

    @staticmethod
    def from_ad(ad_date):
        '''
        Expects a `datetime.date` then returns an equivalent `bikram.samwat` instance
        '''
        return convert_ad_to_bs(ad_date)


# pointers to an equivalent date in both AD and BS
AD_SCALE = date(1944, 1, 1)
BS_SCALE = samwat(2000, 9, 17)


def convert_ad_to_bs(date_in_ad):
    '''
    A function to convert AD dates to BS.
    Expects a `datetime.date` instance and returns an equivalent `bikram.samwat` instance.

    >>> convert_ad_to_bs(date(2018, 3, 14))
    samwat(2074, 11, 30)
    '''
    if 1944 > date_in_ad.year or date_in_ad.year > 2033:
        raise ValueError('A.D. year is out of range...')

    diff_days = (date_in_ad - AD_SCALE).days

    year = BS_SCALE.year
    day = BS_SCALE.day + diff_days
    month = BS_SCALE.month

    while day > BS_YEAR_TO_MONTHS[year][month]:
        day -= BS_YEAR_TO_MONTHS[year][month]

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
    return samwat(year, month, day, date_in_ad)


def convert_bs_to_ad(date_in_bs):
    '''
    A function to convert BS dates to AD.
    Expects a `bikram.samwat` instance and returns an equivalent `datetime.date` instance

    >>> convert_bs_to_ad(samwat(2074, 11, 30))
    datetime.date(2018, 3, 14)

    '''
    if 2000 > date_in_bs.year or date_in_bs.year > 2089:
        raise ValueError('B.S. year is out of range...')

    days = date_in_bs.day + sum(BS_YEAR_TO_MONTHS[date_in_bs.year][1:date_in_bs.month])
    year = date_in_bs.year - 1

    while year >= BS_SCALE.year:
        months_for_year = BS_YEAR_TO_MONTHS[year]
        if year == BS_SCALE.year:
            days += sum(months_for_year[BS_SCALE.month + 1:])
            days += months_for_year[BS_SCALE.month] - BS_SCALE.day
        else:
            days += sum(months_for_year[1:])
        year -= 1
    return AD_SCALE + timedelta(days=days)
