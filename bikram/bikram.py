# -*- coding: utf-8 -*-
from functools import total_ordering
from datetime import date, timedelta
from .constants import BS_YEAR_TO_MONTHS

__all__ = ['samwat', 'convert_ad_to_bs', 'convert_bs_to_ad']


@total_ordering
class samwat(object):

    '''
    This class represents a Bikram Samwat date
    '''
    __slots__ = ('year', 'month', 'day', '_ad')

    def __init__(self, year, month, day, ad=None):
        self.year = year
        self.month = month
        self.day = day
        self._ad = ad

    @property
    def ad(self):
        if self._ad is None:
            self._ad = convert_bs_to_ad(self)
        return self._ad

    def as_tuple(self):
        '''
        Return this date as a tuple
        '''
        return self.year, self.month, self.day

    def replace(self, year=None, month=None, day=None):
        '''
        Return a new copy of samwat
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
        Return today's date in Bikram Samwat
        '''
        return convert_ad_to_bs(date.today())

    @staticmethod
    def from_ad(ad_date):
        '''
        Expects a `datetime.date` then return an equivalent `bikram.samwat` instance
        '''
        return convert_ad_to_bs(ad_date)


# pointers to an equivalent date in both AD and BS
ad_scale = date(1944, 1, 1)
bs_scale = samwat(2000, 9, 17)


def convert_ad_to_bs(date_in_ad):
    '''
    Expects a `datetime.date` instance and returns an equivalent `bikram.samwat` instance
    '''
    if 1944 > date_in_ad.year > 2033:
        raise ValueError('A.D. year is out of range...')

    diff_days = (date_in_ad - ad_scale).days

    year = bs_scale.year
    day = bs_scale.day + diff_days
    month = bs_scale.month

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
    Expects a `bikram.samwat` instance and returns an equivalent `datetime.date` instance
    '''
    if 2000 > date_in_bs.year > 2089:
        raise ValueError('B.S. year is out of range...')

    days = date_in_bs.day + sum(BS_YEAR_TO_MONTHS[date_in_bs.year][1:date_in_bs.month])
    year = date_in_bs.year - 1

    while year >= bs_scale.year:
        months_for_year = BS_YEAR_TO_MONTHS[year]
        if year == bs_scale.year:
            days += sum(months_for_year[bs_scale.month + 1:])
            days += months_for_year[bs_scale.month] - bs_scale.day
        else:
            days += sum(months_for_year[1:])
        year -= 1
    return ad_scale + timedelta(days=days)
