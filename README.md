# SSW555_Group6
Alice Krauze, Connor Tierney, Kent Berry, Kieran Corson, Timothy Ahern

GEDCOM SUBSET — FORMAT SPECIFICATION

SCOPE
- This project uses a limited subset of GEDCOM, not the full GEDCOM standard.
- The file describes two top-level entity types:
    - Individuals
    - Families

LEVEL-0 RECORD FORMS
- A level-0 individual or family definition has this form:
  0 <ID> INDI
  0 <ID> FAM
- In those records:
    - <ID> is between the level number and the tag.
    - <ID> is the unique identifier of the new individual or family.
- A level-0 metadata/comment record has this form:
  0 <TAG> [arguments]
- Allowed metadata/comment tags:
    - HEAD
    - TRLR
    - NOTE
- HEAD and TRLR take no meaningful argument.
- NOTE may contain any string; its content can be ignored by the parser if not needed.

IDENTIFIERS
- Individual IDs and family IDs are arbitrary strings.
- Do NOT assume IDs follow a pattern such as I01, F23, numeric-only, or any particular prefix.
- IDs can reference records that have not yet appeared in the file; forward references are allowed.
- Individual IDs identify INDI records.
- Family IDs identify FAM records.

RECORD GROUPING AND HIERARCHY
- A level-0 INDI record begins an individual definition.
- A level-0 FAM record begins a family definition.
- All later records with level greater than 0 belong to the most recent level-0 entity, until the next level-0 record or end of file.
- An entity definition ends when:
    - another level-0 record begins, or
    - end of file is reached.
- A level-2 DATE record belongs to the immediately preceding applicable level-1 event record.
- DATE is valid only as a child of BIRT, DEAT, MARR, or DIV.

ALLOWED TOP-LEVEL RECORDS
1. Individual:
   0 <Individual_ID> INDI

2. Family:
   0 <Family_ID> FAM

3. Optional header:
   0 HEAD

4. Optional trailer:
   0 TRLR

5. Optional comment:
   0 NOTE <any string>

INDIVIDUAL RECORD FORMAT
An individual begins with:
0 <Individual_ID> INDI

Allowed level-1 records inside an individual:
1 NAME <name>
1 SEX <M-or-F>
1 BIRT
1 DEAT
1 FAMC <Family_ID>
1 FAMS <Family_ID>

INDIVIDUAL FIELD RULES
- NAME:
    - Form:
      1 NAME <string containing surname>
    - The surname must be delimited by slash characters.
    - Example:
      1 NAME Mark /Ardis/
    - The name value can contain spaces.

- SEX:
    - Form:
      1 SEX M
      or
      1 SEX F
    - Only M and F are allowed values in this project subset.
    - The sex of every individual is specified exactly once.

- BIRT:
    - Form:
      1 BIRT
      2 DATE <day> <month> <year>
    - BIRT has no argument on its own line.
    - Each individual has exactly one birth date.
    - BIRT must be followed by its DATE record.

- DEAT:
    - Form:
      1 DEAT
      2 DATE <day> <month> <year>
    - DEAT has no argument on its own line.
    - A death record is optional.
    - If DEAT is absent, treat the individual as alive.
    - If present, DEAT must be followed by its DATE record.

- FAMC:
    - Form:
      1 FAMC <Family_ID>
    - Means the individual is a child in the specified family.
    - An individual is linked to every family in which they are a child, for every such family described in the file.

- FAMS:
    - Form:
      1 FAMS <Family_ID>
    - Means the individual is a spouse in the specified family.
    - An individual is linked to every family in which they are a spouse, for every such family described in the file.

FAMILY RECORD FORMAT
A family begins with:
0 <Family_ID> FAM

Allowed level-1 records inside a family:
1 MARR
1 HUSB <Individual_ID>
1 WIFE <Individual_ID>
1 CHIL <Individual_ID>
1 DIV

FAMILY FIELD RULES
- MARR:
    - Form:
      1 MARR
      2 DATE <day> <month> <year>
    - MARR has no argument on its own line.
    - Every specified family includes a marriage record and marriage date.
    - MARR must be followed by its DATE record.

- HUSB:
    - Form:
      1 HUSB <Individual_ID>
    - Identifies the husband in the family.

- WIFE:
    - Form:
      1 WIFE <Individual_ID>
    - Identifies the wife in the family.

- CHIL:
    - Form:
      1 CHIL <Individual_ID>
    - Identifies a child in the family.
    - Multiple CHIL records are allowed, one per child.

- DIV:
    - Form:
      1 DIV
      2 DATE <day> <month> <year>
    - DIV has no argument on its own line.
    - Divorce is optional.
    - If DIV is absent, treat the marriage as not divorced.
    - If present, DIV must be followed by its DATE record.

DATE RECORD FORMAT
- DATE is allowed only at level 2.
- DATE is allowed only immediately after one of:
    - 1 BIRT
    - 1 DEAT
    - 1 MARR
    - 1 DIV
- Form:
  2 DATE <day> <month> <year>

DATE RULES
- Date format is exactly:
  <day> <month> <year>
- The three date fields are separated by one space.
- Day:
    - Day of the month.
    - No leading zero.
    - Examples: 1, 2, 15, 31.
    - Not allowed: 01, 02, 015.
- Month:
    - Exactly one of:
      JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC
    - Uppercase three-character abbreviation.
- Year:
    - Exactly four digits.
    - Example: 2010.
- Valid example:
  2 DATE 7 APR 1949
- Invalid for this project format:
  2 DATE 07 APR 1949
  2 DATE 7 April 1949
  2 DATE 1949-04-07
  2 DATE APR 7 1949
  2 DATE 7 APR 49