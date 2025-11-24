#!/usr/bin/env python3
"""
Test script to verify invoice processing endpoint
"""

import requests
import json

# API Configuration
API_URL = "http://localhost:8000/process-invoices"
USER_ID = "test_user_123"

# Sample invoice data (single JSON object)
sample_data = {
    "status": "success",
    "results": [
        {
            "status": "success",
            "file_name": "INV_7533934143_-_Maersk_-_Demurrage.pdf",
            "register_entry": {
                "Date": "2025-07-28",
                "Type": "Purchase",
                "VAT %": 0,
                "Currency": "EUR",
                "VAT Amount": 0,
                "Description": "Demurrage Fee MNBU0201708",
                "Nett Amount": 440,
                "Vendor Name": "Maersk A/S",
                "Gross Amount": 440,
                "VAT Category": "Reverse Charge",
                "Customer Name": "DUTCH FOOD SOLUTIONS B.V.",
                "Invoice Number": "7533934143",
                "VAT Amount (EUR)": 0,
                "Nett Amount (EUR)": 440,
                "Gross Amount (EUR)": 440,
                "Full_Extraction_Data": {
                    "vendor_vat_id": "DK53139655",
                    "customer_vat_id": "NL858674257B01",
                    "vendor_address": "Esplanaden 50, 1263 Copenhagen K, Denmark",
                    "customer_address": "2 ERICSSONSTRAAT, RIJEN 5121 ML, Netherlands"
                }
            }
        },
        {
            "status": "success",
            "file_name": "Google_5319090601.pdf",
            "register_entry": {
                "Date": "2025-07-31",
                "Type": "Purchase",
                "VAT %": 14,
                "Currency": "USD",
                "VAT Amount": 2.79,
                "Description": "Google Workspace Business Starter Commitment Jul 1 - Jul 1",
                "Nett Amount": 19.92,
                "Vendor Name": "Google Cloud EMEA Limited",
                "Gross Amount": 22.71,
                "VAT Category": "Standard Rate (from another country)",
                "Customer Name": "Mohamed Soliman",
                "Invoice Number": "5319090601",
                "VAT Amount (EUR)": 2.79,
                "Nett Amount (EUR)": 19.92,
                "Gross Amount (EUR)": 22.71,
                "Full_Extraction_Data": {
                    "vendor_vat_id": "752220365",
                    "customer_vat_id": None,
                    "vendor_address": "Velasco, Clanwilliam Place, Dublin 2, Ireland",
                    "customer_address": "dutchfoodsolutions.com, Egypt"
                }
            }
        }
    ]
}

def test_process_invoices():
    """Test the process-invoices endpoint"""
    print("🧪 Testing Invoice Processing Endpoint")
    print("=" * 50)
    
    headers = {
        "X-User-ID": USER_ID,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📤 Sending request to: {API_URL}")
        print(f"📋 Processing {len(sample_data['results'])} invoices...")
        
        response = requests.post(
            API_URL,
            json=sample_data,
            headers=headers,
            timeout=30
        )

def test_multiple_json_objects():
    """Test with multiple concatenated JSON objects"""
    print("\n🧪 Testing Multiple JSON Objects Format")
    print("=" * 50)
    
    # Create two separate JSON objects
    json1 = {
        "status": "success",
        "results": [sample_data["results"][0]]
    }
    
    json2 = {
        "status": "success",
        "results": [sample_data["results"][1]]
    }
    
    # Concatenate as strings
    combined_json = json.dumps(json1) + json.dumps(json2)
    
    headers = {
        "X-User-ID": USER_ID,
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📤 Sending 2 concatenated JSON objects...")
        
        response = requests.post(
            API_URL,
            data=combined_json,  # Use data instead of json to send raw string
            headers=headers,
            timeout=30
        )
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"   Message: {result.get('message', 'N/A')}")
            if 'details' in result:
                details = result['details']
                print(f"   Processed: {details.get('processed', 0)}")
                print(f"   Skipped: {details.get('skipped', 0)}")
                print(f"   Errors: {details.get('errors', 0)}")
                print(f"   Updated Years: {details.get('updated_years', [])}")
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Detail: {error_detail.get('detail', response.text)}")
            except:
                print(f"   Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   python start_backend.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def validate_json_format(data):
    """Validate JSON format"""
    print("\n🔍 Validating JSON format...")
    
    # Check required fields
    if "status" not in data:
        print("❌ Missing 'status' field")
        return False
    
    if "results" not in data:
        print("❌ Missing 'results' array")
        return False
    
    if not isinstance(data["results"], list):
        print("❌ 'results' must be an array")
        return False
    
    print(f"✅ JSON structure valid")
    print(f"   Results count: {len(data['results'])}")
    
    # Validate each result
    for i, result in enumerate(data["results"]):
        if result.get("status") == "success":
            if "register_entry" not in result:
                print(f"⚠️  Result {i+1}: Missing 'register_entry'")
            else:
                entry = result["register_entry"]
                required_fields = ["Date", "Type", "Invoice Number", "Description"]
                missing = [f for f in required_fields if f not in entry]
                if missing:
                    print(f"⚠️  Result {i+1}: Missing fields: {missing}")
                else:
                    print(f"✅ Result {i+1}: Valid")
        else:
            print(f"⚠️  Result {i+1}: Status is not 'success' (skipped)")
    
    return True

if __name__ == "__main__":
    print("🚀 Invoice Processing Test")
    print("=" * 50)
    
    # Validate format first
    if validate_json_format(sample_data):
        print()
        test_process_invoices()
        test_multiple_json_objects()
    else:
        print("\n❌ JSON validation failed. Please fix the format before testing.")

