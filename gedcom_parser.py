from datetime import date
from xml.parsers.expat import errors
import calendar

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
        try:
            return date(year, MONTHS[mon_str], day)
        except ValueError:
            return None
    elif len(parts) == 2:
        mon_str, year_str = parts
        if mon_str not in MONTHS:
            return None
        try:
            year = int(year_str)
        except ValueError:
            return None
        # Default to first day of the month
        try:
            return date(year, MONTHS[mon_str], 1)
        except ValueError:
            return None
    elif len(parts) == 1:
        year_str = parts[0]
        try:
            year = int(year_str)
        except ValueError:
            return None
        # Default to Jan 1st for year-only
        try:
            return date(year, 1, 1)
        except ValueError:
            return None
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

MAX_LIFESPAN_YEARS = 150


def _validate_individual_lifespan(individual, end_line, errors):
    birth_raw = individual.get('birth')
    if not birth_raw:
        return
    birth_dt = parseGedDate(birth_raw)
    if birth_dt is None:
        return
    death_raw = individual.get('death')
    if death_raw is not None:
        death_dt = parseGedDate(death_raw)
        if death_dt is None:
            return
        if death_dt < birth_dt:
            errors.append(ValidationError(
                end_line, 'INDI_LIFESPAN',
                'Birth must occur before death'))
            return
        age = ageYears(birth_dt, death_dt)
    else:
        age = ageYears(birth_dt, date.today())
    if age > MAX_LIFESPAN_YEARS:
        errors.append(ValidationError(
            end_line, 'INDI_LIFESPAN',
            f'Individual age cannot exceed {MAX_LIFESPAN_YEARS} years'))

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


def _validate_event_dates_not_after_today(entity, end_line, errors, field_names):
    today = date.today()
    for name in field_names:
        raw = entity.get(name)
        if raw is None:
            continue
        parsed = parseGedDate(raw)
        if parsed is not None and parsed > today:
            errors.append(ValidationError(
                end_line, 'DATE_FUTURE',
                'Date must not be after the current date'))


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


# Which kind of record each reference tag must point to
REF_TARGET_TYPE = {'HUSB': 'INDI', 'WIFE': 'INDI', 'CHIL': 'INDI',
                   'FAMC': 'FAM', 'FAMS': 'FAM'}


def _validate_references(references, individuals, families, errors):
    """US38: every referenced individual and family ID must exist."""
    for line_no, owner_id, tag, target_id in references:
        pool = individuals if REF_TARGET_TYPE[tag] == 'INDI' else families
        if target_id not in pool:
            errors.append(ValidationError(
                line_no, 'REF_MISSING',
                f'{tag} {target_id} in {owner_id} does not refer to an existing record'))


def _validate_no_duplicate_references(references, errors):
    """US41: the same reference should not appear twice in one record."""
    seen = set()
    for line_no, owner_id, tag, target_id in references:
        key = (owner_id, tag, target_id)
        if key in seen:
            errors.append(ValidationError(
                line_no, 'REF_DUPLICATE',
                f'Duplicate {tag} {target_id} in {owner_id}'))
        else:
            seen.add(key)

def _validate_corresponding_references(references, individuals, families, errors):
    for line_no, owner_id, tag, target_id in references:

        if tag == 'FAMC':
            family = families.get(target_id)
            if family is not None and owner_id not in family.get('children', []):
                errors.append(
                    ValidationError(
                        line_no,
                        'REF_MISMATCH',
                        f'FAMC {target_id} in {owner_id} does not correspond to CHIL {owner_id} in {target_id}'
                    )
                )

        elif tag == 'FAMS':
            family = families.get(target_id)
            if family is not None and owner_id not in (
                family.get('husband'),
                family.get('wife')
            ):
                errors.append(
                    ValidationError(
                        line_no,
                        'REF_MISMATCH',
                        f'FAMS {target_id} in {owner_id} does not correspond to HUSB/WIFE {owner_id} in {target_id}'
                    )
                )

        elif tag == 'CHIL':
            individual = individuals.get(target_id)
            if individual is not None and owner_id not in individual.get('famc', []):
                errors.append(
                    ValidationError(
                        line_no,
                        'REF_MISMATCH',
                        f'CHIL {target_id} in {owner_id} does not correspond to FAMC {owner_id} in {target_id}'
                    )
                )

        elif tag in ('HUSB', 'WIFE'):
            individual = individuals.get(target_id)
            if individual is not None and owner_id not in individual.get('fams', []):
                errors.append(
                    ValidationError(
                        line_no,
                        'REF_MISMATCH',
                        f'{tag} {target_id} in {owner_id} does not correspond to FAMS {owner_id} in {target_id}'
                    )
                )
