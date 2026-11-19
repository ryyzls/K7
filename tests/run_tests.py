import os
import sys
from pathlib import Path
import unittest

root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir / "backend"))
sys.path.insert(0, str(root_dir / "tests"))

from test_chatbot_scenarios import ChatbotScenariosTest

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(ChatbotScenariosTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 60)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print("=" * 60)
    if result.wasSuccessful():
        print("ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)
