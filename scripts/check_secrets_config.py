import os
import yaml
import sys

def check_env_file():
    """Check .env file configuration"""
    print("Checking .env file...")
    
    env_files = ['.env', '.env.example', '.env.template']
    found_env = None
    
    for env_file in env_files:
        if os.path.exists(env_file):
            found_env = env_file
            print(f"✓ Found {env_file}")
            break
    
    if not found_env:
        print("⚠️ No .env file found")
        return False
    
    # Check for required environment variables
    required_vars = ['DATABASE_URL', 'ANVIL_APP_ID', 'ANVIL_API_KEY']
    with open(found_env, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing required variables in {found_env}: {missing_vars}")
        return False
    
    print("✓ .env file configuration OK")
    return True

def check_anvil_yaml_secrets():
    """Check anvil.yaml for secrets configuration"""
    print("Checking anvil.yaml secrets...")
    
    anvil_yaml_path = 'anvil.yaml'
    if not os.path.exists(anvil_yaml_path):
        print("⚠️ anvil.yaml not found")
        return True  # Not critical
    
    try:
        with open(anvil_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for secrets configuration
        if 'secrets' in config:
            print("✓ Secrets section found in anvil.yaml")
        else:
            print("⚠️ No secrets section in anvil.yaml")
        
        return True
    except Exception as e:
        print(f"Error checking anvil.yaml: {e}")
        return False

def check_vault_integration():
    """Check HashiCorp Vault integration"""
    print("Checking HashiCorp Vault integration...")
    
    # Look for vault-related files
    vault_files = ['vault-config.yaml', '.vault-token', 'vault-secrets.yml']
    found_vault = False
    
    for vault_file in vault_files:
        if os.path.exists(vault_file):
            found_vault = True
            print(f"✓ Found vault configuration: {vault_file}")
            break
    
    if not found_vault:
        print("⚠️ No HashiCorp Vault configuration found")
        return False
    
    print("✓ HashiCorp Vault integration OK")
    return True

def main():
    print("Starting secrets configuration validation...")
    
    checks = [
        check_env_file,
        check_anvil_yaml_secrets,
        check_vault_integration
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()  # Add spacing
    
    if all_passed:
        print("✓ All secrets configuration checks passed!")
        sys.exit(0)
    else:
        print("✗ Some secrets configuration checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()