def validate_gedcom_lines(lines: Iterable[str]):
    """Validate GEDCOM content from an iterable of lines.
    Returns (individuals, families, errors) where errors is a list of ValidationError
    and individuals/families mirror parser()'s data shape.
    """
    individuals: Dict[str, Dict[str, Any]] = {}
    families: Dict[str, Dict[str, Any]] = {}
    errors: List[ValidationError] = []
    # Every HUSB/WIFE/CHIL/FAMC/FAMS seen, as (line_no, owner_id, tag, target_id).
    # Checked after the whole file is read (US38, US41).
    references: List[Tuple[int, str, str, str]] = []

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
            _validate_event_dates_not_after_today(
                current, end_line, errors, ('birth', 'death'))
            _validate_individual_lifespan(current, end_line, errors)
        elif current_type == 'FAM' and current is not None:
            # MARR required and must have a valid DATE
            if not current.get('married'):
                errors.append(ValidationError(end_line, 'FAM_MARR', 'Family must include MARR with DATE'))
            # DIV if present must be valid
            if current.get('divorced') is not None and parseGedDate(current.get('divorced')) is None:
                errors.append(ValidationError(end_line, 'FAM_DIV_DATE', 'DIV must be followed by a valid DATE'))
            _validate_event_dates_not_after_today(
                current, end_line, errors, ('married', 'divorced'))
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
                current = {'id': args, 'name': None, 'sex': None, 'birth': None, 'death': None, 'famc': [], 'fams': [], 'line': i}
                #US 18 edit
                if args in individuals:
                    errors.append(ValidationError(i, 'US18', f'Duplicate individual ID {args!r}'))
                else:
                    individuals[args] = current
                date_context = None
                current_entity_start_line = i
            elif tag == 'FAM':
                current_type = 'FAM'
                current = {'id': args, 'married': None, 'divorced': None, 'husband': None, 'wife': None, 'children': [], 'line': i}
                
                if args in families:
                    errors.append(ValidationError(i, 'US18', f'Duplicate family ID {args!r}'))
                else:
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
                    references.append((i, current['id'], tag, args))
                    date_context = None
                elif tag == 'FAMS':
                    current['fams'].append(args)
                    references.append((i, current['id'], tag, args))
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
                    references.append((i, current['id'], tag, args))
                    date_context = None
                elif tag == 'WIFE':
                    current['wife'] = args
                    references.append((i, current['id'], tag, args))
                    date_context = None
                elif tag == 'CHIL':
                    current['children'].append(args)
                    references.append((i, current['id'], tag, args))
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
            parsed = parseGedDate(args)
            if parsed is None:
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

    #us19 
    _validate_references(references, individuals, families, errors)
    _validate_no_duplicate_references(references, errors)
    _validate_corresponding_references(references, individuals, families, errors)
    errors.extend(check_unique_name_and_birth(individuals))
    errors.extend(check_multiple_births(individuals, families))
    errors.extend(check_sibling_count(individuals, families))
    errors.extend(check_birth_before_parents_death(individuals, families))
    errors.extend(check_marriage_before_death(individuals, families))
    errors.extend(check_birth_after_parents_marriage(individuals, families))
    errors.extend(check_age_at_marriage(individuals, families))
    errors.extend(check_marriage_divorce_death_order(individuals, families))
    errors.extend(check_no_bigamy(individuals, families))
    errors.extend(check_aunt_uncle_marriages(individuals, families))
    return individuals, families, errors

#us 19
def check_unique_name_and_birth(individuals):
    errors = []
    seen = {}
    for indi_id, p in individuals.items():
        if not p.get('name') or not p.get('birth'):
            continue
        key = (p['name'].strip().lower(), parseGedDate(p['birth']) or p['birth'])
        if key in seen:
            errors.append(ValidationError(p.get('line', 0), 'US19',
                f"Individual {displayId(indi_id)} has the same name and birth date as "
                f"{displayId(seen[key])}: {p['name']}, {formatGedDate(p['birth'])}"))
        else:
            seen[key] = indi_id
    return errors

def _add_months(d, months):
    """Returns date d plus the number of months passed in months"""
    month_index=d.month-1+months
    year=d.year+month_index//12
    month=month_index%12+1
    last_day=calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day,last_day))

