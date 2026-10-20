
from flask import Flask, render_template, request
from datetime import date
import json
import os

app = Flask(__name__)

RATE = 6
DATA_FILE = "readings.json"
MONTHLY_LIMIT = 200


def load_readings():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return []


def save_readings(records):
    with open(DATA_FILE, "w") as file:
        json.dump(records, file, indent=4)


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    message_type = "success"
    records = load_readings()

    if request.method == "POST":
        reading_date = request.form.get("reading_date")
        meter_reading = request.form.get("meter_reading")

        try:
            reading_value = float(meter_reading)

            if reading_value < 0 or not reading_date:
                raise ValueError

            existing = next(
                (r for r in records if r["date"] == reading_date),
                None
            )

            if existing:
                existing["reading"] = reading_value
            else:
                records.append({
                    "date": reading_date,
                    "reading": reading_value,
                    "usage": 0
                })

            records.sort(key=lambda r: r["date"])

            previous_reading = None

            for record in records:
                if previous_reading is None:
                    record["usage"] = 0
                else:
                    usage = round(
                        record["reading"] - previous_reading, 2
                    )
                    if usage < 0:
                        raise ValueError
                    record["usage"] = usage

                previous_reading = record["reading"]

            save_readings(records)
            message = "Meter reading saved successfully!"

        except (ValueError, TypeError):
            message = (
                "Invalid reading. Check the date and enter a valid "
                "number that is not less than the previous reading."
            )
            message_type = "error"
            records = load_readings()

    today = date.today().isoformat()
    current_month = today[:7]

    monthly_usage = round(
        sum(
            r["usage"] for r in records
            if r["date"].startswith(current_month)
        ),
        2
    )

    estimated_bill = round(monthly_usage * RATE, 2)

    alert = monthly_usage > MONTHLY_LIMIT
    alert_type = "warning" if alert else "success"

    return render_template(
        "index.html",
        records=records,
        monthly_usage=monthly_usage,
        estimated_bill=estimated_bill,
        rate=RATE,
        today=today,
        message=message,
        message_type=message_type,
        alert=alert,
        alert_type=alert_type
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
