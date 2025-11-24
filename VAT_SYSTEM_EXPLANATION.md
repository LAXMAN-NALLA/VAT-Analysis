# Complete VAT System Explanation

## Table of Contents
1. [VAT Category Assignment Logic](#vat-category-assignment-logic)
2. [System Flow Overview](#system-flow-overview)
3. [VAT Payable Calculation](#vat-payable-calculation)
4. [Detailed Examples](#detailed-examples)

---

## VAT Category Assignment Logic

### Overview
The VAT category assignment uses **Multi-Field Logic** - it checks THREE fields in priority order to determine the correct VAT category code:

1. **VAT Category String** (`vat_category` field)
2. **Transaction Type** (`type` field: "Sales" or "Purchase")
3. **VAT Percentage** (`vat_percentage` field) - **CRITICAL** for resolving ambiguity

### Priority Order

```
Step 1: Check VAT Category String
   ↓
Step 2: Check Transaction Type (Sales/Purchase)
   ↓
Step 3: Check VAT Percentage (21%, 9%, 0%)
   ↓
Result: VAT Category Code (1a, 1b, 1c, 2a, 3a, 3b, 4a, 4b, 4c, 5b)
```

### Detailed Mapping Logic

The mapping function `map_vat_category_simple()` in `app.py` (lines 470-576) implements this logic:

#### 1. Standard VAT / Standard Rate

**For Sales:**
- `"Standard VAT"` + `"Sales"` + `21%` → **1a** (Standard rate sales)
- `"Standard VAT"` + `"Sales"` + `9%` → **1b** (Reduced rate sales)
- `"Standard VAT"` + `"Sales"` + `Other%` → **1a** (Default to standard)

**For Purchases:**
- `"Standard VAT"` + `"Purchase"` + `Any%` → **5b** (Input VAT on domestic purchases)

**Key Point:** The percentage is **critical** here - it distinguishes between 21% (1a) and 9% (1b) for sales.

#### 2. Reduced Rate

**For Sales:**
- `"Reduced Rate"` + `"Sales"` + `Any%` → **1b** (Reduced rate sales - 9%)

**For Purchases:**
- `"Reduced Rate"` + `"Purchase"` + `Any%` → **5b** (Input VAT on domestic purchases)

#### 3. Zero Rated

**For Sales:**
- `"Zero Rated"` + `"Sales"` + `0%` → **1c** (General exports / Zero-rated sales)

**For Purchases:**
- `"Zero Rated"` + `"Purchase"` + `0%` → **4a** (Assumes EU Goods Purchase)

#### 4. EU Goods

**For Sales:**
- `"EU Goods"` + `"Sales"` + `0%` → **3a** (Goods supplied to EU countries)

**For Purchases:**
- `"EU Goods"` + `"Purchase"` + `0%` → **4a** (Goods purchased from EU countries)

#### 5. EU Services

**For Sales:**
- `"EU Services"` + `"Sales"` + `0%` → **3b** (Services supplied to EU countries)

**For Purchases:**
- `"EU Services"` + `"Purchase"` + `0%` → **4b** (Services purchased from EU countries)

#### 6. Reverse Charge

**For Purchases:**
- `"Reverse Charge"` + `"Purchase"` + `0%` → **2a** (Reverse-charge supplies)

**Note:** Reverse charge is only for purchases, not sales.

#### 7. Import

**For Purchases:**
- `"Import"` + `"Purchase"` + `0%` → **4c** (Imports from non-EU countries)

#### 8. Fallback Logic

If the VAT category string is not recognized, the system falls back to:

**For Sales:**
- `21%` → **1a**
- `9%` → **1b**
- `0%` → **1c**
- `Other%` → **1a** (Default)

**For Purchases:**
- `0%` → **2a** (Default to reverse charge)
- `Other%` → **5b** (Default to domestic input VAT)

### VAT Category Codes Reference

| Code | Category Name | Description | VAT Rate |
|------|---------------|-------------|----------|
| **1a** | Sales Taxed at Standard Rate (21%) | Domestic sales at 21% VAT | 21% |
| **1b** | Sales Taxed at Reduced Rate (9%) | Domestic sales at 9% VAT (food, books) | 9% |
| **1c** | Sales Taxed at 0% (EU and Export) | Zero-rated sales (exports, EU supplies) | 0% |
| **2a** | Reverse-Charge Supplies | Reverse charge purchases | 0% |
| **3a** | Supplies of Goods to EU Countries | Goods sold to EU customers | 0% |
| **3b** | Supplies of Services to EU Countries | Services sold to EU customers | 0% |
| **4a** | Purchases of Goods from EU Countries | Goods bought from EU suppliers | 0% |
| **4b** | Purchases of Services from EU Countries | Services bought from EU suppliers | 0% |
| **4c** | Purchases from Non-EU (Imports) | Imports from non-EU countries | 0% |
| **5b** | Input VAT on Domestic Purchases | Domestic purchases with VAT | 21% or 9% |

---

## System Flow Overview

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   1. INVOICE INPUT                           │
│  User sends JSON array of analyzed invoices via API          │
│  POST /process-invoices                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   2. VALIDATION & PROCESSING                 │
│  • Validate required fields                                  │
│  • Extract year from date                                    │
│  • Check for duplicates (by file_name)                       │
│  • Map transaction type (Sales/Purchase)                     │
│  • Map VAT category (using multi-field logic)                │
│  • Normalize amounts                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   3. DATA TRANSFORMATION                      │
│  Transform input format to internal invoice structure:       │
│  {                                                           │
│    "invoice_no": "...",                                      │
│    "date": "...",                                            │
│    "invoice_to": "...",                                      │
│    "transactions": [{                                        │
│      "description": "...",                                   │
│      "amount_pre_vat": 1000.00,                              │
│      "vat_percentage": "21%",                                │
│      "vat_category": "1a"                                    │
│    }],                                                        │
│    "subtotal": 1000.00,                                      │
│    "vat_amount": 210.00,                                     │
│    "total_amount": 1210.00,                                  │
│    "transaction_type": "sale",                              │
│    "source_file": "invoice.pdf"                              │
│  }                                                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   4. STORAGE                                 │
│  Store in in-memory dictionary:                             │
│  user_vat_data[user_id][year]["invoices"] = [...]           │
│                                                              │
│  Organized by:                                               │
│  • User ID                                                   │
│  • Year (extracted from invoice date)                        │
│  • Invoice list                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   5. REPORT GENERATION                       │
│  User requests report:                                       │
│  • GET /vat-report-quarterly?year=2025&quarter=Q3             │
│  • GET /vat-report-monthly?year=2025&month=Sep               │
│  • GET /vat-report-yearly?year=2025                         │
│                                                              │
│  Process:                                                    │
│  1. Retrieve invoices for period                            │
│  2. Filter by quarter/month/year                            │
│  3. Group by VAT category                                    │
│  4. Calculate totals per category                            │
│  5. Calculate VAT collected/deductible/payable              │
│  6. Format as report JSON                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   6. OUTPUT                                 │
│  Return structured VAT report with:                           │
│  • Categories with transactions                              │
│  • Totals per category                                       │
│  • VAT calculation (collected, deductible, payable)           │
│  • Quarterly breakdown (for yearly reports)                  │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Processing Steps

#### Step 1: Invoice Input (`/process-invoices`)

**Input Format:**
```json
[
  {
    "date": "2025-09-25",
    "type": "Purchase",
    "net_amount": 4357.46,
    "vat_amount": null,
    "vat_category": "Zero Rated",
    "vat_percentage": "0",
    "description": "SEPTEMBER SALES",
    "vendor_name": "PAE Business Ltd",
    "gross_amount": 4357.45,
    "file_name": "Invoice_26411.pdf"
  }
]
```

**Processing (app.py lines 327-468):**
1. Validate `X-User-ID` header
2. Validate JSON array format
3. For each invoice:
   - Extract date and determine year
   - Check for duplicates (by `file_name`)
   - Map transaction type: `"Sales"` → `"sale"`, `"Purchase"` → `"purchase"`
   - Map VAT category using `map_vat_category_simple()`
   - Normalize amounts (handle null, string, numeric)
   - Build internal invoice structure
   - Store in `user_vat_data[user_id][year]["invoices"]`

#### Step 2: VAT Category Mapping (`map_vat_category_simple()`)

**Location:** `app.py` lines 470-576

**Logic Flow:**
```python
1. Normalize inputs (lowercase, strip)
2. Parse VAT percentage (handle "21", "21%", etc.)
3. Check category string in priority order:
   - "Standard VAT" / "Standard Rate"
   - "Reduced Rate"
   - "Zero Rated"
   - "EU Goods"
   - "EU Services"
   - "Reverse Charge"
   - "Import"
4. Apply transaction type (Sales/Purchase)
5. Apply VAT percentage (for Standard VAT)
6. Return category code (1a, 1b, 1c, 2a, 3a, 3b, 4a, 4b, 4c, 5b)
```

#### Step 3: Report Generation

**Quarterly Report** (`/vat-report-quarterly`):
- Lines 1093-1289 in `app.py`
- Filters invoices by quarter (Q1-Q4)
- Groups by VAT category
- Calculates totals per category
- Calculates VAT collected/deductible/payable

**Monthly Report** (`/vat-report-monthly`):
- Lines 1485-1662 in `app.py`
- Same as quarterly but filters by specific month

**Yearly Report** (`/vat-report-yearly`):
- Lines 1291-1481 in `app.py`
- Includes quarterly breakdown
- Aggregates all data for the year

---

## VAT Payable Calculation

### Formula

```
VAT Payable = VAT Collected - VAT Deductible
```

Where:
- **VAT Collected** = Sum of VAT from all **Sales** transactions
- **VAT Deductible** = Sum of VAT from all **Purchase** transactions

### Calculation Logic

#### Step 1: Identify Transaction Type

For each invoice, check `transaction_type`:
- `"sale"` → VAT is **collected** (Output VAT)
- `"purchase"` → VAT is **deductible** (Input VAT)

#### Step 2: Extract VAT Amount

For each invoice:
```python
vat_amount = normalize_amount(invoice.get("vat_amount", 0))
```

**Note:** The system handles:
- Null values → 0.0
- String values (e.g., "210.00") → 210.0
- Numeric values → Direct use

#### Step 3: Categorize VAT

```python
if transaction_type == "sale":
    vat_collected += vat_amount
else:
    vat_deductible += vat_amount
```

#### Step 4: Calculate VAT Payable

```python
vat_payable = vat_collected - vat_deductible
```

### VAT Distribution for Multiple Transactions

When an invoice has multiple line items, VAT is distributed proportionally:

```python
# Calculate total net amount
total_net = sum(transaction.amount_pre_vat for transaction in transactions)

# Distribute VAT proportionally
for transaction in transactions:
    vat_amount = (transaction.amount_pre_vat / total_net) * invoice_vat_total
```

**Example:**
- Invoice total VAT: €210.00
- Transaction 1: €600.00 (60% of total)
- Transaction 2: €400.00 (40% of total)
- Total: €1,000.00

**Distribution:**
- Transaction 1 VAT: €210.00 × (600/1000) = €126.00
- Transaction 2 VAT: €210.00 × (400/1000) = €84.00

### VAT Calculation in Reports

**Location:** `app.py` lines 1173-1267 (Quarterly), 1355-1458 (Yearly)

**Process:**
1. Initialize counters: `vat_collected = 0.0`, `vat_deductible = 0.0`
2. For each invoice in the period:
   - Get invoice VAT amount
   - Check transaction type
   - Add to appropriate counter
3. Calculate: `vat_payable = vat_collected - vat_deductible`
4. Round to 2 decimal places

### Result Interpretation

- **Positive VAT Payable** (`vat_payable > 0`): You owe money to tax authorities
- **Negative VAT Payable** (`vat_payable < 0`): You are due a refund
- **Zero VAT Payable** (`vat_payable = 0`): Balanced (no payment/refund)

### Example Calculation

**Sales Invoices:**
- Invoice 1: €1,000.00 net, €210.00 VAT (21%) → VAT Collected: €210.00
- Invoice 2: €500.00 net, €45.00 VAT (9%) → VAT Collected: €45.00
- Invoice 3: €2,000.00 net, €0.00 VAT (0% - export) → VAT Collected: €0.00

**Purchase Invoices:**
- Invoice 4: €3,000.00 net, €0.00 VAT (0% - reverse charge) → VAT Deductible: €0.00
- Invoice 5: €1,800.00 net, €378.00 VAT (21%) → VAT Deductible: €378.00

**Calculation:**
```
VAT Collected = 210.00 + 45.00 + 0.00 = €255.00
VAT Deductible = 0.00 + 378.00 = €378.00
VAT Payable = 255.00 - 378.00 = -€123.00
```

**Result:** You are due a refund of €123.00

---

## Detailed Examples

### Example 1: Standard VAT Sales (21%)

**Input:**
```json
{
  "date": "2025-01-15",
  "type": "Sales",
  "net_amount": 1000.00,
  "vat_amount": 210.00,
  "vat_category": "Standard VAT",
  "vat_percentage": "21",
  "file_name": "invoice_001.pdf"
}
```

**Processing:**
1. Transaction type: `"Sales"` → `"sale"`
2. VAT category mapping:
   - Category: `"Standard VAT"`
   - Type: `"sale"`
   - Percentage: `21`
   - Result: **1a** (Standard rate sales at 21%)
3. Storage: Invoice stored with `vat_category: "1a"`

**Report Output:**
```json
{
  "categories": {
    "1a": {
      "name": "Sales Taxed at the Standard Rate (21%)",
      "transactions": [{
        "date": "2025-01-15",
        "invoice_no": "invoice_001",
        "net_amount": 1000.00,
        "vat_percentage": 21,
        "vat_amount": 210.00
      }],
      "totals": {
        "net": 1000.00,
        "vat": 210.00
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 210.00,
    "vat_deductible": 0.00,
    "vat_payable": 210.00
  }
}
```

### Example 2: Reduced Rate Sales (9%)

**Input:**
```json
{
  "date": "2025-01-20",
  "type": "Sales",
  "net_amount": 500.00,
  "vat_amount": 45.00,
  "vat_category": "Standard VAT",
  "vat_percentage": "9",
  "file_name": "invoice_002.pdf"
}
```

**Processing:**
1. Transaction type: `"Sales"` → `"sale"`
2. VAT category mapping:
   - Category: `"Standard VAT"`
   - Type: `"sale"`
   - Percentage: `9` ← **KEY**: This resolves to 1b, not 1a!
   - Result: **1b** (Reduced rate sales at 9%)

**Key Point:** Even though category is "Standard VAT", the percentage (9%) determines it's actually reduced rate (1b).

### Example 3: Reverse Charge Purchase

**Input:**
```json
{
  "date": "2025-03-05",
  "type": "Purchase",
  "net_amount": 3000.00,
  "vat_amount": null,
  "vat_category": "Reverse Charge",
  "vat_percentage": "0",
  "file_name": "invoice_003.pdf"
}
```

**Processing:**
1. Transaction type: `"Purchase"` → `"purchase"`
2. VAT category mapping:
   - Category: `"Reverse Charge"`
   - Type: `"purchase"`
   - Result: **2a** (Reverse-charge supplies)
3. VAT amount: `null` → `0.00`

**Report Output:**
```json
{
  "categories": {
    "2a": {
      "name": "Reverse-Charge Supplies",
      "transactions": [{
        "net_amount": 3000.00,
        "vat_amount": 0.00
      }],
      "totals": {
        "net": 3000.00,
        "vat": 0.00
      }
    }
  },
  "vat_calculation": {
    "vat_collected": 0.00,
    "vat_deductible": 0.00,  // Reverse charge has no VAT
    "vat_payable": 0.00
  }
}
```

**Note:** Reverse charge means you account for VAT yourself, so no VAT is shown on the invoice.

### Example 4: EU Goods Purchase

**Input:**
```json
{
  "date": "2025-06-18",
  "type": "Purchase",
  "net_amount": 2500.00,
  "vat_amount": null,
  "vat_category": "Zero Rated",
  "vat_percentage": "0",
  "file_name": "invoice_004.pdf"
}
```

**Processing:**
1. Transaction type: `"Purchase"` → `"purchase"`
2. VAT category mapping:
   - Category: `"Zero Rated"`
   - Type: `"purchase"`
   - Result: **4a** (Assumes EU Goods Purchase)

**Note:** "Zero Rated" for purchases defaults to 4a (EU Goods), not 4b (EU Services).

### Example 5: Complete Quarterly Report

**Input Data:**
- Q3 Sales: €3,000.00 net, €630.00 VAT (21%) - Category 1a
- Q3 Sales: €900.00 net, €81.00 VAT (9%) - Category 1b
- Q3 Purchase: €1,500.00 net, €315.00 VAT (21%) - Category 5b

**Report Output:**
```json
{
  "period": "Q3 2025",
  "categories": {
    "1a": {
      "totals": {"net": 3000.00, "vat": 630.00}
    },
    "1b": {
      "totals": {"net": 900.00, "vat": 81.00}
    },
    "5b": {
      "totals": {"net": 1500.00, "vat": 315.00}
    }
  },
  "vat_calculation": {
    "vat_collected": 711.00,    // 630.00 + 81.00
    "vat_deductible": 315.00,    // From purchase
    "vat_payable": 396.00        // 711.00 - 315.00
  }
}
```

---

## Key Takeaways

1. **VAT Category Assignment** uses multi-field logic:
   - Category string → Transaction type → VAT percentage
   - Percentage is **critical** for "Standard VAT" to distinguish 21% (1a) vs 9% (1b)

2. **System Flow**:
   - Input → Validation → Category Mapping → Storage → Report Generation

3. **VAT Payable Calculation**:
   - VAT Collected (from sales) - VAT Deductible (from purchases)
   - Positive = owe money, Negative = refund due

4. **VAT Distribution**:
   - For multiple transactions, VAT is distributed proportionally based on net amounts

5. **Transaction Types**:
   - Sales → VAT Collected (Output VAT)
   - Purchases → VAT Deductible (Input VAT)

---

## Code References

- **VAT Category Mapping**: `app.py` lines 470-576 (`map_vat_category_simple()`)
- **Invoice Processing**: `app.py` lines 327-468 (`process_invoices_simple()`)
- **Quarterly Report**: `app.py` lines 1093-1289 (`get_vat_report_quarterly()`)
- **Yearly Report**: `app.py` lines 1291-1481 (`get_vat_report_yearly()`)
- **Monthly Report**: `app.py` lines 1485-1662 (`get_vat_report_monthly()`)
- **VAT Payable Calculation**: `app.py` lines 1032-1089 (`get_vat_payable()`)
- **Amount Normalization**: `processor.py` lines 168-188 (`normalize_amount()`)