# US05
def check_marriage_before_death(individuals, families):
    """Marriage should occur before death of either spouse."""
    errors = []
    for fam_id, fam in families.items():
        married = parseGedDate(fam.get('married'))
        if married is None:
            continue
        for role in ('husband', 'wife'):
            spouse_id = fam.get(role)
            spouse = individuals.get(spouse_id) if spouse_id else None
            if spouse is None:
                continue
            death = parseGedDate(spouse.get('death'))
            if death is not None and married > death:
                errors.append(ValidationError(fam.get('line', 0), 'US05',
                    f"Family {displayId(fam_id)} married {married.isoformat()} after "
                    f"{role} {displayId(spouse_id)} died {death.isoformat()}"))
    return errors


# US06
def check_birth_after_parents_marriage(individuals, families):
    """Children should be born after their parents' marriage and
    no more than 9 months after their divorce."""
    errors = []
    for fam_id, fam in families.items():
        married = parseGedDate(fam.get('married'))
        divorced = parseGedDate(fam.get('divorced'))
        for child_id in fam.get('children', []):
            child = individuals.get(child_id)
            if child is None:
                continue
            birth = parseGedDate(child.get('birth'))
            if birth is None:
                continue
            if married is not None and birth < married:
                errors.append(ValidationError(child.get('line', 0), 'US06',
                    f"Child {displayId(child_id)} born {birth.isoformat()} before parents' "
                    f"marriage {married.isoformat()} in family {displayId(fam_id)}"))
            if divorced is not None and birth > _add_months(divorced, 9):
                errors.append(ValidationError(child.get('line', 0), 'US06',
                    f"Child {displayId(child_id)} born {birth.isoformat()} more than 9 months "
                    f"after parents' divorce {divorced.isoformat()} in family {displayId(fam_id)}"))
    return errors

# US09 - Birth before death of parents
# - Child should be born before death of mother
# - Child should be born no more than 9 months after death of father

def check_birth_before_parents_death(individuals, families):
    errors = []
    NINE_MONTHS_IN_DAYS = 272  # approximate 9 months

    for fam_id, fam in families.items():
        mother_id = fam.get('wife')
        father_id = fam.get('husband')
        children = fam.get('children', []) or []

        mother = individuals.get(mother_id) if mother_id else None
        father = individuals.get(father_id) if father_id else None

        mother_death = parseGedDate(mother.get('death')) if mother and mother.get('death') else None
        father_death = parseGedDate(father.get('death')) if father and father.get('death') else None

        for child_id in children:
            child = individuals.get(child_id)
            if not child:
                continue
            child_birth = parseGedDate(child.get('birth')) if child.get('birth') else None
            if not child_birth:
                continue  # cannot validate without child birth

            # Check against mother's death: child must be born strictly before mother's death
            if mother_death is not None and child_birth >= mother_death:
                errors.append(ValidationError(
                    fam.get('line', 0), 'US09',
                    f"Child {displayId(child_id)} born {child_birth.isoformat()} is not before mother's death "
                    f"({displayId(mother_id)}: {formatGedDate(mother.get('death'))}) in family {displayId(fam_id)}"))

            # Check against father's death: child must be born no more than 9 months after father's death
            if father_death is not None:
                # Compute threshold = father_death + 272 days
                try:
                    from datetime import timedelta
                    threshold = father_death.toordinal() + NINE_MONTHS_IN_DAYS
                    # Convert back to date for comparison
                    threshold_date = date.fromordinal(threshold)
                except Exception:
                    threshold_date = None
                if threshold_date is not None and child_birth > threshold_date:
                    errors.append(ValidationError(
                        fam.get('line', 0), 'US09',
                        f"Child {displayId(child_id)} born {child_birth.isoformat()} is more than 9 months after father's death "
                        f"({displayId(father_id)}: {formatGedDate(father.get('death'))}) in family {displayId(fam_id)}"))

    return errors

MIN_MARRIAGE_AGE_YEARS = 14


def _iter_spouses(family):
    husband_id = family.get('husband')
    if husband_id:
        yield 'Husband', husband_id
    wife_id = family.get('wife')
    if wife_id:
        yield 'Wife', wife_id


def _person_event_date(individuals, person_id, field):
    person = individuals.get(person_id)
    if person is None:
        return None
    raw = person.get(field)
    if not raw:
        return None
    return parseGedDate(raw)


