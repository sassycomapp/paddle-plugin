#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { open, Database } from "sqlite";
import sqlite3 from "sqlite3";
import { exec, execFile } from "child_process";
import { promisify } from "util";
import path from "path";
import fs from "fs/promises";

const execAsync = promisify(exec);
const execFileAsync = promisify(execFile);

// Database setup
const DB_PATH = path.join(process.cwd(), "mcp_scheduler.db");
let db = null;

async function initializeDatabase() {
  db = await open({
    filename: DB_PATH,
    driver: sqlite3.Database,
  });

  // Enable foreign keys
  await db.exec("PRAGMA foreign_keys = ON");

  // Create tasks table
  await db.exec(`
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      command TEXT NOT NULL,
      run_at DATETIME NOT NULL,
      status TEXT NOT NULL DEFAULT 'scheduled',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      max_retries INTEGER DEFAULT 0,
      retry_count INTEGER DEFAULT 0,
      timeout_ms INTEGER DEFAULT 30000,
      enabled BOOLEAN DEFAULT 1,
      working_directory TEXT,
      environment_variables TEXT
    )
  `);

  // Create task_executions table
  await db.exec(`
    CREATE TABLE IF NOT EXISTS task_executions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      task_id INTEGER NOT NULL,
      execution_time DATETIME NOT NULL,
      status TEXT NOT NULL,
      exit_code INTEGER,
      stdout TEXT,
      stderr TEXT,
      error_message TEXT,
      duration_ms INTEGER,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
    )
  `);

  // Create indexes for better performance
  await db.exec(`
    CREATE INDEX IF NOT EXISTS idx_tasks_run_at ON tasks(run_at) WHERE enabled = 1 AND status = 'scheduled'
  `);
  await db.exec(`
    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
  `);
  await db.exec(`
    CREATE INDEX IF NOT EXISTS idx_executions_task_id ON task_executions(task_id)
  `);

  console.log("Database initialized successfully");
}

// Enhanced logging
const logger = {
  info: (message, data = null) => {
    console.error(`[INFO] ${new Date().toISOString()} - ${message}`, data || "");
  },
  warn: (message, data = null) => {
    console.error(`[WARN] ${new Date().toISOString()} - ${message}`, data || "");
  },
  error: (message, error = null) => {
    console.error(`[ERROR] ${new Date().toISOString()} - ${message}`, error || "");
  },
};

