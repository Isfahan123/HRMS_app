import sys
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')

try:
    from gui.annual_balance import AnnualBalanceWidget
    from gui.sick_balance import SickBalanceWidget
    print('Imported AnnualBalanceWidget and SickBalanceWidget OK')
except Exception as e:
    print('Import failed:', e)
    raise
