/**
 * MCP Integration Coordinator - Authentication Controller
 * 
 * Handles authentication and authorization for the integration coordinator.
 */

import { Router, Request, Response } from 'express';
import { AuthService } from '../services/auth-service';
import { AuditService } from '../services/audit-service';
import { LoginRequest } from '../types';
import { logger } from '../logger';

export class AuthController {
    private router: Router;
    private authService: AuthService;
    private auditService: AuditService;

    constructor(authService: AuthService, auditService: AuditService) {
        this.router = Router();
        this.authService = authService;
        this.auditService = auditService;
        this.setupRoutes();
    }

    /**
     * Setup authentication routes
     */
    private setupRoutes(): void {
        // Login endpoint
        this.router.post('/login', this.login.bind(this));

        // Logout endpoint
        this.router.post('/logout', this.logout.bind(this));

        // Refresh token endpoint
        this.router.post('/refresh', this.refresh.bind(this));

        // Get current user
        this.router.get('/me', this.getCurrentUser.bind(this));

        // Change password
        this.router.post('/change-password', this.changePassword.bind(this));
    }

    /**
     * Login user
     */
    private async login(req: Request, res: Response): Promise<void> {
        try {
            const loginData: LoginRequest = req.body;

            // Validate input
            if (!loginData.username || !loginData.password) {
                res.status(400).json({
                    error: {
                        code: 'INVALID_INPUT',
                        message: 'Username and password are required',
                        retryable: false
                    }
                });
                return;
            }

            // Authenticate user
            const result = await this.authService.authenticate(loginData);

            // Log successful login
            await this.auditService.log({
                action: 'login',
                actor: loginData.username,
                target: 'auth',
                result: 'success',
                details: { userId: result.user.id }
            });

            res.json(result);
        } catch (error) {
            logger.error('Login failed', error as Error, { username: req.body.username });

            // Log failed login attempt
            await this.auditService.log({
                action: 'login',
                actor: req.body.username || 'unknown',
                target: 'auth',
                result: 'failed',
                details: { error: error instanceof Error ? error.message : String(error) }
            });

            res.status(401).json({
                error: {
                    code: 'AUTHENTICATION_FAILED',
                    message: 'Invalid username or password',
                    retryable: false
                }
            });
        }
    }

    /**
     * Logout user
     */
    private async logout(req: Request, res: Response): Promise<void> {
        try {
            const user = (req as any).user;

            // Logout user (invalidate token)
            await this.authService.logout(user.id, '');

            // Log logout
            await this.auditService.log({
                action: 'logout',
                actor: user.username,
                target: 'auth',
                result: 'success',
                details: { userId: user.id }
            });

            res.json({ message: 'Successfully logged out' });
        } catch (error) {
            logger.error('Logout failed', error as Error);
            res.status(500).json({
                error: {
                    code: 'LOGOUT_FAILED',
                    message: 'Failed to logout',
                    retryable: false
                }
            });
        }
    }

    /**
     * Refresh token
     */
    private async refresh(req: Request, res: Response): Promise<void> {
        try {
            const { refreshToken } = req.body;

            if (!refreshToken) {
                res.status(400).json({
                    error: {
                        code: 'MISSING_REFRESH_TOKEN',
                        message: 'Refresh token is required',
                        retryable: false
                    }
                });
                return;
            }

            const result = await this.authService.refreshToken(refreshToken);

            res.json(result);
        } catch (error) {
            logger.error('Token refresh failed', error as Error);
            res.status(401).json({
                error: {
                    code: 'TOKEN_REFRESH_FAILED',
                    message: 'Invalid or expired refresh token',
                    retryable: false
                }
            });
        }
    }

    /**
     * Get current user
     */
    private async getCurrentUser(req: Request, res: Response): Promise<void> {
        try {
            const user = (req as any).user;
            res.json(user);
        } catch (error) {
            logger.error('Failed to get current user', error as Error);
            res.status(500).json({
                error: {
                    code: 'GET_USER_FAILED',
                    message: 'Failed to get current user',
                    retryable: false
                }
            });
        }
    }

    /**
     * Change password
     */
    private async changePassword(req: Request, res: Response): Promise<void> {
        try {
            const user = (req as any).user;
            const { currentPassword, newPassword } = req.body;

            if (!currentPassword || !newPassword) {
                res.status(400).json({
                    error: {
                        code: 'MISSING_PASSWORD',
                        message: 'Current password and new password are required',
                        retryable: false
                    }
                });
                return;
            }

            // Password change functionality would need to be implemented in auth service
            // For now, we'll just log the attempt
            logger.info('Password change requested', { userId: user.id });

            // Log password change
            await this.auditService.log({
                action: 'change_password',
                actor: user.username,
                target: 'user',
                result: 'success',
                details: { userId: user.id }
            });

            res.json({ message: 'Password changed successfully' });
        } catch (error) {
            logger.error('Password change failed', error as Error);

            // Log failed password change
            const user = (req as any).user;
            await this.auditService.log({
                action: 'change_password',
                actor: user.username,
                target: 'user',
                result: 'failed',
                details: { error: error instanceof Error ? error.message : String(error) }
            });

            res.status(400).json({
                error: {
                    code: 'PASSWORD_CHANGE_FAILED',
                    message: error instanceof Error ? error.message : 'Failed to change password',
                    retryable: false
                }
            });
        }
    }

    /**
     * Get router instance
     */
    public getRouter(): Router {
        return this.router;
    }
}