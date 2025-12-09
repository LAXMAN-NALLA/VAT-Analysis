# Interview Quick Reference - One Page Cheat Sheet

## 🎯 Project in 30 Seconds
**Dutch VAT Analysis System** - FastAPI backend that processes invoice data and generates VAT reports for Dutch tax compliance.

## 🏗️ Architecture
```
Client → FastAPI (app.py) → In-Memory Storage → Reports
```

## 📦 Tech Stack
- **Backend**: FastAPI (Python)
- **Storage**: In-memory dictionaries (`defaultdict`)
- **Validation**: Pydantic
- **Server**: Uvicorn

## 🔑 Key Endpoints (12 total)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/process-invoices` | POST | Store invoice data |
| `/vat-report-quarterly` | GET | Quarterly report |
| `/vat-report-monthly` | GET | Monthly report |
| `/vat-report-yearly` | GET | Yearly report |
| `/dreport` | GET | Dutch tax format |
| `/company-details` | POST/GET | Company info |
| `/vat-payable` | GET | Calculate VAT payable |
| `/clear-user-data` | DELETE | Clear data |
| `/health` | GET | Health check |

## 📊 Data Structure

```python
user_vat_data = {
    "user_id": {
        "2025": {
            "invoices": [
                {
                    "invoice_no": "INV_001",
                    "date": "2025-01-15",
                    "vat_category": "1a",  # Dutch VAT code
                    "transactions": [...],
                    "vat_amount": 210.00,
                    "transaction_type": "sale"
                }
            ]
        }
    }
}
```

## 🇳🇱 Dutch VAT Categories

**Sales (Output VAT)**:
- 1a: Standard 21% (NL)
- 1b: Reduced 9% (NL)
- 1c: Zero-rated (NL)
- 1e: Exempt
- 2a: Reverse-charge
- 3a: Goods to EU
- 3b: Services to EU
- 3c: Distance sales EU

**Purchases (Input VAT)**:
- 4a: Goods from non-EU
- 4b: Goods/services from EU
- 5a: Domestic with VAT

## 🧮 VAT Calculations

```python
# VAT Collected (Sales)
vat_collected = sum(vat for sales)

# VAT Deductible (Purchases)
vat_deductible = sum(vat for purchases)

# VAT Payable
vat_payable = vat_collected - vat_deductible

# Dreport Section 5
5a = Sum of sections 1-4 VAT (output)
5b = Sum of purchase VAT (input)
5c = 5a - 5b (payable)
```

## 🔄 Data Flow

1. **Input**: POST `/process-invoices` with JSON array
2. **Process**: Validate → Check duplicates → Store
3. **Output**: GET report endpoints → Filter → Calculate → Return JSON

## ✨ Key Features

- ✅ Pre-classified VAT codes (no mapping)
- ✅ Duplicate prevention (file_name + invoice_number)
- ✅ User isolation (X-User-ID header)
- ✅ Multiple report formats
- ✅ All Dutch VAT categories

## 🎯 Recent Improvements

1. **Direct VAT Code Input**: Accepts `VAT Category (NL) Code` directly
2. **Code Cleanup**: Removed 6 endpoints, ~15% reduction
3. **Better Flexibility**: Handles multiple field name variations

## 💡 Key Code Patterns

```python
# Field name flexibility
vat_code = get_field_value("VAT Category (NL) Code", "vat_category_nl_code", default="")

# Duplicate check
is_duplicate = any(inv.get("source_file") == file_name for inv in existing)

# Quarter filtering
quarter_months = {"Q1": ["Jan", "Feb", "Mar"], ...}
if month in target_months: process()

# Category aggregation
categories[vat_category]["totals"]["vat"] += vat_amount
```

## 🚀 Scalability Ideas

- Replace in-memory with PostgreSQL
- Add Redis caching
- JWT authentication
- Background jobs (Celery)
- API versioning
- Monitoring (Prometheus)

## 📝 Common Questions

**Q: Why FastAPI?**  
A: Fast, auto-docs, type hints, async support

**Q: Why in-memory storage?**  
A: Simple, fast for MVP, easily replaceable

**Q: How prevent duplicates?**  
A: Check file_name and invoice_number before storing

**Q: Biggest challenge?**  
A: VAT mapping complexity → solved by direct code input

**Q: How scale?**  
A: Database, caching, proper auth, background jobs

## 🎤 2-Minute Pitch

"This is a Dutch VAT Analysis System built with FastAPI. It processes pre-analyzed invoice data with Dutch VAT category codes and generates quarterly, monthly, yearly, and Dutch tax format reports. The system handles all Dutch VAT categories, prevents duplicates, isolates user data, and calculates VAT payable. I recently improved it by accepting VAT codes directly instead of mapping, simplifying the code by 15%."

---

**Remember**: Be confident, explain clearly, show enthusiasm! 🚀

