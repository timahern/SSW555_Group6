from datetime import date

TAGS = {('0', 'INDI'), ('0', 'FAM'), ('0', 'HEAD'), ('0', 'TRLR'), ('0', 'NOTE'),('1', 'NAME'), ('1', 'SEX'),  ('1', 'BIRT'),('1', 'DEAT'), ('1', 'FAMC'), ('1', 'FAMS'), ('1', 'MARR'), ('1', 'HUSB'), ('1', 'WIFE'), ('1', 'CHIL'), ('1', 'DIV'), ('2', 'DATE')}

MONTHS = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
          'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}

def parseLines(line):
    toks = line.split()
    level = toks[0]

    if len(toks) >= 3 and toks[2] in ('INDI', 'FAM'):
        tag = toks[2]
        args = toks[1]
    else:
        tag = toks[1]
        if len(toks) >= 3:
            args = line.split(maxsplit=2)[2]
        else:
            args = ''

    if (level, tag) in TAGS:
        isValid = 'Y'
    else:
        isValid = 'N'
    return level, tag, isValid, args

def parser(path):
    individuals = {}
    families = {}
    current = None
    dateContext = None

    with open(path, encoding='utf-8') as f:
        for raw in f:
            theLine = raw.rstrip('\r\n')
            if not theLine.strip():
                continue

            # print(f'--> {theLine}')
            level, tag, isValid, args = parseLines(theLine)
            # print(f'<-- {level}|{tag}|{isValid}|{args}')

            if level == '0' and tag == 'INDI':
                current = {'id': args, 'name': None, 'sex': None,
                           'birth': None, 'death': None, 'famc': [], 'fams': []}
                individuals[args] = current
                dateContext = None
            elif level == '0' and tag == 'FAM':
                current = {'id': args, 'married': None, 'divorced': None,
                           'husband': None, 'wife': None, 'children': []}
                families[args] = current
                dateContext = None
            elif level == '0':
                current = None
                dateContext = None
            elif level == '1' and current is not None:
                if tag == 'NAME':   current['name'] = args
                elif tag == 'SEX':  current['sex'] = args
                elif tag == 'HUSB': current['husband'] = args
                elif tag == 'WIFE': current['wife'] = args
                elif tag == 'CHIL': current['children'].append(args)
                elif tag == 'FAMC': current['famc'].append(args)
                elif tag == 'FAMS': current['fams'].append(args)
                elif tag in ('BIRT', 'DEAT', 'MARR', 'DIV'):
                    dateContext = tag
                else:
                    dateContext = None
            elif level == '2' and tag == 'DATE' and current is not None:
                if dateContext == 'BIRT':   current['birth'] = args
                elif dateContext == 'DEAT': current['death'] = args
                elif dateContext == 'MARR': current['married'] = args
                elif dateContext == 'DIV':  current['divorced'] = args

    return individuals, families

def idSortKey(id):
    num = ''.join(c for c in id if c.isdigit())
    return int(num) if num else id

def displayId(raw):
    s = raw.strip('@')
    letters = ''.join(c for c in s if not c.isdigit())
    num = ''.join(c for c in s if c.isdigit())
    if num:
        return letters + num.zfill(2)
    return s

def parseGedDate(gedDate):
    if not gedDate or gedDate == 'Y':
        return None
    parts = gedDate.split()
    if len(parts) != 3:
        return None
    day, mon, year = parts
    if mon not in MONTHS:
        return None
    return date(int(year), MONTHS[mon], int(day))

def formatGedDate(gedDate):
    d = parseGedDate(gedDate)
    if d is None:
        return 'NA'
    return d.isoformat()

def ageYears(birthDate, onDate):
    age = onDate.year - birthDate.year
    if (onDate.month, onDate.day) < (birthDate.month, birthDate.day):
        age -= 1
    return age

def formatIdSet(ids):
    if not ids:
        return 'NA'
    shown = [displayId(x) for x in ids]
    inner = ', '.join(f"'{x}'" for x in shown)
    return '{' + inner + '}'

def printIndividuals(individuals):
    print()
    print('Individuals')
    print()
    print(f"{'ID':<4}  {'Name':<22}  {'Gender':<6}  {'Birthday':<10}  {'Age':<3}  {'Alive':<5}  {'Death':<10}  {'Child':<8}  {'Spouse'}")
    for rawId in sorted(individuals.keys(), key=idSortKey):
        p = individuals[rawId]
        birth = parseGedDate(p['birth'])
        death = parseGedDate(p['death'])
        alive = p['death'] is None
        if birth and death:
            age = ageYears(birth, death)
        elif birth:
            age = ageYears(birth, date.today())
        else:
            age = 'NA'
        deathStr = formatGedDate(p['death']) if p['death'] else 'NA'
        print(f"{displayId(rawId):<4}  {(p['name'] or 'NA'):<22}  {(p['sex'] or 'NA'):<6}  {formatGedDate(p['birth']):<10}  {str(age):<3}  {str(alive):<5}  {deathStr:<10}  {formatIdSet(p['famc']):<8}  {formatIdSet(p['fams'])}")

def printFamilies(individuals, families):
    print()
    print('Families')
    print()
    print(f"{'ID':<4}  {'Married':<10}  {'Divorced':<8}  {'Husband ID':<12}  {'Husband Name':<22}  {'Wife ID':<7}  {'Wife Name':<22}  {'Children'}")
    for famId in sorted(families.keys(), key=idSortKey):
        fam = families[famId]
        husbId = fam['husband']
        wifeId = fam['wife']
        husbName = individuals.get(husbId, {}).get('name') if husbId else None
        wifeName = individuals.get(wifeId, {}).get('name') if wifeId else None
        print(f"{displayId(famId):<4}  {formatGedDate(fam['married']):<10}  {formatGedDate(fam['divorced']):<8}  {(displayId(husbId) if husbId else 'NA'):<12}  {(husbName or 'NA'):<22}  {(displayId(wifeId) if wifeId else 'NA'):<7}  {(wifeName or 'NA'):<22}  {formatIdSet(fam['children'])}")

if __name__ == '__main__':
    individuals, families = parser('JonesThompsonFamily-1.ged')
    printIndividuals(individuals)
    printFamilies(individuals, families)