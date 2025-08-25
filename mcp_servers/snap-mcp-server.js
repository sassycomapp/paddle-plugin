#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

class SnapWindowsServer {
  constructor() {
    this.server = new Server(
      {
        name: 'snap-windows',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupTools();
  }

  setupTools() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'arrange_windows',
            description: 'Arrange windows in predefined layouts',
            inputSchema: {
              type: 'object',
              properties: {
                layout: {
                  type: 'string',
                  description: 'Layout type (2x2, 3x3, left-right, top-bottom, maximize-all)',
                  enum: ['2x2', '3x3', 'left-right', 'top-bottom', 'maximize-all']
                }
              },
              required: ['layout']
            }
          },
          {
            name: 'snap_to_position',
            description: 'Snap a specific window to a position',
            inputSchema: {
              type: 'object',
              properties: {
                windowTitle: {
                  type: 'string',
                  description: 'Title of the window to snap'
                },
                position: {
                  type: 'string',
                  description: 'Position to snap to',
                  enum: ['left', 'right', 'top', 'bottom', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']
                }
              },
              required: ['windowTitle', 'position']
            }
          },
          {
            name: 'manage_layouts',
            description: 'Save or apply window layouts',
            inputSchema: {
              type: 'object',
              properties: {
                action: {
                  type: 'string',
                  description: 'Action to perform',
                  enum: ['save', 'apply']
                },
                name: {
                  type: 'string',
                  description: 'Name of the layout'
                }
              },
              required: ['action', 'name']
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'arrange_windows':
            return await this.arrangeWindows(args);
          case 'snap_to_position':
            return await this.snapToPosition(args);
          case 'manage_layouts':
            return await this.manageLayouts(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  async arrangeWindows(args) {
    const { layout = '2x2' } = args;
    
    // Validate layout
    const validLayouts = ['2x2', '3x3', 'left-right', 'top-bottom', 'maximize-all'];
    if (!validLayouts.includes(layout)) {
      throw new Error(`Invalid layout. Valid options: ${validLayouts.join(', ')}`);
    }

    // Use PowerShell for window management on Windows
    const script = this.getArrangeScript(layout);
    const { stdout, stderr } = await execAsync(`powershell -Command "${script}"`);
    
    if (stderr) {
      console.error('PowerShell error:', stderr);
    }

    return {
      content: [
        {
          type: 'text',
          text: `Windows arranged using ${layout} layout successfully.`,
        },
      ],
    };
  }

  async snapToPosition(args) {
    const { windowTitle, position } = args;
    
    if (!windowTitle || !position) {
      throw new Error('windowTitle and position are required');
    }

    const validPositions = ['left', 'right', 'top', 'bottom', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'];
    if (!validPositions.includes(position)) {
      throw new Error(`Invalid position. Valid options: ${validPositions.join(', ')}`);
    }

    const script = this.getSnapScript(windowTitle, position);
    const { stdout, stderr } = await execAsync(`powershell -Command "${script}"`);
    
    if (stderr) {
      console.error('PowerShell error:', stderr);
    }

    return {
      content: [
        {
          type: 'text',
          text: `Window "${windowTitle}" snapped to ${position} successfully.`,
        },
      ],
    };
  }

  async manageLayouts(args) {
    const { action, name } = args;
    
    if (!action || !name) {
      throw new Error('action and name are required');
    }

    if (action === 'save') {
      // Create directory if it doesn't exist
      await execAsync(`powershell -Command "if (!(Test-Path '$env:USERPROFILE\\.snap-layouts')) { New-Item -ItemType Directory -Path '$env:USERPROFILE\\.snap-layouts' -Force }"`);
      
      // Save current window layout
      const script = this.getSaveLayoutScript(name);
      const { stdout, stderr } = await execAsync(`powershell -Command "${script}"`);
      
      if (stderr) {
        console.error('PowerShell error:', stderr);
      }

      return {
        content: [
          {
            type: 'text',
            text: `Layout "${name}" saved successfully.`,
          },
        ],
      };
    } else if (action === 'apply') {
      // Apply saved layout
      const script = this.getApplyLayoutScript(name);
      const { stdout, stderr } = await execAsync(`powershell -Command "${script}"`);
      
      if (stderr) {
        console.error('PowerShell error:', stderr);
      }

      return {
        content: [
          {
            type: 'text',
            text: `Layout "${name}" applied successfully.`,
          },
        ],
      };
    } else {
      throw new Error("Invalid action. Use 'save' or 'apply'");
    }
  }

  getArrangeScript(layout) {
    const scripts = {
      '2x2': `
        Add-Type -AssemblyName System.Windows.Forms;
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;
        $windows = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 4;
        $positions = @(
          @{x=0; y=0; w=0.5; h=0.5},
          @{x=0.5; y=0; w=0.5; h=0.5},
          @{x=0; y=0.5; w=0.5; h=0.5},
          @{x=0.5; y=0.5; w=0.5; h=0.5}
        );
        for ($i = 0; $i -lt $windows.Count; $i++) {
          $pos = $positions[$i];
          $hwnd = $windows[$i].MainWindowHandle;
          $rect = New-Object System.Drawing.Rectangle;
          $rect.X = [int]($pos.x * $screen.Width);
          $rect.Y = [int]($pos.y * $screen.Height);
          $rect.Width = [int]($pos.w * $screen.Width);
          $rect.Height = [int]($pos.h * $screen.Height);
          Add-Type @"
            using System.Runtime.InteropServices;
            public class Win32 {
              [DllImport("user32.dll")]
              public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
            }
"@;
            [Win32]::SetWindowPos($hwnd, 0, $rect.X, $rect.Y, $rect.Width, $rect.Height, 0);
        }
      `,
      'left-right': `
        Add-Type -AssemblyName System.Windows.Forms;
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;
        $windows = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 2;
        if ($windows.Count -ge 2) {
          $hwnd1 = $windows[0].MainWindowHandle;
          $hwnd2 = $windows[1].MainWindowHandle;
          Add-Type @"
            using System.Runtime.InteropServices;
            public class Win32 {
              [DllImport("user32.dll")]
              public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
            }
"@;
            [Win32]::SetWindowPos($hwnd1, 0, 0, 0, $screen.Width/2, $screen.Height, 0);
            [Win32]::SetWindowPos($hwnd2, 0, $screen.Width/2, 0, $screen.Width/2, $screen.Height, 0);
        }
      `,
      'maximize-all': `
        $shell = New-Object -ComObject shell.application;
        $windows = $shell.Windows() | Where-Object { $_.Visible -eq $true };
        foreach ($window in $windows) {
          $window.Visible = $false;
          $window.Visible = $true;
        }
      `
    };
    
    return scripts[layout] || scripts['2x2'];
  }

  getSnapScript(windowTitle, position) {
    const positions = {
      'left': { x: 0, y: 0, w: 0.5, h: 1 },
      'right': { x: 0.5, y: 0, w: 0.5, h: 1 },
      'top': { x: 0, y: 0, w: 1, h: 0.5 },
      'bottom': { x: 0, y: 0.5, w: 1, h: 0.5 },
      'top-left': { x: 0, y: 0, w: 0.5, h: 0.5 },
      'top-right': { x: 0.5, y: 0, w: 0.5, h: 0.5 },
      'bottom-left': { x: 0, y: 0.5, w: 0.5, h: 0.5 },
      'bottom-right': { x: 0.5, y: 0.5, w: 0.5, h: 0.5 },
      'center': { x: 0.25, y: 0.25, w: 0.5, h: 0.5 }
    };

    const pos = positions[position];
    return `
      Add-Type -AssemblyName System.Windows.Forms;
      $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds;
      $window = Get-Process | Where-Object { $_.MainWindowTitle -like "*${windowTitle}*" } | Select-Object -First 1;
      if ($window) {
        $hwnd = $window.MainWindowHandle;
        $rect = New-Object System.Drawing.Rectangle;
        $rect.X = [int](${pos.x} * $screen.Width);
        $rect.Y = [int](${pos.y} * $screen.Height);
        $rect.Width = [int](${pos.w} * $screen.Width);
        $rect.Height = [int](${pos.h} * $screen.Height);
        Add-Type @"
          using System.Runtime.InteropServices;
          public class Win32 {
            [DllImport("user32.dll")]
            public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
          }
"@;
          [Win32]::SetWindowPos($hwnd, 0, $rect.X, $rect.Y, $rect.Width, $rect.Height, 0);
      }
    `;
  }

  getSaveLayoutScript(name) {
    return `
      $layout = @{
        name = "${name}"
        timestamp = Get-Date
        windows = @()
      };
      $processes = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 };
      foreach ($proc in $processes) {
        $rect = New-Object System.Drawing.Rectangle;
        Add-Type @"
          using System.Runtime.InteropServices;
          public class Win32 {
            [DllImport("user32.dll")]
            public static extern bool GetWindowRect(IntPtr hWnd, out System.Drawing.Rectangle lpRect);
          }
"@;
          $rect = New-Object System.Drawing.Rectangle;
          [Win32]::GetWindowRect($proc.MainWindowHandle, [ref]$rect);
        $layout.windows += @{
          title = $proc.MainWindowTitle
          process = $proc.ProcessName
          x = $rect.X
          y = $rect.Y
          width = $rect.Width - $rect.X
          height = $rect.Height - $rect.Y
        };
      };
      $layout | ConvertTo-Json -Depth 3 | Out-File "$env:USERPROFILE\\.snap-layouts\\${name}.json" -Force;
    `;
  }

  getApplyLayoutScript(name) {
    return `
      if (Test-Path "$env:USERPROFILE\\.snap-layouts\\${name}.json") {
        $layout = Get-Content "$env:USERPROFILE\\.snap-layouts\\${name}.json" | ConvertFrom-Json;
        foreach ($win in $layout.windows) {
          $process = Get-Process | Where-Object { $_.ProcessName -eq $win.process -and $_.MainWindowTitle -eq $win.title };
          if ($process) {
            $hwnd = $process.MainWindowHandle;
            Add-Type @"
              using System.Runtime.InteropServices;
              public class Win32 {
                [DllImport("user32.dll")]
                public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
              }
"@;
              [Win32]::SetWindowPos($hwnd, 0, $win.x, $win.y, $win.width, $win.height, 0);
          }
        }
      }
    `;
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

// Start the server
const server = new SnapWindowsServer();
server.run().catch(console.error);
