import collections
from datetime import date, datetime
import dateutil.easter
import ics
import arrow
from dateutil import tz
from dateutil.relativedelta import relativedelta, SA as Saturday
import itertools
import json
import pathlib
import random

year_to_generate_for = 2020
midsummer_name = None

names = ['Alfa', 'Beta', 'Gamma', 'Delta', 'Epsilon']

spring_cleaning = 16
autumn_cleaning = 42

cleaning_name = 'TALKOOT'

class Year(dict):
    
    def __init__(self, year_number, midsummer_name):
        self.year = year_number

        if midsummer_name is None:
            midsummer_name = random.choice(names)
        self[self.midsummer_week] = midsummer_name
        
        backward = Rotator(midsummer_name, backward=True)
        for week_number in range(self.midsummer_week-1, 0, -1):
            if (
                (
                    week_number == spring_cleaning and
                    week_number != self.easter_week
                ) or (
                    (week_number + 1) == spring_cleaning and
                    (week_number + 1) == self.easter_week
                )
            ):
                self[week_number] = cleaning_name
            else:
                self[week_number] = backward.next()
                
        forward = Rotator(midsummer_name)
        for week_number in range(self.midsummer_week+1, self.weeks+1):
            if (
                (
                    week_number == autumn_cleaning
                ) or (
                    self.weeks == 53 and
                    week_number - 1 == autumn_cleaning)):
                self[week_number] = cleaning_name
            else:
                self[week_number] = forward.next()
        
    def __str__(self):
        '''
        weeks = '\n'.join(
            map(lambda w: f'{w[0]:02} - {w[1]}', 
                sorted(self.items())))
                
        d = "2013-W26"
r = datetime.datetime.strptime(d + '-1', "%Y-W%W-%w")
print(r)
        '''
        weeks = ''
        for week, name in sorted(self.items()):
            date_monday, date_sunday = self.start_and_end_for_week(week)
            if name == cleaning_name:
                name = f'*{name}*'
            weeks += (f'|**{week:02}**| '
                f'{date_monday.strftime("%d.%m")} - '
                f'{date_sunday.strftime("%d.%m")} | '
                f'{name:10} |\n')
        return (
            f'{self.year}\n'
            f'====\n\n'
            f'|  Vk  | Pvm           | Haltija    |\n'
            f'|:----:|:-------------:|:----------:|\n'
            f'{weeks}'
        )

    def create_icalendar(self):
        calendar = ics.Calendar()
        for week in sorted(self.keys()):
            name = self[week]
            monday, sunday = self.start_and_end_for_week(week)
            event = ics.Event(name=f'Honkaranta: {name}', begin=monday, duration={'days':7})
            calendar.events.add(event)
        return calendar

    def start_and_end_for_week(self, week):
        monday = f'{self.year}-W{week:02}-1'
        sunday = f'{self.year}-W{week:02}-7'
        date_monday = datetime.strptime(monday, '%G-W%V-%u')
        date_sunday = datetime.strptime(sunday, '%G-W%V-%u')
        date_monday = arrow.get(date_monday, tz.gettz('EET'))
        date_sunday = arrow.get(date_sunday, tz.gettz('EET'))
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
        return  week_from_date(dateutil.easter.easter(self.year))
        
    @property
    def midsummer_week(self):
        """ 
        >>> Year(2020).midsummer_week
        25
        >>> Year(2025).midsummer_week
        25
        """
        return week_from_date(
            date(self.year, 6, 20) + 
            relativedelta(weekday=Saturday))

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
        

years_file = pathlib.Path('years.json')

if years_file.exists():
    with years_file.open() as fp:
        years = json.load(fp)
else:
    years = []
    
def distribute_weeks(year_number, midsummer_name):
    """
    >>> years = []
    >>> for _ in range(5): distribute_weeks(years)
    >>> len(years)
    5
    >>> 52 <= len(years[0].weeks) <= 53
    True
    """
    year_number = get_year(years)

    if len(years):
        last_year = years[-1]
        last_name = last_year.midsummer_name
        next_name = Rotator(last_name).next()
    else:
        next_name = random.choice(names)
        
    year = Year(year_number, next_name)
    
    checker = collections.Counter([
        year[key]
        for key in year
        if year[key] != cleaning_name])
    assert all(
        [value == 50/len(names) for value in checker.values()]), 'Mismatch in week count'
        
    years.append(year)


def get_midsummer_name(year):
    return year.weeks[midsummer_week(year.year)]

def week_from_date(date):
    _, week, _ = date.isocalendar()
    return week

year = Year(year_to_generate_for, midsummer_name)

with open(f'../{year_to_generate_for}.md', 'w') as fp:
    fp.write(str(year))

calendar = year.create_icalendar()

with open(f'../honkaranta.ics', 'a+') as  fp:
    fp.write(str(calendar))

print(f'Saved {year_to_generate_for}')
print(str(calendar))