
### 1️⃣ PostgreSQL Reference Sheet (`postgresql_reference.md`)

Copy the entire below content into a file named `postgresql_reference.md`:

```markdown
# PostgreSQL Reference Sheet for Agentic Environment

---

## 1. Installation and Setup Details

- **PostgreSQL Installation Directory:**  
  `C:\Program Files\PostgreSQL\17`

- **Data Directory:**  
  `C:\Program Files\PostgreSQL\17\data`

- **PostgreSQL Version:**  
  `17.5`

- **Database Service Name:**  
  `postgresql-x64-17`

- **OS Account Running Service:**  
  `NT AUTHORITY\NetworkService`

- **Default Listening Port:**  
  `5432`

- **Database Superuser Username:**  
  `postgres`

- **Windows Service Management Commands:**  
  - Start Service:  
    ```
    net start postgresql-x64-17
    ```
  - Stop Service:  
    ```
    net stop postgresql-x64-17
    ```
  - Check Status:  
    ```
    Get-Service -Name postgresql-x64-17
    sc query postgresql-x64-17
    ```
  
- **Manual Server Control Using pg_ctl:**  
  ```
  pg_ctl stop -D "C:\Program Files\PostgreSQL\17\data"
  pg_ctl start -D "C:\Program Files\PostgreSQL\17\data" -l logfile.txt
  ```
  
---

## 2. Connection Credentials & Strings

- **Typical psql CLI Connection:**  
  ```
  psql -h localhost -p 5432 -U postgres -d postgres
  Password for user postgres: 
  ```

- **Connection String URI Format:**  
  ```
  postgresql://:@:/
  ```
  
- **Actual MCP Connection String:**  
  ```
  postgresql://postgres:2001@localhost:5432/postgres
  ```

- **Alternative Key-Value Format:**  
  ```
  host=localhost port=5432 dbname=postgres user=postgres password=2001
  ```

---

## 3. Configuration Files and Key Settings

- **`postgresql.conf` Location:**  
  `C:\Program Files\PostgreSQL\17\data\postgresql.conf`

- **Key `postgresql.conf` Settings:**  
  ```
  listen_addresses = 'localhost'  # Use 'localhost' or '*' for remote access
  port = 5432
  ```

- **`pg_hba.conf` Location:**  
  `C:\Program Files\PostgreSQL\17\data\pg_hba.conf`

- **Common `pg_hba.conf` Entries for Windows:**  
  ```
  # TYPE  DATABASE        USER            ADDRESS                 METHOD
  local   all             postgres                                trust
  host    all             all             127.0.0.1/32            md5
  host    all             all             ::1/128                 md5
  ```
  > *Note:* Windows does not support `local` as Unix does. Use `host` entries with `127.0.0.1` and `::1`.

---

## 4. pgvector Extension Details

- **Extension Files Location:**  
  `C:\Program Files\PostgreSQL\17\share\extension\`

- **Extension Version Installed/Enabled:**  
  `0.8.0`

- **Enable Extension SQL Commands (inside `psql` shell):**  
  ```
  CREATE EXTENSION IF NOT EXISTS vector;
  SELECT * FROM pg_extension WHERE extname = 'vector';
  ```

- **Build & Install Summary:**  
  - Installed Visual Studio 2022 Build Tools (with C++ workload)  
  - Cloned pgvector repo, branch `v0.8.0`  
  - Initialized build env with `vcvars64.bat`  
  - Built and installed using `nmake` commands

---

## 5. MCP Integration Details

- **Connection String Used:**  
  ```
  postgresql://postgres:2001@localhost:5432/postgres
  ```

- **MCP-related Config Files Updated:**  
  - `.vscode/mcp.json`
  - `C:\Users\salib\AppData\Roaming\Code\User\globalStorage\kilocode.kilocode\settings\kilocode_mcp_settings.json`

- **Test Queries Confirmed Connected:**  
  ```
  SELECT 1;
  ```

---

## 6. Recommended Next Steps for Agentic Environment

- **Create Dedicated Database (optional but recommended):**  
  ```
  CREATE DATABASE my_mcp_db;
  \c my_mcp_db
  CREATE EXTENSION vector;
  ```

- **Create Tables With Vector Columns:**  
  ```
  CREATE TABLE items (
      id SERIAL PRIMARY KEY,
      description TEXT,
      embedding vector(1536)  -- Use dimensionality according to your embedding model
  );
  ```

- **Create Vector Index for Faster Searches:**  
  ```
  CREATE INDEX ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
  ```

- **Sample Vector Similarity Query:**  
  ```
  SELECT *, embedding  '[0.1, 0.2, 0.3, ...]' AS distance
  FROM items
  ORDER BY distance
  LIMIT 5;
  ```

- **Backup and Security Recommendations:**  
  - Use `pg_dump` or continuous archiving to backup your databases.  
  - Use proper authentication methods in `pg_hba.conf` and secure roles/users.  
  - Ensure encryption and firewall rules if exposing PostgreSQL on network.

---

## 7. Summary Table of Key Credentials and Configs

| Aspect                    | Value / Location                                   |
|---------------------------|--------------------------------------------------|
| PostgreSQL Install Path    | `C:\Program Files\PostgreSQL\17`                   |
| Data Directory            | `C:\Program Files\PostgreSQL\17\data`              |
| Default Port              | 5432                                             |
| Superuser Username        | `postgres`                                       |
| Default Database Name     | `postgres` (or created, e.g. `my_mcp_db`)         |
| MCP Connection String     | `postgresql://postgres:2001@localhost:5432/postgres` |
| `postgresql.conf`         | `listen_addresses = 'localhost'`, `port = 5432`  |
| `pg_hba.conf`             | Uses `host` method with `md5` for local IPv4 & IPv6 |
| pgvector Extension Version| `0.8.0`                                           |
| Visual Studio Build Env   | `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat` |

