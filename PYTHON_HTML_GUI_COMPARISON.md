# Python GUI vs HTML GUI Feature Comparison

This document tracks the systematic comparison between the PyQt5 desktop GUI and the web-based HTML GUI to ensure feature parity.

## Status Legend
- ✅ **Aligned**: Features match between Python and HTML
- ⚠️ **Partial**: Some features missing in HTML
- ❌ **Missing**: Major features missing in HTML
- 🔄 **In Progress**: Currently being worked on

---

## 1. Attendance Tab ✅

### Status: **ALIGNED**

| Feature | Python GUI | HTML GUI | Notes |
|---------|-----------|----------|-------|
| Date range filters (From/To) | ✅ | ✅ | Match |
| Filter by field (Email/Date) | ✅ | ✅ | Match |
| Search input | ✅ | ✅ | Match |
| Export to CSV | ✅ | ✅ | Match |
| Working hours settings | ✅ | ✅ | Clock-in, Clock-out, Clock-in Limit |
| Save settings button | ✅ | ✅ | Match |
| Table columns | 4 cols | 5 cols | HTML adds "Status" column (improvement) |
| Employee display | Email only | Name + fallback | HTML has better UX |

**Conclusion**: HTML version is actually superior with better UX. No changes needed.

---

## 2. Leave Management Tab ⚠️

### Status: **PARTIAL - Missing 3 subtabs**

### Subtabs Comparison

| Subtab | Python GUI | HTML GUI | Status |
|--------|-----------|----------|--------|
| Pending | ✅ | ✅ | ✅ Aligned |
| Approved/Rejected | ✅ | ✅ | ⚠️ Missing advanced filters |
| Submit Leave Request | ✅ | ✅ | ✅ Aligned |
| Annual Leave Balance | ✅ | ✅ | ⚠️ Missing advanced features |
| Sick Leave Balance | ✅ | ❌ | **MISSING** |
| Unpaid Leave | ✅ | ❌ | **MISSING** |
| Calendar/Holidays | ✅ | ❌ | **MISSING** (exists as separate tab) |

### Detailed Feature Comparison

#### 2.1 Pending Leave Requests
| Feature | Python | HTML | Status |
|---------|--------|------|--------|
| Basic table view | ✅ | ✅ | ✅ |
| Approve/Reject actions | ✅ | ✅ | ✅ |
| View details | ✅ | ✅ | ✅ |
| Filter by employee | ✅ | ✅ | ✅ |
| Date range filter | ✅ | ✅ | ✅ |
| Leave type filter | ✅ | ❓ | Need to verify |
| Export pending to CSV | ✅ | ❓ | Need to verify |

#### 2.2 Approved/Rejected
| Feature | Python | HTML | Status |
|---------|--------|------|--------|
| Basic table view | ✅ | ✅ | ✅ |
| Status filter (All/Approved/Rejected/Cancelled) | ✅ | ❓ | Need to verify |
| Reviewed date range | ✅ | ❓ | Need to verify |
| Employee search | ✅ | ❓ | Need to verify |
| Export to CSV | ✅ | ❓ | Need to verify |

#### 2.3 Submit Leave Request
| Feature | Python | HTML | Status |
|---------|--------|------|--------|
| Employee selector | ✅ | ✅ | ✅ Recently fixed |
| Leave type dropdown | ✅ | ✅ | ✅ |
| Start/End date pickers | ✅ | ✅ | ✅ |
| Half day option | ✅ | ✅ | ✅ |
| Reason field | ✅ | ✅ | ✅ |
| Days calculation | ✅ | ❓ | Need to verify |
| Document attachment | ✅ | ❌ | **MISSING** |

#### 2.4 Annual Leave Balance
| Feature | Python | HTML | Status |
|---------|--------|------|--------|
| View all employee balances | ✅ | ✅ | ✅ |
| Search/filter employees | ✅ | ❓ | Need to verify |
| Adjust balance manually | ✅ | ❌ | **MISSING** |
| Edit employee balance | ✅ | ❌ | **MISSING** |
| Year-end carry forward | ✅ | ❌ | **MISSING** |
| Set carried forward for all | ✅ | ❌ | **MISSING** |
| Export balances | ✅ | ❓ | Need to verify |
| Configure leave policies | ✅ | ❌ | **MISSING** |
| Employment Act info button | ✅ | ❌ | **MISSING** |

#### 2.5 Sick Leave Balance ❌
**Entire subtab missing in HTML**
- View sick leave balances per employee
- Filter employees
- View sick leave details
- Export sick leave balances
- Employment Act info for sick leave

#### 2.6 Unpaid Leave ❌
**Entire subtab missing in HTML**
- View unpaid leave records
- Track unpaid leave days
- Export unpaid leave data

#### 2.7 Calendar/Holidays
**Exists as separate tab in HTML** - Need to verify feature parity

---

## 3. Payroll Tab 🔄

### Status: **To Be Analyzed**

Python GUI features to check:
- Multiple subtabs (need to enumerate)
- Payroll run history
- Generate payroll
- View contributions
- Tax calculations
- Payroll reports

---

## 4. Bonuses Tab 🔄

### Status: **To Be Analyzed**

---

## 5. Employee Profile/List Tab 🔄

### Status: **To Be Analyzed**

---

## 6. Salary History Tab 🔄

### Status: **To Be Analyzed**

---

## 7. Activities Tab 🔄

### Status: **To Be Analyzed**

Python GUI subtabs:
- Training Courses
- Overseas Trips  
- Engagements

---

## 8. Calendar/Holidays Tab 🔄

### Status: **To Be Analyzed**

Exists in both but need to compare features.

---

## Priority Action Items

### High Priority (Critical Missing Features)
1. ❌ Add Sick Leave Balance subtab to Leave Management
2. ❌ Add Unpaid Leave subtab to Leave Management
3. ❌ Add leave policy configuration
4. ❌ Add year-end carry forward functionality
5. ❌ Add manual balance adjustment for Annual Leave

### Medium Priority (Enhanced Features)
6. ⚠️ Add advanced filters to Approved/Rejected leave
7. ⚠️ Add document attachment to Submit Leave Request
8. ⚠️ Add Employment Act info buttons
9. ⚠️ Verify and add missing export functions

### Low Priority (Nice to Have)
10. Analyze remaining tabs (Payroll, Bonuses, Profile, etc.)
11. Add any missing minor features found

---

## Implementation Notes

- Work one tab at a time, one commit per major feature
- Test each feature after implementation
- Maintain backward compatibility
- Follow existing HTML/JS patterns
- Use Python GUI as authoritative reference for functionality

---

*Last Updated: 2025-11-20*
*Status: Initial comparison complete for Attendance and Leave tabs*
