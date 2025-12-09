# Complete Test Inputs Guide

## Available Test Files

### 1. **test_inputs_minimal.json** (3 invoices)
**Purpose**: Quick test with basic scenarios
- 1a: Sales with 21% VAT
- 4a: Purchase from EU
- Credit note with negative amounts

**Use when**: You need a quick smoke test

---

### 2. **test_inputs_new_format.json** (20 invoices)
**Purpose**: Comprehensive test covering all Q1 categories
- All VAT categories (1a, 1b, 1c, 1e, 2a, 3a, 3b, 3c, 4a, 4b, 5a)
- Q1 2025 dates (Jan-Mar)
- Various transaction types

**Use when**: Testing Q1 reports and all categories

---

### 3. **test_inputs_extended.json** (22 invoices) ⭐ NEW
**Purpose**: Extended test covering Q2, Q3, Q4
- Q2: June transactions
- Q3: July, August, September transactions
- Q4: October, November, December transactions
- Large amounts (50,000 EUR)
- Multiple credit notes
- Various EU and non-EU transactions

**Use when**: Testing multiple quarters and yearly reports

---

### 4. **test_inputs_edge_cases.json** (20 invoices) ⭐ NEW
**Purpose**: Edge cases and boundary conditions
- Minimal amounts (0.01 EUR)
- Large amounts (999,999.99 EUR)
- Decimal precision tests
- Null VAT amounts
- Zero amount transactions
- Previous year transactions (2024)
- Future year transactions (2026)
- Complex decimal calculations
- Rounded VAT calculations

**Use when**: Testing edge cases and data validation

---

### 5. **test_inputs_multiple_years.json** (6 invoices) ⭐ NEW
**Purpose**: Test multiple years
- 2024 transactions
- 2025 transactions
- 2026 transactions

**Use when**: Testing year filtering and multi-year data

---

### 6. **test_inputs_all_categories.json** (11 invoices) ⭐ NEW
**Purpose**: One invoice per category for quick category testing
- 1a, 1b, 1c, 1e (Sales)
- 2a (Sales and Purchase)
- 3a, 3b, 3c (Sales)
- 4a, 4b (Purchases)
- 5a (Purchase)

**Use when**: Testing all categories systematically

---

## Test Scenarios Covered

### ✅ All VAT Categories
- **1a**: Standard rate sales (21%)
- **1b**: Reduced rate sales (9%)
- **1c**: Zero-rated sales
- **1e**: Exempt supplies
- **2a**: Reverse charge (sales and purchases)
- **3a**: EU goods (B2B)
- **3b**: EU services (B2B)
- **3c**: EU B2C goods
- **4a**: Non-EU purchases
- **4b**: EU purchases
- **5a**: Domestic purchases with VAT

### ✅ Transaction Types
- Sales transactions
- Purchase transactions
- Credit notes (negative amounts)
- Regular invoices

### ✅ Date Ranges
- Q1 2025 (Jan-Mar)
- Q2 2025 (Apr-Jun)
- Q3 2025 (Jul-Sep)
- Q4 2025 (Oct-Dec)
- 2024 transactions
- 2026 transactions

### ✅ Amount Scenarios
- Small amounts (0.01 EUR)
- Large amounts (999,999.99 EUR)
- Decimal amounts (1234.56)
- Zero amounts
- Negative amounts (credit notes)

### ✅ Country Scenarios
- NL (Domestic)
- EU countries (BE, DE, FR, IT, ES, SE, DK, PL, CZ, FI, AT, etc.)
- Non-EU countries (US, GB, CN, JP, CH, AU)

### ✅ VAT Scenarios
- 21% VAT
- 9% VAT
- 0% VAT
- Null VAT amounts
- Negative VAT (credit notes)

## Quick Test Workflows

### Test 1: Basic Functionality
```bash
# Use minimal test
POST /process-invoices
Body: test_inputs_minimal.json

# Verify
GET /vat-report-quarterly?year=2025&quarter=Q3
```

### Test 2: All Categories
```bash
# Use all categories test
POST /process-invoices
Body: test_inputs_all_categories.json

# Verify all categories appear
GET /vat-report-yearly?year=2025
```

