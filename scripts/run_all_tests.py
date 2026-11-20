import sys
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

test_files = [
    ROOT / "tests" / "test_carisehat_feature_freeze.py",
    ROOT / "tests" / "test_freeze_live_http.py",
    ROOT / "tests" / "test_specialties.py",
    ROOT / "backend" / "tests" / "test_sparql_guard.py",
    ROOT / "tests" / "test_carisehat2_features.py",
    ROOT / "tests" / "test_chatbot_scenarios.py",
    ROOT / "tests" / "test_sirs_integration.py",
]

loader = unittest.TestLoader()
suite = unittest.TestSuite()

for tf in test_files:
    if tf.exists():
        spec = importlib.util.spec_from_file_location(tf.stem, tf)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tests = loader.loadTestsFromModule(mod)
        suite.addTests(tests)
        print(f"Loaded {tests.countTestCases()} tests from {tf.name}")
    else:
        print(f"Warning: {tf} not found")

print(f"\nRunning {suite.countTestCases()} total tests...\n")
runner = unittest.TextTestRunner(verbosity=1)
result = runner.run(suite)

if not result.wasSuccessful():
    sys.exit(1)
