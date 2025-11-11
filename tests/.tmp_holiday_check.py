from datetime import date
from workalendar.asia import Malaysia
import holidays

cal = Malaysia()
my_hols = holidays.Malaysia()

check_dates = [date(2025,12,25), date(2026,1,1)]
# Also print all Malaysia holidays in 2025 to locate Deepavali
print('Workalendar holidays 2025 (sample):')
for d, name in cal.holidays(2025):
    print(d, name)

print('\nCheck specific dates:')
for d in check_dates:
    try:
        print(d, 'workalendar.is_working_day ->', cal.is_working_day(d))
    except Exception as e:
        print('workalendar error for', d, e)
    print(d, 'in holidays.Malaysia ->', d in my_hols, my_hols.get(d))
