# Multi-Format Invoice Processing

The `/process-invoices` endpoint now supports **multiple input formats** and automatically detects how many invoices are in the request.

## Supported Input Formats

### Format 1: Single JSON with Results Array (Standard)
```json
{
  "status": "success",
  "results": [
    {
      "status": "success",
      "file_name": "invoice1.pdf",
      "register_entry": {...}
    },
    {
      "status": "success",
      "file_name": "invoice2.pdf",
      "register_entry": {...}
    }
  ]
}
```

### Format 2: Multiple Concatenated JSON Objects
```json
{"status":"success","results":[{"status":"success","file_name":"invoice1.pdf","register_entry":{...}}]}{"status":"success","results":[{"status":"success","file_name":"invoice2.pdf","register_entry":{...}}]}
```

### Format 3: Single Invoice Object
```json
{
  "status": "success",
  "file_name": "invoice1.pdf",
  "register_entry": {...}
}
```

### Format 4: Mixed Formats
The system will automatically detect and combine invoices from any combination of the above formats.

## How It Works

1. **Detection**: The system automatically detects the input format
2. **Parsing**: Parses single or multiple JSON objects
3. **Extraction**: Extracts all invoice data from all formats
4. **Combination**: Combines all invoices into a single processing batch
5. **Processing**: Processes all invoices together

## Example Usage

### Python - Single JSON
```python
import requests

data = {
    "status": "success",
    "results": [
        {"status": "success", "file_name": "inv1.pdf", "register_entry": {...}},
        {"status": "success", "file_name": "inv2.pdf", "register_entry": {...}}
    ]
}

response = requests.post(
    "http://localhost:8000/process-invoices",
    json=data,
    headers={"X-User-ID": "user123"}
)
```

### Python - Multiple Concatenated JSONs
```python
import requests
import json

# Create multiple JSON objects
json1 = {"status": "success", "results": [{"status": "success", "file_name": "inv1.pdf", "register_entry": {...}}]}
json2 = {"status": "success", "results": [{"status": "success", "file_name": "inv2.pdf", "register_entry": {...}}]}

# Concatenate as string
combined = json.dumps(json1) + json.dumps(json2)

response = requests.post(
    "http://localhost:8000/process-invoices",
    data=combined,  # Use 'data' not 'json' for raw string
    headers={
        "X-User-ID": "user123",
        "Content-Type": "application/json"
    }
)
```

### cURL - Single JSON
```bash
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "success",
    "results": [
      {"status": "success", "file_name": "inv1.pdf", "register_entry": {...}}
    ]
  }'
```

### cURL - Multiple JSONs
```bash
curl -X POST "http://localhost:8000/process-invoices" \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{"status":"success","results":[{"status":"success","file_name":"inv1.pdf","register_entry":{...}}]}{"status":"success","results":[{"status":"success","file_name":"inv2.pdf","register_entry":{...}}]}'
```

## Response Format

The response includes information about how many invoices were detected:

```json
{
  "status": "success",
  "message": "Processed 5 invoices, skipped 0, errors: 0",
  "details": {
    "processed": 5,
    "skipped": 0,
    "errors": 0,
    "updated_years": ["2025"]
  },
  "total_invoices_detected": 5
}
```

## Key Features

✅ **Automatic Format Detection** - No need to specify the format  
✅ **Multiple JSON Support** - Handles concatenated JSON objects  
✅ **Error Handling** - Skips invalid entries and continues processing  
✅ **Duplicate Detection** - Prevents processing the same invoice twice  
✅ **Flexible Input** - Accepts any combination of supported formats  

## Important Notes

1. **Invoice Detection**: The system counts invoices by looking for:
   - Objects with `register_entry` field
   - Objects in `results` arrays
   - Objects with `status` and `file_name` fields

2. **Error Handling**: 
   - Invalid JSON objects are skipped
   - Entries with `status != "success"` are skipped
   - Missing `register_entry` entries are skipped

3. **Processing Order**: All invoices are processed in the order they appear in the input

4. **Performance**: Processing multiple invoices in one request is more efficient than multiple requests

## Testing

Use the provided test script:
```bash
python test_invoice_processing.py
```

This will test both single and multiple JSON object formats.

