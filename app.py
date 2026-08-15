from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "fee_database.json"

app = Flask(__name__)
app.json.sort_keys = False


def load_database() -> dict[str, Any]:
    with DATABASE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def money(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def format_indian_number(value: float) -> str:
    whole, dot, fraction = f"{value:.2f}".partition(".")
    sign = ""
    if whole.startswith("-"):
        sign = "-"
        whole = whole[1:]
    if len(whole) <= 3:
        grouped = whole
    else:
        grouped = whole[-3:]
        remaining = whole[:-3]
        while remaining:
            grouped = f"{remaining[-2:]},{grouped}"
            remaining = remaining[:-2]
    return f"{sign}{grouped}{dot}{fraction}"


def format_amount(value: Any, currency: str) -> str:
    amount = money(value)
    if currency == "INR":
        return f"₹{format_indian_number(amount)}"
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f}"


def find_branch(db: dict[str, Any], category_id: str, course_id: str, branch_id: str) -> dict[str, Any] | None:
    category = db["categories"].get(category_id)
    if not category:
        return None
    course = category.get("courses", {}).get(course_id)
    if not course:
        return None
    return course.get("branches", {}).get(branch_id)


def label_for(options: dict[str, Any], key: str | None, fallback: str = "Not applicable") -> str:
    if not key:
        return fallback
    return options.get(key, {}).get("label", fallback)


def scholarship_applies(scholarship: dict[str, Any], group: str) -> bool:
    groups = scholarship.get("groups", [])
    return "all" in groups or group in groups


def hostel_charge(db: dict[str, Any], student_type: str, room_id: str | None, mess_option: str | None) -> dict[str, float]:
    if student_type != "hosteller":
        return {"hostel_rent": 0.0, "mess_and_utility_deposit": 0.0}

    room = db["hostel"]["rooms"].get(room_id, {})
    mess = db["hostel"]["mess_options"].get(mess_option, {})
    return {
        "hostel_rent": money(room.get("rent")),
        "mess_and_utility_deposit": money(mess.get("mess_and_utility_deposit")),
    }


@app.template_filter("currency_amount")
def currency_amount(value: Any, currency: str) -> str:
    return format_amount(value, currency)


def calculate_fee(payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    db = load_database()
    category_id = payload.get("category")
    course_id = payload.get("course")
    branch_id = payload.get("branch")
    payment_mode = payload.get("payment_mode")
    student_type = payload.get("student_type")
    room_id = payload.get("room_category")
    mess_option = payload.get("mess_option")
    scholarship_type = payload.get("scholarship_type") or "none"
    scholarship_percent = money(payload.get("scholarship_percent"))

    category = db["categories"].get(category_id)
    course = category.get("courses", {}).get(course_id) if category else None
    branch = find_branch(db, category_id, course_id, branch_id)
    scholarship = db["scholarships"].get(scholarship_type)
    if not category or not course or not branch:
        return {"error": "Invalid category, course, or branch selection."}, 400
    if student_type == "hosteller" and (not room_id or not mess_option):
        return {"error": "Room category and mess choice are required for hostellers."}, 400
    if not scholarship:
        return {"error": "Invalid scholarship selection."}, 400
    if scholarship_percent not in [money(percent) for percent in scholarship.get("percentages", [])]:
        return {"error": "Invalid scholarship percentage for the selected scholarship."}, 400
    if scholarship_type != "none" and not scholarship_applies(scholarship, branch.get("scholarship_group", "")):
        return {"error": "Selected scholarship is not applicable for this course and branch."}, 400

    fees = branch["fees"]
    currency = branch.get("currency") or category.get("currency", "INR")
    hostel = hostel_charge(db, student_type, room_id, mess_option)
    selected = {
        "category": category["label"],
        "course": course["label"],
        "branch": branch["label"],
        "student_type": "Hosteller" if student_type == "hosteller" else "Day-Scholar",
        "room_category": label_for(db["hostel"]["rooms"], room_id),
        "mess": label_for(db["hostel"]["mess_options"], mess_option),
        "scholarship": scholarship["label"],
    }

    if payment_mode == "lumpsum":
        base_fee = money(fees.get("lumpsum"))
        course_fee = base_fee * (1 - scholarship_percent / 100)
        total = course_fee + hostel["hostel_rent"] + hostel["mess_and_utility_deposit"]
        result = {
            "currency": currency,
            "payment_mode": "Lump Sum",
            "selected": selected,
            "scholarship_percent": scholarship_percent,
            "base_fee": base_fee,
            "items": [
                {"label": "Course fee before scholarship", "amount": base_fee, "muted": True},
                {"label": "Course fee after scholarship", "amount": course_fee},
                {"label": "Hostel rent", "amount": hostel["hostel_rent"]},
                {"label": "Mess and utility deposit", "amount": hostel["mess_and_utility_deposit"]},
            ],
            "total": total,
        }
        return result, 200

    if payment_mode == "installments":
        first_base = money(fees.get("first_installment"))
        second_base = money(fees.get("second_installment"))
        first_sem = first_base * (1 - scholarship_percent / 100)
        second_sem = second_base * (1 - scholarship_percent / 100)
        first_sem_total = first_sem + hostel["hostel_rent"] + hostel["mess_and_utility_deposit"]
        return {
            "currency": currency,
            "payment_mode": "Installments",
            "selected": selected,
            "scholarship_percent": scholarship_percent,
            "base_fee": first_base + second_base,
            "first_semester": {
                "items": [
                    {"label": "1st installment before scholarship", "amount": first_base, "muted": True},
                    {"label": "1st installment after scholarship", "amount": first_sem},
                    {"label": "Hostel rent", "amount": hostel["hostel_rent"]},
                    {"label": "Mess and utility deposit", "amount": hostel["mess_and_utility_deposit"]},
                ],
                "total": first_sem_total,
            },
            "second_semester": {
                "items": [
                    {"label": "2nd installment before scholarship", "amount": second_base, "muted": True},
                    {"label": "2nd installment after scholarship", "amount": second_sem},
                ],
                "total": second_sem,
            },
            "total": first_sem_total + second_sem,
        }, 200

    return {"error": "Invalid payment mode."}, 400


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/result")
def result():
    result_data, status = calculate_fee(request.form.to_dict())
    if status != 200:
        return render_template("index.html", error=result_data["error"]), status
    return render_template("result.html", result=result_data)


@app.get("/api/database")
def database():
    db = load_database()
    return jsonify(db)


@app.post("/api/calculate")
def calculate():
    result, status = calculate_fee(request.get_json(force=True))
    return jsonify(result), status


if __name__ == "__main__":
    app.run(debug=True)
