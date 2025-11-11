import os
import sys
import json
import bcrypt
import pytz
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services import supabase_service


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, state):
        self.state = state
        self._select_cols = None
        self._eq_field = None
        self._update_payload = None

    def select(self, cols):
        self._select_cols = cols
        return self

    def eq(self, field, value):
        self._eq_field = (field, value)
        return self

    def execute(self):
        # select read
        if self._update_payload is None:
            # Return a copy so callers can mutate but we reflect updates later
            return FakeResponse([self.state.copy()])
        else:
            # update: apply payload
            self.state.update(self._update_payload)
            # reset update payload for next call
            self._update_payload = None
            return FakeResponse([self.state.copy()])

    def update(self, payload):
        # prepare an update; execute() will apply it
        self._update_payload = payload
        return self


class FakeSupabase:
    def __init__(self, initial_row):
        # single-row store keyed by email
        self.row = initial_row

    def table(self, name):
        assert name == 'user_logins'
        return FakeTable(self.row)


def _clear_log():
    log_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'security.log'))
    try:
        if os.path.exists(log_path):
            os.remove(log_path)
    except Exception:
        pass
    return log_path


def _read_log_lines():
    log_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'security.log'))
    if not os.path.exists(log_path):
        return []
    with open(log_path, 'r', encoding='utf-8') as fh:
        return [l.strip() for l in fh.readlines() if l.strip()]


def test_success_resets_counters(tmp_path, monkeypatch):
    # Prepare a user with a known password and failed attempts
    password_plain = 'CorrectHorseBatteryStaple'
    hashed = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user = {
        'email': 'alice@example.com',
        'password': hashed,
        'role': 'employee',
        'failed_attempts': 3,
        'locked_until': None
    }

    fake = FakeSupabase(user)
    monkeypatch.setattr(supabase_service, 'supabase', fake)
    # Force the module to think columns exist
    monkeypatch.setattr(supabase_service, 'user_logins_has_lockout_columns', lambda: True)

    # Ensure logs start empty
    _clear_log()

    res = supabase_service.login_user('alice@example.com', password_plain)
    assert res.get('success') is True
    # After success, counters reset
    assert user.get('failed_attempts') == 0
    assert user.get('locked_until') is None

    lines = _read_log_lines()
    assert any('"event_type": "login_success"' in line for line in lines)


def test_failed_attempts_and_lock(monkeypatch):
    # Lower threshold for test speed
    monkeypatch.setattr(supabase_service, 'LOGIN_LOCK_THRESHOLD', 3)
    monkeypatch.setattr(supabase_service, 'LOGIN_LOCK_DURATION_MINUTES', 1)

    wrong_pw = 'wrongpassword'
    hashed = bcrypt.hashpw('secret'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    # start with failed_attempts one less than threshold
    user = {
        'email': 'bob@example.com',
        'password': hashed,
        'role': 'employee',
        'failed_attempts': 2,
        'locked_until': None
    }
    fake = FakeSupabase(user)
    monkeypatch.setattr(supabase_service, 'supabase', fake)
    monkeypatch.setattr(supabase_service, 'user_logins_has_lockout_columns', lambda: True)

    _clear_log()
    # perform a failing login (wrong password)
    res = supabase_service.login_user('bob@example.com', wrong_pw)
    assert res.get('success') is False
    # failed_attempts should have incremented to threshold and locked_until set
    assert int(user.get('failed_attempts', 0)) >= 3
    assert user.get('locked_until') is not None

    lines = _read_log_lines()
    assert any('"event_type": "login_failure"' in line for line in lines)
    # Check that a failure entry mentions lock due to repeated failures
    assert any('Account locked' in line or 'locked due to repeated failures' in line for line in lines)


def test_locked_account_rejected(monkeypatch):
    # Set a locked_until in the future
    hashed = bcrypt.hashpw('secret'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    future = (datetime.now(pytz.UTC) + timedelta(minutes=10)).isoformat()
    user = {
        'email': 'charlie@example.com',
        'password': hashed,
        'role': 'employee',
        'failed_attempts': 5,
        'locked_until': future
    }
    fake = FakeSupabase(user)
    monkeypatch.setattr(supabase_service, 'supabase', fake)
    monkeypatch.setattr(supabase_service, 'user_logins_has_lockout_columns', lambda: True)

    _clear_log()
    # Even with correct password, should be rejected because locked
    res = supabase_service.login_user('charlie@example.com', 'secret')
    assert res.get('success') is False
    assert 'locked_until' in res and res['locked_until'] is not None

    lines = _read_log_lines()
    assert any('"event_type": "login_failure"' in line for line in lines)
    assert any('Account locked' in line or 'locked until' in line for line in lines)
