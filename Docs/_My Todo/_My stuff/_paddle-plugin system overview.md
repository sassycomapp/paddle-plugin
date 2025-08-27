 ____________________________________________ 
# Paddle-plugin Systems Overview

## Introduction:
    The systems and MCPs have for the most part (99%) been installed, Configured, integrated and documented.
				A problem is that many things have been over designed and over implemented. 
    
				The CREDO is: Simple, Robust, Secure, Fit for purpose

## Basic architecture:
    The system is intended to be a semi-autonomous Agentic IDE
        - OS: Win 11; WSL2; Ubuntu 22.04; Nodejs
        - Principle UI: Kilo Code
        - Orchestrators: Kilo Code; AG2
        - Collection of Agentic systems
        - Collection of MCPs
        - PostgresDB
        - Podman Containerization
    
## Python
    - There are various python versions implemented in vscode
    - The mybizz app which we are not working on as yet, requires 3.7x. I was not able to find the 3.7x version and installed 3.8 for the sake of supporting the mybizz application. 
    - Version 3.13 was installed as the default system python interpreter
    - During the setup of this agentic IDE in vscode, kilo code may have installed other versions for supporting various dependencies. Likely these will be found in venv's

## Virtual Environments
    During the setup of the agentic IDE in vscode, the AI assistants have created several venv's to overcome compatibility/ integration conflicts. The creation of the venv's was never considered as a whole which led to other complications such as;
        - The appearance that many elements which are installed in venv's appear to not be found and hence believed to not exist. This in itself gave rise to several elements being implemented multiple times for different purposes
        - Integrations depending on the wrong paths

## This not That
    a. We DO use Podman, 
    we do NOT use Docker
    b. We DO use PostgreSQLDB and Pgvector,
    We do NOT use ChromaDB
    c. We DO use KiloCode and AG2,
				We do NOT use PM2
				d. We do use MCP EasyOCRmcp
				We do not use SimpleOCR mcp, PaddleOCR mcp

## Workspaces, Nodes and Libraries
    Not enough thought has been given to workspaces. These must be properly defined and consideration must be given to what is actually required and how to maintain efficiency and the resource overhead budget

    The nodes and libraries which are currently implemented were selected to support the Agentic IDE but some thought needs to be given to typical requirements of the apps which are to be developed in the Agentic IDE
    
    By contrast, constant vigilance needs to be applied in order to not over -strain the current hardware resources. The system is running on  an Asus x515EA laptop with 8Gb Ram and no GPU

    Several prominent libraries exist in the system
        Langchain
        Torch
        Sentence-transformers
        FAISS
        FastAPI
        Uvicorn
        Psycopg2
    We need to take stock of the libraries and node modules in use and determine a set which supports the Agentic IDE and the potential project applications which we intend to build here.
    Use npm prune or define more granular package.json files for each workspace.

