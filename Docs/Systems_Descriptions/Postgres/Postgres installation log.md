# Postgres installation log

## confirm the PostgreSQL service is running properly on your Windows machine

			PS C:\Users\salib> net start postgresql-x64-17
				The requested service has already been started.
		This should either start the service or tell you it is already running

		check the service status:
			PS C:\Users\salib> net start postgresql-x64-17
				The requested service has already been started.
				More help is available by typing NET HELPMSG 2182.
				PS C:\Users\salib> sc query postgresql-x64-17
				PS C:\Users\salib>
		Look for the STATE information in the output. It should say RUNNING

		provide the full output of sc query postgresql-x64-17
			PS C:\Users\salib> sc query postgresql-x64-17
			PS C:\Users\salib>
			No response returned. indicates a possible issue with Windows Service itself or how it's registered

			Investigate further:
				1. Review PostgreSQL log files in your data directory (e.g., C:\Program Files\PostgreSQL\17\data\log) for startup errors: [No log found for today]

				2. open the Windows Event Viewer:click the Start menu, type Event Viewer, and then click on the app in the search results 
							Warning:
							Event Viewer allows you to view detailed logs of application and system events including errors, warnings, and informational messages, crucial for troubleshooting. Be cautious when running Event Viewer as administrator, as it grants elevated system privileges.
							No errors found in logs

				3. Try to start/stop the PostgreSQL server manually using pg_ctl tool from the bin directory to get more direct error messages:
							PS C:\Users\salib> & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" stop -D "C:\Program Files\PostgreSQL\17\data"
							waiting for server to shut down.... done
							server stopped
							PS C:\Users\salib>

							PS C:\Users\salib> & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" start -D "C:\Program Files\PostgreSQL\17\data" -l logfile.txt
							waiting for server to start.... done
							server started
							
							Log:
							2025-08-08 12:26:44 SAST LOG:  starting PostgreSQL 17.5 on x86_64-windows, compiled by msvc-19.44.35209, 64-bit
							2025-08-08 12:26:44 SAST LOG:  listening on IPv6 address "::", port 5432
							2025-08-08 12:26:44 SAST LOG:  listening on IPv4 address "0.0.0.0", port 5432
							2025-08-08 12:26:44 SAST LOG:  database system was shut down at 2025-08-08 12:25:22 SAST
							2025-08-08 12:26:44 SAST LOG:  database system is ready to accept connections

				4. Check Server status:
							PS C:\Users\salib> Get-Service -Name postgresql-x64-17
							Status   Name               DisplayName
							------   ----               -----------
							Stopped  postgresql-x64-17  postgresql-x64-17 - PostgreSQL Serv...
												
					#### Discrepency explained
							In point 3 we started the service using pg_ctl which manually starts the PostgreSQL server process directly in the current user session.
							In point 4, the server shows status = "stopped". The Get-Service -Name postgresql-x64-17 command queries the Windows Service Manager about the PostgreSQL service's status. This service is configured to start, stop, and control PostgreSQL as a background Windows service.
							To start the PostgreSQL service on Windows so that its status shows as "Running," use these commands:
							Start-Service -Name postgresql-x64-17  (or) net start postgresql-x64-17
							Stop-Service -Name postgresql-x64-17 (or) net stop postgresql-x64-17
							Check Status: Get-Service -Name postgresql-x64-17 (or) sc query postgresql-x64-17
							##### Note:
									If the service has been started using pg_ctl, then it must first be stopped using pg_ctl before it can be started globally using Start-Service -Name postgresql-x64-17  (or) net start postgresql-x64-17
			
				5. Stop the user session Server: & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" stop -D "C:\Program Files\PostgreSQL\17\data"
							Start the Global service: PS C:\Users\salib> Start-Service -Name postgresql-x64-17
							PS C:\Users\salib>
							When Start-Service completes silently without errors, it typically indicates the service was started and is running under Windows Service Manager control.

				6. Check status globally: Get-Service -Name postgresql-x64-17
							PS C:\Users\salib> Get-Service -Name postgresql-x64-17

							Status   Name               DisplayName
							------   ----               -----------
							Running  postgresql-x64-17  postgresql-x64-17 - PostgreSQL Serv..
									
## Verify basic connectivity to your PostgreSQL server on port 5432 and confirm that your database superuser can connect properly.
				Bash
						salib@SA2309 MINGW64 ~
						$ psql -h localhost -p 5432 -U postgres -d postgres
						Password for user postgres:

						psql (17.5)
						WARNING: Console code page (437) differs from Windows code page (1252)
															8-bit characters might not work correctly. See psql reference
															page "Notes for Windows users" for details.
						Type "help" for help.

						postgres=#
			If the prompt connects and you see the postgres=# shell, your connection is working fine.

			Run a simple query
					postgres=# SELECT 1;
						?column?
					----------
													1
					(1 row)

			Then exit by typing:
					postgres=# \q

