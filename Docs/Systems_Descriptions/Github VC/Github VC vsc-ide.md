# Github VC - vsc_ide

This process requires that the entire "mybizz" project is in gitignore.

To back up your entire VS Code environment (including the “semi‑autonomous agentic IDE” in the `paddle‑plugin` folder) and make it reproducible, you need to collect both your project files and your editor‑level configuration.  VS Code keeps profile settings, keybindings, snippets and extensions outside of your project folder in a platform‑specific location.  The official documentation shows that the user‑settings JSON file for a profile is stored in `%APPDATA%\Code\User\profiles\<profile ID>\settings.json` on Windows, `$HOME/Library/Application Support/Code/User/profiles/<profile ID>/settings.json` on macOS and `$HOME/.config/Code/User/profiles/<profile ID>/settings.json` on Linux.  VS Code’s *Export Profile* command allows you to package these settings and choose whether to save to a GitHub gist or to a local file with the `.code‑profile` extension.  You can also list all installed extensions with the command‑line tool (`code --list-extensions`) and save the list or generate installation commands.

## 0. Objective
Thecurrent project is named "paddle-plugin" but this is wrong, it should be named "vsc_ide". The project vsc_ide holds the entire Semi_autonomous agentic IDE which is setup in vscode. It does not hold any Applicaton development projects (my apps). When backing up the vsc_ide repo to github, the Applicaton development project (my app name) will be in gitignore so that it is not included with the vsc_ide "app". When the the Applicaton development project (my app name) is backed up to the (My app name) repo on github, the vsc_ide will be in the gitignore

### 1. Collect your VS Code configuration

1. **Identify what to back up** – Your VS Code configuration includes global/user settings, keybindings, snippets, tasks, UI layout and the list of extensions.  Each profile stores its own `settings.json` and related files under the profile directory described above.  Workspace‑specific settings live inside `.vscode` folders of your projects.

2. **Export a profile (recommended)** – In VS Code go to **File → Preferences → Profiles (Default) → Export Profile…**.  This opens the *Profiles* view and lets you uncheck items you don’t want to include.  When you select **Export**, VS Code asks you to save the profile to a GitHub gist or to your local file system.  Saving locally produces a `.code-profile` file containing your settings, snippets, keybindings and extension list.  Store this file in your repository (see below).

3. **Manually copy the settings (optional)** – If you prefer manual control, copy the relevant files from your profile directory.  On Linux, this will be in `~/.config/Code/User/profiles/<profile ID>/`; on macOS it is under `$HOME/Library/Application Support/Code/User/profiles/<profile ID>/`; on Windows it is `%APPDATA%\Code\User\profiles\<profile ID>\`.  The files you typically need are:

   * `settings.json` – user settings.
   * `keybindings.json` – keyboard shortcuts.
   * `snippets` folder – custom snippets.
   * `tasks.json` and `launch.json` if you have tasks or launch configurations.
   * `.vscode` folder inside `paddle‑plugin` (workspace settings).

4. **Record installed extensions** – Run the following command in a terminal to list your extensions and save them to a file:

   ```bash
   code --list-extensions > extensions.txt
   ```

   Alternatively, pipe the output to create install commands:
   `code --list-extensions | xargs -L 1 echo code --install-extension > install-extensions.sh`.  Add `extensions.txt` or `install-extensions.sh` to your repository.

5. **Document global dependencies** – Note any software installed at the system level (Node.js, Python, specific toolchains, the VS Code edition you’re using, etc.) because they are not included in the editor profile.  Document their versions in a `docs/restore-guide.md` file so they can be reinstalled later.

### 2. Set up a Git repository for your environment

1. **Create a repository** – In the root of your `paddle‑plugin` folder, run:

   ```bash
   git init
   git add .
   git commit -m "Initial commit of paddle-plugin project and VS Code config"
   ```

   If you already have the `sassycomapp/paddle-plugin` repository on GitHub, add it as the remote with `git remote add origin https://github.com/sassycomapp/paddle-plugin.git`.

2. **Add your VS Code configuration** – Create a subfolder, e.g. `vscode-profile/`, and place your exported `.code-profile` file or the manually copied `settings.json`, `keybindings.json`, snippets folder, and your `extensions.txt` or `install-extensions.sh` file there.  Commit these files:

   ```bash
   mkdir vscode-profile
   mv ~/Downloads/MyProfile.code-profile vscode-profile/  # or copy the manual files
   git add vscode-profile
   git commit -m "Add VS Code profile and extension list"
   ```

3. **Write a restore guide** – In the repository add a `restore-guide.md` (or expand `README.md`) that explains:

   * Which system‑level tools (VS Code version, Node.js, Python, etc.) must be installed.
   * How to import the profile: open VS Code and choose **File → Preferences → Profiles → Import Profile**, select your `.code-profile` file and click **Create**.  Remind the reader to click the cloud‑download icon to install extensions when prompted.
   * Alternatively, how to restore manually: copy `settings.json` to the appropriate user directory, copy `keybindings.json` and snippets, then run `sh install-extensions.sh` or `while read -r ext; do code --install-extension "$ext"; done < extensions.txt` to reinstall extensions.  On Linux the config directory is `~/.config/Code/User/`; adjust the path for macOS or Windows accordingly.
   * How to restore workspace‑specific settings by copying the `.vscode` directory in `paddle‑plugin`.

4. **Push to GitHub** – When ready, push your commits:

   ```bash
   git push -u origin main
   ```

   (replace `main` with your branch name if different).

### 3. Keeping the backup up‑to‑date

* Whenever you install or remove extensions or change settings, either re‑export your profile or update `settings.json` and rerun `code --list-extensions` to refresh the list.  Commit and push these changes to keep your repository current.
* For small edits, you can manually adjust `settings.json` in the `vscode-profile` folder, but remember to copy the changes back to your user profile or export a fresh `.code-profile` to avoid divergence.

### 4. Optional: use Settings Sync

VS Code has a built‑in Settings Sync feature that can automatically synchronize settings, keyboard shortcuts, user snippets, tasks, UI state, extensions and profiles across machines.  You can enable it via **Backup and Sync Settings…** in the gear menu.  Settings Sync stores your preferences in the cloud and only requires signing in with GitHub or Microsoft.  While this is convenient, keeping a version‑controlled backup as described above provides full transparency and allows you to restore the environment even without signing into Microsoft/GitHub or if a specific extension version is needed.

By following these steps, you’ll have a GitHub repository that contains both your project (`paddle‑plugin`) and a self‑contained snapshot of your VS Code environment.  The restore guide ensures you (or collaborators) can recreate the development environment on another machine or after a fresh installation.
