# installation of HashiCorp Vault on Windows 11**
 follow this actionable workflow based on Chocolatey package manager, which is straightforward and professional-grade:

1. **Open PowerShell as Administrator**  
   - Right-click the Start menu, select "Windows Terminal (Admin)" or "PowerShell (Admin)".

2. **Install Chocolatey** (if not already installed)  
   Run this command to install Chocolatey, the Windows package manager:  
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; `
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; `
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

3. **Install HashiCorp Vault using Chocolatey**  
   Run this command to install Vault:  
   ```powershell
   choco install vault -y
   ```

4. **Verify Vault Installation**  
   Close and reopen the terminal, then run:  
   ```powershell
   vault -v
   ```
   This confirms Vault is installed and shows its version.

5. **Initialize and Start Vault**  
   For local development, you can run Vault in dev mode to test:  
   ```powershell
   vault server -dev
   ```
   This starts Vault with an in-memory storage backend and outputs a root token for use.

6. **Setup Environment Variable (Optional but recommended)**  
   Add Vault’s executable path to the system PATH if Chocolatey didn't automatically do so, usually found at:  
   `C:\ProgramData\chocolatey\bin`

7. **Integrate Vault into your environment**  
   Since you use VSCode and other tools, use the VSCode Vault extension for easier secret management inside the IDE.

This workflow delivers a **simple, reliable, and fully functional Vault setup on Windows 11**, suitable for development to early production uses without unnecessary complexity.[1][2][3][5][8]

[1] https://www.youtube.com/watch?v=kjEOK6FCQsc
[2] https://www.liquidweb.com/blog/vault-secrets/
[3] https://community.chocolatey.org/packages/vault
[4] https://chocolatey.org/install
[5] https://tekanaid.com/courses/hashicorp-vault-101-certified-vault-associate/lessons/install-vault-windows-users/
[6] https://developer.hashicorp.com/vault/tutorials/get-started/install-binary
[7] https://developer.hashicorp.com/vault/tutorials/kubernetes-introduction/kubernetes-minikube-raft
[8] https://www.devopsschool.com/blog/hashicorp-vault-windows-lab-manual-1/


The unseal key and root token are displayed below in case you want to       
seal/unseal the Vault or re-authenticate.

Unseal Key: eATCQhdgiPp72id4JyUG/O05ZfdpN0OT9y/DAGuxk9Y=
Root Token: hvs.RQ2KK3iSPqaPbV1IxefJdVRz