"""
Jakaa kesäviikot nimien kesken tasavälein
niin että juhannus kiertää tasaisesti.

Tuottaa (ylikirjoittaa) 
vuosikalenteritiedostot (.md) kuluvalle ja 
seuraavalle vuodelle. Tuottaa yhden 
nettikalenteritiedoston (.ics) jossa kuluva 
ja seuraava vuosi.

Jos "juhannusnimeä" ei ole asetettu, arpoo
nimen kuluvan vuoden juhannukselle.

Asenna tarvittavat:
    pip install -r requirements.txt
    
Testattu Python 3.6-3.8.
"""

import collections
from datetime import date, datetime
import itertools
import random

import arrow
import dateutil.easter
from dateutil import tz
from dateutil.relativedelta import relativedelta, SA as Saturday
import ics

# ---------------------------------------

year_to_generate_for = 2020

names = ['Alfa', 'Beta', 'Gamma', 'Delta', 'Epsilon']
midsummer_name = 'Alfa'
midsummer_name_year = 2018

first_week = 17
last_week = 41

spring_cleaning = 16
autumn_cleaning = 42

cleaning_name = 'TALKOOT'

# ---------------------------------------

weeks_in_total = last_week - first_week + 1
assert weeks_in_total == 25
weeks_per_name = weeks_in_total / len(names)
assert weeks_per_name == 5


class Year(dict):
    def __init__(self, year_number, midsummer_name):
        self.year = year_number

        self[self.midsummer_week] = midsummer_name

        backward = Rotator(midsummer_name, backward=True)
        self.update({
            week_number: backward.next()
            for week_number in range(self.midsummer_week - 1, first_week - 1,
                                     -1)
        })

        forward = Rotator(midsummer_name)
        self.update({
            week_number: forward.next()
            for week_number in range(self.midsummer_week + 1, last_week + 1)
        })

        counter = collections.Counter(self.values())
        assert all([count == weeks_per_name for count in counter.values()])

        spring_clean = (spring_cleaning if spring_cleaning != self.easter_week
                        else spring_cleaning - 1)
        self[spring_clean] = cleaning_name
        self[autumn_cleaning] = cleaning_name

        assert len(self) == weeks_in_total + 2

    def __str__(self):
        weeks = ''
        for week, name in sorted(self.items()):
            date_monday, date_sunday = self.start_and_end_for_week(week)
            if name == cleaning_name:
                name = f'*{name}*'
            weeks += (f'|**{week:02}**| '
                      f'{date_monday.strftime("%d.%m")} - '
                      f'{date_sunday.strftime("%d.%m")} | '
                      f'{name:10} |\n')
        return (f'{self.year}\n'
                f'====\n\n'
                f'|  Vk  | Pvm           | Haltija    |\n'
                f'|:----:|:-------------:|:----------:|\n'
                f'{weeks}')

    def create_icalendar(self, calendar=None):
        calendar = calendar or ics.Calendar()
        for week in sorted(self.keys()):
            name = self[week]
            monday, sunday = self.start_and_end_for_week(week)
            event = ics.Event(
                name=f'Honkaranta: {name}',
                begin=monday,
                duration={'days': 6,
                          'hours': 14})
            event.make_all_day()
            if type(calendar.events) is list:
                calendar.events.append(event)
            else:
                calendar.events.add(event)
        return calendar

    def start_and_end_for_week(self, week):
        monday = f'{self.year}-W{week:02}-1'
        sunday = f'{self.year}-W{week:02}-7'
        date_monday = datetime.strptime(monday, '%G-W%V-%u')
        date_sunday = datetime.strptime(sunday, '%G-W%V-%u')
        return date_monday, date_sunday

    @property
    def weeks(self):
        return week_from_date(date(self.year, 12, 31))

    @property
    def easter_week(self):
        """ 
        >>> Year(2020).easter_week
        15
        >>> Year(2025).easter_week
        16
        """
        return week_from_date(dateutil.easter.easter(self.year))

    @property
    def midsummer_week(self):
        """ 
        >>> Year(2020).midsummer_week
        25
        >>> Year(2025).midsummer_week
        25
        """
        return week_from_date(
            date(self.year, 6, 20) + relativedelta(weekday=Saturday))

    @property
    def midsummer_name(self):
        return self.get(self.midsummer_week)


class Rotator:
    def __init__(self, start_name, backward=False):
        if not backward:
            self.iter = itertools.cycle(names)
        else:
            self.iter = itertools.cycle(reversed(names))
        while next(self.iter) != start_name:
            pass

    def next(self):
        return next(self.iter)


def get_midsummer_name(name):
    global midsummer_name_year
    if name is None:
        name = random.choice(names)
        rotator = Rotator(name)
        
    else:
        assert midsummer_name_year is not None, 'Aseta myös vuosi'
        assert midsummer_name_year <= year_to_generate_for, 'Tarkista vuosi'
        
        rotator = Rotator(name)
        while midsummer_name_year < year_to_generate_for:
            name = rotator.next()
            midsummer_name_year += 1
    return name, rotator

def week_from_date(date):
    _, week, _ = date.isocalendar()
    return week

# GENERATE

year_to_generate_for = date.today().year
midsummer_name, rotator = get_midsummer_name(midsummer_name)

year1 = Year(year_to_generate_for, midsummer_name)

midsummer_name = rotator.next()

year2 = Year(year_to_generate_for + 1, midsummer_name)

for year in (year1, year2):
    with open(f'../{year.year}.md', 'w') as fp:
        fp.write(str(year))

calendar = year1.create_icalendar()
#calendar = year2.create_icalendar(calendar)

icalendar_str = str(calendar).replace(
    'BEGIN:VEVENT',
    'X-WR-TIMEZONE:EET\nBEGIN:VEVENT',
    1)

with open(f'../honkaranta.ics', 'w') as fp:
    fp.write(icalendar_str)

print('Valmis')

