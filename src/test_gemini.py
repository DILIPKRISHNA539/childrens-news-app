"""
Test script to debug Google Gemini API connection.

"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("="*70)
print("🔍 GOOGLE GEMINI API DEBUGGER (2.5 Preview Models)")
print("="*70)

# Check 1: Environment variable
print("\n1️⃣  Checking GOOGLE_API_KEY in environment...")
api_key = os.getenv('GOOGLE_API_KEY')
if api_key and api_key.startswith("AIzaSy"):
    print(f"   ✅ Found: {api_key[:7]}...{api_key[-5:]}")
else:
    print("   ❌ NOT FOUND or invalid! Key should start with 'AIzaSy'.")
    print("      Add GOOGLE_API_KEY to your .env file.")
    exit(1)

# Check 2: LiteLLM installation
print("\n2️⃣  Checking LiteLLM installation...")
try:
    import litellm
    version = getattr(litellm, '__version__', 'version not available')
    print(f"   ✅ LiteLLM installed (version: {version})")
except ImportError as e:
    print(f"   ❌ LiteLLM not installed: {e}")
    print("      Run: pip install litellm")
    exit(1)

# Check 3: Test Gemini 2.5 model names with LiteLLM
print("\n3️⃣  Testing Gemini API with LiteLLM...")

# This list is now based on the models you have access to.
models_to_test = [
    "gemini/gemini-2.5-flash-lite",
]

from litellm import completion
successful_model = None

for model in models_to_test:
    print(f"\n   Testing model: '{model}'")
    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": "Hello! How are you today?"}],
            max_tokens=20,
            timeout=15 
        )
        
        result = response.choices[0].message.content.strip()
        print(f"   ✅ SUCCESS! Response: '{result}'")
        successful_model = model
        break # Stop after the first success
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ FAILED: {error_msg[:120]}")

if not successful_model:
    print("\n   ❌ All LiteLLM tests failed. Check API key and internet connection.")

# Check 4: Direct Google API test with a valid model
print("\n4️⃣  Testing direct connection with 'google-generativeai'...")
try:
    import google.generativeai as genai
    print("   ✅ 'google-generativeai' is installed.")
    
    genai.configure(api_key=api_key)
    
    # Test with a model name we know you have access to
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Hello! How are you today?")
    print(f"\n   ✅ Direct API call works! Response: '{response.text.strip()}'")
    
except ImportError:
    print("   ⚠️  'google-generativeai' not installed.")
    print("      Install with: pip install google-generativeai")
except Exception as e:
    # This will catch the 404 error if the model name is wrong for this library
    print(f"   ❌ Direct API call FAILED: {str(e)[:120]}")

# Check 5: Recommendations
print("\n" + "="*70)
print("📋 RECOMMENDATIONS")
print("="*70)

if successful_model:
    print(f"\n✅ The model '{successful_model}' is working correctly!")
    print(f"   Make sure your config.py uses this model:")
    print(f"   LITELLM_MODEL = '{successful_model}'")
else:
    print("""
If tests failed, try these solutions:

1️⃣  VERIFY YOUR API KEY:
    - Go to: https://aistudio.google.com/app/apikey
    - Ensure the key is for a project with the 'Generative Language API' enabled.
    - Copy the FULL key (it must start with AIzaSy...).

2️⃣  UPDATE YOUR PACKAGES:
    - Run: pip install --upgrade litellm google-generativeai

3️⃣  CHECK API RESTRICTIONS:
    - In your Google Cloud project, ensure the API key has no restrictions
      (like IP address or application restrictions) that might block your script.
""")

print("="*70)