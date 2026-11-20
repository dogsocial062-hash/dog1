"""Load the content calendar and find the row for a given date."""
import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLAN_PATH = ROOT / "content_plan.csv"


def load_plan(path=PLAN_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_row(date_str, path=PLAN_PATH):
    for row in load_plan(path):
        if row["date"] == date_str:
            return row
    return None
