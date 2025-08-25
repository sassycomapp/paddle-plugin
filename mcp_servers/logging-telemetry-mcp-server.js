#!/usr/bin/env node

import express from "express";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { promises as fs } from "fs";
import { z } from "zod";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const LOG_FILE_PATH = join(__dirname, "logs", "telemetry.log");
const METRICS_FILE_PATH = join(__dirname, "metrics", "metrics.json");

// Ensure log and metrics directories exist
const ensureDirectories = async () => {
  await fs.mkdir(join(__dirname, "logs"), { recursive: true });
  await fs.mkdir(join(__dirname, "metrics"), { recursive: true });
};

// Telemetry event schema
const TelemetryEventSchema = z.object({
  timestamp: z.string().default(() => new Date().toISOString()),
  type: z.enum(["tool_call", "error", "info", "performance"]),
  source: z.string(),
  details: z.record(z.any()),
});

let metrics = {
  totalCalls: 0,
  errors: 0,
  toolUsage: {},
};

// Load existing metrics
const loadMetrics = async () => {
  try {
    const data = await fs.readFile(METRICS_FILE_PATH, "utf-8");
    metrics = JSON.parse(data);
  } catch (error) {
    // File doesn't exist or is empty, start with default metrics
    metrics = {
      totalCalls: 0,
      errors: 0,
      toolUsage: {},
    };
  }
};

// Save metrics
const saveMetrics = async () => {
  await fs.writeFile(METRICS_FILE_PATH, JSON.stringify(metrics, null, 2));
};

// Log telemetry event
const logEvent = async (event) => {
  const validatedEvent = TelemetryEventSchema.parse(event);
  const logEntry = JSON.stringify(validatedEvent) + "\n";

  try {
    await fs.appendFile(LOG_FILE_PATH, logEntry);
    console.log(`Logged event: ${validatedEvent.type} from ${validatedEvent.source}`);
  } catch (error) {
    console.error("Failed to log event:", error);
  }
};

// Update metrics
const updateMetrics = (event) => {
  metrics.totalCalls++;
  if (event.type === "error") {
    metrics.errors++;
  }
  if (event.type === "tool_call" && event.details.tool_name) {
    metrics.toolUsage[event.details.tool_name] = (metrics.toolUsage[event.details.tool_name] || 0) + 1;
  }
  saveMetrics();
};

// Get logs
const getLogs = async (type, limit = 100) => {
  try {
    const data = await fs.readFile(LOG_FILE_PATH, "utf-8");
    const logs = data
      .split("\n")
      .filter(line => line.trim())
      .map(line => JSON.parse(line))
      .filter(log => !type || log.type === type)
      .slice(-limit);
    return logs;
  } catch (error) {
    console.error("Failed to read logs:", error);
    return [];
  }
};

// Get metrics
const getMetrics = () => {
  return metrics;
};

// Create Express app
const app = express();
app.use(express.json());

// Telemetry endpoint
app.post("/telemetry", async (req, res) => {
  try {
    const event = req.body;
    await logEvent(event);
    updateMetrics(event);
    res.status(200).send({ success: true });
  } catch (error) {
    console.error("Error processing telemetry event:", error);
    res.status(400).send({ error: "Invalid event data" });
  }
});

// Logs endpoint
app.get("/logs", async (req, res) => {
  const type = req.query.type;
  const limit = parseInt(req.query.limit) || 100;
  const logs = await getLogs(type, limit);
  res.status(200).json(logs);
});

// Metrics endpoint
app.get("/metrics", (req, res) => {
  res.status(200).json(getMetrics());
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok", timestamp: new Date().toISOString() });
});

// Start server
const startServer = async () => {
  await ensureDirectories();
  await loadMetrics();

  const PORT = process.env.PORT || 3001;
  app.listen(PORT, () => {
    console.log(`MCP Logging and Telemetry Server running on port ${PORT}`);
    console.log(`Log file: ${LOG_FILE_PATH}`);
    console.log(`Metrics file: ${METRICS_FILE_PATH}`);
  });
};

startServer().catch(console.error);
