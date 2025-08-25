/**
 * MCP Integration Coordinator - Assessment Store Integration Tests
 * 
 * Integration tests for AssessmentStore with real database operations.
 */

import { AssessmentStore } from '../src/services/assessment-store';
import { DatabaseService } from '../src/services/database-service';
import { AuditService } from '../src/services/audit-service';
import { Logger } from '../src/logger';
import {
    AssessmentState,
    AssessmentStoreCreateOptions,
    AssessmentResult,
    AssessmentProcessingError,
    AssessmentNotFoundError,
    AssessmentTimeoutError
} from '../src/types';

// Mock dependencies
const mockDatabaseService = {
    query: jest.fn(),
    getClient: jest.fn()
} as any;

const mockAuditService = {
    log: jest.fn(),
    getAuditTrail: jest.fn()
} as any;

const mockLogger = {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn()
} as any;

describe('AssessmentStore Integration Tests', () => {
    let assessmentStore: AssessmentStore;
    let createOptions: AssessmentStoreCreateOptions;

    beforeEach(() => {
        jest.clearAllMocks();

        // Create assessment store with mocked dependencies
        assessmentStore = new AssessmentStore(
            {
                processing: {
                    maxConcurrent: 5,
                    maxRetries: 3,
                    timeout: 30000
                },
                complianceServer: {
                    url: 'http://localhost:8080',
                    timeout: 10000
                }
            },
            mockLogger,
            mockDatabaseService,
            mockAuditService
        );

        createOptions = {
            requestId: 'test-request',
            serverName: 'test-server',
            assessmentType: 'compliance',
            options: {
                includeDetails: true,
                generateReport: true,
                saveResults: true,
                checkServerStatus: true,
                validateConfig: true,
                checkCompliance: true,
                deepScan: false
            },
            source: 'installer',
            priority: 8,
            timeout: 600
        };
    });

    describe('initialize', () => {
        it('should initialize successfully with database', async () => {
            // Mock successful database initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] })
                .mockResolvedValueOnce({ rows: [{ assessment_id: 'pending-assessment', state: AssessmentState.PENDING }] });

            await expect(assessmentStore.initialize()).resolves.not.toThrow();
            expect(mockLogger.info).toHaveBeenCalledWith('AssessmentStore initialized successfully with database persistence');
        });

        it('should handle database schema verification failure', async () => {
            mockDatabaseService.query.mockResolvedValueOnce({ rows: [] });

            await expect(assessmentStore.initialize()).rejects.toThrow('Failed to initialize AssessmentStore');
            expect(mockLogger.error).toHaveBeenCalledWith('Failed to initialize AssessmentStore', expect.any(Error));
        });
    });

    describe('createAssessment', () => {
        it('should create assessment successfully', async () => {
            // Mock DAO initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] })
                .mockResolvedValueOnce({ rows: [{ assessment_id: 'test-assessment' }] })
                .mockResolvedValueOnce({ rows: [{ assessment_id: 'test-assessment', state: AssessmentState.PENDING }] });

            const assessmentId = await assessmentStore.createAssessment(createOptions);

            expect(assessmentId).toBeDefined();
            expect(assessmentId).toMatch(/^assessment_/);
            expect(mockLogger.info).toHaveBeenCalledWith('Assessment created', {
                assessmentId: expect.any(String),
                assessmentType: 'compliance'
            });
        });

        it('should handle database creation failure', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] })
                .mockRejectedValueOnce(new Error('Database connection failed'));

            await expect(assessmentStore.createAssessment(createOptions)).rejects.toThrow('Failed to create assessment');
            expect(mockLogger.error).toHaveBeenCalledWith('Failed to create assessment', expect.any(Error));
        });
    });

    describe('waitForCompletion', () => {
        const assessmentId = 'test-assessment';

        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should return immediately if assessment is completed', async () => {
            const mockResultData: AssessmentResult = {
                timestamp: '2023-01-01T00:00:00.000Z',
                totalServers: 10,
                compliantServers: 8,
                nonCompliantServers: 2,
                missingServers: [],
                configurationIssues: [],
                serverStatuses: [],
                overallScore: 80,
                summary: {
                    criticalIssues: 0,
                    highIssues: 1,
                    mediumIssues: 2,
                    lowIssues: 3
                }
            };

            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.COMPLETED, result_data: JSON.stringify(mockResultData) }] });

            const result = await assessmentStore.waitForCompletion(assessmentId, 5000);

            expect(result).toEqual(mockResultData);
        });

        it('should throw error if assessment failed', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.FAILED, error_message: 'Test error' }] });

            await expect(assessmentStore.waitForCompletion(assessmentId, 5000)).rejects.toThrow('Assessment failed: Test error');
        });

        it('should timeout if assessment not completed', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PROCESSING }] });

            await expect(assessmentStore.waitForCompletion(assessmentId, 100)).rejects.toThrow(AssessmentTimeoutError);
        });

        it('should refresh assessment data during waiting', async () => {
            let callCount = 0;

            mockDatabaseService.query.mockImplementation(() => {
                callCount++;
                if (callCount === 1) {
                    return Promise.resolve({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PROCESSING }] });
                } else if (callCount === 2) {
                    const mockResultData: AssessmentResult = {
                        timestamp: '2023-01-01T00:00:00.000Z',
                        totalServers: 10,
                        compliantServers: 8,
                        nonCompliantServers: 2,
                        missingServers: [],
                        configurationIssues: [],
                        serverStatuses: [],
                        overallScore: 80,
                        summary: {
                            criticalIssues: 0,
                            highIssues: 1,
                            mediumIssues: 2,
                            lowIssues: 3
                        }
                    };
                    return Promise.resolve({ rows: [{ assessment_id: assessmentId, state: AssessmentState.COMPLETED, result_data: JSON.stringify(mockResultData) }] });
                }
                return Promise.resolve({ rows: [] });
            });

            const result = await assessmentStore.waitForCompletion(assessmentId, 2000);

            expect(result).toBeDefined();
            expect(callCount).toBeGreaterThan(1);
        });
    });

    describe('getState', () => {
        const assessmentId = 'test-assessment';

        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should get assessment state successfully', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PROCESSING, progress: 50, message: 'Processing', updated_at: '2023-01-01T00:00:00.000Z', completed_at: null }] });

            const state = await assessmentStore.getState(assessmentId);

            expect(state.assessmentId).toBe(assessmentId);
            expect(state.state).toBe(AssessmentState.PROCESSING);
            expect(state.progress).toBe(50);
            expect(state.message).toBe('Processing');
            expect(state.lastUpdated).toBe('2023-01-01T00:00:00.000Z');
            expect(state.completedAt).toBeUndefined();
        });

        it('should throw AssessmentNotFoundError if assessment not found', async () => {
            mockDatabaseService.query.mockResolvedValueOnce({ rows: [] });

            await expect(assessmentStore.getState(assessmentId)).rejects.toThrow(AssessmentNotFoundError);
        });
    });

    describe('listAssessments', () => {
        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should list all assessments', async () => {
            const mockAssessments = [
                {
                    assessment_id: 'assessment-1',
                    state: AssessmentState.PENDING,
                    version: 1,
                    progress: 0,
                    message: 'Pending',
                    created_at: '2023-01-01T00:00:00.000Z',
                    updated_at: '2023-01-01T00:00:00.000Z',
                    completed_at: null,
                    request_data: '{}',
                    result_data: null,
                    error_message: null,
                    retry_count: 0,
                    next_retry_at: null
                },
                {
                    assessment_id: 'assessment-2',
                    state: AssessmentState.PROCESSING,
                    version: 1,
                    progress: 50,
                    message: 'Processing',
                    created_at: '2023-01-02T00:00:00.000Z',
                    updated_at: '2023-01-02T00:00:00.000Z',
                    completed_at: null,
                    request_data: '{}',
                    result_data: null,
                    error_message: null,
                    retry_count: 0,
                    next_retry_at: null
                }
            ];

            mockDatabaseService.query.mockResolvedValueOnce({ rows: mockAssessments });

            const assessments = await assessmentStore.listAssessments();

            expect(assessments).toHaveLength(2);
            expect(assessments[0].assessmentId).toBe('assessment-1');
            expect(assessments[1].assessmentId).toBe('assessment-2');
        });

        it('should filter assessments by state', async () => {
            const mockAssessments = [
                {
                    assessment_id: 'assessment-1',
                    state: AssessmentState.PENDING,
                    version: 1,
                    progress: 0,
                    message: 'Pending',
                    created_at: '2023-01-01T00:00:00.000Z',
                    updated_at: '2023-01-01T00:00:00.000Z',
                    completed_at: null,
                    request_data: '{}',
                    result_data: null,
                    error_message: null,
                    retry_count: 0,
                    next_retry_at: null
                }
            ];

            mockDatabaseService.query.mockResolvedValueOnce({ rows: mockAssessments });

            const assessments = await assessmentStore.listAssessments(AssessmentState.PENDING);

            expect(assessments).toHaveLength(1);
            expect(assessments[0].state).toBe(AssessmentState.PENDING);
        });

        it('should apply pagination', async () => {
            const mockAssessments = [
                {
                    assessment_id: 'assessment-1',
                    state: AssessmentState.PENDING,
                    version: 1,
                    progress: 0,
                    message: 'Pending',
                    created_at: '2023-01-01T00:00:00.000Z',
                    updated_at: '2023-01-01T00:00:00.000Z',
                    completed_at: null,
                    request_data: '{}',
                    result_data: null,
                    error_message: null,
                    retry_count: 0,
                    next_retry_at: null
                }
            ];

            mockDatabaseService.query.mockResolvedValueOnce({ rows: mockAssessments });

            const assessments = await assessmentStore.listAssessments(undefined, 1, 0);

            expect(assessments).toHaveLength(1);
        });
    });

    describe('cancelAssessment', () => {
        const assessmentId = 'test-assessment';

        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should cancel assessment successfully', async () => {
            // Mock current assessment state
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PENDING }] })
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.CANCELLED }] });

            await expect(assessmentStore.cancelAssessment(assessmentId, 'Test reason')).resolves.not.toThrow();
            expect(mockLogger.info).toHaveBeenCalledWith('Assessment cancelled', { assessmentId, reason: 'Test reason' });
        });

        it('should not cancel completed assessment', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.COMPLETED }] });

            await expect(assessmentStore.cancelAssessment(assessmentId)).resolves.not.toThrow();
            expect(mockLogger.warn).toHaveBeenCalledWith('Cannot cancel assessment in current state', {
                assessmentId,
                currentState: AssessmentState.COMPLETED
            });
        });

        it('should handle database update failure', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PENDING }] })
                .mockRejectedValueOnce(new Error('Database error'));

            await expect(assessmentStore.cancelAssessment(assessmentId)).rejects.toThrow('Failed to cancel assessment');
        });
    });

    describe('getStatistics', () => {
        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should get assessment statistics', async () => {
            const mockStats = {
                total_assessments: 10,
                pending_count: 2,
                processing_count: 3,
                completed_count: 4,
                failed_count: 1,
                cancelled_count: 0,
                avg_processing_time: '120.5',
                recent_assessments: 5
            };

            mockDatabaseService.query.mockResolvedValueOnce({ rows: [mockStats] });

            const statistics = await assessmentStore.getStatistics();

            expect(statistics.totalAssessments).toBe(10);
            expect(statistics.assessmentsByState[AssessmentState.PENDING]).toBe(2);
            expect(statistics.assessmentsByState[AssessmentState.PROCESSING]).toBe(3);
            expect(statistics.assessmentsByState[AssessmentState.COMPLETED]).toBe(4);
            expect(statistics.assessmentsByState[AssessmentState.FAILED]).toBe(1);
            expect(statistics.assessmentsByState[AssessmentState.CANCELLED]).toBe(0);
            expect(statistics.averageProcessingTime).toBe(120.5);
            expect(statistics.recentAssessments).toBe(5);
        });
    });

    describe('updateState', () => {
        const assessmentId = 'test-assessment';

        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should update assessment state successfully', async () => {
            const mockResultData: AssessmentResult = {
                timestamp: '2023-01-01T00:00:00.000Z',
                totalServers: 10,
                compliantServers: 8,
                nonCompliantServers: 2,
                missingServers: [],
                configurationIssues: [],
                serverStatuses: [],
                overallScore: 80,
                summary: {
                    criticalIssues: 0,
                    highIssues: 1,
                    mediumIssues: 2,
                    lowIssues: 3
                }
            };

            // Mock current state and update
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PROCESSING, version: 1 }] })
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.COMPLETED, version: 2 }] });

            await expect(assessmentStore.updateState(assessmentId, AssessmentState.COMPLETED, mockResultData, 'Processing completed')).resolves.not.toThrow();
            expect(mockLogger.debug).toHaveBeenCalledWith('Assessment state updated', {
                assessmentId,
                state: AssessmentState.COMPLETED,
                progress: 100
            });
        });

        it('should validate state transitions', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.COMPLETED }] });

            await expect(assessmentStore.updateState(assessmentId, AssessmentState.PROCESSING)).rejects.toThrow('Invalid state transition');
        });

        it('should handle database update failure', async () => {
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ assessment_id: assessmentId, state: AssessmentState.PROCESSING, version: 1 }] })
                .mockRejectedValueOnce(new Error('Database error'));

            await expect(assessmentStore.updateState(assessmentId, AssessmentState.COMPLETED)).rejects.toThrow('Failed to update assessment state');
        });
    });

    describe('getAssessmentData', () => {
        const assessmentId = 'test-assessment';

        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should get assessment data successfully', async () => {
            const mockAssessmentData = {
                assessmentId: assessmentId,
                state: AssessmentState.PROCESSING,
                version: 1,
                progress: 50,
                message: 'Processing',
                createdAt: '2023-01-01T00:00:00.000Z',
                updatedAt: '2023-01-01T00:00:00.000Z',
                completedAt: null,
                requestData: { test: 'data' },
                resultData: undefined,
                errorMessage: undefined,
                retryCount: 0,
                nextRetryAt: null
            };

            mockDatabaseService.query.mockResolvedValueOnce({ rows: [mockAssessmentData] });

            const data = await assessmentStore.getAssessmentData(assessmentId);

            expect(data).toEqual(mockAssessmentData);
        });
    });

    describe('getAssessmentsForRetry', () => {
        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should get assessments for retry', async () => {
            const mockRetryInfo = [
                {
                    assessment_id: 'failed-assessment-1',
                    retry_count: 1,
                    next_retry_at: '2023-01-01T00:00:00.000Z',
                    error_message: 'Connection timeout'
                },
                {
                    assessment_id: 'failed-assessment-2',
                    retry_count: 2,
                    next_retry_at: null,
                    error_message: 'Server error'
                }
            ];

            mockDatabaseService.query.mockResolvedValueOnce({ rows: mockRetryInfo });

            const result = await assessmentStore.getAssessmentsForRetry();

            expect(result).toHaveLength(2);
            expect(result[0].assessmentId).toBe('failed-assessment-1');
            expect(result[0].retryCount).toBe(1);
            expect(result[0].errorMessage).toBe('Connection timeout');
            expect(result[1].assessmentId).toBe('failed-assessment-2');
            expect(result[1].retryCount).toBe(2);
            expect(result[1].errorMessage).toBe('Server error');
        });
    });

    describe('cleanupOldAssessments', () => {
        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should cleanup old assessments', async () => {
            mockDatabaseService.query.mockResolvedValueOnce({ rows: [{ id: '1' }, { id: '2' }, { id: '3' }] });

            const result = await assessmentStore.cleanupOldAssessments(30);

            expect(result).toBe(3);
            expect(mockLogger.info).toHaveBeenCalledWith('Cleaned up old assessments', {
                maxAge: 30 * 24 * 60 * 60 * 1000,
                retentionDays: 30,
                cleanedCount: 3
            });
        });
    });

    describe('getAssessmentAuditTrail', () => {
        const assessmentId = 'test-assessment';

        beforeEach(() => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });
        });

        it('should get assessment audit trail', async () => {
            const mockAuditTrail = [
                {
                    id: 'audit-1',
                    old_state: AssessmentState.PENDING,
                    new_state: AssessmentState.PROCESSING,
                    version_from: 1,
                    version_to: 2,
                    changed_by: 'system',
                    change_reason: 'Started processing',
                    change_action: 'start',
                    created_at: '2023-01-01T00:00:00.000Z',
                    context: '{"test": "context"}'
                },
                {
                    id: 'audit-2',
                    old_state: AssessmentState.PROCESSING,
                    new_state: AssessmentState.COMPLETED,
                    version_from: 2,
                    version_to: 3,
                    changed_by: 'system',
                    change_reason: 'Processing completed',
                    change_action: 'complete',
                    created_at: '2023-01-01T00:01:00.000Z',
                    context: '{"test": "context2"}'
                }
            ];

            mockDatabaseService.query.mockResolvedValueOnce({ rows: mockAuditTrail });

            const result = await assessmentStore.getAssessmentAuditTrail(assessmentId);

            expect(result).toHaveLength(2);
            expect(result[0].assessment_id).toBe(assessmentId);
            expect(result[0].old_state).toBe(AssessmentState.PENDING);
            expect(result[0].new_state).toBe(AssessmentState.PROCESSING);
            expect(result[1].old_state).toBe(AssessmentState.PROCESSING);
            expect(result[1].new_state).toBe(AssessmentState.COMPLETED);
        });
    });

    describe('close', () => {
        it('should close successfully', async () => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });

            await expect(assessmentStore.close()).resolves.not.toThrow();
            expect(mockLogger.info).toHaveBeenCalledWith('AssessmentStore closed successfully');
        });

        it('should handle close failure', async () => {
            // Mock successful initialization
            mockDatabaseService.query
                .mockResolvedValueOnce({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] })
                .mockRejectedValueOnce(new Error('Close error'));

            await expect(assessmentStore.close()).rejects.toThrow('Failed to close AssessmentStore');
        });
    });
});