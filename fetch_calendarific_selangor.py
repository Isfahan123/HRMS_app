import os
from services.calendarific_service import fetch_calendarific_holidays

os.environ['CALENDARIFIC_API_KEY'] = os.environ.get('CALENDARIFIC_API_KEY', 'vcFzqfmid6eahZiEhBMefeFfNMDqwcqJ')

h = fetch_calendarific_holidays(2025, country='MY', state='Selangor')
print('Selangor holidays count:', len(h))
for item in h:
    print(item)
