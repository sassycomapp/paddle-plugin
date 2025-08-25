/**
 * MCP Integration Coordinator - Authentication Middleware
 * 
 * Handles JWT token verification and user authentication.
 */

import { AuthService } from '../services/auth-service';
import { logger } from '../logger';
import { Request, Response } from 'express';

export interface AuthenticatedRequest extends Request {
    user?: {
        id: string;
        username: string;
        email: string;
        role: string;
        permissions: string[];
    };
}

export class AuthMiddleware {
    private authService: AuthService;

    constructor(authService: AuthService) {
        this.authService = authService;
    }

    /**
     * Verify JWT token and authenticate user
     */
    authenticate = async (req: AuthenticatedRequest, res: Response, next: Function): Promise<void> => {
        try {
            const authHeader = (req as any).headers?.authorization;

            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                res.status(401).json({
                    error: {
                        code: 'MISSING_TOKEN',
                        message: 'Authorization token is required',
                        retryable: false
                    }
                });
                return;
            }

            const token = authHeader.substring(7); // Remove 'Bearer ' prefix

            try {
                const decoded = this.authService.verifyToken(token);

                // Add user to request object
                req.user = {
                    id: decoded.userId,
                    username: 'user', // In a real implementation, you'd fetch this from the database
                    email: 'user@example.com',
                    role: decoded.role,
                    permissions: decoded.permissions
                };

                next();
            } catch (error) {
                res.status(401).json({
                    error: {
                        code: 'INVALID_TOKEN',
                        message: 'Invalid or expired token',
                        retryable: false
                    }
                });
                return;
            }
        } catch (error) {
            logger.error('Authentication middleware error', error as Error);
            res.status(500).json({
                error: {
                    code: 'AUTH_ERROR',
                    message: 'Authentication failed',
                    retryable: false
                }
            });
        }
    };

    /**
     * Check if user has specific permission
     */
    requirePermission = (permission: string) => {
        return (req: AuthenticatedRequest, response: Response, next: Function): void => {
            if (!req.user) {
                response.status(401).json({
                    error: {
                        code: 'NOT_AUTHENTICATED',
                        message: 'User not authenticated',
                        retryable: false
                    }
                });
                return;
            }

            if (!req.user.permissions.includes(permission) && req.user.role !== 'admin') {
                response.status(403).json({
                    error: {
                        code: 'INSUFFICIENT_PERMISSIONS',
                        message: `Required permission: ${permission}`,
                        retryable: false
                    }
                });
                return;
            }

            next();
        };
    };

    /**
     * Check if user has specific role
     */
    requireRole = (role: string) => {
        return (req: AuthenticatedRequest, response: Response, next: Function): void => {
            if (!req.user) {
                response.status(401).json({
                    error: {
                        code: 'NOT_AUTHENTICATED',
                        message: 'User not authenticated',
                        retryable: false
                    }
                });
                return;
            }

            if (req.user.role !== role && req.user.role !== 'admin') {
                response.status(403).json({
                    error: {
                        code: 'INSUFFICIENT_ROLE',
                        message: `Required role: ${role}`,
                        retryable: false
                    }
                });
                return;
            }

            next();
        };
    };

    /**
     * Optional authentication - doesn't fail if no token provided
     */
    optionalAuth = async (req: AuthenticatedRequest, _response: Response, next: Function): Promise<void> => {
        try {
            const authHeader = (req as any).headers?.authorization;

            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                next();
                return;
            }

            const token = authHeader.substring(7);

            try {
                const decoded = this.authService.verifyToken(token);

                // Add user to request object
                req.user = {
                    id: decoded.userId,
                    username: 'user',
                    email: 'user@example.com',
                    role: decoded.role,
                    permissions: decoded.permissions
                };
            } catch (error) {
                // Token is invalid, but we continue without authentication
                logger.warn('Invalid token in optional auth', { error: (error as Error).message });
            }

            next();
        } catch (error) {
            logger.error('Optional authentication middleware error', error as Error);
            next();
        }
    };
}