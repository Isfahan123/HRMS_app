# UI Troubleshooting Guide

## Problem: Changes Don't Appear After Merge/Deploy

If you've merged the PR but the interface still shows the old purple gradient style instead of the new PyQt5 desktop style, this is likely a **browser caching issue**.

### Solution 1: Hard Refresh Browser Cache

**Chrome/Edge/Firefox:**
- Windows/Linux: Press `Ctrl + Shift + R` or `Ctrl + F5`
- Mac: Press `Cmd + Shift + R`

**Safari:**
- Press `Cmd + Option + E` (to empty cache), then `Cmd + R` (to reload)

### Solution 2: Clear Browser Cache Completely

**Chrome:**
1. Press `Ctrl + Shift + Delete` (or `Cmd + Shift + Delete` on Mac)
2. Select "Cached images and files"
3. Click "Clear data"
4. Reload the page

**Firefox:**
1. Press `Ctrl + Shift + Delete`
2. Select "Cache"
3. Click "Clear Now"
4. Reload the page

### Solution 3: Use Incognito/Private Mode

Open the website in an incognito/private browsing window to bypass cache entirely.

### Solution 4: Check Server is Serving New Files

```bash
# After deploying, verify the CSS file contains the new styles
curl http://localhost:8000/static/css/style.css | head -20
```

You should see:
```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: #ecf0f1;    /* <-- Should be #ecf0f1 (gray), NOT gradient */
    min-height: 100vh;
    color: #2c3e50;
}
```

If you see `background: linear-gradient(...)`, the server is serving old files.

## What You Should See After Changes

### Login Page
- **Background**: Light gray (#ecf0f1) instead of purple gradient
- **Login button**: Solid blue (#3498db) instead of purple gradient
- **Box**: Simple border instead of dramatic shadow

### Dashboard
- **Header**: Dark gray (#34495e) with white text
- **Tabs**: Flat, connected tabs (not rounded pills)
- **Active tab**: White background with blue top border
- **Subtabs**: Horizontal layout with blue underline for active

### Payroll Tab Should Show 6 Subtabs:
1. Payroll History (active by default, shows in blue)
2. Skipped Payroll
3. View Contributions
4. 💰 Bonuses
5. 📊 Variable %
6. 🏛️ LHDN Tax

### Leaves Tab Should Show 8 Subtabs:
1. Pending
2. Approved/Rejected
3. Submit Leave
4. Annual Balance
5. Sick Balance
6. Unpaid Leave
7. Calendar
8. ⚙️ Configuration

## Comparing with Python GUI

The HTML interface now matches the Python GUI structure:

**Python GUI (PyQt5):**
- QTabWidget with flat tabs
- Default Qt color scheme (blues and grays)
- Connected tab layout
- Subtabs using nested QTabWidget

**HTML Interface (Now):**
- Flat, connected tabs matching QTabWidget style
- PyQt5 color scheme (#3498db blue, #34495e dark gray)
- Desktop application appearance
- Subtabs with same structure as Python GUI

## Still Having Issues?

### Check Browser Console for Errors
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for any error messages
4. Check Network tab to see if CSS loaded correctly (should show status 200)

### Verify File Versions
The CSS link should include version parameter:
```html
<link rel="stylesheet" href="/static/css/style.css?v=2.0">
```

If it doesn't have `?v=2.0`, you may need to re-deploy.

### Server-Side Cache
If using a reverse proxy (nginx, Apache), clear server cache:
```bash
# Nginx
sudo nginx -s reload

# Apache
sudo service apache2 reload
```

## Contact

If none of these solutions work, provide:
1. Screenshot of what you're seeing
2. Browser and version
3. Output of: `curl http://localhost:8000/static/css/style.css | grep "background:"`