### Test 3: Multiple Quarters
```bash
# Use extended test
POST /process-invoices
Body: test_inputs_extended.json

# Test each quarter
GET /vat-report-quarterly?year=2025&quarter=Q2
GET /vat-report-quarterly?year=2025&quarter=Q3
GET /vat-report-quarterly?year=2025&quarter=Q4

# Test yearly with quarterly breakdown
GET /vat-report-yearly?year=2025
```

### Test 4: Edge Cases
```bash
# Use edge cases test
POST /process-invoices
Body: test_inputs_edge_cases.json

# Verify edge cases handled correctly
GET /vat-report-yearly?year=2025
```

### Test 5: Multiple Years
```bash
# Use multiple years test
POST /process-invoices
Body: test_inputs_multiple_years.json

# Test each year
GET /vat-report-yearly?year=2024
GET /vat-report-yearly?year=2025
GET /vat-report-yearly?year=2026
```

### Test 6: Comprehensive Test
```bash
# Process all test files
POST /process-invoices
Body: test_inputs_new_format.json

POST /process-invoices
Body: test_inputs_extended.json

# Generate comprehensive report
GET /vat-report-yearly?year=2025
GET /dreport?year=2025&quarter=Q1
```

## Expected Results Summary

### After Processing test_inputs_new_format.json (20 invoices)
- **Q1 Total**: 13 invoices
- **Categories**: 1a, 1b, 1c, 1e, 2a, 3a, 3b, 3c, 4a, 4b, 5a
- **VAT Collected**: 255.00 (Q1)
- **VAT Deductible**: 510.00 (Q1)

### After Processing test_inputs_extended.json (22 invoices)
- **Q2**: 3 invoices
- **Q3**: 9 invoices
- **Q4**: 10 invoices
- **Total**: 22 invoices across Q2-Q4

### After Processing test_inputs_all_categories.json (11 invoices)
- **All 11 categories** represented
- One invoice per category
- Easy to verify category mapping

## Testing Checklist

- [ ] Process minimal test - verify basic functionality
- [ ] Process all categories test - verify all categories appear
- [ ] Process extended test - verify multiple quarters
- [ ] Process edge cases - verify edge cases handled
- [ ] Process multiple years - verify year filtering
- [ ] Generate quarterly reports - verify Q1, Q2, Q3, Q4
- [ ] Generate monthly reports - verify specific months
- [ ] Generate yearly reports - verify yearly totals
- [ ] Generate dreport - verify Dutch tax format
- [ ] Test credit notes - verify negative amounts
- [ ] Test large amounts - verify calculations
- [ ] Test decimal precision - verify rounding

## File Sizes

- `test_inputs_minimal.json`: 3 invoices (~1 KB)
- `test_inputs_new_format.json`: 20 invoices (~8 KB)
- `test_inputs_extended.json`: 22 invoices (~9 KB) ⭐ NEW
- `test_inputs_edge_cases.json`: 20 invoices (~7 KB) ⭐ NEW
- `test_inputs_multiple_years.json`: 6 invoices (~2 KB) ⭐ NEW
- `test_inputs_all_categories.json`: 11 invoices (~4 KB) ⭐ NEW

**Total**: 82 test invoices across all files

## Usage Examples

### PowerShell
```powershell
# Test minimal
$body = Get-Content -Path "test_inputs_minimal.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/process-invoices" `
  -Method Post -Headers @{"X-User-ID" = "369"; "Content-Type" = "application/json"} -Body $body

# Test extended
$body = Get-Content -Path "test_inputs_extended.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/process-invoices" `
  -Method Post -Headers @{"X-User-ID" = "369"; "Content-Type" = "application/json"} -Body $body
```

### cURL
```bash
# Test all categories
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d @test_inputs_all_categories.json

# Test edge cases
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d @test_inputs_edge_cases.json
```

## Notes

- All test files use the new format with `VAT Category (NL) Code` and `VAT Category (NL) Description`
- Dates are spread across different quarters/years for comprehensive testing
- Includes various edge cases for robust testing
- All amounts are in EUR
- VAT calculations are included for verification

