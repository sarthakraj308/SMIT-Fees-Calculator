# Fee Calculator

A Flask-based fee calculator that uses `fee_database.json` as the single editable
source of truth for categories, courses, branches, hostel charges, mess charges,
and scholarships.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Open `http://127.0.0.1:5000`.

## Data

Edit `fee_database.json` to replace the sample fee values with the exact values
from your PDF. The application reads this file on every request, so you can edit
the JSON and refresh the browser.

After editing, validate the database:

```powershell
python scripts\validate_database.py
```

See `DATA_GUIDE.md` for the JSON structure and fee formula.
