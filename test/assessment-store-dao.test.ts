/**
 * MCP Integration Coordinator - Assessment Store DAO Tests
 * 
 * Unit tests for AssessmentStore database operations.
 */

import { AssessmentStoreDAO } from '../src/services/assessment-store-dao';
import { DatabaseService } from '../src/services/database-service';
import { Logger } from '../src/logger';
import {
    AssessmentState,
    AssessmentStoreCreateOptions,
    AssessmentResult,
    AssessmentProcessingError,
    AssessmentNotFoundError
} from '../src/types';

// Mock database service
const mockDatabaseService = {
    query: jest.fn(),
    getClient: jest.fn()
} as any;

// Mock logger
const mockLogger = {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn()
} as any;

describe('AssessmentStoreDAO', () => {
    let dao: AssessmentStoreDAO;

    beforeEach(() => {
        jest.clearAllMocks();
        dao = new AssessmentStoreDAO(mockDatabaseService, mockLogger);
    });

    describe('initialize', () => {
        it('should initialize successfully', async () => {
            mockDatabaseService.query.mockResolvedValue({ rows: [{ table_name: 'assessment_states' }, { table_name: 'assessment_state_audit' }] });

            await expect(dao.initialize()).resolves.not.toThrow();
            expect(mockLogger.info).toHaveBeenCalledWith('AssessmentStore DAO initialized successfully');
        });

        it('should throw error when schema verification fails', async () => {
            mockDatabaseService.query.mockResolvedValue({ rows: [{ table_name: 'assessment_states' }] });

            await expect(dao.initialize()).rejects.toThrow('Database schema verification failed');
            expect(mockLogger.error).toHaveBeenCalledWith('Database schema verification failed', expect.any(Error));
        });
    });

    describe('createAssessment', () => {
        const createOptions: AssessmentStoreCreateOptions = {
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

        it('should create assessment successfully', async () => {
            const mockResult = {
                rows: [{ id: 'test-id' }]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const assessmentId = await dao.createAssessment(createOptions);

            expect(assessmentId).toBeDefined();
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('INSERT INTO assessment_states'),
                expect.arrayContaining([
                    expect.stringContaining('assessment_'),
                    AssessmentState.PENDING,
                    1,
                    0,
                    expect.any(String),
                    expect.any(String),
                    expect.any(String),
                    expect.stringContaining('"requestId"'),
                    8,
                    600
                ])
            );
            expect(mockLogger.info).toHaveBeenCalledWith('Assessment created in database', { assessmentId: expect.any(String) });
        });

        it('should use provided assessment ID', async () => {
            const mockResult = {
                rows: [{ id: 'test-id' }]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const assessmentId = await dao.createAssessment(createOptions, 'custom-assessment-id');

            expect(assessmentId).toBe('custom-assessment-id');
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('assessment_id = $1'),
                ['custom-assessment-id']
            );
        });

        it('should throw error when database operation fails', async () => {
            mockDatabaseService.query.mockRejectedValue(new Error('Database error'));

            await expect(dao.createAssessment(createOptions)).rejects.toThrow('Failed to create assessment');
            expect(mockLogger.error).toHaveBeenCalledWith('Failed to create assessment in database', expect.any(Error), { assessmentId: undefined });
        });
    });

    describe('getAssessment', () => {
        const mockAssessmentData = {
            assessment_id: 'test-assessment',
            state: AssessmentState.PENDING,
            version: 1,
            progress: 0,
            message: 'Test message',
            created_at: '2023-01-01T00:00:00.000Z',
            updated_at: '2023-01-01T00:00:00.000Z',
            completed_at: null,
            request_data: '{"test": "data"}',
            result_data: null,
            error_message: null,
            retry_count: 0,
            next_retry_at: null
        };

        it('should get assessment successfully', async () => {
            const mockResult = {
                rows: [mockAssessmentData]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.getAssessment('test-assessment');

            expect(result.assessmentId).toBe('test-assessment');
            expect(result.state).toBe(AssessmentState.PENDING);
            expect(result.version).toBe(1);
            expect(result.progress).toBe(0);
            expect(result.requestData).toEqual({ test: 'data' });
        });

        it('should throw AssessmentNotFoundError when assessment not found', async () => {
            const mockResult = {
                rows: []
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            await expect(dao.getAssessment('non-existent')).rejects.toThrow(AssessmentNotFoundError);
        });

        it('should throw error when database operation fails', async () => {
            mockDatabaseService.query.mockRejectedValue(new Error('Database error'));

            await expect(dao.getAssessment('test-assessment')).rejects.toThrow('Failed to get assessment');
            expect(mockLogger.error).toHaveBeenCalledWith('Failed to get assessment from database', expect.any(Error), { assessmentId: 'test-assessment' });
        });
    });

    describe('updateAssessment', () => {
        const mockCurrentData = {
            assessment_id: 'test-assessment',
            state: AssessmentState.PENDING,
            version: 1,
            progress: 0,
            message: 'Test message',
            created_at: '2023-01-01T00:00:00.000Z',
            updated_at: '2023-01-01T00:00:00.000Z',
            completed_at: null,
            request_data: '{"test": "data"}',
            result_data: null,
            error_message: null,
            retry_count: 0,
            next_retry_at: null
        };

        it('should update assessment state successfully', async () => {
            const mockResult = {
                rows: [{ version: 2 }]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const updateOptions = {
                state: AssessmentState.PROCESSING,
                progress: 50,
                message: 'Processing'
            };

            const result = await dao.updateAssessment('test-assessment', updateOptions, 1);

            expect(result).toBe(2);
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE assessment_states'),
                expect.arrayContaining([
                    expect.any(String), // updated_at
                    AssessmentState.PROCESSING,
                    50,
                    'Processing',
                    'test-assessment',
                    1
                ])
            );
        });

        it('should throw error when assessment not found', async () => {
            const mockResult = {
                rows: []
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const updateOptions = {
                state: AssessmentState.PROCESSING
            };

            await expect(dao.updateAssessment('non-existent', updateOptions, 1)).rejects.toThrow('Assessment not found or version mismatch');
        });

        it('should handle completed timestamp for terminal states', async () => {
            const mockResult = {
                rows: [{ version: 2 }]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const updateOptions = {
                state: AssessmentState.COMPLETED,
                resultData: { success: true } as AssessmentResult
            };

            await dao.updateAssessment('test-assessment', updateOptions, 1);

            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('completed_at = $'),
                expect.anything()
            );
        });
    });

    describe('listAssessments', () => {
        const mockAssessments = [
            {
                assessment_id: 'assessment-1',
                state: AssessmentState.PENDING,
                version: 1,
                progress: 0,
                message: 'Test message 1',
                created_at: '2023-01-01T00:00:00.000Z',
                updated_at: '2023-01-01T00:00:00.000Z',
                completed_at: null,
                request_data: '{"test": "data1"}',
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
                message: 'Test message 2',
                created_at: '2023-01-02T00:00:00.000Z',
                updated_at: '2023-01-02T00:00:00.000Z',
                completed_at: null,
                request_data: '{"test": "data2"}',
                result_data: null,
                error_message: null,
                retry_count: 0,
                next_retry_at: null
            }
        ];

        it('should list all assessments', async () => {
            const mockResult = {
                rows: mockAssessments
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.listAssessments();

            expect(result).toHaveLength(2);
            expect(result[0].assessmentId).toBe('assessment-1');
            expect(result[1].assessmentId).toBe('assessment-2');
        });

        it('should filter by state', async () => {
            const mockResult = {
                rows: [mockAssessments[0]]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.listAssessments({ state: AssessmentState.PENDING });

            expect(result).toHaveLength(1);
            expect(result[0].state).toBe(AssessmentState.PENDING);
        });

        it('should filter by server name', async () => {
            const mockResult = {
                rows: [mockAssessments[0]]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.listAssessments({ serverName: 'test-server' });

            expect(result).toHaveLength(1);
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('request_data->>\'serverName\' = $'),
                expect.arrayContaining(['test-server'])
            );
        });

        it('should apply pagination', async () => {
            const mockResult = {
                rows: [mockAssessments[0]]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.listAssessments({ limit: 1, offset: 0 });

            expect(result).toHaveLength(1);
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('LIMIT $'),
                expect.arrayContaining([1])
            );
        });

        it('should sort by specified field', async () => {
            const mockResult = {
                rows: mockAssessments
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.listAssessments({ orderBy: 'updated_at', orderDirection: 'ASC' });

            expect(result).toHaveLength(2);
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('ORDER BY updated_at ASC'),
                expect.anything()
            );
        });
    });

    describe('deleteAssessment', () => {
        it('should delete assessment successfully', async () => {
            const mockResult = {
                rows: [{ id: 'test-id' }]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.deleteAssessment('test-assessment');

            expect(result).toBe(true);
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('UPDATE assessment_states SET state = \'cancelled\''),
                ['test-assessment']
            );
            expect(mockLogger.info).toHaveBeenCalledWith('Assessment soft deleted', { assessmentId: 'test-assessment' });
        });

        it('should return false when assessment not found', async () => {
            const mockResult = {
                rows: []
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.deleteAssessment('non-existent');

            expect(result).toBe(false);
            expect(mockLogger.warn).toHaveBeenCalledWith('Assessment not found for deletion', { assessmentId: 'non-existent' });
        });
    });

    describe('getAssessmentsForRetry', () => {
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

        it('should get assessments for retry', async () => {
            const mockResult = {
                rows: mockRetryInfo
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.getAssessmentsForRetry(3);

            expect(result).toHaveLength(2);
            expect(result[0].assessmentId).toBe('failed-assessment-1');
            expect(result[0].retryCount).toBe(1);
            expect(result[0].errorMessage).toBe('Connection timeout');
            expect(result[1].assessmentId).toBe('failed-assessment-2');
            expect(result[1].retryCount).toBe(2);
            expect(result[1].errorMessage).toBe('Server error');
        });

        it('should filter by max retries', async () => {
            const mockResult = {
                rows: [mockRetryInfo[0]]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.getAssessmentsForRetry(1);

            expect(result).toHaveLength(1);
            expect(result[0].assessmentId).toBe('failed-assessment-1');
        });
    });

    describe('getAssessmentStatistics', () => {
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

        it('should get assessment statistics', async () => {
            const mockResult = {
                rows: [mockStats]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.getAssessmentStatistics();

            expect(result.totalAssessments).toBe(10);
            expect(result.assessmentsByState[AssessmentState.PENDING]).toBe(2);
            expect(result.assessmentsByState[AssessmentState.PROCESSING]).toBe(3);
            expect(result.assessmentsByState[AssessmentState.COMPLETED]).toBe(4);
            expect(result.assessmentsByState[AssessmentState.FAILED]).toBe(1);
            expect(result.assessmentsByState[AssessmentState.CANCELLED]).toBe(0);
            expect(result.averageProcessingTime).toBe(120.5);
            expect(result.recentAssessments).toBe(5);
        });
    });

    describe('cleanupOldAssessments', () => {
        it('should cleanup old assessments', async () => {
            const mockResult = {
                rows: [{ id: '1' }, { id: '2' }, { id: '3' }]
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.cleanupOldAssessments(30);

            expect(result).toBe(3);
            expect(mockDatabaseService.query).toHaveBeenCalledWith(
                expect.stringContaining('DELETE FROM assessment_states'),
                expect.arrayContaining([expect.any(String)])
            );
            expect(mockLogger.info).toHaveBeenCalledWith('Cleaned up old assessments', {
                retentionDays: 30,
                deletedCount: 3
            });
        });
    });

    describe('loadPendingAssessments', () => {
        const mockPendingAssessments = [
            {
                assessment_id: 'pending-assessment-1',
                state: AssessmentState.PENDING,
                version: 1,
                progress: 0,
                message: 'Pending message',
                created_at: '2023-01-01T00:00:00.000Z',
                updated_at: '2023-01-01T00:00:00.000Z',
                completed_at: null,
                request_data: '{"test": "data1"}',
                result_data: null,
                error_message: null,
                retry_count: 0,
                next_retry_at: null
            },
            {
                assessment_id: 'failed-assessment-1',
                state: AssessmentState.FAILED,
                version: 1,
                progress: 100,
                message: 'Failed message',
                created_at: '2023-01-02T00:00:00.000Z',
                updated_at: '2023-01-02T00:00:00.000Z',
                completed_at: '2023-01-02T00:00:00.000Z',
                request_data: '{"test": "data2"}',
                result_data: null,
                error_message: 'Test error',
                retry_count: 1,
                next_retry_at: '2023-01-03T00:00:00.000Z'
            }
        ];

        it('should load pending assessments', async () => {
            const mockResult = {
                rows: mockPendingAssessments
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.loadPendingAssessments();

            expect(result).toHaveLength(2);
            expect(result[0].assessmentId).toBe('pending-assessment-1');
            expect(result[0].state).toBe(AssessmentState.PENDING);
            expect(result[1].assessmentId).toBe('failed-assessment-1');
            expect(result[1].state).toBe(AssessmentState.FAILED);
        });
    });

    describe('getAssessmentAuditTrail', () => {
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

        it('should get assessment audit trail', async () => {
            const mockResult = {
                rows: mockAuditTrail
            };
            mockDatabaseService.query.mockResolvedValue(mockResult);

            const result = await dao.getAssessmentAuditTrail('test-assessment');

            expect(result).toHaveLength(2);
            expect(result[0].assessment_id).toBe('test-assessment');
            expect(result[0].old_state).toBe(AssessmentState.PENDING);
            expect(result[0].new_state).toBe(AssessmentState.PROCESSING);
            expect(result[1].old_state).toBe(AssessmentState.PROCESSING);
            expect(result[1].new_state).toBe(AssessmentState.COMPLETED);
        });
    });

    describe('close', () => {
        it('should close successfully', async () => {
            await expect(dao.close()).resolves.not.toThrow();
            expect(mockLogger.info).toHaveBeenCalledWith('AssessmentStore DAO closed successfully');
        });
    });
});