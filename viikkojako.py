import collections
from datetime import date, datetime
import dateutil.easter
from dateutil.relativedelta import relativedelta, SA as Saturday
import itertools
import json
import pathlib
import random

'''
| Tables        | Are           | Cool  |
| ------------- |:-------------:| -----:|
| col 3 is      | right-aligned | $1600 |
| col 2 is      | centered      |   $12 |
| zebra stripes | are neat      |    $1 |
'''

names = ['Alfa', 'Beta', 'Gamma', 'Delta', 'Epsilon']

spring_cleaning = 16
autumn_cleaning = 42

cleaning_name = 'TALKOOT'

class Year(dict):
    
    def __init__(self, year_number, midsummer_name):
        self.year = year_number
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
            monday = f'{self.year}-W{week:02}-1'
            sunday = f'{self.year}-W{week:02}-7'
            date_monday = datetime.strptime(monday, '%G-W%V-%u')
            date_sunday = datetime.strptime(sunday, '%G-W%V-%u')
            if name == cleaning_name:
                name = f'*{name}*'
            weeks += (f'| {week:02} | '
                f'{date_monday.strftime("%d.%m")} - '
                f'{date_sunday.strftime("%d.%m")} | '
                f'{name:10} |\n')
        return (
            f'{self.year}\n'
            f'====\n\n'
            f'| Vk | Pvm           | Haltija    |\n'
            f'|:--:|:-------------:|:----------:|\n'
            f'{weeks}'
        )
        
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
    
def distribute_weeks(years):
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
    
def get_year(years):
    """
    >>> get_year([])
    2020
    >>> test_years = [ns(year=2021), ns(year=2022)]
    >>> get_year(test_years)
    2023
    """
    if len(years):
        return years[-1].year + 1
    else:
        return date.today().year

def get_midsummer_name(year):
    return year.weeks[midsummer_week(year.year)]

def week_from_date(date):
    _, week, _ = date.isocalendar()
    return week
    
def get_candidates(names_listed):
    """
    >>> midsummer_names = ['Beta', 'Gamma', 'Delta', 'Epsilon']
    >>> get_candidates(midsummer_names)
    ['Alfa']
    """
    counts = collections.Counter(names + names_listed)
    min_count = min(counts.values())
    return [ name 
        for (name, count) in counts.items() 
        if count == min_count ]

for i in range(2):
    distribute_weeks(years)
    print(years[i])
    print()

with open('2020.md', 'w') as fp:
    fp.write(str(years[0]))
