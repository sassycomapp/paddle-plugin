/**
 * MCP Integration Coordinator - Authentication Service
 * 
 * Handles user authentication and authorization.
 */

import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { DatabaseService } from './database-service';
import { Logger } from '../logger';
import { User, AuthToken, LoginRequest, LoginResponse, Role, Permission } from '../types';

export class AuthService {
    private logger: Logger;
    private databaseService: DatabaseService;
    private jwtSecret: string;
    private jwtExpiration: string;
    private bcryptRounds: number;

    constructor(databaseService: DatabaseService, logger: Logger, config: {
        jwtSecret: string;
        jwtExpiration: string;
        bcryptRounds: number;
    }) {
        this.databaseService = databaseService;
        this.logger = logger;
        this.jwtSecret = config.jwtSecret;
        this.jwtExpiration = config.jwtExpiration;
        this.bcryptRounds = config.bcryptRounds;
    }

    /**
     * Hash a password
     */
    private async hashPassword(password: string): Promise<string> {
        try {
            return await bcrypt.hash(password, this.bcryptRounds);
        } catch (error) {
            this.logger.error('Failed to hash password', error as Error);
            throw new Error('Password hashing failed');
        }
    }

    /**
     * Verify a password
     */
    private async verifyPassword(password: string, hashedPassword: string): Promise<boolean> {
        try {
            return await bcrypt.compare(password, hashedPassword);
        } catch (error) {
            this.logger.error('Failed to verify password', error as Error);
            throw new Error('Password verification failed');
        }
    }

    /**
     * Generate JWT token
     */
    private generateToken(userId: string, role: Role, permissions: Permission[]): AuthToken {
        const accessToken = jwt.sign(
            { userId, role, permissions },
            this.jwtSecret,
            { expiresIn: this.jwtExpiration }
        );

        const refreshToken = jwt.sign(
            { userId, type: 'refresh' },
            this.jwtSecret,
            { expiresIn: '7d' }
        );

        const expiresAt = new Date();
        expiresAt.setSeconds(expiresAt.getSeconds() + parseInt(this.jwtExpiration));

        return {
            accessToken,
            refreshToken,
            expiresAt: expiresAt.toISOString(),
            role,
            permissions
        };
    }

    /**
     * Verify JWT token
     */
    verifyToken(token: string): { userId: string; role: Role; permissions: Permission[] } {
        try {
            const decoded = jwt.verify(token, this.jwtSecret) as any;
            return {
                userId: decoded.userId,
                role: decoded.role,
                permissions: decoded.permissions || []
            };
        } catch (error) {
            this.logger.error('Token verification failed', error as Error);
            throw new Error('Invalid token');
        }
    }

    /**
     * Refresh access token
     */
    async refreshToken(refreshToken: string): Promise<AuthToken> {
        try {
            const decoded = jwt.verify(refreshToken, this.jwtSecret) as any;

            if (decoded.type !== 'refresh') {
                throw new Error('Invalid refresh token');
            }

            // Get user from database
            const user = await this.getUserById(decoded.userId);
            if (!user || !user.active) {
                throw new Error('User not found or inactive');
            }

            return this.generateToken(user.id, user.role, user.permissions);
        } catch (error) {
            this.logger.error('Token refresh failed', error as Error);
            throw new Error('Token refresh failed');
        }
    }

    /**
     * Create a new user
     */
    async createUser(userData: {
        username: string;
        email: string;
        password: string;
        role: Role;
        permissions: Permission[];
    }): Promise<User> {
        try {
            // Check if user already exists
            const existingUser = await this.getUserByUsername(userData.username);
            if (existingUser) {
                throw new Error('Username already exists');
            }

            // Hash password
            const hashedPassword = await this.hashPassword(userData.password);

            // Insert user into database
            const result = await this.databaseService.query(
                `INSERT INTO users 
                (username, email, password, role, permissions, active, last_login) 
                VALUES ($1, $2, $3, $4, $5, $6, $7) 
                RETURNING id, username, email, role, permissions, active, last_login`,
                [
                    userData.username,
                    userData.email,
                    hashedPassword,
                    userData.role,
                    JSON.stringify(userData.permissions),
                    true,
                    new Date().toISOString()
                ]
            );

            const user = result.rows[0];
            return {
                id: user.id,
                username: user.username,
                email: user.email,
                role: user.role,
                permissions: JSON.parse(user.permissions || '[]'),
                active: user.active,
                lastLogin: user.last_login
            };
        } catch (error) {
            this.logger.error('Failed to create user', error as Error);
            throw error;
        }
    }

