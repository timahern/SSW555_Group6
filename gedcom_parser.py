import sys

TAGS = {('0', 'INDI'), ('0', 'FAM'), ('0', 'HEAD'), ('0', 'TRLR'), ('0', 'NOTE'),('1', 'NAME'), ('1', 'SEX'),  ('1', 'BIRT'),('1', 'DEAT'), ('1', 'FAMC'), ('1', 'FAMS'), ('1', 'MARR'), ('1', 'HUSB'), ('1', 'WIFE'), ('1', 'CHIL'), ('1', 'DIV'), ('2', 'DATE')}

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

            print(f'--> {theLine}')
            level, tag, isValid, args = parseLines(theLine)
            print(f'<-- {level}|{tag}|{isValid}|{args}')

            if level == '0' and tag == 'INDI':
                current = {'id': args, 'name': None, 'sex': None,
                           'birth': None, 'death': None}
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

def printIndividuals(individuals):
    print()
    print('Individuals')
    print()
    print(f"{'ID':<4}  {'Name'}")
    for rawId in sorted(individuals.keys(), key=idSortKey):
        p = individuals[rawId]
        print(f"{displayId(rawId):<4}  {p['name'] or 'NA'}")

def printFamilies(individuals, families):
    print()
    print('Families')
    print()
    print(f"{'Family ID':<10}  {'Spouse ID':<10}  {'Spouse Name'}")
    for famId in sorted(families.keys(), key=idSortKey):
        fam = families[famId]
        if fam['husband']:
            husb = individuals.get(fam['husband'], {})
            print(f"{displayId(famId):<10}  {displayId(fam['husband']):<10}  {husb.get('name') or 'NA'}")
        if fam['wife']:
            wife = individuals.get(fam['wife'], {})
            print(f"{displayId(famId):<10}  {displayId(fam['wife']):<10}  {wife.get('name') or 'NA'}")

if __name__ == '__main__':
    individuals, families = parser('JonesThompsonFamily-1.ged')
    printIndividuals(individuals)
    printFamilies(individuals, families)