// Server setup
const server = new Server(
  {
    name: "mcp-scheduler-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool argument schemas
const scheduleTaskArgsSchema = z.object({
  name: z.string().min(1).describe("The name of the task."),
  command: z.string().min(1).describe("The shell command to execute."),
  runAt: z.string().describe("The ISO 8601 timestamp to run the task at (e.g., YYYY-MM-DDTHH:mm:ss.sssZ)."),
  maxRetries: z.number().min(0).max(10).default(0).describe("Maximum number of retries on failure."),
  timeoutMs: z.number().min(1000).max(300000).default(30000).describe("Timeout in milliseconds for task execution."),
  workingDirectory: z.string().optional().describe("Working directory for command execution."),
  environmentVariables: z.object({}).optional().describe("Environment variables for command execution."),
});

const listTasksArgsSchema = z.object({
  status: z.enum(["scheduled", "running", "completed", "failed", "cancelled"]).optional().describe("Filter by task status."),
  enabled: z.boolean().optional().describe("Filter by enabled/disabled tasks."),
});

const cancelTaskArgsSchema = z.object({
  taskId: z.number().describe("The ID of the task to cancel."),
});

const runTaskNowArgsSchema = z.object({
  taskId: z.number().describe("The ID of the task to run immediately."),
});

// Database helper functions
async function createTask(taskData) {
  const { name, command, runAt, maxRetries, timeoutMs, workingDirectory, environmentVariables } = taskData;
  
  const result = await db.run(
    `INSERT INTO tasks (name, command, run_at, max_retries, timeout_ms, working_directory, environment_variables)
     VALUES (?, ?, ?, ?, ?, ?, ?)`,
    [name, command, new Date(runAt).toISOString(), maxRetries, timeoutMs, workingDirectory, environmentVariables ? JSON.stringify(environmentVariables) : null]
  );
  
  return { id: result.lastID, ...taskData };
}

async function getTasks(filter = {}) {
  let query = "SELECT * FROM tasks WHERE 1=1";
  const params = [];

  if (filter.status) {
    query += " AND status = ?";
    params.push(filter.status);
  }

  if (filter.enabled !== undefined) {
    query += " AND enabled = ?";
    params.push(filter.enabled ? 1 : 0);
  }

  query += " ORDER BY created_at DESC";

  return await db.all(query, params);
}

async function getTaskById(taskId) {
  return await db.get("SELECT * FROM tasks WHERE id = ?", [taskId]);
}

async function updateTaskStatus(taskId, status, error = null) {
  const result = await db.run(
    "UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
    [status, taskId]
  );
  
  if (result.changes === 0) {
    throw new Error(`Task with ID ${taskId} not found`);
  }
  
  return await getTaskById(taskId);
}

async function deleteTask(taskId) {
  const result = await db.run("DELETE FROM tasks WHERE id = ?", [taskId]);
  return result.changes > 0;
}

async function createTaskExecution(taskId, executionData) {
  const { status, exitCode, stdout, stderr, errorMessage, durationMs } = executionData;
  
  await db.run(
    `INSERT INTO task_executions (task_id, execution_time, status, exit_code, stdout, stderr, error_message, duration_ms)
     VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)`,
    [taskId, status, exitCode, stdout, stderr, errorMessage, durationMs]
  );
}

// Task execution with proper error handling and logging
async function executeTask(task) {
  const startTime = Date.now();
  
  try {
    logger.info(`Starting execution of task ${task.id}: ${task.name}`);
    
    // Update task status to running
    await updateTaskStatus(task.id, "running");
    
    const executionEnv = task.environment_variables ? JSON.parse(task.environment_variables) : {};
    const execOptions = {
      timeout: task.timeout_ms || 30000,
      cwd: task.working_directory || process.cwd(),
      env: { ...process.env, ...executionEnv },
    };

    // Execute the command
    const { stdout, stderr } = await execAsync(task.command, execOptions);
    const durationMs = Date.now() - startTime;
    
    // Log execution result
    logger.info(`Task ${task.id} completed successfully`, {
      duration: durationMs,
      stdout: stdout.substring(0, 1000), // Log first 1000 chars
      stderr: stderr.substring(0, 1000),
    });
    
    // Record successful execution
    await createTaskExecution(task.id, {
      status: "completed",
      exitCode: 0,
      stdout: stdout,
      stderr: stderr,
      durationMs: durationMs,
    });
    
    // Update task status
    await updateTaskStatus(task.id, "completed");
    
    return { success: true, output: stdout, error: stderr };
    
  } catch (error) {
    const durationMs = Date.now() - startTime;
    const errorMessage = error.message;
    
    logger.error(`Task ${task.id} failed: ${errorMessage}`, error);
    
    // Record failed execution
    await createTaskExecution(task.id, {
      status: "failed",
      exitCode: error.code || -1,
      stdout: "",
      stderr: errorMessage,
      error_message: errorMessage,
      durationMs: durationMs,
    });
    
    // Check if we should retry
    const taskData = await getTaskById(task.id);
    const shouldRetry = taskData.retry_count < taskData.max_retries;
    
    if (shouldRetry) {
      // Schedule retry with exponential backoff
      const retryDelay = Math.min(1000 * Math.pow(2, taskData.retry_count), 300000); // Max 5 minutes
      const nextRunAt = new Date(Date.now() + retryDelay).toISOString();
      
      await db.run(
        `UPDATE tasks SET 
         retry_count = retry_count + 1,
         run_at = ?,
         status = 'scheduled',
         updated_at = CURRENT_TIMESTAMP
         WHERE id = ?`,
        [nextRunAt, task.id]
      );
      
      logger.info(`Task ${task.id} scheduled for retry #${taskData.retry_count + 1} at ${nextRunAt}`);
    } else {
      // Mark task as failed permanently
      await updateTaskStatus(task.id, "failed");
    }
    
    return { success: false, error: errorMessage };
  }
}

// Task scheduler
async function checkAndExecuteTasks() {
  try {
    const now = new Date().toISOString();
    
    // Get tasks that are scheduled to run now
    const tasksToRun = await db.all(
      "SELECT * FROM tasks WHERE run_at <= ? AND status = 'scheduled' AND enabled = 1",
      [now]
    );
    
    logger.info(`Found ${tasksToRun.length} tasks to execute`);
    
    for (const task of tasksToRun) {
      await executeTask(task);
    }
    
  } catch (error) {
    logger.error("Error checking and executing tasks", error);
  }
}

// Set up periodic task checking
let taskCheckInterval;
function startTaskScheduler() {
  // Check tasks every 30 seconds
  taskCheckInterval = setInterval(checkAndExecuteTasks, 30000);
  logger.info("Task scheduler started (checking every 30 seconds)");
  
  // Initial check
  checkAndExecuteTasks();
}

function stopTaskScheduler() {
  if (taskCheckInterval) {
    clearInterval(taskCheckInterval);
    taskCheckInterval = null;
    logger.info("Task scheduler stopped");
  }
}

// Request handlers
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "schedule_task",
        description: "Schedules a shell command to be executed at a specific time.",
        inputSchema: scheduleTaskArgsSchema,
      },
      {
        name: "list_scheduled_tasks",
        description: "Lists all currently scheduled tasks with optional filtering.",
        inputSchema: listTasksArgsSchema,
      },
      {
        name: "cancel_task",
        description: "Cancels a scheduled task by its ID.",
        inputSchema: cancelTaskArgsSchema,
      },
      {
        name: "run_task_now",
        description: "Immediately executes a scheduled task by its ID.",
        inputSchema: runTaskNowArgsSchema,
      },
      {
        name: "get_task_executions",
        description: "Gets execution history for a specific task.",
        inputSchema: z.object({
          taskId: z.number().describe("The ID of the task to get execution history for."),
        }),
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "schedule_task": {
        const parsedArgs = scheduleTaskArgsSchema.parse(args);
        const task = await createTask(parsedArgs);
        
        logger.info(`Task scheduled: ID ${task.id}, "${task.name}" at ${parsedArgs.runAt}`);
        
        return {
          content: [
            {
              type: "text",
              text: `Task "${task.name}" scheduled for ${new Date(parsedArgs.runAt).toISOString()} with ID ${task.id}.`,
            },
          ],
        };
      }

      case "list_scheduled_tasks": {
        const filter = {};
        if (args?.status) filter.status = args.status;
        if (args?.enabled !== undefined) filter.enabled = args.enabled;
        
        const tasks = await getTasks(filter);
        
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(tasks, null, 2),
            },
          ],
        };
      }

      case "cancel_task": {
        const parsedArgs = cancelTaskArgsSchema.parse(args);
        
        // Check if task exists
        const task = await getTaskById(parsedArgs.taskId);
        if (!task) {
          throw new Error(`Task with ID ${parsedArgs.taskId} not found`);
        }
        
        // Only allow cancelling scheduled or running tasks
        if (task.status === "completed" || task.status === "failed" || task.status === "cancelled") {
          throw new Error(`Cannot cancel task with status: ${task.status}`);
        }
        
        await updateTaskStatus(parsedArgs.taskId, "cancelled");
        
        return {
          content: [
            {
              type: "text",
              text: `Task ID ${parsedArgs.taskId} ("${task.name}") cancelled.`,
            },
          ],
        };
      }

      case "run_task_now": {
        const parsedArgs = runTaskNowArgsSchema.parse(args);
        
        const task = await getTaskById(parsedArgs.taskId);
        if (!task) {
          throw new Error(`Task with ID ${parsedArgs.taskId} not found`);
        }
        
        if (!task.enabled) {
          throw new Error(`Task ${parsedArgs.taskId} is disabled`);
        }
        
        const result = await executeTask(task);
        
        return {
          content: [
            {
              type: "text",
              text: `Task ${task.name} execution ${result.success ? "succeeded" : "failed"}: ${result.success ? result.output : result.error}`,
            },
          ],
        };
      }

      case "get_task_executions": {
        const parsedArgs = z.object({ taskId: z.number() }).parse(args);
        
        const executions = await db.all(
          "SELECT * FROM task_executions WHERE task_id = ? ORDER BY execution_time DESC",
          [parsedArgs.taskId]
        );
        
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(executions, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    logger.error(`Error in tool ${name}:`, error);
    
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Server lifecycle management
async function runServer() {
  try {
    // Initialize database
    await initializeDatabase();
    
    // Start task scheduler
    startTaskScheduler();
    
    // Set up transport
    const transport = new StdioServerTransport();
    await server.connect(transport);
    
    logger.info("MCP Scheduler Server running on stdio.");
    
    // Handle graceful shutdown
    process.on("SIGINT", async () => {
      logger.info("Received SIGINT, shutting down gracefully...");
      stopTaskScheduler();
      if (db) {
        await db.close();
      }
      process.exit(0);
    });
    
    process.on("SIGTERM", async () => {
      logger.info("Received SIGTERM, shutting down gracefully...");
      stopTaskScheduler();
      if (db) {
        await db.close();
      }
      process.exit(0);
    });
    
  } catch (error) {
    logger.error("Failed to start server:", error);
    process.exit(1);
  }
}

// Start server
runServer().catch((error) => {
  logger.error("Server crashed:", error);
  process.exit(1);
});
