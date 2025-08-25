

## Overview

- **Anvil.works** is the authoritative source of truth where the project is built and hosted. The App is named "mybizz"
    
- Anvil automatically syncs the project with its associated **GitHub repository**. The repository is called "mybizz"
    
- The mybizz GitHub repository will be cloned into **VS Code** for local code development and testing once the vscode agentic IDE setup has been completed
       
- GitHub then automatically syncs these changes back to the live Anvil project.
    

## Development Workflow

1. **Cloning the Project**  
    Clone the project repository from GitHub into VS Code for local development. This repository contains all app files synced from Anvil.
    
2. **Code Development and Testing**

    - Anvil.works runs Python 3.7x
    
    - Develop and test your Python 3.7.x compatible code locally in VS Code.
        
    - Maintain Python 3.7.x compatibility to ensure consistency with Anvil’s runtime environment.

    As I could not get Python 3.7x, I installed 3.8 as it is closest to 3.7x
        
3. **File Management and Version Control**
    
    - Use a strict `.gitignore` to exclude any files not part of the mybizz app
        
    - Only files that exist in the Anvil project repository should be committed and pushed to GitHub.
        
4. **New File Creation Fallback Protocol**

    This protocol is a fall measure in case newly created mybizz files in VScode do not get synced back to Anvil.wors. 

    Do not implement this fall back unless required
    
    - When a new file is needed, **create it first in the Anvil project** via the Anvil web editor.
        
    - Then, sync or create the corresponding file in your local VS Code project.
        
    - This ensures new files are properly tracked and managed by Anvil and GitHub.
        
5. **Pushing Changes**
    
    - After finalizing and testing changes, commit and push only the relevant app files back to GitHub from VS Code.
        
    - GitHub automatically syncs these changes to the live Anvil project, updating the hosted app.
        

## Key Points

- **Anvil is the single source of truth**; all app files originate from and are managed by Anvil.
    
- **GitHub acts as the synchronization bridge** between Anvil and your local VS Code environment.
    
- **Gitignore is rigorously applied** to prevent pushing non-app or local files to GitHub.
    
- **New files Fallback Protocol**
Files must be created in Anvil first before local development to maintain sync integrity.
    
- As I work solo, so this simple, linear workflow minimizes complexity and avoids conflicts