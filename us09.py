from gedcom_parser import parseGedDate, ageYears


#CODED VIA PAIR PROGRAMMING WITH KENT BERRY AND TIMOTHY AHERN

MOTHER_LIMIT = 60
FATHER_LIMIT = 80
 
 
def parents_not_too_old(individuals, families):
    errors = []
 
    for famId, fam in families.items():
        for role, limit in (('wife', MOTHER_LIMIT), ('husband', FATHER_LIMIT)):
            parentId = fam.get(role)
            if not parentId or parentId not in individuals:
                continue
 
            parentBirth = parseGedDate(individuals[parentId].get('birth'))
            if parentBirth is None:
                continue
 
            for childId in fam.get('children', []):
                if childId not in individuals:
                    continue
 
                childBirth = parseGedDate(individuals[childId].get('birth'))
                if childBirth is None:
                    continue
 
                gap = ageYears(parentBirth, childBirth)
                if gap >= limit:
                    label = 'Mother' if role == 'wife' else 'Father'
                    errors.append(
                        f"ERROR: FAMILY: US09: {famId}: {label} {parentId} is "
                        f"{gap} years older than child {childId} "
                        f"(must be less than {limit})"
                    )
 
    return errors
 