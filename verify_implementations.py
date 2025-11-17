#!/usr/bin/env python3
"""
Verification script to check which HTML features are actually implemented
and which ones are just placeholders.
"""

import os
import re
from pathlib import Path

def check_js_file_completeness(filepath):
    """Check if a JavaScript file has real implementation or just stubs"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    results = {
        'file': filepath.name,
        'lines': len(content.splitlines()),
        'has_fetch_calls': bool(re.search(r'fetch\([\'"`]/api/', content)),
        'has_todo_comments': bool(re.search(r'TODO|FIXME|PLACEHOLDER', content, re.IGNORECASE)),
        'has_alert_fallbacks': bool(re.search(r'alert\(.*\)\s*;.*(?:TODO|implement)', content, re.IGNORECASE)),
        'function_count': len(re.findall(r'(?:async\s+)?function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?function', content)),
        'api_endpoints': list(set(re.findall(r'fetch\([\'"`](/api/[^\'"]+)', content)))
    }
    return results

def check_api_endpoint_implementation(filepath):
    """Check if API endpoints in web_app.py are real or mocks"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find all endpoint definitions
    endpoint_pattern = r'@app\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)\s*\nasync def (\w+)'
    endpoints = re.findall(endpoint_pattern, content)
    
    results = []
    for method, path, func_name in endpoints:
        # Find the function body
        func_pattern = rf'async def {func_name}\([^)]*\):(.*?)(?=\n(?:@app\.|async def|def|class|\Z))'
        match = re.search(func_pattern, content, re.DOTALL)
        
        if match:
            func_body = match.group(1)
            is_mock = bool(re.search(r'mock|Mock|placeholder|PLACEHOLDER|TODO', func_body, re.IGNORECASE))
            uses_supabase = bool(re.search(r'supabase\.table', func_body))
            has_try_except = bool(re.search(r'try:', func_body))
            
            results.append({
                'method': method.upper(),
                'path': path,
                'function': func_name,
                'is_mock': is_mock,
                'uses_supabase': uses_supabase,
                'has_error_handling': has_try_except,
                'lines': len(func_body.splitlines())
            })
    
    return results

def check_html_placeholders(filepath):
    """Check for placeholder text in HTML files"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    placeholder_patterns = [
        r'coming soon',
        r'not implemented',
        r'placeholder',
        r'under construction',
        r'to be added'
    ]
    
    results = {
        'file': filepath.name,
        'placeholders': []
    }
    
    for pattern in placeholder_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Get line number
            line_no = content[:match.start()].count('\n') + 1
            # Get context (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].replace('\n', ' ').strip()
            results['placeholders'].append({
                'line': line_no,
                'pattern': pattern,
                'context': context
            })
    
    return results

def main():
    """Main verification function"""
    print("=" * 80)
    print("HRMS WEB APPLICATION - IMPLEMENTATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Check JavaScript files
    print("📝 JavaScript Implementation Status")
    print("-" * 80)
    js_dir = Path("web/static/js")
    js_files = [
        "bonus.js",
        "calendar.js",
        "lhdn_config.js",
        "leave_config.js",
        "admin_dashboard.js"
    ]
    
    for js_file in js_files:
        filepath = js_dir / js_file
        if filepath.exists():
            results = check_js_file_completeness(filepath)
            print(f"\n{results['file']}:")
            print(f"  Lines of code: {results['lines']}")
            print(f"  Functions: {results['function_count']}")
            print(f"  Has API calls: {'✅' if results['has_fetch_calls'] else '❌'}")
            print(f"  Has TODOs: {'⚠️' if results['has_todo_comments'] else '✅'}")
            print(f"  API endpoints called: {len(results['api_endpoints'])}")
            if results['api_endpoints']:
                for endpoint in sorted(results['api_endpoints'])[:5]:
                    print(f"    - {endpoint}")
                if len(results['api_endpoints']) > 5:
                    print(f"    ... and {len(results['api_endpoints']) - 5} more")
    
    # Check API endpoints
    print("\n\n🔌 API Endpoint Implementation Status")
    print("-" * 80)
    api_results = check_api_endpoint_implementation("web_app.py")
    
    # Group by implementation status
    real_endpoints = [e for e in api_results if not e['is_mock'] and e['uses_supabase']]
    mock_endpoints = [e for e in api_results if e['is_mock']]
    no_db_endpoints = [e for e in api_results if not e['is_mock'] and not e['uses_supabase']]
    
    print(f"\nTotal endpoints: {len(api_results)}")
    print(f"✅ Fully implemented: {len(real_endpoints)}")
    print(f"⚠️  Using mock/placeholder data: {len(mock_endpoints)}")
    print(f"❓ No database interaction: {len(no_db_endpoints)}")
    
    if mock_endpoints:
        print("\n⚠️  Endpoints with mock/placeholder data:")
        for endpoint in mock_endpoints:
            print(f"  {endpoint['method']} {endpoint['path']}")
    
    # Check HTML placeholders
    print("\n\n📄 HTML Template Placeholder Status")
    print("-" * 80)
    html_files = [
        Path("web/templates/admin_dashboard.html"),
        Path("web/templates/dashboard.html")
    ]
    
    total_placeholders = 0
    for filepath in html_files:
        if filepath.exists():
            results = check_html_placeholders(filepath)
            if results['placeholders']:
                print(f"\n{results['file']}:")
                for placeholder in results['placeholders']:
                    print(f"  Line {placeholder['line']}: {placeholder['pattern']}")
                    print(f"    Context: {placeholder['context'][:100]}...")
                total_placeholders += len(results['placeholders'])
    
    if total_placeholders == 0:
        print("✅ No placeholder text found in HTML templates")
    
    # Summary
    print("\n\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"\n✅ JavaScript files with implementations: {len([f for f in js_files if (js_dir / f).exists()])}")
    print(f"✅ Fully implemented API endpoints: {len(real_endpoints)}")
    print(f"⚠️  Endpoints needing work: {len(mock_endpoints) + len(no_db_endpoints)}")
    print(f"{'✅' if total_placeholders == 0 else '⚠️'} HTML placeholders: {total_placeholders}")
    
    # Recommendations
    print("\n\n📋 RECOMMENDATIONS")
    print("=" * 80)
    if mock_endpoints:
        print("\n1. Replace mock data implementations with real database queries:")
        for endpoint in mock_endpoints:
            print(f"   - {endpoint['method']} {endpoint['path']}")
    
    if no_db_endpoints:
        print(f"\n2. Add database integration for {len(no_db_endpoints)} endpoints without DB calls")
    
    if total_placeholders > 0:
        print(f"\n3. Remove {total_placeholders} placeholder text from HTML templates")
    
    print("\n" + "=" * 80)
    print()

if __name__ == "__main__":
    main()
