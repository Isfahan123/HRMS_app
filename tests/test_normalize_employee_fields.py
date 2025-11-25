"""Tests for the _normalize_employee_fields function in supabase_service.

These tests verify that empty string values from form submissions are properly
converted to the correct types for database insertion, preventing error 22P02
(invalid input syntax for type integer).
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.supabase_service import _normalize_employee_fields


class TestNormalizeEmployeeFieldsInteger:
    """Tests for integer field normalization."""
    
    def test_number_of_children_empty_string_becomes_zero(self):
        """Empty string for number_of_children should become 0."""
        data = {"number_of_children": ""}
        result = _normalize_employee_fields(data)
        assert result["number_of_children"] == 0
        assert isinstance(result["number_of_children"], int)
    
    def test_number_of_children_none_becomes_zero(self):
        """None for number_of_children should become 0."""
        data = {"number_of_children": None}
        result = _normalize_employee_fields(data)
        assert result["number_of_children"] == 0
    
    def test_number_of_children_string_converts_to_int(self):
        """String number for number_of_children should convert to int."""
        data = {"number_of_children": "3"}
        result = _normalize_employee_fields(data)
        assert result["number_of_children"] == 3
        assert isinstance(result["number_of_children"], int)
    
    def test_number_of_children_invalid_string_becomes_zero(self):
        """Invalid string for number_of_children should become 0."""
        data = {"number_of_children": "abc"}
        result = _normalize_employee_fields(data)
        assert result["number_of_children"] == 0
    
    def test_graduation_year_empty_string_becomes_none(self):
        """Empty string for graduation_year should become None."""
        data = {"graduation_year": ""}
        result = _normalize_employee_fields(data)
        assert result["graduation_year"] is None
    
    def test_graduation_year_string_converts_to_int(self):
        """String year for graduation_year should convert to int."""
        data = {"graduation_year": "2020"}
        result = _normalize_employee_fields(data)
        assert result["graduation_year"] == 2020
        assert isinstance(result["graduation_year"], int)
    
    def test_days_in_malaysia_empty_string_becomes_none(self):
        """Empty string for days_in_malaysia_current_year should become None."""
        data = {"days_in_malaysia_current_year": ""}
        result = _normalize_employee_fields(data)
        assert result["days_in_malaysia_current_year"] is None


class TestNormalizeEmployeeFieldsBoolean:
    """Tests for boolean field normalization."""
    
    def test_spouse_working_empty_string_becomes_none(self):
        """Empty string for spouse_working should become None."""
        data = {"spouse_working": ""}
        result = _normalize_employee_fields(data)
        assert result["spouse_working"] is None
    
    def test_spouse_working_yes_becomes_true(self):
        """'Yes' for spouse_working should become True."""
        data = {"spouse_working": "Yes"}
        result = _normalize_employee_fields(data)
        assert result["spouse_working"] is True
    
    def test_spouse_working_no_becomes_false(self):
        """'No' for spouse_working should become False."""
        data = {"spouse_working": "No"}
        result = _normalize_employee_fields(data)
        assert result["spouse_working"] is False


class TestNormalizeEmployeeFieldsDate:
    """Tests for date field normalization."""
    
    def test_date_of_birth_empty_string_becomes_none(self):
        """Empty string for date_of_birth should become None."""
        data = {"date_of_birth": ""}
        result = _normalize_employee_fields(data)
        assert result["date_of_birth"] is None
    
    def test_join_date_empty_string_becomes_none(self):
        """Empty string for join_date should become None."""
        data = {"join_date": ""}
        result = _normalize_employee_fields(data)
        assert result["join_date"] is None
    
    def test_date_joined_empty_string_becomes_none(self):
        """Empty string for date_joined should become None."""
        data = {"date_joined": ""}
        result = _normalize_employee_fields(data)
        assert result["date_joined"] is None
    
    def test_date_leave_empty_string_becomes_none(self):
        """Empty string for date_leave should become None."""
        data = {"date_leave": ""}
        result = _normalize_employee_fields(data)
        assert result["date_leave"] is None


class TestNormalizeEmployeeFieldsNumeric:
    """Tests for numeric field normalization."""
    
    def test_basic_salary_empty_string_becomes_none(self):
        """Empty string for basic_salary should become None."""
        data = {"basic_salary": ""}
        result = _normalize_employee_fields(data)
        assert result["basic_salary"] is None
    
    def test_basic_salary_string_converts_to_float(self):
        """String number for basic_salary should convert to float."""
        data = {"basic_salary": "5000.50"}
        result = _normalize_employee_fields(data)
        assert result["basic_salary"] == 5000.50
        assert isinstance(result["basic_salary"], float)
    
    def test_sip_amount_empty_string_becomes_none(self):
        """Empty string for sip_amount should become None."""
        data = {"sip_amount": ""}
        result = _normalize_employee_fields(data)
        assert result["sip_amount"] is None


class TestNormalizeEmployeeFieldsComplete:
    """Tests for complete form data normalization."""
    
    def test_full_form_with_empty_strings(self):
        """Test normalization of a complete form submission with empty strings."""
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "number_of_children": "",
            "graduation_year": "",
            "days_in_malaysia_current_year": "",
            "basic_salary": "",
            "spouse_working": "",
            "date_of_birth": "",
            "sip_amount": "",
        }
        result = _normalize_employee_fields(data)
        
        # Check integer field with default 0
        assert result["number_of_children"] == 0
        
        # Check integer fields with default None
        assert result["graduation_year"] is None
        assert result["days_in_malaysia_current_year"] is None
        
        # Check numeric field
        assert result["basic_salary"] is None
        assert result["sip_amount"] is None
        
        # Check boolean field
        assert result["spouse_working"] is None
        
        # Check date field
        assert result["date_of_birth"] is None
        
        # Original string fields should be unchanged
        assert result["full_name"] == "Test User"
        assert result["email"] == "test@example.com"
    
    def test_normalization_does_not_modify_valid_data(self):
        """Valid data should not be modified."""
        data = {
            "full_name": "Test User",
            "number_of_children": 2,
            "graduation_year": 2020,
            "basic_salary": 5000.0,
            "spouse_working": True,
        }
        original = data.copy()
        result = _normalize_employee_fields(data)
        
        assert result["number_of_children"] == original["number_of_children"]
        assert result["graduation_year"] == original["graduation_year"]
        assert result["basic_salary"] == original["basic_salary"]
        assert result["spouse_working"] == original["spouse_working"]
