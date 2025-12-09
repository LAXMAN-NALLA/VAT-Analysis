# VAT Category Processing Update

## Overview

The system has been updated to use **pre-classified Dutch VAT category codes** instead of performing classification internally. This change simplifies the processing and ensures accuracy by using the provided classification.

## What Changed

### Before (Old Approach)
- System received `vat_category` as a string (e.g., "Standard VAT", "Zero Rated")
- System performed complex mapping logic to determine Dutch VAT return category code
- Mapping considered: category string, transaction type, VAT percentage, and country

### After (New Approach)
- System receives **`VAT Category (NL) Code`** directly (e.g., "1a", "1b", "3b", "4a")
- System receives **`VAT Category (NL) Description`** for human-readable labels
- System uses the provided code directly - **no classification needed**
- Mapping function kept as fallback for backward compatibility

## New Input Fields

### Required Fields (New)
```json
{
  "VAT Category (NL) Code": "1a",
  "VAT Category (NL) Description": "Sales taxed at the standard rate (21%)"
}
```

### Field Name Variations Accepted
The system accepts multiple field name formats:
- `VAT Category (NL) Code` (primary)
- `vat_category_nl_code`
- `vat_category_code`
- `VAT Category Code`

- `VAT Category (NL) Description` (primary)
- `vat_category_nl_description`
- `vat_category_description`
- `VAT Category Description`

## Dutch VAT Return Categories

### Sales Categories
- **1a**: Sales taxed at standard rate (21%) - NL customer
- **1b**: Sales taxed at reduced rate (9%) - NL customer
- **1c**: Sales taxed at other rates / zero-rated supplies (0% but not reverse charge)
- **1e**: Exempt / out-of-scope supplies
- **2a**: Domestic reverse-charge supplies
- **3a**: Intra-EU goods B2B - EU (not NL) customer, goods, 0% VAT, VAT ID present
- **3b**: Intra-EU services B2B - EU (not NL) customer, services, 0% VAT, VAT ID present
- **3c**: Intra-EU B2C goods (distance/installation sales without VAT ID)

### Purchase Categories
- **4a**: Purchases of goods from non-EU countries
- **4b**: Purchases of goods/services from EU countries (non-NL EU vendor)
- **5a**: Domestic purchases with Dutch VAT (NL vendor and VAT > 0)

## Example Input

```json
[
  {
    "date": "2025-09-17",
    "type": "Sales",
    "net_amount": 967.6,
    "vat_amount": 203.19,
    "vat_percentage": "21",
    "description": "Premier Subscription Package",
    "customer_name": "PAE NL B.V.",
    "file_name": "24700492.pdf",
    "VAT Category (NL) Code": "1a",
    "VAT Category (NL) Description": "Sales taxed at the standard rate (21%)"
  },
  {
    "date": "2025-09-25",
    "type": "Purchase",
    "net_amount": 4357.46,
    "vat_amount": null,
    "vat_percentage": "0",
    "description": "SEPTEMBER SALES",
    "vendor_name": "PAE Business Ltd",
    "file_name": "Invoice_26411.pdf",
    "VAT Category (NL) Code": "4a",
    "VAT Category (NL) Description": "Purchases of goods from EU countries"
  },
  {
    "date": "2025-09-15",
    "type": "Sales",
    "net_amount": 5000.00,
    "vat_amount": 0.00,
    "vat_percentage": "0",
    "description": "IT Consulting Services",
    "customer_name": "German Tech Solutions GmbH",
    "file_name": "invoice_eu_service.pdf",
    "VAT Category (NL) Code": "3b",
    "VAT Category (NL) Description": "Supplies of services to EU countries"
  }
]
```

## Backward Compatibility

The system maintains backward compatibility:
- If `VAT Category (NL) Code` is **not provided**, the system will:
  1. Look for old `vat_category` field
  2. Attempt to map it using the existing `map_vat_category_simple()` function
  3. Use the old category string as description if no description provided

## Storage

The system now stores:
- `vat_category`: The Dutch VAT return category code (e.g., "1a", "3b", "4a")
- `vat_category_description`: Human-readable description of the category

Both fields are included in:
- Invoice transaction records
- VAT reports (quarterly, monthly, yearly)
- Transaction lists
- Summary endpoints

## Benefits

1. **Accuracy**: Uses pre-classified codes, eliminating classification errors
2. **Simplicity**: No complex mapping logic needed
3. **Transparency**: Description field provides clear category meaning
4. **Flexibility**: Supports all Dutch VAT return categories
5. **Backward Compatible**: Still works with old format

## Migration Guide

### For New Integrations
Use the new format with `VAT Category (NL) Code` and `VAT Category (NL) Description` fields.

### For Existing Integrations
Continue using the old format - the system will automatically map it. However, consider migrating to the new format for better accuracy and clarity.

## API Endpoints Affected

- **POST /process-invoices**: Now accepts new fields
- **GET /vat-report-quarterly**: Returns `vat_category_description` in transactions
- **GET /vat-report-monthly**: Returns `vat_category_description` in transactions
- **GET /vat-report-yearly**: Returns `vat_category_description` in transactions
- **GET /transactions**: Returns `vat_category_description` in transactions
- **GET /vat-summary**: Returns `vat_category` (code) in transactions

## Testing

Test with the new format:
```bash
POST /process-invoices
Headers:
  X-User-ID: 369
  Content-Type: application/json
Body:
[
  {
    "date": "2025-09-17",
    "type": "Sales",
    "net_amount": 1000.00,
    "vat_amount": 210.00,
    "vat_percentage": "21",
    "description": "Test Invoice",
    "customer_name": "Test Customer",
    "file_name": "test.pdf",
    "VAT Category (NL) Code": "1a",
    "VAT Category (NL) Description": "Sales taxed at the standard rate (21%)"
  }
]
```

Verify the response includes the category code and description in stored transactions.

