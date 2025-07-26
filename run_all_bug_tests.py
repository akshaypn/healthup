#!/usr/bin/env python3
"""
Master Test Runner for HealthUp Bug Detection

This script runs all bug detection tests and provides a comprehensive security report.
"""

import sys
import os
import json
import subprocess
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_packages = ['requests', 'jwt', 'psycopg2', 'cryptography']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False
    
    return True

def check_services():
    """Check if HealthUp services are running"""
    print("\n🔍 Checking HealthUp services...")
    
    import requests
    
    services = {
        "Backend API": "http://localhost:8000",
        "Frontend": "http://localhost:3000", 
        "Database": "postgresql://healthup:healthup_secure_password_a2032334186a8000@localhost:5433/healthup"
    }
    
    for service, url in services.items():
        try:
            if service == "Database":
                import psycopg2
                conn = psycopg2.connect(url)
                conn.close()
                print(f"✅ {service}")
            else:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service}")
                else:
                    print(f"⚠️  {service} - Status {response.status_code}")
        except Exception as e:
            print(f"❌ {service} - {str(e)[:50]}")
            
def run_bug_tests():
    """Run all bug detection tests"""
    print("\n" + "="*60)
    print("🐛 HealthUp Comprehensive Bug Detection Suite")
    print("="*60)
    
    all_results = {}
    
    # Import and run basic bug tests
    try:
        from test_bug_detection import BugDetectionTests
        basic_tester = BugDetectionTests()
        basic_results = basic_tester.run_all_tests()
        all_results.update(basic_results)
    except ImportError as e:
        print(f"❌ Could not import basic tests: {e}")
    
    # Import and run security tests
    try:
        from test_security_bugs import SecurityBugTests
        security_tester = SecurityBugTests()
        security_results = security_tester.run_security_tests()
        all_results.update(security_results)
    except ImportError as e:
        print(f"❌ Could not import security tests: {e}")
    
    return all_results

def generate_report(results):
    """Generate comprehensive bug report"""
    print("\n" + "="*60)
    print("📊 FINAL BUG ANALYSIS REPORT")
    print("="*60)
    
    if not results:
        print("❌ No test results available")
        return
    
    # Categorize results
    critical_bugs = []
    high_bugs = []
    medium_bugs = []
    low_bugs = []
    passed_tests = []
    
    bug_severity = {
        'test_bug_1_default_secret_key': 'CRITICAL',
        'test_bug_2_database_credentials_exposure': 'CRITICAL', 
        'test_bug_3_encryption_key_security': 'HIGH',
        'test_bug_4_token_type_validation': 'HIGH',
        'test_bug_5_session_management': 'HIGH',
        'test_bug_6_transaction_rollback': 'MEDIUM',
        'test_bug_9_sql_injection_food_update': 'HIGH',
        'test_bug_10_food_parser_injection': 'MEDIUM',
        'test_bug_11_data_validation': 'MEDIUM',
        'test_bug_13_no_rate_limiting': 'HIGH',
        'test_bug_15_debug_mode_production': 'HIGH'
    }
    
    for test, passed in results.items():
        if passed:
            passed_tests.append(test)
        else:
            severity = bug_severity.get(test, 'MEDIUM')
            if severity == 'CRITICAL':
                critical_bugs.append(test)
            elif severity == 'HIGH':
                high_bugs.append(test)
            elif severity == 'MEDIUM':
                medium_bugs.append(test)
            else:
                low_bugs.append(test)
    
    # Print summary
    total_tests = len(results)
    total_bugs = len(critical_bugs) + len(high_bugs) + len(medium_bugs) + len(low_bugs)
    
    print(f"📈 SUMMARY:")
    print(f"   Total Tests Run: {total_tests}")
    print(f"   Tests Passed: {len(passed_tests)}")
    print(f"   Bugs Detected: {total_bugs}")
    print()
    
    # Security score
    if total_tests > 0:
        security_score = (len(passed_tests) / total_tests) * 100
        print(f"🔒 SECURITY SCORE: {security_score:.1f}%")
        
        if security_score >= 90:
            print("   Status: ✅ EXCELLENT")
        elif security_score >= 80:
            print("   Status: ⚠️  GOOD")
        elif security_score >= 70:
            print("   Status: ⚠️  FAIR")
        else:
            print("   Status: ❌ POOR - IMMEDIATE ACTION REQUIRED")
    
    print()
    
    # Detailed breakdown
    if critical_bugs:
        print("🚨 CRITICAL BUGS DETECTED:")
        for bug in critical_bugs:
            print(f"   - {bug}")
        print("   ⚠️  IMMEDIATE FIXES REQUIRED BEFORE PRODUCTION!")
        print()
    
    if high_bugs:
        print("🔴 HIGH SEVERITY BUGS:")
        for bug in high_bugs:
            print(f"   - {bug}")
        print()
    
    if medium_bugs:
        print("🟡 MEDIUM SEVERITY BUGS:")
        for bug in medium_bugs:
            print(f"   - {bug}")
        print()
    
    if low_bugs:
        print("🟢 LOW SEVERITY BUGS:")
        for bug in low_bugs:
            print(f"   - {bug}")
        print()
    
    # Recommendations
    print("🔧 IMMEDIATE ACTIONS:")
    if critical_bugs or high_bugs:
        print("   1. DO NOT deploy to production")
        print("   2. Fix critical and high severity bugs immediately")
        print("   3. Review security configuration")
        print("   4. Implement proper input validation")
        print("   5. Add rate limiting and monitoring")
    else:
        print("   1. Address medium/low severity issues")
        print("   2. Implement comprehensive monitoring")
        print("   3. Regular security reviews")
    
    # Save detailed report
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed_tests': len(passed_tests),
        'total_bugs': total_bugs,
        'security_score': security_score if total_tests > 0 else 0,
        'critical_bugs': critical_bugs,
        'high_bugs': high_bugs,
        'medium_bugs': medium_bugs,
        'low_bugs': low_bugs,
        'detailed_results': results
    }
    
    with open('bug_report.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: bug_report.json")

def main():
    """Main test runner"""
    print("🔬 HealthUp Security Analysis Tool")
    print("Starting comprehensive bug detection...")
    
    # Check prerequisites
    if not check_dependencies():
        print("❌ Missing dependencies. Please install required packages.")
        sys.exit(1)
    
    check_services()
    
    # Run tests
    results = run_bug_tests()
    
    # Generate report
    generate_report(results)
    
    # Exit with appropriate code
    if results:
        failed_count = sum(1 for passed in results.values() if not passed)
        if failed_count > 0:
            print(f"\n⚠️  {failed_count} security issues detected!")
            sys.exit(1)
        else:
            print("\n✅ All security tests passed!")
            sys.exit(0)
    else:
        print("\n❌ No tests could be executed")
        sys.exit(1)

if __name__ == "__main__":
    main() 