    /**
     * Authenticate user
     */
    async authenticate(loginRequest: LoginRequest): Promise<LoginResponse> {
        try {
            // Get user by username
            const user = await this.getUserByUsername(loginRequest.username);
            if (!user || !user.active) {
                throw new Error('Invalid credentials');
            }

            // Verify password
            const isValidPassword = await this.verifyPassword(loginRequest.password, user.password!);
            if (!isValidPassword) {
                throw new Error('Invalid credentials');
            }

            // Update last login
            await this.updateLastLogin(user.id);

            // Generate token
            const token = this.generateToken(user.id, user.role, user.permissions);

            // Log successful login
            this.logger.info('User authenticated successfully', { username: user.username });

            return {
                token,
                user: {
                    id: user.id,
                    username: user.username,
                    email: user.email,
                    role: user.role,
                    permissions: user.permissions,
                    active: user.active,
                    lastLogin: user.lastLogin
                }
            };
        } catch (error) {
            this.logger.error('Authentication failed', error as Error, { username: loginRequest.username });
            throw error;
        }
    }

    /**
     * Get user by ID
     */
    async getUserById(userId: string): Promise<User | null> {
        try {
            const result = await this.databaseService.query(
                'SELECT id, username, email, role, permissions, active, last_login FROM users WHERE id = $1',
                [userId]
            );

            if (result.rows.length === 0) {
                return null;
            }

            const user = result.rows[0];
            return {
                id: user.id,
                username: user.username,
                email: user.email,
                role: user.role,
                permissions: JSON.parse(user.permissions || '[]'),
                active: user.active,
                lastLogin: user.last_login
            };
        } catch (error) {
            this.logger.error('Failed to get user by ID', error as Error);
            throw error;
        }
    }

    /**
     * Get user by username
     */
    async getUserByUsername(username: string): Promise<User | null> {
        try {
            const result = await this.databaseService.query(
                'SELECT id, username, email, password, role, permissions, active, last_login FROM users WHERE username = $1',
                [username]
            );

            if (result.rows.length === 0) {
                return null;
            }

            const user = result.rows[0];
            return {
                id: user.id,
                username: user.username,
                email: user.email,
                password: user.password, // Include password for verification
                role: user.role,
                permissions: JSON.parse(user.permissions || '[]'),
                active: user.active,
                lastLogin: user.last_login
            };
        } catch (error) {
            this.logger.error('Failed to get user by username', error as Error);
            throw error;
        }
    }

    /**
     * Update last login
     */
    async updateLastLogin(userId: string): Promise<void> {
        try {
            await this.databaseService.query(
                'UPDATE users SET last_login = $1 WHERE id = $2',
                [new Date().toISOString(), userId]
            );
        } catch (error) {
            this.logger.error('Failed to update last login', error as Error);
            throw error;
        }
    }

    /**
     * Check if user has permission
     */
    hasPermission(user: User, permission: Permission): boolean {
        return user.permissions.includes(permission) || user.role === Role.ADMIN;
    }

    /**
     * Check if user has role
     */
    hasRole(user: User, role: Role): boolean {
        return user.role === role || user.role === Role.ADMIN;
    }

    /**
     * Logout user (invalidate refresh token)
     */
    async logout(userId: string, _refreshToken: string): Promise<void> {
        try {
            // Add refresh token to blacklist (in a real implementation, you'd store this in Redis)
            this.logger.info('User logged out', { userId });
        } catch (error) {
            this.logger.error('Logout failed', error as Error);
            throw error;
        }
    }
}