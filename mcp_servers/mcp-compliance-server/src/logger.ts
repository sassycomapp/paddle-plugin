/**
 * MCP Configuration and Compliance Server - Logger
 * 
 * A simple logger implementation for the compliance server.
 */

export interface Logger {
    debug(message: string, meta?: any): void;
    info(message: string, meta?: any): void;
    warn(message: string, meta?: any): void;
    error(message: string, error?: Error, meta?: any): void;
    child(context: Record<string, any>): Logger;
}

export class DefaultLogger implements Logger {
    private context: Record<string, any> = {};
    private level: 'debug' | 'info' | 'warn' | 'error' = 'info';

    constructor(initialContext: Record<string, any> = {}) {
        this.context = { ...initialContext };
    }

    setLevel(level: 'debug' | 'info' | 'warn' | 'error'): void {
        this.level = level;
    }

    private shouldLog(level: 'debug' | 'info' | 'warn' | 'error'): boolean {
        const levels = ['debug', 'info', 'warn', 'error'];
        return levels.indexOf(level) >= levels.indexOf(this.level);
    }

    private formatMessage(level: string, message: string, meta?: any): string {
        const timestamp = new Date().toISOString();
        const contextStr = Object.keys(this.context).length > 0
            ? ` [${JSON.stringify(this.context)}]`
            : '';
        const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';
        return `[${timestamp}] ${level.toUpperCase()}${contextStr}: ${message}${metaStr}`;
    }

    debug(message: string, meta?: any): void {
        if (this.shouldLog('debug')) {
            console.log(this.formatMessage('debug', message, meta));
        }
    }

    info(message: string, meta?: any): void {
        if (this.shouldLog('info')) {
            console.log(this.formatMessage('info', message, meta));
        }
    }

    warn(message: string, meta?: any): void {
        if (this.shouldLog('warn')) {
            console.warn(this.formatMessage('warn', message, meta));
        }
    }

    error(message: string, error?: Error, meta?: any): void {
        if (this.shouldLog('error')) {
            const errorStr = error ? `: ${error.message}` : '';
            const fullMessage = this.formatMessage('error', message + errorStr, meta);
            console.error(fullMessage);

            if (error && error.stack) {
                console.error(error.stack);
            }
        }
    }

    child(context: Record<string, any>): Logger {
        return new DefaultLogger({ ...this.context, ...context });
    }
}

// Create a default logger instance
export const logger = new DefaultLogger();