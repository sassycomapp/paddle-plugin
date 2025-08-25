#!/usr/bin/env python3
"""
Comprehensive test suite for environment detection utility.

Tests all aspects of the environment management system including:
- Environment detection
- Virtual environment validation
- Dependency checking
- Tesseract OCR configuration
- Fallback mechanisms
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the utils directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

try:
    from environment import Environment, setup_environment
except ImportError:
    try:
        # Try relative import
        from ..utils.environment import Environment, setup_environment
    except ImportError:
        print("❌ Environment utility not found")
        sys.exit(1)


class TestEnvironmentDetection(unittest.TestCase):
    """Test environment detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env = Environment(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_environment_initialization(self):
        """Test environment initialization."""
        self.assertIsNotNone(self.env)
        self.assertEqual(self.env.workspace_root, Path(self.temp_dir))
        self.assertIsNone(self.env._environment_info)
    
    @patch('environment.sys')
    @patch('environment.os.environ')
    def test_virtual_environment_detection(self, mock_environ, mock_sys):
        """Test virtual environment detection."""
        # Test virtual environment
        mock_environ.get.return_value = '/path/to/venv'
        result = self.env._is_virtual_environment()
        self.assertTrue(result)
        
        # Test global environment
        mock_environ.get.return_value = None
        result = self.env._is_virtual_environment()
        self.assertFalse(result)
    
    @patch('environment.os.path.exists')
    def test_site_packages_detection(self, mock_exists):
        """Test site packages detection."""
        # Test user site-packages exists
        mock_exists.return_value = True
        result = self.env._get_site_packages()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
    
    
    @patch('environment.__import__')
    def test_dependency_checking(self, mock_import):
        """Test dependency checking."""
        # Test all dependencies available
        mock_import.return_value = MagicMock()
        missing = self.env._check_dependencies()
        self.assertEqual(len(missing), 0)
        
        # Test missing dependencies
        mock_import.side_effect = ImportError("Package not found")
        missing = self.env._check_dependencies()
        self.assertGreater(len(missing), 0)
    
    def test_environment_classification(self):
        """Test environment classification."""
        # Test virtual environment
        result = self.env._classify_environment(True, '/path/to/venv')
        self.assertEqual(result, 'virtual')
        
        # Test conda environment
        result = self.env._classify_environment(True, '/path/to/conda')
        self.assertEqual(result, 'conda')
        
        # Test global environment
        result = self.env._classify_environment(False, None)
        self.assertEqual(result, 'global')


class TestEnvironmentSetup(unittest.TestCase):
    """Test environment setup functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.env = Environment(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_environment_detection(self):
        """Test environment detection."""
        result = self.env.detect_environment()
        self.assertIsInstance(result, dict)
        self.assertIn('environment_type', result)
        self.assertIn('is_virtual', result)
        self.assertIn('python_version', result)
    
    @patch('environment.os.environ')
    def test_environment_configuration(self, mock_environ):
        """Test environment configuration."""
        # Mock environment info
        self.env._environment_info = {
            'site_packages': ['/path/to/site-packages']
        }
        
        result = self.env.configure_environment()
        self.assertIsInstance(result, dict)
        self.assertIn('actions_taken', result)
        self.assertIn('settings_applied', result)
        self.assertIn('errors', result)
    
    def test_environment_validation(self):
        """Test environment validation."""
        # Mock environment info
        self.env._environment_info = {
            'python_version': 'Python 3.9.0',
            'is_virtual': True,
            'missing_dependencies': []
        }
        
        result = self.env.validate_environment()
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertIn('critical_issues', result)
        self.assertIn('warnings', result)
        
        # Test valid environment
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(len(result['critical_issues']), 0)
    
    def test_environment_info_saving(self):
        """Test environment info saving."""
        # Mock environment info
        self.env._environment_info = {
            'environment_type': 'virtual',
            'is_virtual': True,
            'python_version': 'Python 3.9.0'
        }
        
        output_file = os.path.join(self.temp_dir, 'test_env_info.json')
        result = self.env.save_environment_info(output_file)
        
        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))


class TestGlobalFunctions(unittest.TestCase):
    """Test global utility functions."""
    
    def test_setup_environment(self):
        """Test setup_environment function."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            result = setup_environment(temp_dir)
            self.assertIsInstance(result, dict)
            self.assertIn('environment_info', result)
            self.assertIn('configuration', result)
            self.assertIn('validation', result)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_environment_info_none_handling(self):
        """Test handling of None environment info."""
        env = Environment()
        
        # Test with None environment info
        env._environment_info = None
        
        # Should not raise exceptions
        result = env.get_environment_info()
        self.assertIsInstance(result, dict)
    
    def test_fallback_mechanisms(self):
        """Test fallback mechanisms."""
        env = Environment()
        
        # Test with missing environment utility
        with patch.dict('sys.modules', {'utils.environment': None}):
            with self.assertRaises(ImportError):
                from utils.environment import setup_environment
                setup_environment()
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        env = Environment()
        
        # Test with invalid workspace path
        env = Environment('/invalid/path')
        self.assertIsNotNone(env)
        
        # Test environment detection with mocked errors
        with patch.object(env, '_detect_dependencies') as mock_detect:
            mock_detect.return_value = []
            result = env.detect_environment()
            self.assertIsInstance(result, dict)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete environment system."""
    
    def test_complete_environment_workflow(self):
        """Test complete environment workflow."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create environment manager
            env = Environment(temp_dir)
            
            # Step 1: Detect environment
            env_info = env.detect_environment()
            self.assertIsInstance(env_info, dict)
            
            # Step 2: Configure environment
            config_result = env.configure_environment()
            self.assertIsInstance(config_result, dict)
            
            # Step 3: Validate environment
            validation_result = env.validate_environment()
            self.assertIsInstance(validation_result, dict)
            
            # Step 4: Save environment info
            env_file = env.save_environment_info()
            self.assertTrue(os.path.exists(env_file))
            
            # Step 5: Test global functions
            from utils.environment import setup_environment
            setup_result = setup_environment(temp_dir)
            self.assertIsInstance(setup_result, dict)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility."""
        # Test with different platform types
        platforms = ['windows', 'linux', 'darwin']
        
        for platform in platforms:
            with patch('environment.platform.system', return_value=platform):
                env = Environment()
                result = env.detect_environment()
                self.assertIsInstance(result, dict)
                self.assertIn('environment_type', result)


def run_tests():
    """Run all tests and return results."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestEnvironmentDetection,
        TestEnvironmentSetup,
        TestGlobalFunctions,
        TestEdgeCases,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


def main():
    """Main function to run tests."""
    print("=" * 70)
    print("Environment Detection Utility - Test Suite")
    print("=" * 70)
    
    # Run tests
    result = run_tests()
    
    # Print results
    print("\n" + "=" * 70)
    print("Test Results Summary:")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())