/**
 * KiloCode Logger Utility
 * Provides consistent logging across all KiloCode integration scripts
 */

const fs = require('fs-extra');
const path = require('path');

class Logger {
    constructor(options = {}) {
        this.logLevel = options.level || process.env.KILOCODE_LOG_LEVEL || 'INFO';
        this.logToFile = options.logToFile !== false;
        this.logFilePath = options.logFilePath || path.join(process.cwd(), 'logs', 'kilocode-integration.log');
        this.enableConsole = options.enableConsole !== false;
        this.enableTimestamp = options.enableTimestamp !== false;

        // Ensure log directory exists
        if (this.logToFile) {
            const logDir = path.dirname(this.logFilePath);
            fs.ensureDirSync(logDir);
        }

        // Log levels
        this.levels = {
            ERROR: 0,
            WARN: 1,
            INFO: 2,
            DEBUG: 3
        };
    }

    /**
     * Get timestamp string
     */
    getTimestamp() {
        return new Date().toISOString();
    }

    /**
     * Format log message
     */
    formatMessage(level, message, data = null) {
        const timestamp = this.enableTimestamp ? `[${this.getTimestamp()}]` : '';
        const levelStr = `[${level}]`;
        const msg = typeof message === 'string' ? message : JSON.stringify(message);

        let formatted = `${timestamp} ${levelStr} ${msg}`;

        if (data) {
            formatted += ` ${JSON.stringify(data)}`;
        }

        return formatted;
    }

    /**
     * Check if level should be logged
     */
    shouldLog(level) {
        return this.levels[level] <= this.levels[this.logLevel];
    }

    /**
     * Write log to file
     */
    async writeToFile(formattedMessage) {
        if (this.logToFile) {
            try {
                await fs.appendFile(this.logFilePath, formattedMessage + '\n');
            } catch (error) {
                // If file logging fails, continue with console logging
                console.error('Failed to write to log file:', error.message);
            }
        }
    }

    /**
     * Write log to console
     */
    writeToConsole(formattedMessage) {
        if (this.enableConsole) {
            const level = formattedMessage.match(/\[(ERROR|WARN|INFO|DEBUG)\]/)?.[1] || 'INFO';

            switch (level) {
                case 'ERROR':
                    console.error(formattedMessage);
                    break;
                case 'WARN':
                    console.warn(formattedMessage);
                    break;
                case 'INFO':
                    console.log(formattedMessage);
                    break;
                case 'DEBUG':
                    console.debug(formattedMessage);
                    break;
                default:
                    console.log(formattedMessage);
            }
        }
    }

    /**
     * Log error message
     */
    async error(message, data = null) {
        if (!this.shouldLog('ERROR')) return;

        const formattedMessage = this.formatMessage('ERROR', message, data);
        await this.writeToFile(formattedMessage);
        this.writeToConsole(formattedMessage);
    }

    /**
     * Log warning message
     */
    async warn(message, data = null) {
        if (!this.shouldLog('WARN')) return;

        const formattedMessage = this.formatMessage('WARN', message, data);
        await this.writeToFile(formattedMessage);
        this.writeToConsole(formattedMessage);
    }

    /**
     * Log info message
     */
    async info(message, data = null) {
        if (!this.shouldLog('INFO')) return;

        const formattedMessage = this.formatMessage('INFO', message, data);
        await this.writeToFile(formattedMessage);
        this.writeToConsole(formattedMessage);
    }

    /**
     * Log debug message
     */
    async debug(message, data = null) {
        if (!this.shouldLog('DEBUG')) return;

        const formattedMessage = this.formatMessage('DEBUG', message, data);
        await this.writeToFile(formattedMessage);
        this.writeToConsole(formattedMessage);
    }

    /**
     * Log success message
     */
    async success(message, data = null) {
        if (!this.shouldLog('INFO')) return;

        const formattedMessage = this.formatMessage('SUCCESS', message, data);
        await this.writeToFile(formattedMessage);
        this.writeToConsole(formattedMessage);
    }

    /**
     * Log with custom level
     */
    async log(level, message, data = null) {
        if (!this.shouldLog(level)) return;

        const formattedMessage = this.formatMessage(level, message, data);
        await this.writeToFile(formattedMessage);
        this.writeToConsole(formattedMessage);
    }

    /**
     * Set log level
     */
    setLevel(level) {
        if (this.levels[level] !== undefined) {
            this.logLevel = level;
        }
    }

    /**
     * Get current log level
     */
    getLevel() {
        return this.logLevel;
    }

    /**
     * Create a child logger with additional context
     */
    child(context) {
        return new ChildLogger(this, context);
    }
}

/**
 * Child Logger class that adds context to all log messages
 */
class ChildLogger {
    constructor(parent, context) {
        this.parent = parent;
        this.context = context;
    }

    async error(message, data = null) {
        await this.parent.error(message, { ...this.context, ...data });
    }

    async warn(message, data = null) {
        await this.parent.warn(message, { ...this.context, ...data });
    }

    async info(message, data = null) {
        await this.parent.info(message, { ...this.context, ...data });
    }

    async debug(message, data = null) {
        await this.parent.debug(message, { ...this.context, ...data });
    }

    async success(message, data = null) {
        await this.parent.success(message, { ...this.context, ...data });
    }

    async log(level, message, data = null) {
        await this.parent.log(level, message, { ...this.context, ...data });
    }

    setLevel(level) {
        this.parent.setLevel(level);
    }

    getLevel() {
        return this.parent.getLevel();
    }

    child(context) {
        return new ChildLogger(this.parent, { ...this.context, ...context });
    }
}

// Create a default logger instance
const defaultLogger = new Logger();

// Export the Logger class and default instance
module.exports = { Logger, defaultLogger };