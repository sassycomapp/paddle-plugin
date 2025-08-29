import os
import yaml
import sys

def validate_anvil_yaml():
    """Validate anvil.yaml structure and content"""
    print("Validating anvil.yaml...")
    
    anvil_yaml_path = 'anvil.yaml'
    if not os.path.exists(anvil_yaml_path):
        print("⚠️ anvil.yaml not found")
        return False
    
    try:
        with open(anvil_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Basic structure validation
        required_sections = ['app', 'database', 'secrets']
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️ Missing required sections in anvil.yaml: {missing_sections}")
            return False
        
        # Validate app section
        if 'name' not in config['app']:
            print("⚠️ Missing app name in anvil.yaml")
            return False
        
        # Validate database section
        if 'schema' not in config['database']:
            print("⚠️ Missing database schema in anvil.yaml")
            return False
        
        # Check for secrets references
        if 'secrets' in config:
            secrets = config['secrets']
            if not isinstance(secrets, dict) or len(secrets) == 0:
                print("⚠️ Empty or invalid secrets section in anvil.yaml")
                return False
        
        print("✓ anvil.yaml structure and content OK")
        return True
        
    except yaml.YAMLError as e:
        print(f"⚠️ YAML syntax error in anvil.yaml: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Error validating anvil.yaml: {e}")
        return False

def check_database_schema():
    """Check database schema files"""
    print("Checking database schema...")
    
    schema_dir = 'src/database/schema'
    if not os.path.exists(schema_dir):
        print("⚠️ Database schema directory not found")
        return False
    
    schema_files = [f for f in os.listdir(schema_dir) if f.endswith('.sql')]
    if not schema_files:
        print("⚠️ No SQL schema files found")
        return False
    
    print(f"✓ Found {len(schema_files)} schema files")
    return True

def main():
    print("Starting anvil.yaml validation...")
    
    checks = [
        validate_anvil_yaml,
        check_database_schema
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()  # Add spacing
    
    if all_passed:
        print("✓ All anvil.yaml validation checks passed!")
        sys.exit(0)
    else:
        print("✗ Some anvil.yaml validation checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()