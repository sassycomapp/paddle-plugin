import chalk from 'chalk';

export class Logger {
    private getTimestamp(): string {
        return new Date().toISOString();
    }

    private formatMessage(level: string, message: string): string {
        const timestamp = this.getTimestamp();
        return `[${timestamp}] ${level}: ${message}`;
    }

    info(message: string): void {
        console.log(this.formatMessage('INFO', chalk.blue(message)));
    }

    success(message: string): void {
        console.log(this.formatMessage('SUCCESS', chalk.green(message)));
    }

    warn(message: string): void {
        console.log(this.formatMessage('WARN', chalk.yellow(message)));
    }

    error(message: string): void {
        console.log(this.formatMessage('ERROR', chalk.red(message)));
    }

    debug(message: string): void {
        if (process.env.DEBUG) {
            console.log(this.formatMessage('DEBUG', chalk.gray(message)));
        }
    }
}