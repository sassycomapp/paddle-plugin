# Instructional Guide: Using Custom Rules in Kilo Code

## 1. Introduction
Custom Rules in **Kilo Code** are a powerful feature that allows you to define consistent behaviors and constraints for the AI model.  
- They are essentially **text files with instructions** for the AI.  
- Supported formats: Markdown (`.md`), XML, or similar.  
- Purpose: Guide the AI model to follow specific instructions across projects and modes.  

Examples include:
- Restricting access to sensitive files.  
- Enforcing specific package managers (e.g., always use **Yarn** instead of **npm**).  
- Applying project-specific or team-wide coding guidelines.  

---

## 2. How Custom Rules Work
Rules are inserted directly into the **system prompt** that is sent to the AI.  

The **system prompt** consists of three parts:  
1. Base system prompt  
2. Environment details  
3. Task instructions  

➡️ **Your custom rules are appended** to the system prompt, making them part of every interaction with the model.

---

## 3. Types of Rules
There are **three scopes** for rules in Kilo Code:

### 3.1 Global Rules
- Always applied across **all projects**.  
- Useful when you want consistency (e.g., always use **Yarn**).  
- Location: stored in your **home folder** under:  
  ```
  ~/.killercode/rules
  ```  
  *(Exact path depends on your operating system)*  

### 3.2 Workspace (Project) Rules
- Applied **only to a specific project/workspace**.  
- Stored inside the project folder:  
  ```
  <project>/.killercode/rules
  ```  
- Useful for team projects, so rules can be **version-controlled and shared** (e.g., coding style guides, linting conventions).  

### 3.3 Mode Rules
- Applied **per project and per mode**.  
- Examples:  
  - Rules for **Code Mode** (applied only when coding).  
  - Rules for **Ask Mode** (applied only when asking questions).  
  - Rules for custom modes you define.  
- Location:  
  ```
  <project>/.killercode/rules-<mode>
  ```  

---

## 4. Creating Rules

### 4.1 Using the Graphical User Interface (GUI)
- In the bottom-right corner of Kilo Code, click the **Rule Management button**.  
- Options:  
  - **Create Global Rule** → file created in the home folder.  
  - **Create Workspace Rule** → file created inside the project folder.  
- Files appear immediately in your editor, ready to be edited.  

**Example (Global Rule)**  
- Create `yarn.md` inside global rules folder.  
- Contents:  
  ```md
  Always use yarn instead of npm.
  ```  
- Applied to **all projects** automatically.  

**Example (Workspace Rule)**  
- Create `tooling.md` inside `.killercode/rules` of a specific project.  
- Contents:  
  ```md
  Always use yarn for this project.
  ```  
- Applied only to this project.  

### 4.2 Manually in the Filesystem
- Create rule files directly in the appropriate rules folder.  
- Example for Mode Rules:  
  ```
  ~/.killercode/rules-code/
  ~/.killercode/rules-ask/
  ```  
- Add `.md` files with instructions.  

---

## 5. Rule Execution Examples

- In **Ask Mode**, rules placed under `rules-ask` will be applied.  
- In **Code Mode**, rules from `rules-code` will apply instead.  
- Switching modes changes which rules get appended to the system prompt.  

**Verification**:  
- You can check the system prompt in the editor to confirm which rules were included.  

---

## 6. Best Practices & Considerations
1. **Use Rules for Repetition**  
   - If you repeat instructions often, move them into a rule file.  

2. **Avoid Overloading the System Prompt**  
   - Every rule is appended to **every request**.  
   - Too many or overly verbose rules may **exceed context window limits**.  

3. **Prompt Engineering Tips**  
   - Use **examples** in rules.  
   - Format text (lists, code blocks) for clarity.  

4. **Model Limitations**  
   - Some less capable models may **ignore or misinterpret rules**.  
   - Effectiveness depends on both the model and how well the rule is written.  

5. **Team Collaboration**  
   - Store **workspace rules in version control (Git)** for team-wide consistency.  

---

## 7. Key Takeaways
- **Global Rules** → Always apply across all projects.  
- **Workspace Rules** → Apply only within a specific project.  
- **Mode Rules** → Apply based on the mode you’re working in.  
- **Rules = Memory foundation** → They simplify workflows by embedding repeated instructions into the system prompt.  

---

## 8. Conclusion
Custom Rules are a **core productivity tool** in Kilo Code:  
- They automate repetitive instructions.  
- Help enforce consistency across projects and teams.  
- Support project-specific and mode-specific workflows.  

By thoughtfully defining rules, you can streamline your coding experience, reduce mistakes, and boost efficiency.
