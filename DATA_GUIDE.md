# Fee Database Guide

`fee_database.json` controls every dropdown and calculation in the app.

## Where To Edit

- `categories`: admission category, course, branch, currency, and tuition fee.
- `hostel.rooms`: room names and hostel rent.
- `hostel.mess_options`: mess choice and utility deposit.
- `scholarships`: scholarship type, allowed student groups, and percentages.

## Fee Formula

For lump sum:

```text
lump sum fee x (1 - scholarship percentage / 100)
+ hostel rent, if hosteller
+ mess and utility deposit, if hosteller
```

For installments:

```text
1st semester = 1st installment x (1 - scholarship percentage / 100)
             + hostel rent, if hosteller
             + mess and utility deposit, if hosteller

2nd semester = 2nd installment x (1 - scholarship percentage / 100)
```

## Validate After Editing

Run:

```powershell
.\.venv\Scripts\python scripts\validate_database.py
```

If you are using the bundled Codex Python in this workspace, run:

```powershell
& 'C:\Users\sarth\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\validate_database.py
```

Warnings mean a value is still `0`; errors mean the JSON structure needs fixing.
