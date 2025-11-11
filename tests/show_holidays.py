#!/usr/bin/env python3
"""Headless helper: print holidays collected by CalendarTab for a year.
Usage: python tools/show_holidays.py [YEAR]
"""
import sys
from PyQt5.QtWidgets import QApplication
from gui.calendar_tab import CalendarTab

def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else None
    app = QApplication([])
    ct = CalendarTab()
    if year is None:
        try:
            year = ct.current_year
        except Exception:
            from datetime import date
            year = date.today().year
    ct.load_year(year)
    dates = sorted([d.isoformat() for d in ct.holidays])
    print(f"Collected holidays for {year} ({len(dates)}):")
    for d in dates:
        names = ct.holiday_details.get(__import__('datetime').date.fromisoformat(d), [])
        print(f"  {d} -> {', '.join(names) if names else '(no details)'}")

if __name__ == '__main__':
    main()
