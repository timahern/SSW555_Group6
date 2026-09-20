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
    with open(path, encoding='utf-8') as f:
        for raw in f:
            theLine = raw.rstrip('\r\n')
            if not theLine.strip():
                continue
            print(f'--> {theLine}')
            level, tag, isValid, args = parseLines(theLine)
            print(f'<-- {level}|{tag}|{isValid}|{args}')

if __name__ == '__main__':
    parser('JonesThompsonFamily.ged')