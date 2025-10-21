"""
A simple script to test the connection to a local Ollama model using the litellm library.
"""

print("="*70)
print("🔍 OLLAMA CONNECTION & MODEL TESTER")
print("="*70)

# 1. Check if litellm is installed
try:
    from litellm import completion
    import litellm
    litellm.set_verbose = False
    print("✅ Step 1: `litellm` library is installed.")
except ImportError:
    print("❌ Step 1 FAILED: The `litellm` library is not installed.")
    print("   Please run: pip install litellm")
    exit()

# 2. Define the local model to test
# This is the name litellm uses to find your local Ollama model
OLLAMA_MODEL = "ollama/llama3:8b"
print(f"\n✅ Step 2: Will test model '{OLLAMA_MODEL}'.")

# 3. Attempt to connect and get a response
print("\n⏳ Step 3: Attempting to get a response from the model...")
try:
    response = completion(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": "In one short sentence, explain why the sky is blue."
            }
        ],
        stream=False, # Set to False for a single response
        timeout=30    # Give it up to 30 seconds to respond
    )

    # Extract the response text
    result_text = response.choices[0].message.content.strip()

    print("\n" + "="*70)
    print("🎉 SUCCESS! Connection to Ollama is working.")
    print("="*70)
    print(f"\n💬 Model Response:\n   '{result_text}'")

except Exception as e:
    error_message = str(e).lower()
    print("\n" + "="*70)
    print("❌ FAILED! Could not get a response from Ollama.")
    print("="*70)
    
    print(f"\nError Details: {str(e)}")
    
    print("\n📋 TROUBLESHOOTING:")
    if "connection refused" in error_message:
        print("   ➡️  The Ollama application is likely not running.")
        print("       Solution: Start the Ollama desktop app and try again.")
    elif "model" in error_message and "not found" in error_message:
        print(f"   ➡️  The model '{OLLAMA_MODEL}' has not been downloaded yet.")
        print("       Solution: Open your terminal and run the command:")
        print(f"       ollama pull {OLLAMA_MODEL.split('/')[1]}")
    else:
        print("   ➡️  An unexpected error occurred. Check the details above.")
        print("       - Is the Ollama server running correctly?")
        print("       - Is the model name spelled correctly?")