---

*Document generated: 2025-08-08*

---

# End of PostgreSQL Reference Sheet
```

***

### 2️⃣ Sample PostgreSQL Connection & MCP Environment Config Script

I provide two sample scripts so you can pick depending on your environment:

***

**Option A: PowerShell Script (`set_pg_env.ps1`)**

```powershell
# PostgreSQL Connection Environment Variables for MCP / KiloCode

# Database connection info
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGUSER = "postgres"
$env:PGPASSWORD = "2001"
$env:PGDATABASE = "postgres"

# Optional: MCP specific environment variables
# Set your MCP connection string if needed
$env:MCP_POSTGRES_CONNECTION_STRING = "postgresql://postgres:2001@localhost:5432/postgres"

Write-Host "PostgreSQL/MCP environment variables set."
```

***

**Option B: Bash Script (`set_pg_env.sh`)**  
(For use in WSL, Git Bash, or Linux environment)

```bash
#!/bin/bash

# PostgreSQL Connection Environment Variables for MCP / KiloCode

export PGHOST="localhost"
export PGPORT="5432"
export PGUSER="postgres"
export PGPASSWORD="2001"
export PGDATABASE="postgres"

# Optional: MCP specific environment variable
export MCP_POSTGRES_CONNECTION_STRING="postgresql://postgres:2001@localhost:5432/postgres"

echo "PostgreSQL/MCP environment variables set."
```

***

### How to save:

- Copy the PostgreSQL reference sheet and save as `postgresql_reference.md` with any text editor (e.g., Notepad, VSCode).
- Copy one of the config scripts and save as `set_pg_env.ps1` or `set_pg_env.sh` accordingly.
- Make sure to adjust any passwords or usernames if they differ or become rotated.
- Run the PowerShell script in a PowerShell session to set environment variables, or source the bash script in your Linux environment.

***

If you want, I can also help you create scripts to initialize databases or run test queries programmatically. Just let me know!