## Separate Projects
    Paddle-plugin
        Paddle-plugin is the name of the agentic IDE setup in VSCode. The name "paddle-plugin" has no relation to Paddle.com or PaddleOCR or any other entity named "Paddle". This is also NOT a plugin. The name "paddle-plugin" is a random name given to this setup. Paddle-plugin (The Agentic IDE setup in VSCode Does have a Github repo by the same name and has active Version Control to this repo.
        
        The name cannot be changed to a more appropriate name as this would break many file paths in the UIDE Setup

        This Agentic IDE is intended to be a "Workshop" to develop Agentic and non agentic apps and web apps
        
        We are currently ONLY developing the paddle-plugin project and are not focusing on other projects
        
    Mybizz
        Mybizz is a project built in Anvil.works. There is a repo for this application on github. Anvil keeps the app on Anvil and the github repo constantly sync'd
        
        We do intend to develop the  mybizz code in vscode in the future
        
    Vsc_ide
        Vsc-ide repo was intended to be the Agentic IDE project in vscode, However it was repurposed for use as the audit repo for auditing the paddle-plugin agentic IDE setup on vscode
        
        This is a repo on github and on the local PC


## Agentic IDE Architectural overview

    The user operates the agentic IDE through the Kilo Code UI, chat interface.
				The kilo code system has 5 principle modes: Ask, Code, Orchestrator, Architect, Debug. 
    The orchestrator mode manages all the modes unless one of the other 4 are specifically , manually selected.
    
				The user selects the model. Kilocode or AG2 do not select models

    The user submits a task to the kilo code/ orchestrator mode. 
    Orchestrator mode will enlist the services of the Architect mode. Once kilo code has completed the plan  and the plan has been approved by the user, the orchestrator mode will appoint the Code mode to produce the code
    
    The Kilo code system needs to tie into the AG2 Orchestration system to make use of the various paddle-plugin systems and MCPs. Whilst much design and implementation has happened, this Orchestration layer is not correctly setup as yet. This is the immediate task.

    The paddle-plugin is designed to overcome the typical challenges in  application development and agentic development work as well as meeting  the challenge of limited hardware and budget. The Agentic IDE is thus comprised of the integrated systems and MCPs listed below.

## Files related to initializing the agentic environment:
    - C:\_1mybizz\paddle-plugin\Docs\_My Todo\Kilocode, MCP setup and config Task.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\Integration Architecture Design.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Compliance Validation Standards.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Documentation Index.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Installer Assessment Report.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Naming Conventions and Organization Standards.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Security and Performance Benchmarks.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Server Configuration Requirements.md
    - C:\_1mybizz\paddle-plugin\Docs\Kilocode\KiloCode MCP Server Validation Checklists.md
    
## Files relating to the design and modus operandii of paddle-plugin:
    - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\api-documentation\server-communication-api.md
    - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\architecture-diagrams\integration-architecture.md
    - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\database-schema\assessment-store-schema.md
    - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\database-schema\assessment-store-schema.sql
    - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\database-schema\database-schema-specifications.md

## Essential system guides:
    C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides:
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\admin-configuration.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\admin-installation.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\admin-monitoring.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\admin-security.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\api-documentation.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\compliance-validation-instructions.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\compliance-validation.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\configuration-procedures.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\configuration.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\database-schema.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\developer-api-documentation.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\developer-getting-started.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\documentation-quality-standards.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\documentation-review-processes.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\documentation-update-procedures.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\documentation-version-control.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\installation-guides.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\installation.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\integration-architecture.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\troubleshooting-guides.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\troubleshooting.md
        - C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\guides\user-guides.md
    
## Integrated systems
C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Complete Unified Setup Achieved.md
    Cache management system:
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Cache Management
        Anticipatory Intelligent Caching Architecture
            3.1. Predictive Cache  
            Zero-token hinting layer for anticipated context usage.  
             3.2. Semantic Cache  
            Adaptive prompt reuse layer based on behavioral context.  
            3.3. Vector Cache  
            Embedding-based context selector and reranker.  
            3.4. Global Knowledge Cache  
            Fallback memory leveraging persistent LLM training data or static knowledge bases.  
            Persistent Context Memory (Vector Diary)  
    
    CI/CD system
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Ci,CD system
        To be finalized and implemented
    
    Github Version Control
        Paddle-plugin (vscode <-> github)
            Note that all references in the all the VSCode files to vsc_ide are actually meant to be "paddle-plugin" and not "vsc_ide"
            C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Github VC\Github VC vsc-ide.md
        Mybizz (vscode <-> Github <-> Anvil)
            C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Github VC\Github VC mybizz.md
        Vsc_ide (c:\vsc-ide <-> Github)
            The name "vsc_ide" now ONLY applies to paddle-plugin audits and NOT to the paddle-plugin system per se
            
    Memory system
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Memory
        Episodic memory
								Semantic Memory
        Working Memory
        
        Memory System Components:
        PostgreSQL Backend: Structured storage for episodic and semantic memories with pgvector extension
        PGvector/SQLite-vec: Vector database for semantic search and similarity matching
        Memory Bank: Markdown-based document memory for project context and active sessions
        MCP Server: Standardized interface for memory operations via Model Context Protocol
        Working Memory: Short-term context storage for active sessions with TTL management
        
    Orchestration System (AG2)
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Orchestration
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Orchestration (AG2)
        multi-agent platform designed to coordinate and manage various AI agents working together to accomplish complex tasks. The system provides a unified interface for agent collaboration, memory management, and task distribution.
        
    Podman
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Podman
        The containerization system deployed in our environment. Podman (Pod Manager) is a daemonless container engine for developing, managing, and running OCI Containers on our System.
        
    Postgres
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Postgres
        a fully functional, production-ready database installation with pgvector extension support, integrated with multiple MCP (Model Context Protocol) servers for various AI and memory-related operations.
        
    RAG System
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Rag
        RAG System Design incorporating the agreed solutions of using Simba for Knowledge Management and AG2 for agentic decision-making logic and interaction orchestration.
        
    Secrets management system
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Secrets Management
        The Secrets Management System is designed to centralize and secure all sensitive information across the paddle-plugin ecosystem. The system leverages HashiCorp Vault as the primary secrets management platform with comprehensive fallback mechanisms and validation systems.
    
    Simba knowledge Management system
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Simba
        Simba Knowledge Management System (KMS) is an open-source, portable KMS designed to integrate seamlessly with Retrieval-Augmented Generation (RAG) systems
        
    Testing, Validation System
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Testing, Validation system
        Design to be finalized. Aimed at providing testing a validation infrastructure for use when developing user apps
        
    Token management system
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Token Management
        The Token Management System provides comprehensive control over AI token usage across various applications and services to effectively manage their token quotas, monitor usage, and optimize their AI interactions.
        
    Vector system
        C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions\Vector
        The Vector System provides semantic search and retrieval capabilities using PostgreSQL with the pgvector extension, integrated with MCP (Model Context Protocol) servers for RAG (Retrieval-Augmented Generation) functionality.
        
## Supporting features:
    Memory bank
        C:\_1mybizz\paddle-plugin\memorybank
    Test Bank
        C:\_1mybizz\paddle-plugin\Test Bank
        Intended to be the central repository for all tests. To be organized in a structured, categorical manner. This is to keep all the tests in a central location for easy management by the Testing, validation system

## MCPs Installed and available:
(Rewrite implies that the docs have been updated/ rewritten)
        MCP Agent Memory (rewrite)
        MCP Brave Search (rewrite)
        MCP Configuration and Compliance Server Architecture
        MCP Container Control (rewrite)
        MCP EasyOCRmcp (rewrite)
        MCP Everything Search MCP Server (rewrite)
        MCP Fastmcp (rewrite)
        MCP file-mcp-server (rewrite)
        MCP filesystem (rewrite)
        MCP Generic MCP Package Installer (NOT Installed) (Rewrite)
        MCP Github (Pending)
        MCP KiloCode MCP Server Installer (rewrite)
        MCP Logging Telemetry (rewrite)
        MCP Memory System (rewrite)
        MCP Playwright (rewrite)
        MCP Postgres (rewrite)
        MCP Pytest (rewrite)
        MCP RAG-PGvector (rewrite)
        MCP Scheduler (rewrite)
        MCP Server-Fetch (rewrite)
        MCP Snap-Windows (rewrite)
        MCP Testing Validation

## Assessment Store Feature:
    The assessment store was developed by Kilo Code as during the attempt to integrate the Orchestration system. This system needs to be evaluated and it needs to be determined whether this system is applicable, relevant or whether it should be removed or further developed: 
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_API_Methods.md
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_Architecture_Design.md
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_Implementation_Roadmap.md
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_Migration_Strategy.md
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_Performance_Scalability.md
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_Service_Design.md
        C:\_1mybizz\paddle-plugin\Docs\AssessmentStore_TypeScript_Interfaces.md
        
## Current Priorities:
    1. ### Orchestrator layer integration (100% the highest priority)
        The  .kilocode / Kilocode UI needs to be  correctly setup to allow kilocode and AG2 to find and use the MCP tools as required and to make kilocode environmentally aware of the systems available.
        There have been several big attmpts at gettimng this intgration establish and there are many documents to consider.However, I feel that previous attempt have been too wide, deep and sophisticated where as a simple robust approach is preferrred
        The README may be completely wrong and must be re-evaluated
								The role of AG2 needs to be determined definitively and applied as AG2 can add immense value to the agentic IDE
    2. ### Virtual Environments
        Venv's need to be examined. 
        There may be a very bad situation where totally inappropriate duplicate installations have been implemented
        It may be that essential elements are too deeply nested and cannot be found by the orchestration system.
        The integration points contained in the venv's may need to be correctly identified and mapped
    3. ### Partial CI/CD setup
        This system has only partially been designed and also partially implemented and partially documented. The CI/CD system needs to be properly scoped, architected, validated and implemented.
    4. ### TestBank
        the Test Bank is a repository of tests meant to serve application development projects rather than the VS Code setup. However, Kilo Code has interpreted the testing system as part of the IDE configuration. The pyproject.toml defines pytest.ini_options for testsGitHub and the restore guide suggests running environment testsGitHub, but a dedicated repository for application‑level tests would keep the IDE lean.
        Ideally, the testbank is part of the overall Testing, validation system and must be setup to support the testing, validation system with logical catagorization and further segmentaion as required
        The Test bank is the central repo for all tests in order to keep the IDE system clean, lean and well managed
    5. ### Secrets
        The vscode Agentic IDE requires to have all credentials managed by the 'Secrets Management' system which is Hashicorp based. Currently there may be API Keys and passwords stored in hardcoding in the files and in environment variables.
        Secrets must not be passed to github, they must remain well protrected within the hashicorp secrets system
    6. ### Podman
        It may be that Podman is not being used as effectively as possible. We want to ensure that optimum use is made of podman. Perhaps the use of podman can obviate having an excessive situation with the venv's
    7. ### Kilo Code file generation
        Review the output of Kilo Code and remove unnecessary or misinterpreted files. Establish stricter prompts or parameters to prevent it from generating large numbers of irrelevant documents.
        Kilo code often runs ahead of the architect and produces an implementation which no longer aligns with the architecture. It is essential that the architect is responsible for the design which is implemented. Kilo Code, 'Code Mode',  must not be permitted to implement systems and subsystems on the fly without testing against the Architects plan. When the implementation is required to differ from the architects plan, the Architect must review the proposed alteration and iterate the plan. This will help to produce a well integrated and contiguous implementation
    8. ### Workspace, Nodes and Heavy Libraries
        Review and set up appropriate workspaces
        We need to take stock of the libraries and node modules in use and determine a set which supports the Agentic IDE and the potential project applications which we intend to build here.
    9. ### Orphans
        There have been many installations that have been implemented and removed, Others have gone through phases of iteration, the result is that there are many orphaned Docs, folders, files and configurations which need to be identified and removed
        There is a serious risk of potentially removing an element which appears to be redundant yet actually is required somewhere and then accidentally breaking the code.
        The source of truth must be the overall Architectural plan
    10. ### The architectural plan
        The vscode agentic IDE started when I had an Anvil application and repo called paddle-plugin vscode. I needed to add tools to assist me and in this way, the system was built. Now the system is fairly well designed and almost 100% completely built but proper thought still needs to be given to objective based system scoping and subsequent overall architecture. Strictly speaking there is currently no comprehensive architectural plan. An architectural plan will address many of the issues which we are currently facing in the system
        
        
    
    
