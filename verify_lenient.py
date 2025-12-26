
import sys
import os
import subprocess
from unittest.mock import MagicMock, patch

# Add current dir to path
sys.path.append(os.getcwd())

from optimizer.optimize import CLIReflectionLM

def test_lenient_exit_code():
    print("Initializing CLIReflectionLM...")
    lm = CLIReflectionLM()
    
    print("Testing non-zero exit code with content...")
    
    # Mock subprocess.Popen to simulate exit code 130 but with stdout content
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.communicate.return_value = ('{"valid": "json"}', 'some stderr warning')
        mock_process.returncode = 130
        mock_popen.return_value = mock_process
        
        # We need to mock binary_path to avoid file check if it does any? 
        # Actually CLIReflectionLM doesn't check existence in init, so it's fine.
        
        try:
            response = lm("test prompt")
            print(f"Response: {response}")
            if response == ['{"valid": "json"}']:
                 print("SUCCESS: Content preserved despite error code.")
            else:
                 print(f"FAILURE: Unexpected response: {response}")
        except Exception as e:
            print(f"FAILURE: Exception raised: {e}")

if __name__ == "__main__":
    test_lenient_exit_code()
