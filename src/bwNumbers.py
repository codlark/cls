from dataclasses import dataclass
import bwUtils
import re



@dataclass
class Unit():
    '''Unit represents a unitized number'''
    sign: str
    num: int
    unit: str
    def toFloat(self, **data):
        'return the number as an int according to type'
        if self.unit in ('px', 'pt'):
            return int(self.num)
        elif self.unit == 'in':
            if 'dpi' in data:
                return self.num*data['dpi']
            else:
                return self.num
        elif self.unit == 'mm':
            if 'dpi' in data:
                return self.num/25.4*data['dpi']
            else:
                return int(self.num)
        elif self.unit == '%':
            if 'whole' in data:
                return self.num/100*data['whole']
            else:
                return self.num
    def toInt(self, **data):
        return int(self.toFloat(**data))
    
    @staticmethod
    def fromStr(string, signs='-+', units=('px', 'in', 'mm'), frame=None):
        if units == 'all':
            units = ('px', 'pt', 'in', 'mm', '%')

        signs = r'^(?P<sign>['+signs+r']?)'
        unitRe = r' *(?P<unit>(?:' + '|'.join(units) + r')?)$'
        whole = signs + r'(?P<num>\d+)' + unitRe
        flt = signs + r'(?P<num>\d*\.\d+)' + unitRe
        frac = signs + r'(?P<whole>\d+) (?P<numer>\d+)/(?P<denom>\d+)' + unitRe
        fracOnly = signs + r'(?P<numer>\d+)/(?P<denom>\d+)' + unitRe

        if (match := re.match(whole, string)) or (match := re.match(flt, string)):
            sign = match.group('sign')
            num = float(match.group('num'))
            unit = match.group('unit')
        elif match := re.match(fracOnly, string):
            sign = match.group('sign')
            numer = match.group('numer')
            denom = match.group('denom')
            unit = match.group('unit')
            num = (int(numer)/int(denom))
        elif match := re.match(frac, string):
            sign = match.group('sign')
            whole = match.group('whole')
            numer = match.group('numer')
            denom = match.group('denom')
            unit = match.group('unit')
            num = int(whole)+(int(numer)/int(denom))
        else:
            return None
        
        if sign == '-':
            num *= -1
        if unit == '':
            unit = units[0]
        return Unit(sign, num, unit)


if __name__ == '__main__':
    print(Unit.fromStr('4%', units=('%')))
    print(Unit.fromStr('12', units=('pt', 'px')))
    print(Unit.fromStr('.5in'))
    print(Unit.fromStr('1/16 in').toInt(dpi=300))