from services.supabase_service import calculate_working_days
# Test around expected Eid al-Fitr 2025 (approx 1 Shawwal 1446 -> around April 2025)
print('Days (2025-04-09 to 2025-04-13):', calculate_working_days('2025-04-09','2025-04-13'))
# Test Eid al-Adha 2025 approximate
print('Days (2025-06-15 to 2025-06-20):', calculate_working_days('2025-06-15','2025-06-20'))
