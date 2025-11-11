#!/usr/bin/env python3
"""
Test script to verify that the approval process works correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.supabase_service import update_leave_request_status

def test_approval_function():
    """Test that the update_leave_request_status function requires admin_email"""
    print("Testing update_leave_request_status function signature...")
    
    try:
        # This should fail with missing argument error
        result = update_leave_request_status("test_id", "approved")
        print("❌ ERROR: Function call succeeded without admin_email parameter")
        return False
    except TypeError as e:
        if "missing 1 required positional argument: 'admin_email'" in str(e):
            print("✅ SUCCESS: Function correctly requires admin_email parameter")
            print(f"   Error message: {e}")
            return True
        else:
            print(f"❌ ERROR: Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected exception: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("LEAVE REQUEST APPROVAL FIX VERIFICATION")
    print("=" * 50)
    
    success = test_approval_function()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED")
        print("The admin_email parameter requirement is working correctly.")
        print("The UI should now pass the admin email when approving/rejecting requests.")
    else:
        print("❌ TESTS FAILED")
        print("The function signature may not be as expected.")
    print("=" * 50)