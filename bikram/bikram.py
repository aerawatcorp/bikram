"""
This module contains the :code:`samwat`, a container class for Bikram Samwat dates.

To run the examples in this page, import :code:`samwat` like this:

>>> from bikram import samwat

Some examples require the :code:`datetime.date`, and :code:`datetime.timedelta`
objects. Please import them as follows:

>>> from datetime import date, timedelta

"""

import re
from typing import List
from functools import total_ordering
from datetime import date, timedelta
from .constants import (
    BS_YEAR_TO_MONTHS,
    month_name_re_fragment,
    month_name_to_numbers,
    month_number_month_name_map,
    month_number_dev_name_map,
    dev_digits_re_fragment,
    DEV_TO_ENG_DIGITS_TRANSTABLE as DEV_ENG_TRANS,
    ENG_TO_DEV_DIGITS_TRANSTABLE as ENG_DEV_TRANS,
)


__all__ = ['samwat', 'convert_ad_to_bs', 'convert_bs_to_ad']


_PATTERNS_CACHE = {}


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

    _to_str_converters = {
        "%d": lambda obj: str(obj.day).zfill(2),
        "%-d": lambda obj: str(obj.day).rjust(2),

        "%dne": lambda obj: str(obj.day).zfill(2).translate(ENG_DEV_TRANS),
        "%-dne": lambda obj: str(obj.day).rjust(2).translate(ENG_DEV_TRANS),

        "%m": lambda obj: str(obj.month).zfill(2),
        "%-m": lambda obj: str(obj.month).rjust(2),

        "%mne": lambda obj: str(obj.month).zfill(2).translate(ENG_DEV_TRANS),
        "%-mne": lambda obj: str(obj.month).rjust(2).translate(ENG_DEV_TRANS),

        "%y": lambda obj: str(obj.year)[2:],
        "%Y": lambda obj: str(obj.year),

        "%yne": lambda obj: str(obj.year)[2:].translate(ENG_DEV_TRANS),
        "%Yne": lambda obj: str(obj.year).translate(ENG_DEV_TRANS),

        "%B": lambda obj: month_number_month_name_map[obj.month],
        "%Bne": lambda obj: month_number_dev_name_map[obj.month],
    }

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

    def strftime(self, formatstr: str):
        """
        Format a samwat object to specified date string.
        The format strings are similar to those accepted by :func:`~bikram.samwat.parse`
        with the following additions/modifications:

        - "%B": Formats to Nepali month name(Example: Baisakh, Jestha, etc.)
        - "%Bne": Formats to Nepali Devnagari month name(Example:'वैशाख', 'जेष्ठ',  etc.)
        """
        formatted = formatstr
        matches = [match.group() for match in self._code_re.finditer(formatstr)]

        for match in matches:
            try:
                converter = self._to_str_converters[match]
            except KeyError:
                raise ValueError(f"Invalid date pattern {match}")
            try:
                formatted = formatted.replace(match, converter(self))
            except KeyError:
                raise ValueError(f"Invalid value for month")
        return formatted

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

    _code_patterns = {
        "%d": r"(?P<day>\d{2})",
        "%-d": r"(?P<day>\d{1,2})",

        "%dne": rf"(?P<ned>{dev_digits_re_fragment}{{2}})",
        "%-dne": rf"(?P<ned>{dev_digits_re_fragment}{{1,2}})",

        "%m": r"(?P<m>\d{2})",
        "%-m": r"(?P<m>\d{1,2})",

        "%mne": rf"(?P<nem>{dev_digits_re_fragment}{{2}})",
        "%-mne": rf"(?P<nem>{dev_digits_re_fragment}{{1,2}})",

        "%y": r"(?P<sy>\d{2})",
        "%Y": r"(?P<y>\d{4})",

        "%yne": rf"(?P<ney>{dev_digits_re_fragment}{{2}})",
        "%Yne": rf"(?P<ney>{dev_digits_re_fragment}{{4}})",

        "%B": rf"(?P<ml>{month_name_re_fragment})",
    }

    _code_re = re.compile(r"(?P<code>%-?\w{1,3})")

    @classmethod
    def _get_pattern_from_codes(cls, codes: List[str]):
        patterns = []

        for code in codes:
            try:
                pattern_str = cls._code_patterns[code]
            except KeyError:
                raise ValueError(f"Invalid code: {code}")

            patterns.append(pattern_str)

        pattern = re.compile(r".".join(patterns))
        return pattern

    @staticmethod
    def _translate_number_from_devanagari(numberstr: str) -> int:
        if not numberstr:
            raise ValueError("Trying to translate invalid numberstr from devanagari")
        return int(numberstr.translate(DEV_ENG_TRANS))

    @classmethod
    def parse(cls, datestr: str, parsestr: str):
        """
        parse bikram samwat date string and return a `bikram.samwat` instance.

        - "%d": zero padded day of month, 07
        - "%-d": padded day of month, 7

        - "%dne": zero-padded day of month in devanagari digits, ०७
        - "%-dne": day of month in devanagari digits, ७

        - "%m": zero-padded month number, 01
        - "%-m": month number, 1

        - "%mne": zero-added month number in devanagari digits, ०१
        - "%-mne": month number in devanagari digits, १

        - "%y": two digit year, 73 implies 2073
        - "%Y": four digit year, 2073

        - "%yne": two digit year in devanagari digits, ७३ implies २०७३
        - "%Yne": four digit year in devanagari digits, २०७३

        - "%B": name of bikram samwat months in English spelling, English spelling short
            (abbr. by first three letters), Devanagari spelling. Any one of the list below:

        ```
            [
                'वैशाख', 'जेष्ठ', 'आषाढ़', 'श्रावण', 'भाद्र', 'आश्विन', 'कार्तिक',
                'मंसिर', 'पौष', 'माघ', 'फाल्गुन', 'चैत्र',

                'Baisakh', 'Jestha', 'Ashadh', 'Shrawan', 'Bhadra', 'Ashwin', 'Kartik',
                'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra',

                'Bai', 'Jes', 'Ash', 'Shr', 'Bha', 'Ash', 'Kar',
                'Man', 'Pou', 'Mag', 'Fal', 'Cha',
            ]
        ```
        """
        codes = cls._code_re.findall(parsestr)

        # Check if three different patterns, each for year, month and days are present.
        # Just check if there are y, (m or b) and d or not
        unique_codes = [
            c.replace("%", "").replace("-", "").replace("ne", "").lower()
            for c in codes
        ]

        if len(set(unique_codes)) != 3:
            raise ValueError("Invalid number of date codes in the parse pattern")

        # patterns are usually static across a codebase -- this is a
        # micro optimization to avoid calling re.compile for same
        # parsestr all the time
        # and using try..except is faster if `parse` is being called many times
        try:
            pattern = _PATTERNS_CACHE[parsestr]
        except KeyError:
            pattern = cls._get_pattern_from_codes(codes)
            _PATTERNS_CACHE[parsestr] = pattern

        match = pattern.match(datestr)
        if not match:
            raise ValueError(f"Could not match {parsestr} with {datestr}")

        date_dict = match.groupdict()
        if not len(date_dict):
            raise ValueError("Something is wrong with the pattern")

        if 'ml' in date_dict:
            ml = date_dict['ml']
            date_dict['m'] = month_name_to_numbers[ml]

        if 'sy' in date_dict:
            date_dict['y'] = int(f"20{date_dict['sy']}")

        if 'ney' in date_dict:
            date_dict['y'] = cls._translate_number_from_devanagari(date_dict['ney'])

        if 'nem' in date_dict:
            date_dict['m'] = cls._translate_number_from_devanagari(date_dict['nem'])

        if 'ned' in date_dict:
            date_dict['day'] = cls._translate_number_from_devanagari(date_dict['ned'])

        datetuple = list(map(int, [date_dict['y'], date_dict['m'], date_dict['day']]))
        return cls(*datetuple)

    @classmethod
    def from_iso(cls, datestr: str):
        '''
        Naive way to parse date from a ISO8601 (YYYY-MM-DD) BS date
        string and return `bikram.samwat` instance.
        '''
        try:
            return cls.parse(datestr, "%Y-%m-%d")
        except ValueError as err:
            raise ValueError(f"Invalid datestr provided. Original error: {err}")


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
