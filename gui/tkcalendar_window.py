import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime
from services.holidays_service import get_holidays_for_year

def run_calendar(year=None):
    root = tk.Tk()
    root.title('TK Calendar (holiday view)')
    year = year or datetime.now().year
    cal = Calendar(root, selectmode='day', year=year, month=1)
    cal.pack(fill='both', expand=True)

    # highlight holidays by changing background of day cells
    try:
        h = get_holidays_for_year(year)
        for d in h:
            try:
                cal.calevent_create(d, 'Holiday', 'hol')
            except Exception:
                pass
        cal.tag_config('hol', background='red', foreground='white')
    except Exception:
        pass

    root.mainloop()

if __name__ == '__main__':
    run_calendar()
