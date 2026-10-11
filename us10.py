from gedcom_parser import parseGedDate
 
TWIN_THRESHOLD_DAYS = 1
MIN_MONTHS_APART = 8
 
 
def _months_between(earlier, later):
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)
 
 
def siblings_spacing(individuals, families):
    errors = []
 
    for famId, fam in families.items():
        childIds = fam.get('children', [])
        births = []
 
        for childId in childIds:
            if childId not in individuals:
                continue
            birth = parseGedDate(individuals[childId].get('birth'))
            if birth is None:
                continue
            births.append((childId, birth))
 
        births.sort(key=lambda x: x[1])
 
        for i in range(len(births)):
            for j in range(i + 1, len(births)):
                id1, date1 = births[i]
                id2, date2 = births[j]
 
                days_apart = abs((date2 - date1).days)
                months_apart = _months_between(date1, date2)
 
                if days_apart > TWIN_THRESHOLD_DAYS and months_apart <= MIN_MONTHS_APART:
                    errors.append(
                        f"ERROR: FAMILY: US10: {famId}: Siblings {id1} and "
                        f"{id2} are born {days_apart} days apart "
                        f"(must be more than 8 months apart or within 1 day)"
                    )
 
    return errors