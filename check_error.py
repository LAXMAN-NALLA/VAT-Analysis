#!/usr/bin/env python3
"""
Quick script to check for import errors
"""

try:
    import app
    print("✅ app.py imported successfully")
    print(f"✅ FastAPI app created: {app.app}")
    print("✅ No import errors found")
except Exception as e:
    print(f"❌ Error importing app.py:")
    print(f"   {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