## check your PostgreSQL configuration files to ensure they are properly set up for your intended usage and security.

		Let's start with the main configuration file postgresql.conf:

				Locate and open the file at:
						C:\Program Files\PostgreSQL\17\data\postgresql.conf

				Check these key settings:
						listen_addresses
								Confirm it's set to allow local connections (usually localhost or * if remote access needed):
						listen_addresses = 'localhost'
						port
								Confirm the port is set to 5432 (or your intended port):
								port = 5432

		Next, open and inspect your pg_hba.conf file at:
				C:\Program Files\PostgreSQL\17\data\pg_hba.conf
						This file controls client authentication. For local development, you want to see entries like:
								# TYPE  DATABASE        USER            ADDRESS                 METHOD
								local   all             postgres                                trust
								host    all             all             127.0.0.1/32            md5
								host    all             all             ::1/128                 md5
								Since Windows doesn’t natively support “local” connections like Unix, you typically rely on host with 127.0.0.1 or your IP.

## Next, let's verify the pgvector extension status in your PostgreSQL database
		These are the steps:
				Connect to your database (e.g., postgres) with psql:
						bash
						$ psql -h localhost -p 5432 -U postgres -d postgres
								Password for user postgres:

								psql (17.5)
						WARNING: Console code page (437) differs from Windows code page (1252)
															8-bit characters might not work correctly. See psql reference
															page "Notes for Windows users" for details.
						Type "help" for help.

						postgres=# psql -h localhost -p 5432 -U postgres -d postgres
										
		Run this query to see if the vector extension is installed and enabled:
        ^
				postgres=# SELECT * FROM pg_extension WHERE extname = 'vector';
					oid | extname | extowner | extnamespace | extrelocatable | extversion | extconfig | extcondition
				-----+---------+----------+--------------+----------------+------------+-----------+--------------
				(0 rows)

		that output is correct and means the vector extension is not currently installed or enabled in your postgres database.
		The query ran successfully.
		No rows were returned, indicating pgvector is not present.

Next step, if you want to use pgvector, is to install and enable this extension in your database.

Step 1: Check if the pgvector extension file is available
Look inside your PostgreSQL extension directory:

text
C:\Program Files\PostgreSQL\17\share\extension\
Check if you see files starting with vector--*.sql or vector.control.

If these files are not present, it means pgvector is not installed with your PostgreSQL installation and you’ll need to install it manually, since PGVector Windows binaries are not always bundled by default.

The files starting with vector--*.sql or vector.control are not present

1. Install Build Tools & Dependencies
		Install Microsoft Visual Studio 2022 Build Tools with the C++ workload (VC Tools), which provides the compiler and build environment needed
		After installation, open the Developer Command Prompt for Visual Studio 2022 (search for it in the Start menu)

2. Set Environment Variables and Clone pgvector
		In the Developer Command Prompt, run:
				text
				set "PGROOT=C:\Program Files\PostgreSQL\17"
				cd %TEMP%
				git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
				cd pgvector

3. Build and Install pgvector Extension
		Still in the Developer Command Prompt, run:
				text
				call "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
Outcome:
		C:\Users\salib\AppData\Local\Temp\pgvector>call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
		**********************************************************************
		** Visual Studio 2022 Developer Command Prompt v17.14.11
		** Copyright (c) 2025 Microsoft Corporation
		**********************************************************************
		[vcvarsall.bat] Environment initialized for: 'x64'
		C:\Users\salib\AppData\Local\Temp\pgvector>

		Run these commnds separately:
				nmake /F Makefile.win
				nmake /F Makefile.win install

		The vcvars64.bat path may vary slightly depending on your Visual Studio installation folder, so adjust the path if necessary.
		nmake will compile and then install the pgvector extension binaries into your PostgreSQL installation.

4. Enable pgvector in your Database
		Powershell: 
				PS C:\Users\salib> psql -h localhost -p 5432 -U postgres -d postgres
				Password for user postgres:

				psql (17.5)
				WARNING: Console code page (437) differs from Windows code page (1252)
													8-bit characters might not work correctly. See psql reference
													page "Notes for Windows users" for details.
				Type "help" for help.

				postgres=# CREATE EXTENSION IF NOT EXISTS vector;
				CREATE EXTENSION
				postgres=#
				"CREATE EXTENSION" Response, means the pgvector extension was enabled successfully in the postgres database.

Now you can verify the installation by running:

				sql
						postgres=# SELECT * FROM pg_extension WHERE extname = 'vector';
				Response:
								oid  | extname | extowner | extnamespace | extrelocatable | extversion | extconfig | extcondition
						-------+---------+----------+--------------+----------------+------------+-----------+--------------
							24576 | vector  |       10 |         2200 | t              | 0.8.0      |           |
						(1 row)

This output confirms that the pgvector extension is successfully installed and enabled in your postgres database:
		extname = vector
		extversion = 0.8.0
You have one row indicating the extension is active.

Your PostgreSQL setup is now ready to support vector operations needed for your Agentic IDE and related AI/RAG systems that rely on vector similarity search.

