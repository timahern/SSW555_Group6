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
    # Accept full dates (DD MON YYYY), month-year (MON YYYY), or year-only (YYYY)
    # For partial dates, default the missing components to the first day/month so
    # downstream age calculations and ISO formatting can still operate.
    if not gedDate or gedDate == 'Y':
        return None
    parts = gedDate.split()
    # Normalize and validate by arity
    if len(parts) == 3:
        day_str, mon_str, year_str = parts
        if mon_str not in MONTHS:
            return None
        try:
            day = int(day_str)
            year = int(year_str)
        except ValueError:
            return None
        return date(year, MONTHS[mon_str], day)
    elif len(parts) == 2:
        mon_str, year_str = parts
        if mon_str not in MONTHS:
            return None
        try:
            year = int(year_str)
        except ValueError:
            return None
        # Default to first day of the month
        return date(year, MONTHS[mon_str], 1)
    elif len(parts) == 1:
        year_str = parts[0]
        try:
            year = int(year_str)
        except ValueError:
            return None
        # Default to Jan 1st for year-only
        return date(year, 1, 1)
    else:
        return None

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

# --- Validation support ---
from typing import Iterable, List, Dict, Any, Optional, Tuple


class ValidationError:
    def __init__(self, line_no: int, code: str, message: str):
        self.line_no = line_no
        self.code = code
        self.message = message

    def __repr__(self):
        return f"ValidationError(line_no={self.line_no}, code={self.code!r}, message={self.message!r})"


def _is_level_token(token: str) -> bool:
    return token.isdigit()


def _parse_level_tag_args_raw(raw_line: str) -> Tuple[Optional[int], Optional[str], str]:
    """Parse a raw GEDCOM line into (level, tag, args) while preserving
    the special level-0 form: 0 <ID> INDI | 0 <ID> FAM.
    Returns (None, None, '') on malformed line."""
    toks = raw_line.split()
    if len(toks) < 2:
        return None, None, ''
    if not _is_level_token(toks[0]):
        return None, None, ''
    level = int(toks[0])
    # Special level-0 entity form
    if level == 0 and len(toks) >= 3 and toks[2] in ('INDI', 'FAM'):
        tag = toks[2]
        args = toks[1]
        return level, tag, args
    # Standard form: <level> <tag> [args...]
    tag = toks[1]
    args = raw_line.split(maxsplit=2)[2] if len(toks) >= 3 else ''
    return level, tag, args


