import os
import yaml
import sys
import subprocess

def load_anvil_schema():
    """Load database schema from anvil.yaml"""
    print("Loading schema from anvil.yaml...")
    
    anvil_yaml_path = 'anvil.yaml'
    if not os.path.exists(anvil_yaml_path):
        print("⚠️ anvil.yaml not found")
        return False
    
    try:
        with open(anvil_yaml_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if database section exists
        if 'database' not in config:
            print("⚠️ No database section in anvil.yaml")
            return False
        
        # Get database configuration
        db_config = config['database']
        
        # Create schema directory if it doesn't exist
        schema_dir = 'src/database/schema'
        os.makedirs(schema_dir, exist_ok=True)
        
        # Generate schema files
        if 'tables' in db_config:
            generate_table_schemas(db_config['tables'], schema_dir)
        
        if 'indexes' in db_config:
            generate_index_schemas(db_config['indexes'], schema_dir)
        
        if 'functions' in db_config:
            generate_function_schemas(db_config['functions'], schema_dir)
        
        print("✓ Schema files generated successfully")
        return True
        
    except Exception as e:
        print(f"Error loading schema from anvil.yaml: {e}")
        return False

def generate_table_schemas(tables, schema_dir):
    """Generate SQL table schemas"""
    print("Generating table schemas...")
    
    table_schema_file = os.path.join(schema_dir, 'tables.sql')
    
    with open(table_schema_file, 'w') as f:
        f.write("-- Generated from anvil.yaml\n")
        f.write("-- Table schemas\n\n")
        
        for table_name, table_config in tables.items():
            f.write(f"-- Table: {table_name}\n")
            f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
            
            columns = table_config.get('columns', {})
            primary_key = table_config.get('primary_key')
            foreign_keys = table_config.get('foreign_keys', [])
            
            # Generate column definitions
            column_defs = []
            for col_name, col_config in columns.items():
                col_def = f"    {col_name} {col_config['type']}"
                
                if col_config.get('primary_key', False) or col_name == primary_key:
                    col_def += " PRIMARY KEY"
                
                if col_config.get('not_null', False):
                    col_def += " NOT NULL"
                
                if 'default' in col_config:
                    col_def += f" DEFAULT {col_config['default']}"
                
                column_defs.append(col_def)
            
            # Add foreign keys
            for fk in foreign_keys:
                fk_def = f"    FOREIGN KEY ({fk['column']}) REFERENCES {fk['references']}({fk['references_column']})"
                if fk.get('on_delete'):
                    fk_def += f" ON DELETE {fk['on_delete']}"
                if fk.get('on_update'):
                    fk_def += f" ON UPDATE {fk['on_update']}"
                column_defs.append(fk_def)
            
            f.write(",\n".join(column_defs))
            f.write("\n);\n\n")

def generate_index_schemas(indexes, schema_dir):
    """Generate SQL index schemas"""
    print("Generating index schemas...")
    
    index_schema_file = os.path.join(schema_dir, 'indexes.sql')
    
    with open(index_schema_file, 'w') as f:
        f.write("-- Generated from anvil.yaml\n")
        f.write("-- Index schemas\n\n")
        
        for index_name, index_config in indexes.items():
            f.write(f"-- Index: {index_name}\n")
            
            unique = "UNIQUE " if index_config.get('unique', False) else ""
            columns = ", ".join(index_config['columns'])
            
            f.write(f"CREATE {unique}INDEX IF NOT EXISTS {index_name} ON {index_config['table']} ({columns});\n\n")

def generate_function_schemas(functions, schema_dir):
    """Generate SQL function schemas"""
    print("Generating function schemas...")
    
    function_schema_file = os.path.join(schema_dir, 'functions.sql')
    
    with open(function_schema_file, 'w') as f:
        f.write("-- Generated from anvil.yaml\n")
        f.write("-- Function schemas\n\n")
        
        for func_name, func_config in functions.items():
            f.write(f"-- Function: {func_name}\n")
            
            params = ", ".join([f"{param['name']} {param['type']}" for param in func_config['parameters']])
            return_type = func_config.get('return_type', 'void')
            body = func_config['body']
            
            f.write(f"CREATE OR REPLACE FUNCTION {func_name}({params}) RETURNS {return_type} AS $$\n")
            f.write(body)
            f.write("\n$$ LANGUAGE plpgsql;\n\n")

def main():
    print("Starting anvil.yaml schema loading...")
    
    if load_anvil_schema():
        print("✓ Schema loading completed successfully!")
        sys.exit(0)
    else:
        print("✗ Schema loading failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()