# Instructional Guide: Memory Bank in Kilo Code

## Overview
**Problem**: AI assistants reset context between sessions, leading to wasted time, repeated explanations, and higher token costs.  
**Solution**: **Memory Bank** – persistent project memory for Kilo Code that stores briefs, context, and project knowledge in Markdown.  

**Benefits:**
- ✅ Instant context recovery — no need to rescan codebases  
- ✅ Works with any programming language or tech stack  
- ✅ Captures "tribal knowledge" that usually lives only in developers’ heads  
- ✅ Produces self-documenting projects usable by both humans and AI  
- ✅ Scales with project size — larger projects yield larger savings  

---

## Setup Instructions (Under 5 Minutes)

### 1. Create Directory
```bash
mkdir -p .kilocode/rules/memory-bank
```

### 2. Add Project Brief
- Inside the new folder, create a **project brief** describing:  
  - **Product** – what it is and why it exists  
  - **Context** – current tasks or problems being addressed  
  - **Tech** – languages, frameworks, tools used  
  - **Architecture** – high-level design/structure  

Example brief:
```markdown
# Project Brief
Product: Formation – system configuration tool for Mac setup
Context: Automating installation of packages, apps, and configs
Tech: Bash, Homebrew, ASDF, npm packages
Architecture: Shell scripts with defined setup flow
```

### 3. Add Memory Bank Instructions
- Create a file called:
```bash
memory-bank-instructions.md
```
- Paste the official **Memory Bank instructions** from Kilo Code documentation.

### 4. Initialize in Architect Mode
- Switch to **Architect Mode** in Kilo Code.  
- Ensure a **high-capacity AI model** is selected (avoid lightweight models).  
- Run:
```bash
Initialize memory bank
```

---

## Post-Initialization

### 5. Review Generated Files
- **Brief** → high-level description of the project  
- **Context** → current focus/task (e.g., “Memory Bank initialization”)  
- **Package Inventory** → list of installed packages  
- **Tech** → technologies in use (e.g., Bash shell scripts)  
- **Architecture** → structural overview  

**Action Required:** Carefully review and refine these files for accuracy. This ensures AI has correct, persistent knowledge.

---

## Example Workflow

1. **Error without Memory Bank:**  
   - Formation setup failed because Google Chrome wasn’t installed by Brew.  
   - AI assistant had to re-learn project context, costing **$0.30** in model usage.  

2. **Error with Memory Bank:**  
   - Same issue handled after Memory Bank setup.  
   - AI immediately recognized context and solved it.  
   - Cost reduced to **$0.16**.  

**Result:** ~50% savings + faster troubleshooting.

---

## Pro Tips
- Only include essential information in rules/briefs. Too much data bloats the system prompt and reduces model efficiency.  
- Use formatted Markdown (lists, code blocks, examples) for clarity.  
- Store **workspace rules** in Git for team-wide consistency.  
- Always validate AI-generated files after initialization.  

---

## Useful Links
- 🔗 [Kilo Code](https://kilocode.ai)  
- 🔗 [Full Blog Post](https://blog.kilocode.ai/p/how-memory...)  
- 🔗 [Discord Community](https://kilo.love/discord)  
- 🔗 [Memory Bank Setup Guide](https://kilocode.ai/docs/advanced-usa...)  

---

## Conclusion
Memory Bank transforms Kilo Code into a **persistent development partner** by:  
- Embedding briefs, context, and architecture into the system prompt  
- Reducing repetitive explanations  
- Lowering token costs  
- Improving productivity across sessions  

Integrate Memory Bank to achieve **smarter, faster, and more cost-effective AI-assisted development**.

