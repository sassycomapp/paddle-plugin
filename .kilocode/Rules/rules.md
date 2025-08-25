## Enforcement: strict

### Rule: DocumentationLocationRules
**MCPDocumentation:**  
C:\_1mybizz\paddle-plugin\Docs\MCP_Tools\MCP Details

**SystemsDocumentation:**  
C:\_1mybizz\paddle-plugin\Docs\Systems_Descriptions

**Instruction:**  
Always save converted files to the same folder as the source file.

**Priority:**  
Always check these directories first when looking for information about MCP servers or system components.

---

### Rule: WriteGuard (ALLOWLIST ONLY)
**AllowedWriteDirs:**
- C:\_1mybizz\paddle-plugin\.kilocode\
- C:\_1mybizz\paddle-plugin\Docs\
- C:\_1mybizz\paddle-plugin\mcp_servers\
- C:\_1mybizz\paddle-plugin\testing-validation-system\

**DeniedPatterns (block):**
- ***/node_modules/**
- ***/.git/**
- ***/.venv/**  ***/venv/**
- ***/dist/**  ***/build/**
- ***/__pycache__/**  ***/.cache/**
- **/*.tmp  **/*.bak  **/*_backup.*  **/*copy*.*  **/*draft*.*

**Behavior:**
- If target path NOT under AllowedWriteDirs → DENY.
- If filename matches DeniedPatterns → DENY.
- Never create “test”, “sample”, or “junk” files unless user explicitly requests and provides exact path.

---

### Rule: ApprovalBeforeWrite
**Behavior:**
- For any new file OR file > 200 lines change → REQUIRE explicit approval with filepath diff summary.
- No multi-file writes in one action unless user provides a list of exact paths.

---

### Rule: MCPUsagePolicy
**Behavior:**
- Prefer MCP servers for: file I/O (filesystem), RAG (rag-mcp-server), memory ops (agent-memory, mcp-memory-service), DB (postgres), web fetch (fetch), search (Everything).
- If an MCP is defined for an operation, use it. Do not re-implement functionality.
- On MCP error → report error and stop. Do not fallback to ad-hoc code generation.

---

### Rule: Logging
**Behavior:**
- Summarize actions before execution (paths, counts).
- After execution, list exactly what changed (paths, adds/modifies).