def check_age_at_marriage(individuals, families):
    errors = []
    for fam in families.values():
        married_raw = fam.get('married')
        married_dt = parseGedDate(married_raw) if married_raw else None
        if married_dt is None:
            continue
        line_no = fam.get('line', 0)
        fam_label = displayId(fam.get('id', ''))
        for role, spouse_id in _iter_spouses(fam):
            birth_dt = _person_event_date(individuals, spouse_id, 'birth')
            if birth_dt is None:
                continue
            spouse_label = displayId(spouse_id)
            if birth_dt >= married_dt:
                errors.append(ValidationError(
                    line_no, 'US02',
                    f'{role} {spouse_label} in {fam_label} must be born before marriage'))
                continue
            if ageYears(birth_dt, married_dt) < MIN_MARRIAGE_AGE_YEARS:
                errors.append(ValidationError(
                    line_no, 'US02',
                    f'{role} {spouse_label} in {fam_label} must be at least '
                    f'{MIN_MARRIAGE_AGE_YEARS} years old at marriage'))
    return errors


def check_marriage_divorce_death_order(individuals, families):
    errors = []
    for fam in families.values():
        divorced_raw = fam.get('divorced')
        if not divorced_raw:
            continue
        divorced_dt = parseGedDate(divorced_raw)
        if divorced_dt is None:
            continue
        line_no = fam.get('line', 0)
        fam_label = displayId(fam.get('id', ''))
        married_raw = fam.get('married')
        married_dt = parseGedDate(married_raw) if married_raw else None
        if married_dt is not None and married_dt >= divorced_dt:
            errors.append(ValidationError(
                line_no, 'US04',
                f'Marriage in {fam_label} must occur before divorce'))
        for role, spouse_id in _iter_spouses(fam):
            death_dt = _person_event_date(individuals, spouse_id, 'death')
            if death_dt is None:
                continue
            if divorced_dt >= death_dt:
                errors.append(ValidationError(
                    line_no, 'US04',
                    f'Divorce in {fam_label} must occur before '
                    f'{role.lower()} {displayId(spouse_id)} death'))
    return errors


# US08 - No bigamy: Marriage should not occur during marriage to another spouse
# Implementation notes:
# - For each individual, we gather all marriage intervals from their FAM records.
# - Interval start: family['married'] date (required for consideration). If missing, we skip the interval.
# - Interval end: earliest of family['divorced'], spouse death, or self death. If none known, it's open-ended (None).
# - We then perform a simple O(n^2) pairwise overlap check among intervals for that person.
# - If two intervals overlap, we report a ValidationError with code 'US08'.

def check_no_bigamy(individuals, families):
    errors = []

    def _fam_interval_for_person(person_id, fam):
        # Build interval for this person within given family
        married_raw = fam.get('married')
        start = parseGedDate(married_raw) if married_raw else None
        if start is None:
            return None  # cannot form interval without a start date
        # Identify spouse and compute end date as earliest of divorce, spouse death, or self death
        end_candidates = []
        # Divorce
        div_raw = fam.get('divorced')
        if div_raw:
            div_dt = parseGedDate(div_raw)
            if div_dt:
                end_candidates.append(div_dt)
        # Determine spouse and their death
        spouse_id = None
        if fam.get('husband') == person_id:
            spouse_id = fam.get('wife')
        elif fam.get('wife') == person_id:
            spouse_id = fam.get('husband')
        # Self death
        self_death = _person_event_date(individuals, person_id, 'death')
        if self_death is not None:
            end_candidates.append(self_death)
        # Spouse death
        if spouse_id:
            spouse_death = _person_event_date(individuals, spouse_id, 'death')
            if spouse_death is not None:
                end_candidates.append(spouse_death)
        end = min(end_candidates) if end_candidates else None
        return (start, end)

    # Build intervals per person (refactored to avoid duplication)
    intervals_by_person = {}
    for fam in families.values():
        for _, person_id in _iter_spouses(fam):
            interval = _fam_interval_for_person(person_id, fam)
            if interval is None:
                continue
            start, end = interval
            intervals_by_person.setdefault(person_id, []).append((fam, start, end))

    # Check overlaps per person using sort-and-scan (O(n log n))
    for person_id, intervals in intervals_by_person.items():
        intervals.sort(key=lambda x: (x[1] or date.min, x[2] or date.max))
        prev = None  # (fam, start, end)
        for current in intervals:
            fam_c, s_c, e_c = current
            if s_c is None:
                continue
            if prev is None:
                prev = current
                continue
            fam_p, s_p, e_p = prev
            # Overlap if current start is before or equal to previous end (or previous end is open)
            if e_p is None or s_c <= e_p:
                line_no = max(fam_p.get('line', 0), fam_c.get('line', 0))
                p_label = displayId(person_id)
                f1 = displayId(fam_p.get('id', ''))
                f2 = displayId(fam_c.get('id', ''))
                def fmt(dt):
                    return dt.isoformat() if dt else 'NA'
                msg = (f"Individual {p_label} has overlapping marriages between families "
                       f"{f1} [{fmt(s_p)} - {fmt(e_p)}] and {f2} [{fmt(s_c)} - {fmt(e_c)}]")
                errors.append(ValidationError(line_no, 'US08', msg))
                # Merge intervals to continue scanning
                # Extend previous interval to cover the furthest end to catch chains of overlaps
                if e_p is None or (e_c is not None and e_c > e_p):
                    prev = (fam_p, s_p, e_c)
                # else keep prev as is
            else:
                prev = current
    return errors

