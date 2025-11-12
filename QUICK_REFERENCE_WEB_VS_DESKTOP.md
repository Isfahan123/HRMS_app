# Quick Reference: Web vs Desktop HRMS

## 🚀 Quick Start

### Desktop Version (Current)
```bash
python main.py
```
- **Interface**: PyQt5 native windows
- **Access**: Local machine only
- **Platform**: Windows, Mac, Linux (with Python)

### Web Version (From PR #2)
```bash
# Restore from PR #2 first, then:
pip install Flask==3.0.0
python app.py
# Open browser to http://localhost:5000
```
- **Interface**: HTML/CSS/JavaScript in browser
- **Access**: Any device with browser
- **Platform**: Any (Windows, Mac, Linux, iOS, Android)

---

## 📊 Comparison Table

| Feature | Desktop (main.py) | Web (app.py) |
|---------|------------------|--------------|
| **Installation** | Python + PyQt5 | Python + Flask |
| **Interface** | Native GUI | Browser-based |
| **Access** | Local only | Network/Internet |
| **Mobile Support** | ❌ No | ✅ Yes |
| **Updates** | Manual | Automatic |
| **Multi-user** | Single instance | Multiple users |
| **Database** | ✅ Supabase | ✅ Supabase |
| **Features** | ✅ Complete | ✅ Complete |
| **Status** | ✅ Active | ⏸️ Available in PR #2 |

---

## 📁 Where Are the HTML Files?

### Current Branch
- **No HTML files** - PR #2 was reverted

### To Get HTML Files:
1. **View on GitHub**: https://github.com/Isfahan123/HRMS_app/pull/2/files
2. **Checkout PR #2**:
   ```bash
   git fetch origin
   git checkout copilot/rewrite-files-to-html
   ```
3. **See documentation**: `HOW_TO_USE_HTML_FILES.md` (this repo)

---

## 🗂️ HTML Files Location (when restored)

```
HRMS_app/
├── app.py                              # Flask web server
├── templates/                          # HTML files (19 total)
│   ├── base.html                      # Base template
│   ├── index.html                     # Landing page
│   ├── login.html                     # Login page
│   ├── dashboard.html                 # Employee dashboard
│   ├── admin_dashboard.html           # Admin dashboard
│   ├── employee_*.html                # 5 employee pages
│   └── admin_*.html                   # 9 admin pages
├── static/
│   ├── css/style.css                  # Styles
│   └── js/
│       ├── main.js                    # Utilities
│       └── dashboard.js               # Dashboard logic
└── services/                          # Backend (unchanged)
```

---

## ⚡ Running Both Versions

You can run both simultaneously:

```bash
# Terminal 1: Desktop
python main.py

# Terminal 2: Web
python app.py
```

Both connect to the same Supabase database, so data stays synced!

---

## 🎯 Use Cases

### Use Desktop When:
- ✅ Working offline
- ✅ Need native OS integration
- ✅ Prefer traditional desktop apps
- ✅ Single-user scenario

### Use Web When:
- ✅ Need remote access
- ✅ Multiple users need access
- ✅ Want mobile access
- ✅ Easier deployment/updates
- ✅ No installation required

---

## 🔑 Key Commands

### Desktop
```bash
# Run desktop app
python main.py

# Install dependencies
pip install -r requirements.txt
```

### Web
```bash
# Install Flask (if restoring from PR #2)
pip install Flask==3.0.0

# Run web server
python app.py

# Production deployment
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📖 Documentation

- **This file**: Quick reference
- **HOW_TO_USE_HTML_FILES.md**: Complete guide (469 lines)
- **PR #2**: Full implementation with docs
  - README_WEB.md
  - QUICKSTART.md
  - API_DOCUMENTATION.md
  - CONVERSION_SUMMARY.md
  - And 4 more docs

---

## 🤔 FAQ

**Q: Where are the HTML files now?**  
A: They were in PR #2 but got reverted in PR #3. You can restore them from PR #2.

**Q: Can I use both versions?**  
A: Yes! Run both `main.py` and `app.py` simultaneously.

**Q: Which version should I use?**  
A: Desktop for local/offline use, Web for remote/multi-user access.

**Q: Do they share data?**  
A: Yes! Both use the same Supabase database.

**Q: How do I get the web version?**  
A: Checkout PR #2 branch or follow HOW_TO_USE_HTML_FILES.md

---

## 📞 Getting Help

1. Read **HOW_TO_USE_HTML_FILES.md**
2. View PR #2 on GitHub
3. Check Flask docs: https://flask.palletsprojects.com/
4. Check existing docs in `/docs` folder

---

**Last Updated**: 2025-11-12  
**Current**: Desktop app (`main.py`)  
**Available**: Web app in PR #2 (`app.py`)
