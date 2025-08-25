/**
 * MCP Integration Coordinator - Logger (JavaScript Version)
 * 
 * Handles logging for the integration coordinator.
 */

const winston = require('winston');

class Logger {
    constructor(options = {}) {
        this.name = options.name || 'IntegrationCoordinator';
        this.level = options.level || 'info';
        this.enableConsole = options.enableConsole !== false;

        // Create logger instance
        this.logger = winston.createLogger({
            level: this.level,
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.errors({ stack: true }),
                winston.format.json()
            ),
            defaultMeta: { service: this.name },
            transports: []
        });

        // Add console transport if enabled
        if (this.enableConsole) {
            this.logger.add(new winston.transports.Console({
                format: winston.format.combine(
                    winston.format.colorize(),
                    winston.format.simple()
                )
            }));
        }
    }

    /**
     * Log an error message
     */
    error(message, error = null, meta = {}) {
        const logData = { message, ...meta };
        if (error) {
            logData.error = error.message || error;
            logData.stack = error.stack;
        }
        this.logger.error(logData);
    }

    /**
     * Log a warning message
     */
    warn(message, meta = {}) {
        this.logger.warn({ message, ...meta });
    }

    /**
     * Log an info message
     */
    info(message, meta = {}) {
        this.logger.info({ message, ...meta });
    }

    /**
     * Log a debug message
     */
    debug(message, meta = {}) {
        this.logger.debug({ message, ...meta });
    }

    /**
     * Log a verbose message
     */
    verbose(message, meta = {}) {
        this.logger.verbose({ message, ...meta });
    }
}

module.exports = { Logger };