# Test Scenarios - All VAT Categories

This document describes the test scenarios included in `sample_all_vat_categories.json`.

## Overview

The sample file contains **27 invoices** covering all VAT categories across all 4 quarters of 2025.

## VAT Categories Covered

### Sales Transactions (Output VAT)

#### 1a - Standard VAT (21%) - Sales
- **Files**: `INV_001`, `INV_011`, `INV_016`, `INV_022`
- **Description**: Domestic sales at standard 21% VAT rate
- **Examples**: Product sales, general services
- **Expected Mapping**: `vat_category: "Standard VAT"` → Code `1a`

#### 1b - Reduced Rate (9%) - Sales
- **Files**: `INV_002`, `INV_012`, `INV_020`
- **Description**: Domestic sales at reduced 9% VAT rate
- **Examples**: Food products, books, medicines
- **Expected Mapping**: `vat_category: "Reduced Rate"` → Code `1b`

#### 1c - Zero Rated - Sales
- **Files**: `INV_003`, `INV_015`, `INV_026`
- **Description**: Sales with 0% VAT (exports, EU supplies)
- **Examples**: Exports to non-EU countries
- **Expected Mapping**: `vat_category: "Zero Rated"` → Code `1c`

#### 3a - Supplies of Goods to EU Countries
- **Files**: `INV_004`, `INV_018`
- **Description**: Goods supplied to EU member states
- **Examples**: Physical products shipped to EU customers
- **Expected Mapping**: `vat_category: "EU Goods"` → Code `3a`

#### 3b - Supplies of Services to EU Countries
- **Files**: `INV_005`, `INV_024`
- **Description**: Services supplied to EU member states
- **Examples**: Consulting, software services to EU customers
- **Expected Mapping**: `vat_category: "EU Services"` → Code `3b`

### Purchase Transactions (Input VAT)

#### 2a - Reverse Charge Supplies
- **Files**: `INV_006`, `INV_013`, `INV_023`
- **Description**: Services received from foreign vendors (reverse charge mechanism)
- **Examples**: IT services from UK, consulting from US
- **Expected Mapping**: `vat_category: "Reverse Charge"` → Code `2a`

#### 4a - Purchases of Goods from EU Countries
- **Files**: `INV_007`, `INV_017`
- **Description**: Goods purchased from EU member states
- **Examples**: Products bought from German/Belgian suppliers
- **Expected Mapping**: `vat_category: "Zero Rated"` (Purchase) → Code `4a`

#### 4b - Purchases of Services from EU Countries
- **Files**: `INV_008`, `INV_025`
- **Description**: Services purchased from EU member states
- **Examples**: Services from French/Polish companies
- **Expected Mapping**: `vat_category: "EU Services"` (Purchase) → Code `4b`

#### 4c - Purchases from Non-EU Countries (Imports)
- **Files**: `INV_009`, `INV_019`
- **Description**: Goods imported from non-EU countries
- **Examples**: Imports from US, China
- **Expected Mapping**: `vat_category: "Import"` → Code `4c`

#### 5b - Input VAT on Domestic Purchases
- **Files**: `INV_010`, `INV_014`, `INV_021`, `INV_027`
- **Description**: Domestic purchases with VAT
- **Examples**: Office supplies, equipment from Dutch suppliers
- **Expected Mapping**: `vat_category: "Standard VAT"` (Purchase) → Code `5b`

## Test Scenarios by Quarter

### Q1 2025 (Jan-Mar)
- **Invoices**: 10 invoices
- **Sales**: 1a, 1b, 1c, 3a, 3b
- **Purchases**: 2a, 4a, 4b, 4c, 5b

### Q2 2025 (Apr-Jun)
- **Invoices**: 5 invoices
- **Sales**: 1a, 1b, 1c
- **Purchases**: 2a, 5b

### Q3 2025 (Jul-Sep)
- **Invoices**: 6 invoices
- **Sales**: 1a, 1b, 3a
- **Purchases**: 4a, 4c, 5b

### Q4 2025 (Oct-Dec)
- **Invoices**: 6 invoices
- **Sales**: 1a, 1c, 3b
- **Purchases**: 2a, 4b, 5b

## How to Test

### 1. Process All Invoices
```bash
POST /process-invoices
Headers: X-User-ID: 369
Body: [paste contents of sample_all_vat_categories.json]
```

### 2. Test Quarterly Reports

**Q1 2025:**
```bash
GET /vat-report-quarterly?year=2025&quarter=Q1
Headers: X-User-ID: 369
```

**Q2 2025:**
```bash
GET /vat-report-quarterly?year=2025&quarter=Q2
Headers: X-User-ID: 369
```

**Q3 2025:**
```bash
GET /vat-report-quarterly?year=2025&quarter=Q3
Headers: X-User-ID: 369
```

**Q4 2025:**
```bash
GET /vat-report-quarterly?year=2025&quarter=Q4
Headers: X-User-ID: 369
```

### 3. Test Monthly Reports

**January 2025:**
```bash
GET /vat-report-monthly?year=2025&month=1
Headers: X-User-ID: 369
```

**September 2025:**
```bash
GET /vat-report-monthly?year=2025&month=9
Headers: X-User-ID: 369
```

### 4. Test Yearly Report
```bash
GET /vat-report-yearly?year=2025
Headers: X-User-ID: 369
```

## Expected Results

### VAT Collected (Output VAT)
- **1a (Standard 21%)**: Should sum all invoices with `vat_category: "Standard VAT"` and `type: "Sales"`
- **1b (Reduced 9%)**: Should sum all invoices with `vat_category: "Reduced Rate"` and `type: "Sales"`
- **1c (Zero Rated)**: Should show transactions but VAT = 0
- **3a (EU Goods)**: Should show transactions but VAT = 0
- **3b (EU Services)**: Should show transactions but VAT = 0

### VAT Deductible (Input VAT)
- **2a (Reverse Charge)**: Should show transactions but VAT = 0
- **4a (EU Goods)**: Should show transactions but VAT = 0
- **4b (EU Services)**: Should show transactions but VAT = 0
- **4c (Imports)**: Should show transactions but VAT = 0
- **5b (Domestic VAT)**: Should sum all invoices with `vat_category: "Standard VAT"` and `type: "Purchase"`

### VAT Payable Calculation
```
VAT Payable = VAT Collected - VAT Deductible
```

## Verification Checklist

- [ ] All 27 invoices processed successfully
- [ ] All VAT categories mapped correctly
- [ ] Quarterly reports show correct transactions per quarter
- [ ] Monthly reports show correct transactions per month
- [ ] Yearly report aggregates all quarters correctly
- [ ] VAT amounts calculated correctly (21%, 9%, 0%)
- [ ] Net amounts match input data
- [ ] Gross amounts calculated correctly (net + VAT)
- [ ] Transaction types (Sales/Purchase) categorized correctly
- [ ] Duplicate detection works (try processing same file twice)

## Sample cURL Commands

### Process Invoices
```bash
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: 369" \
  -H "Content-Type: application/json" \
  -d @sample_all_vat_categories.json
```

### Get Q1 Report
```bash
curl -X GET "http://localhost:8000/vat-report-quarterly?year=2025&quarter=Q1" \
  -H "X-User-ID: 369"
```

### Get Yearly Report
```bash
curl -X GET "http://localhost:8000/vat-report-yearly?year=2025" \
  -H "X-User-ID: 369"
```

## Notes

- All amounts are in EUR
- Dates are in YYYY-MM-DD format
- VAT amounts are null for zero-rated transactions
- File names are unique to prevent duplicates
- Some invoices include optional fields (country, VAT IDs) for testing