def validate_gedcom_file(path: str):
    with open(path, encoding='utf-8') as f:
        return validate_gedcom_lines(f)

#us11

def check_multiple_births(individuals, families):
    errors = []

    for family in families.values():
        birth_dates = {}

        for child_id in family['children']:
            if child_id in individuals:
                birth_date = individuals[child_id]['birth']

                if birth_date:
                    birth_dates[birth_date] = birth_dates.get(birth_date, 0) + 1

        for birth_date, count in birth_dates.items():
            if count > 5:
                errors.append(
                    ValidationError(
                        family['line'],
                        'US11',
                        f"Family {family['id']} has more than 5 children born on {birth_date}"
                    )
                )

    return errors

#us12

def check_sibling_count(individuals, families):
    errors = []

    for family in families.values():
        if len(family['children']) >= 15:
            errors.append(
                ValidationError(
                    family['line'],
                    'US12',
                    f"Family {family['id']} has 15 or more children"
                )
            )

    return errors


def check_aunt_uncle_marriages(individuals, families):
    """US17: Aunts and uncles should not marry their nieces or nephews.
    Identify if any marriage is between an individual and their aunt/uncle.
    """
    errors = []

    # Build parents mapping: child_id -> set of parent_ids
    parents_of = {}
    children_of_fam = {}
    for fam in families.values():
        husb = fam.get('husband')
        wife = fam.get('wife')
        children = fam.get('children', []) or []
        children_of_fam[fam.get('id')] = set(children)
        for child in children:
            pset = parents_of.setdefault(child, set())
            if husb:
                pset.add(husb)
            if wife:
                pset.add(wife)

    # Build siblings mapping via shared family children lists
    siblings_of = {iid: set() for iid in individuals.keys()}
    for fam in families.values():
        kids = fam.get('children', []) or []
        kidset = set(kids)
        for kid in kids:
            siblings_of.setdefault(kid, set()).update(kidset - {kid})

    # Precompute aunts/uncles for each individual: siblings of each parent
    aunts_uncles_of = {iid: set() for iid in individuals.keys()}
    for person_id in individuals.keys():
        au = aunts_uncles_of.setdefault(person_id, set())
        for parent in parents_of.get(person_id, set()):
            au.update(siblings_of.get(parent, set()))

    # Check each family marriage for aunt/uncle relation between spouses
    for fam in families.values():
        husb = fam.get('husband')
        wife = fam.get('wife')
        if not husb or not wife:
            continue
        # If either spouse is an aunt/uncle of the other, flag
        if husb in aunts_uncles_of.get(wife, set()) or wife in aunts_uncles_of.get(husb, set()):
            h_label = displayId(husb)
            w_label = displayId(wife)
            f_label = displayId(fam.get('id', ''))
            errors.append(
                ValidationError(
                    fam.get('line', 0) or 0,
                    'US17',
                    f"Family {f_label} has an invalid marriage between aunt/uncle {h_label} and niece/nephew {w_label}"
                )
            )
    return errors


def compute_siblings_by_age(individuals, families):
    """US24: Order siblings by age (oldest first) for each family.
    Returns a dict mapping family_id -> list of child_ids ordered by decreasing age.

    Ordering rules:
    - Oldest first (earliest birth date first).
    - Unknown or invalid birth dates are placed at the end.
    - Ties (same birth date) are broken by ascending displayId(child_id) for determinism.
    """
    from datetime import date as _date

    def _child_sort_key(child_id: str):
        indi = individuals.get(child_id, {})
        b_raw = indi.get('birth')
        b = parseGedDate(b_raw) if b_raw else None
        # Unknown birth: send to the end (use date.max)
        b_key = b if b is not None else _date.max
        return (b_key, displayId(child_id))

    ordered = {}
    for fam_id, fam in families.items():
        kids = list(fam.get('children', []) or [])
        kids.sort(key=_child_sort_key)
        ordered[fam_id] = kids
    return ordered


if __name__ == '__main__':
    individuals, families = parser('JonesThompsonFamily-1.ged')
    printIndividuals(individuals)
    printFamilies(individuals, families)
