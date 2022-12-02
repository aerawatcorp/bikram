"""
This file has the necessary constants for date conversion.
"""

__all__ = [
    'month_name', 'month_name_dev', 'month_number_dev', 'ENG_TO_DEV_DIGITS',
    'BS_YEAR_TO_MONTHS', 'month_name_to_numbers', 'month_number_month_name_map',
    'month_number_dev_name_map', 'month_number_shahmukhi_name_map',
]

from .calendar_data import BS_YEAR_TO_MONTHS

month_name_dev = [
    '', 'वैशाख', 'जेष्ठ', 'आषाढ़', 'श्रावण', 'भाद्र', 'आश्विन', 'कार्तिक',
    'मंसिर', 'पौष', 'माघ', 'फाल्गुन', 'चैत्र',
]
month_number_dev_name_map = dict(enumerate(month_name_dev[1:], 1))

month_name = [
    '', 'Baisakh', 'Jestha', 'Ashadh', 'Shrawan', 'Bhadra', 'Ashwin', 'Kartik',
    'Mangsir', 'Poush', 'Magh', 'Falgun', 'Chaitra',
]
month_number_month_name_map = dict(enumerate(month_name[1:], 1))

month_name_shahmukhi = [
    '', 'بیساکھ', 'جیٹھ', 'ہاڑ', 'ساون', 'بھادوں', 'اسو', 'کتا',
    'مگھر', 'پوہ', 'ماگھ', 'پھگن', 'چیت',
]
month_number_shahmukhi_name_map = dict(enumerate(month_name_shahmukhi[1:], 1))


_month_name_lower = list(map(str.lower, month_name))


month_name_abbr = [
    '', 'Bai', 'Jes', 'Ash', 'Shr', 'Bha', 'Ash', 'Kar',
    'Man', 'Pou', 'Mag', 'Fal', 'Cha',
]
month_number_month_name_abbr_map = dict(enumerate(month_name_abbr[1:], 1))

_month_name_abbr_lower = list(map(str.lower, month_name_abbr))


_all_month_names = (
    month_name[1:] +
    _month_name_lower[1:] +
    month_name_abbr[1:] +
    _month_name_abbr_lower[1:] +
    month_name_dev[1:]
)

month_name_re_fragment = r"|".join(_all_month_names)

_month_names_list = [
    month_name,
    _month_name_lower,
    month_name_abbr,
    _month_name_abbr_lower,
    month_name_dev,
]

month_name_to_numbers = {}
for name_list in _month_names_list:
    for i, mname in enumerate(name_list):
        month_name_to_numbers[mname] = i


month_number_dev = ['', '१', '२', '३', '४', '५', '६', '७', '८', '९', '१०', '११', '१२']

dev_digits_re_fragment = r'[०१२३४५६७८९]'

ENG_TO_DEV_DIGITS = {
    '0': '०',
    '1': '१',
    '2': '२',
    '3': '३',
    '4': '४',
    '5': '५',
    '6': '६',
    '7': '७',
    '8': '८',
    '9': '९',
}
DEV_TO_ENG_DIGITS = {v: k for k, v in ENG_TO_DEV_DIGITS.items()}

ENG_TO_DEV_DIGITS_TRANSTABLE = {ord(k): v for k, v in ENG_TO_DEV_DIGITS.items()}
DEV_TO_ENG_DIGITS_TRANSTABLE = {ord(k): v for k, v in DEV_TO_ENG_DIGITS.items()}

# The keys are years in Bikram Samwat and the values are
# tuple containing the number of days for each month.
# The first item is None for consistency.
