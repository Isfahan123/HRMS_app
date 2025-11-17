#!/usr/bin/env python3
"""
Test script to verify which API endpoints are working and which fail
"""

import asyncio
import httpx
from typing import Dict, List

BASE_URL = "http://localhost:8000"

# Endpoints to test (GET requests that don't require authentication)
TEST_ENDPOINTS = [
    ("GET", "/api/employees", "List all employees"),
    ("GET", "/api/admin/leave-requests", "List leave requests"),
    ("GET", "/api/admin/bonuses", "List bonuses"),
    ("GET", "/api/admin/payroll-runs", "List payroll runs"),
    ("GET", "/api/admin/leave-balances", "View leave balances"),
    ("GET", "/api/admin/sick-leave-balances", "View sick leave balances"),
    ("GET", "/api/admin/unpaid-leave-summary", "View unpaid leave summary"),
    ("GET", "/api/admin/payroll-contributions", "View contributions"),
    ("GET", "/api/admin/variable-percentage", "List variable percentage rules"),
    ("GET", "/api/admin/skipped-payroll", "List skipped payroll"),
    ("GET", "/api/admin/salary-history", "View salary history"),
    ("GET", "/api/admin/employee-history", "View employee history"),
    ("GET", "/api/admin/lhdn/tax-rates", "List LHDN tax rates"),
    ("GET", "/api/admin/lhdn/relief-max", "List LHDN relief maximums"),
    ("GET", "/api/admin/lhdn/relief-overrides", "List LHDN relief overrides"),
    ("GET", "/api/admin/engagements/all", "List all engagements"),
    ("GET", "/api/admin/attendance", "List attendance records"),
]

async def test_endpoint(client: httpx.AsyncClient, method: str, path: str, description: str) -> Dict:
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{path}", timeout=5.0)
        else:
            return {"path": path, "status": "skipped", "description": description}
        
        data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
        
        return {
            "path": path,
            "description": description,
            "status_code": response.status_code,
            "success": data.get("success", False) if isinstance(data, dict) else False,
            "data_count": len(data.get("data", [])) if isinstance(data, dict) and isinstance(data.get("data"), list) else 0,
            "has_data": bool(data.get("data")) if isinstance(data, dict) else False,
            "error": data.get("message") if isinstance(data, dict) and not data.get("success") else None
        }
    except httpx.ConnectError:
        return {
            "path": path,
            "description": description,
            "status": "connection_error",
            "error": "Cannot connect to server"
        }
    except Exception as e:
        return {
            "path": path,
            "description": description,
            "status": "error",
            "error": str(e)
        }

async def main():
    """Main test function"""
    print("=" * 80)
    print("HRMS API ENDPOINT TESTING")
    print("=" * 80)
    print(f"\nTesting against: {BASE_URL}")
    print(f"Total endpoints to test: {len(TEST_ENDPOINTS)}\n")
    
    async with httpx.AsyncClient() as client:
        # Test all endpoints
        tasks = [test_endpoint(client, method, path, desc) for method, path, desc in TEST_ENDPOINTS]
        results = await asyncio.gather(*tasks)
    
    # Categorize results
    working = []
    working_with_data = []
    working_no_data = []
    failed = []
    connection_errors = []
    
    for result in results:
        if result.get("status") == "connection_error":
            connection_errors.append(result)
        elif result.get("status") == "error":
            failed.append(result)
        elif result.get("status_code") == 200 and result.get("success"):
            if result.get("has_data"):
                working_with_data.append(result)
            else:
                working_no_data.append(result)
            working.append(result)
        else:
            failed.append(result)
    
    # Print results
    if connection_errors:
        print("⚠️  CONNECTION ERROR")
        print("-" * 80)
        print("Cannot connect to the server. Make sure it's running:")
        print("  python web_app.py")
        print()
        return
    
    print("✅ WORKING ENDPOINTS WITH DATA")
    print("-" * 80)
    if working_with_data:
        for result in working_with_data:
            print(f"  {result['path']}")
            print(f"    {result['description']}")
            print(f"    Data count: {result['data_count']} records")
            print()
    else:
        print("  None\n")
    
    print("✅ WORKING ENDPOINTS (No Data)")
    print("-" * 80)
    if working_no_data:
        for result in working_no_data:
            print(f"  {result['path']}")
            print(f"    {result['description']}")
            print(f"    Status: Returns empty array (table may be empty)")
            print()
    else:
        print("  None\n")
    
    print("❌ FAILED ENDPOINTS")
    print("-" * 80)
    if failed:
        for result in failed:
            print(f"  {result['path']}")
            print(f"    {result['description']}")
            if result.get('error'):
                print(f"    Error: {result['error']}")
            if result.get('status_code'):
                print(f"    Status code: {result['status_code']}")
            print()
    else:
        print("  None\n")
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Working: {len(working)} / {len(TEST_ENDPOINTS)}")
    print(f"   - With data: {len(working_with_data)}")
    print(f"   - Empty: {len(working_no_data)}")
    print(f"❌ Failed: {len(failed)}")
    print()
    
    # Recommendations
    if failed:
        print("📋 RECOMMENDATIONS")
        print("-" * 80)
        print("Failed endpoints may need:")
        print("  1. Database tables to be created")
        print("  2. Schema migrations to be run")
        print("  3. Initial data to be seeded")
        print()
        print("Check SQL files in ./data/ directory for table creation scripts")
        print()

if __name__ == "__main__":
    asyncio.run(main())
