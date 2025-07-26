# HealthUp Test Suite

This directory contains all test files, bug reports, and testing documentation for the HealthUp application.

## 📁 Test Files Organization

### 🔍 **Core Test Suites**

#### **Comprehensive AI and Integration Tests**
- `test_comprehensive_ai_fixes.py` - Main comprehensive test suite covering AI integration, database types, API formats, and frontend integration
- `test_food_logging_integration.py` - Food logging system integration tests
- `test_food_logging_bugs.py` - Focused tests for food logging specific bugs
- `test_food_analysis_fix.py` - Food analysis and AI parsing tests

#### **Security and Bug Detection**
- `test_security_bugs.py` - Security-focused tests (JWT, encryption, input validation)
- `test_bug_detection.py` - Core vulnerability and bug detection tests
- `run_all_bug_tests.py` - Master test runner that orchestrates all bug tests

#### **Feature-Specific Tests**
- `test_new_features.py` - Tests for new application features
- `test_insights.py` - AI insights generation tests
- `test_insight_generation.py` - Insight generation functionality tests
- `test_food_parser.py` - AI food parsing functionality tests

#### **API and Endpoint Tests**
- `test_api_response.py` - API response format and structure tests
- `test_all_endpoints.sh` - Shell script to test all API endpoints
- `test_amazfit_endpoint.py` - Amazfit API endpoint tests
- `test_amazfit_flow.py` - Complete Amazfit integration flow tests
- `test_amazfit_with_real_credentials.py` - Real credential testing for Amazfit
- `test_complete_amazfit_flow.py` - End-to-end Amazfit integration tests
- `test_authenticated_amazfit.py` - Authenticated Amazfit API tests

### 🔧 **Shell Script Tests**

#### **Authentication and Session Tests**
- `test-auth.sh` - Basic authentication tests
- `test-cookie-auth.sh` - Cookie-based authentication tests
- `test-session.sh` - Session management tests
- `test-frontend-auth.sh` - Frontend authentication tests
- `test-frontend-backend.sh` - Frontend-backend integration tests

#### **Deployment and Setup Tests**
- `test-deployment.sh` - Deployment verification tests
- `test-current-setup.sh` - Current setup verification script
- `test-tailscale-session.sh` - Tailscale deployment session tests

### 📊 **Reports and Documentation**

#### **Bug Analysis and Reports**
- `bug_analysis_report.md` - Comprehensive analysis of 20 identified bugs
- `bug_report.json` - JSON format bug report data
- `BUG_TESTING_GUIDE.md` - Complete guide for running bug tests
- `SECURITY_FIXES_SUMMARY.md` - Summary of security improvements implemented
- `FOOD_LOGGING_BUGS_REPORT.md` - Detailed report of food logging system bugs
- `INTEGRATION_TESTING_SUMMARY.md` - Summary of integration testing results

## 🚀 **How to Run Tests**

### **Quick Setup Verification**
```bash
# From project root
./tests/test-current-setup.sh
```

### **Comprehensive Test Suite**
```bash
# From project root
python tests/test_comprehensive_ai_fixes.py
```

### **Security Tests**
```bash
# From project root
python tests/test_security_bugs.py
python tests/test_bug_detection.py
```

### **All Bug Tests**
```bash
# From project root
python tests/run_all_bug_tests.py
```

### **Shell Script Tests**
```bash
# From project root
./tests/test-auth.sh
./tests/test-all_endpoints.sh
./tests/test-session.sh
```

## 📈 **Test Results Summary**

### **Overall Test Performance**
- **Comprehensive AI Tests**: 83.3% pass rate
- **Security Tests**: All critical vulnerabilities fixed
- **Integration Tests**: Full frontend-backend integration verified
- **API Tests**: All endpoints responding correctly

### **Key Test Categories**
1. **AI Integration**: OpenAI API, food parsing, timeout handling
2. **Database**: Type handling, constraints, persistence
3. **Security**: Rate limiting, input validation, JWT tokens
4. **API**: Response formats, error handling, authentication
5. **Frontend**: Graph ranges, data display, user interactions
6. **Integration**: Service communication, data flow

## 🔧 **Test Environment Setup**

### **Prerequisites**
```bash
# Create virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install test dependencies
pip install requests psycopg2-binary PyJWT cryptography
```

### **Environment Variables**
```bash
# Required for AI tests
export OPENAI_API_KEY="your_openai_api_key"
export GEMINI_API_KEY="your_gemini_api_key"

# Database connection
export DATABASE_URL="postgresql://healthup:password@localhost:5433/healthup"
```

## 📋 **Test Maintenance**

### **Adding New Tests**
1. Create test file in appropriate category
2. Follow naming convention: `test_[feature]_[purpose].py`
3. Include comprehensive docstring
4. Add to relevant test runner if applicable

### **Updating Test Documentation**
1. Update this README when adding new test categories
2. Update test results summary after major test runs
3. Document any new test dependencies or setup requirements

## 🎯 **Test Coverage Areas**

- ✅ **Authentication & Authorization**
- ✅ **AI Integration & Food Parsing**
- ✅ **Database Operations & Type Handling**
- ✅ **API Endpoints & Response Formats**
- ✅ **Frontend Integration & Data Display**
- ✅ **Security Features & Input Validation**
- ✅ **Error Handling & Fallback Mechanisms**
- ✅ **Performance & Timeout Handling**
- ✅ **Deployment & Environment Configuration**

## 📞 **Support**

For test-related issues or questions:
1. Check the specific test file documentation
2. Review the bug reports and analysis documents
3. Run individual test suites to isolate issues
4. Check the main project README for setup instructions 