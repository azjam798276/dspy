
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from optimizer.optimize import CLIReflectionLM

def test_lm():
    print("Initializing CLIReflectionLM...")
    lm = CLIReflectionLM()
    print("Calling LM with simple prompt...")
    try:
        response = lm("test prompt")
        print(f"Response Type: {type(response)}")
        print(f"Response Content: {response}")
        
        # Simulate DSPy adapter iteration
        print("Attempting iteration (DSPy simulation)...")
        for i, output in enumerate(response):
             print(f"Output {i}: {output}")
        print("SUCCESS: Response is iterable.")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    test_lm()