def validate_gedcom_lines(lines: Iterable[str]):
    """Validate GEDCOM content from an iterable of lines.
    Returns (individuals, families, errors) where errors is a list of ValidationError
    and individuals/families mirror parser()'s data shape.
    """
    individuals: Dict[str, Dict[str, Any]] = {}
    families: Dict[str, Dict[str, Any]] = {}
    errors: List[ValidationError] = []

    current: Optional[Dict[str, Any]] = None
    current_type: Optional[str] = None  # 'INDI' | 'FAM' | None
    date_context: Optional[str] = None  # 'BIRT'|'DEAT'|'MARR'|'DIV'|None

    # Track last line seen for current entity to anchor end-of-entity errors
    current_entity_start_line: int = 0

    def close_entity(end_line: int):
        nonlocal current, current_type, date_context
        # Post-validation for required fields
        if current_type == 'INDI' and current is not None:
            # SEX required and must be M or F
            if current.get('sex') not in ('M', 'F'):
                errors.append(ValidationError(end_line, 'INDI_SEX', 'Individual must have SEX M or F exactly once'))
            # BIRT required and must have a valid DATE
            if not current.get('birth'):
                errors.append(ValidationError(end_line, 'INDI_BIRT', 'Individual must have a birth date (BIRT/DATE)'))
            # DEAT if present must be valid
            if current.get('death') is not None and parseGedDate(current.get('death')) is None:
                errors.append(ValidationError(end_line, 'INDI_DEAT_DATE', 'DEAT must be followed by a valid DATE'))
            # NAME if present must contain /surname/
            nm = current.get('name')
            if nm is not None and ('/' not in nm or nm.count('/') < 2):
                errors.append(ValidationError(end_line, 'INDI_NAME', 'NAME must include surname delimited by slashes, e.g., Mark /Ardis/'))
        elif current_type == 'FAM' and current is not None:
            # MARR required and must have a valid DATE
            if not current.get('married'):
                errors.append(ValidationError(end_line, 'FAM_MARR', 'Family must include MARR with DATE'))
            # DIV if present must be valid
            if current.get('divorced') is not None and parseGedDate(current.get('divorced')) is None:
                errors.append(ValidationError(end_line, 'FAM_DIV_DATE', 'DIV must be followed by a valid DATE'))
        # Reset context
        current = None
        current_type = None
        date_context = None

    last_line_no = 0
    for i, raw in enumerate(lines, start=1):
        last_line_no = i
        line = raw.rstrip('\r\n')
        if not line.strip():
            continue
        level, tag, args = _parse_level_tag_args_raw(line)
        if level is None or tag is None:
            errors.append(ValidationError(i, 'LINE_FORM', 'Invalid line structure: expected <level> <tag> [...]'))
            continue
        if level not in (0, 1, 2):
            errors.append(ValidationError(i, 'LEVEL_RANGE', f'Unsupported level {level}; only 0, 1, 2 are allowed'))
            continue
        if (str(level), tag) not in TAGS:
            errors.append(ValidationError(i, 'TAG', f'Invalid tag {tag!r} at level {level}'))

        if level == 0:
            # Starting a new entity closes the previous one
            if current is not None:
                close_entity(i - 1)
            if tag == 'INDI':
                current_type = 'INDI'
                current = {'id': args, 'name': None, 'sex': None, 'birth': None, 'death': None, 'famc': [], 'fams': []}
                individuals[args] = current
                date_context = None
                current_entity_start_line = i
            elif tag == 'FAM':
                current_type = 'FAM'
                current = {'id': args, 'married': None, 'divorced': None, 'husband': None, 'wife': None, 'children': []}
                families[args] = current
                date_context = None
                current_entity_start_line = i
            else:
                # HEAD/TRLR/NOTE: not an entity container in our model
                current = None
                current_type = None
                date_context = None
        elif level == 1:
            if current is None or current_type not in ('INDI', 'FAM'):
                errors.append(ValidationError(i, 'ORPHAN_L1', 'Level-1 record must be inside an INDI or FAM entity'))
                date_context = None
                continue
            if current_type == 'INDI':
                if tag == 'NAME':
                    current['name'] = args
                    date_context = None
                elif tag == 'SEX':
                    current['sex'] = args
                    date_context = None
                elif tag == 'BIRT':
                    date_context = 'BIRT'
                elif tag == 'DEAT':
                    date_context = 'DEAT'
                elif tag == 'FAMC':
                    current['famc'].append(args)
                    date_context = None
                elif tag == 'FAMS':
                    current['fams'].append(args)
                    date_context = None
                else:
                    date_context = None
            else:  # FAM
                if tag == 'MARR':
                    date_context = 'MARR'
                elif tag == 'DIV':
                    date_context = 'DIV'
                elif tag == 'HUSB':
                    current['husband'] = args
                    date_context = None
                elif tag == 'WIFE':
                    current['wife'] = args
                    date_context = None
                elif tag == 'CHIL':
                    current['children'].append(args)
                    date_context = None
                else:
                    date_context = None
        elif level == 2:
            if tag != 'DATE':
                errors.append(ValidationError(i, 'L2_TAG', 'Only DATE is allowed at level 2'))
                date_context = None
                continue
            if current is None or date_context not in ('BIRT', 'DEAT', 'MARR', 'DIV'):
                errors.append(ValidationError(i, 'DATE_PARENT', 'DATE must immediately follow BIRT, DEAT, MARR, or DIV'))
                date_context = None
                continue
            # Validate and assign the date string
            if parseGedDate(args) is None:
                errors.append(ValidationError(i, 'DATE_FORMAT', f'Invalid date: {args!r}'))
            if current_type == 'INDI':
                if date_context == 'BIRT':
                    current['birth'] = args
                elif date_context == 'DEAT':
                    current['death'] = args
            else:  # FAM
                if date_context == 'MARR':
                    current['married'] = args
                elif date_context == 'DIV':
                    current['divorced'] = args
            date_context = None

    # Close any open entity at EOF
    if current is not None:
        close_entity(last_line_no)

    return individuals, families, errors


def validate_gedcom_file(path: str):
    with open(path, encoding='utf-8') as f:
        return validate_gedcom_lines(f)


if __name__ == '__main__':
    individuals, families = parser('JonesThompsonFamily-1.ged')
    printIndividuals(individuals)
    printFamilies(individuals, families)