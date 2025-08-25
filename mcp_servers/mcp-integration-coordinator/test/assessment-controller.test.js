/**
 * MCP Integration Coordinator - Assessment Controller Tests
 *
 * Unit tests for the AssessmentController using Promise-based API
 * from AssessmentStore and AssessmentProcessor services.
 */

const { AssessmentController } = require('../src/controllers/assessment-controller');
const { AssessmentStore } = require('../src/services/assessment-store');
const { AssessmentProcessor } = require('../src/services/assessment-processor');
const { AuditService } = require('../src/services/audit-service');
const { AssessmentRequest, AssessmentState, AssessmentResult } = require('../src/types');

// Define enum values directly to avoid Jest mocking issues
const PENDING = 'pending';
const PROCESSING = 'processing';
const COMPLETED = 'completed';
const FAILED = 'failed';
const CANCELLED = 'cancelled';

// Mock dependencies
const mockLogger = {
    info: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
    debug: jest.fn()
};

const mockAuditService = {
    log: jest.fn().mockResolvedValue(undefined)
};

const mockAssessmentStore = {
    createAssessment: jest.fn(),
    waitForCompletion: jest.fn(),
    getState: jest.fn(),
    listAssessments: jest.fn(),
    cancelAssessment: jest.fn(),
    getStatistics: jest.fn()
};

const mockAssessmentProcessor = {
    processAssessment: jest.fn()
};

// Mock jest functions
jest.mock('../src/logger', () => ({
    logger: {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
        debug: jest.fn()
    }
}));

// Get the mocked logger instance
const { logger: mockedLogger } = require('../src/logger');

// Mock the AssessmentStore, AssessmentProcessor, and AuditService
jest.mock('../src/services/assessment-store', () => {
    const MockAssessmentStore = jest.fn().mockImplementation(() => ({
        createAssessment: jest.fn(),
        waitForCompletion: jest.fn(),
        getState: jest.fn(),
        listAssessments: jest.fn(),
        cancelAssessment: jest.fn(),
        getStatistics: jest.fn()
    }));
    return { AssessmentStore: MockAssessmentStore };
});

jest.mock('../src/services/assessment-processor', () => {
    const MockAssessmentProcessor = jest.fn().mockImplementation(() => ({
        processAssessment: jest.fn()
    }));
    return { AssessmentProcessor: MockAssessmentProcessor };
});

jest.mock('../src/services/audit-service', () => {
    const MockAuditService = jest.fn().mockImplementation(() => ({
        log: mockAuditService.log
    }));
    return { AuditService: MockAuditService };
});

// Add Jest global functions
global.jest = jest;
global.describe = describe;
global.beforeEach = beforeEach;
global.afterEach = afterEach;
global.it = it;
global.expect = expect;

describe('AssessmentController', () => {
    let assessmentController;

    beforeEach(() => {
        // Reset all mocks
        jest.clearAllMocks();

        // Create controller instance with mocked services
        const { AssessmentStore } = require('../src/services/assessment-store');
        const { AssessmentProcessor } = require('../src/services/assessment-processor');
        const { AuditService } = require('../src/services/audit-service');

        assessmentController = new AssessmentController(
            new AssessmentStore(),
            new AssessmentProcessor(),
            new AuditService()
        );
    });

    describe('requestAssessment', () => {
        const mockRequest = {
            body: {
                assessmentType: 'compliance',
                options: {
                    includeDetails: true,
                    generateReport: false
                }
            },
            user: { username: 'testuser' },
            ip: '127.0.0.1',
            get: jest.fn().mockReturnValue('test-agent')
        };

        const mockResponse = {
            json: jest.fn(),
            status: jest.fn().mockReturnThis()
        };

        it('should successfully create and start processing an assessment', async () => {
            const assessmentId = 'assessment_123';

            // Get the mocked service instances
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            const assessmentProcessorInstance = assessmentController['assessmentProcessor'];
            const auditServiceInstance = assessmentController['auditService'];

            // Convert AssessmentRequest to AssessmentStoreCreateOptions
            const createOptions = {
                assessmentType: mockRequest.body.assessmentType,
                options: mockRequest.body.options,
                serverName: undefined,
                source: 'installer'
            };

            assessmentStoreInstance.createAssessment.mockResolvedValue(assessmentId);

            // Add debug logging
            console.log('Mock createAssessment called with:', createOptions);
            console.log('Mock createAssessment resolved with:', assessmentId);

            await assessmentController['requestAssessment'](mockRequest, mockResponse);

            expect(assessmentStoreInstance.createAssessment).toHaveBeenCalledWith(
                expect.objectContaining({
                    assessmentType: 'compliance',
                    options: expect.objectContaining({
                        includeDetails: true,
                        generateReport: false
                    })
                })
            );
            expect(assessmentProcessorInstance.processAssessment).toHaveBeenCalledWith(assessmentId);
            expect(mockResponse.json).toHaveBeenCalledWith({
                assessmentId,
                status: 'requested',
                message: 'Assessment request received and processing',
                estimatedTime: 30000
            });
        });

        it('should return 400 error for missing required fields', async () => {
            const invalidRequest = {
                body: {
                    assessmentType: 'compliance'
                    // Missing options
                }
            };

            await assessmentController['requestAssessment'](invalidRequest, mockResponse);

            expect(mockResponse.status).toHaveBeenCalledWith(400);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'INVALID_REQUEST',
                    message: 'Missing required fields: assessmentType and options',
                    retryable: false
                }
            });
        });

        it('should handle assessment creation errors', async () => {
            const error = new Error('Database error');
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.createAssessment).mockRejectedValue(error);

            await assessmentController['requestAssessment'](mockRequest, mockResponse);

            expect(mockedLogger.error).toHaveBeenCalledWith('Assessment request failed', error);
            expect(mockResponse.status).toHaveBeenCalledWith(500);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENT_REQUEST_FAILED',
                    message: 'Failed to request assessment',
                    retryable: false
                }
            });
        });
    });

    describe('getAssessmentResults', () => {
        const mockRequest = {
            params: { assessmentId: 'assessment_123' },
            query: { timeout: '15000' }
        };

        const mockResponse = {
            json: jest.fn(),
            status: jest.fn().mockReturnThis()
        };

        it('should successfully get assessment results', async () => {
            const mockResults = {
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
                    highIssues: 2,
                    mediumIssues: 0,
                    lowIssues: 0
                }
            };

            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.waitForCompletion).mockResolvedValue(mockResults);

            await assessmentController['getAssessmentResults'](mockRequest, mockResponse);

            expect(assessmentStoreInstance.waitForCompletion).toHaveBeenCalledWith('assessment_123', 15000);
            expect(mockResponse.json).toHaveBeenCalledWith({
                assessmentId: 'assessment_123',
                results: mockResults
            });
        });

        it('should handle assessment timeout', async () => {
            const error = new Error('Assessment timeout');
            (error).message = 'Assessment timeout after 30000ms';
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.waitForCompletion).mockRejectedValue(error);

            await assessmentController['getAssessmentResults'](mockRequest, mockResponse);

            expect(mockedLogger.error).toHaveBeenCalledWith(
                'Failed to get assessment results',
                error,
                { assessmentId: 'assessment_123' }
            );
            expect(mockResponse.status).toHaveBeenCalledWith(408);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENT_TIMEOUT',
                    message: 'Assessment processing timed out',
                    retryable: true
                }
            });
        });

        it('should handle assessment failure', async () => {
            const error = new Error('Assessment failed');
            (error).message = 'Assessment failed: Server error';
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.waitForCompletion).mockRejectedValue(error);

            await assessmentController['getAssessmentResults'](mockRequest, mockResponse);

            expect(mockResponse.status).toHaveBeenCalledWith(400);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENT_FAILED',
                    message: 'Assessment failed: Server error',
                    retryable: false
                }
            });
        });
    });

    describe('getAssessmentStatus', () => {
        const mockRequest = {
            params: { assessmentId: 'assessment_123' }
        };

        const mockResponse = {
            json: jest.fn(),
            status: jest.fn().mockReturnThis()
        };

        it('should successfully get assessment status', async () => {
            const mockStatus = {
                assessmentId: 'assessment_123',
                state: PROCESSING,
                progress: 50,
                message: 'Processing servers',
                lastUpdated: '2023-01-01T00:00:00.000Z',
                completedAt: undefined
            };

            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.getState).mockResolvedValue(mockStatus);

            await assessmentController['getAssessmentStatus'](mockRequest, mockResponse);

            expect(assessmentStoreInstance.getState).toHaveBeenCalledWith('assessment_123');
            expect(mockResponse.json).toHaveBeenCalledWith({
                assessmentId: 'assessment_123',
                status: PROCESSING,
                progress: 50,
                message: 'Processing servers',
                lastUpdated: '2023-01-01T00:00:00.000Z',
                completedAt: undefined
            });
        });

        it('should handle assessment not found', async () => {
            const error = new Error('Assessment not found');
            (error).message = 'Assessment not found: assessment_123';
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.getState).mockRejectedValue(error);

            await assessmentController['getAssessmentStatus'](mockRequest, mockResponse);

            expect(mockedLogger.error).toHaveBeenCalledWith(
                'Failed to get assessment status',
                error,
                { assessmentId: 'assessment_123' }
            );
            expect(mockResponse.status).toHaveBeenCalledWith(404);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENT_NOT_FOUND',
                    message: 'Assessment not found',
                    retryable: false
                }
            });
        });
    });

    describe('listAssessments', () => {
        const mockRequest = {
            query: {
                state: PENDING,
                limit: '50',
                offset: '0'
            }
        };

        const mockResponse = {
            json: jest.fn(),
            status: jest.fn().mockReturnThis()
        };

        it('should successfully list assessments', async () => {
            const mockAssessments = [
                {
                    assessmentId: 'assessment_1',
                    state: PENDING,
                    progress: 0,
                    message: 'Pending',
                    createdAt: '2023-01-01T00:00:00.000Z',
                    updatedAt: '2023-01-01T00:00:00.000Z',
                    requestData: {},
                    retryCount: 0
                }
            ];

            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.listAssessments).mockResolvedValue(mockAssessments);

            await assessmentController['listAssessments'](mockRequest, mockResponse);

            expect(assessmentStoreInstance.listAssessments).toHaveBeenCalledWith(
                PENDING,
                50,
                0
            );
            expect(mockResponse.json).toHaveBeenCalledWith({
                assessments: mockAssessments,
                pagination: {
                    limit: 50,
                    offset: 0,
                    total: 1
                }
            });
        });

        it('should handle list assessments errors', async () => {
            const error = new Error('Database error');
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.listAssessments).mockRejectedValue(error);

            await assessmentController['listAssessments'](mockRequest, mockResponse);

            expect(mockedLogger.error).toHaveBeenCalledWith('Failed to list assessments', error);
            expect(mockResponse.status).toHaveBeenCalledWith(500);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENTS_LIST_FAILED',
                    message: 'Failed to list assessments',
                    retryable: false
                }
            });
        });
    });

    describe('getAssessmentStatistics', () => {
        const mockRequest = {};
        const mockResponse = {
            json: jest.fn(),
            status: jest.fn().mockReturnThis()
        };

        it('should successfully get assessment statistics', async () => {
            const mockStatistics = {
                totalAssessments: 100,
                assessmentsByState: {
                    [PENDING]: 10,
                    [PROCESSING]: 5,
                    [COMPLETED]: 80,
                    [FAILED]: 3,
                    [CANCELLED]: 2
                },
                averageProcessingTime: 15000,
                recentAssessments: 25
            };

            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.getStatistics).mockResolvedValue(mockStatistics);

            await assessmentController['getAssessmentStatistics'](mockRequest, mockResponse);

            expect(assessmentStoreInstance.getStatistics).toHaveBeenCalled();
            expect(mockResponse.json).toHaveBeenCalledWith({
                statistics: mockStatistics
            });
        });

        it('should handle statistics errors', async () => {
            const error = new Error('Database error');
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.getStatistics).mockRejectedValue(error);

            await assessmentController['getAssessmentStatistics'](mockRequest, mockResponse);

            expect(mockedLogger.error).toHaveBeenCalledWith('Failed to get assessment statistics', error);
            expect(mockResponse.status).toHaveBeenCalledWith(500);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENT_STATISTICS_FAILED',
                    message: 'Failed to get assessment statistics',
                    retryable: false
                }
            });
        });
    });

    describe('cancelAssessment', () => {
        const mockRequest = {
            params: { assessmentId: 'assessment_123' },
            body: { reason: 'User requested cancellation' },
            user: { username: 'testuser' },
            ip: '127.0.0.1',
            get: jest.fn().mockReturnValue('test-agent')
        };

        const mockResponse = {
            json: jest.fn(),
            status: jest.fn().mockReturnThis()
        };

        it('should successfully cancel an assessment', async () => {
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            const auditServiceInstance = assessmentController['auditService'];
            (assessmentStoreInstance.cancelAssessment).mockResolvedValue(undefined);

            await assessmentController['cancelAssessment'](mockRequest, mockResponse);

            expect(assessmentStoreInstance.cancelAssessment).toHaveBeenCalledWith(
                'assessment_123',
                'User requested cancellation'
            );
            expect(auditServiceInstance.log).toHaveBeenCalledWith(expect.objectContaining({
                action: 'assessment_cancelled',
                actor: 'testuser',
                result: 'success'
            }));
            expect(mockResponse.json).toHaveBeenCalledWith({
                assessmentId: 'assessment_123',
                status: 'cancelled',
                message: 'Assessment cancelled successfully'
            });
        });

        it('should handle assessment not found during cancellation', async () => {
            const error = new Error('Assessment not found');
            (error).message = 'Assessment not found: assessment_123';
            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.cancelAssessment).mockRejectedValue(error);

            await assessmentController['cancelAssessment'](mockRequest, mockResponse);

            expect(mockedLogger.error).toHaveBeenCalledWith(
                'Failed to cancel assessment',
                error,
                { assessmentId: 'assessment_123' }
            );
            expect(mockResponse.status).toHaveBeenCalledWith(404);
            expect(mockResponse.json).toHaveBeenCalledWith({
                error: {
                    code: 'ASSESSMENT_NOT_FOUND',
                    message: 'Assessment not found',
                    retryable: false
                }
            });
        });

        it('should use default reason when not provided', async () => {
            const requestWithoutReason = {
                ...mockRequest,
                body: {}
            };

            const assessmentStoreInstance = assessmentController['assessmentStore'];
            (assessmentStoreInstance.cancelAssessment).mockResolvedValue(undefined);

            await assessmentController['cancelAssessment'](requestWithoutReason, mockResponse);

            expect(assessmentStoreInstance.cancelAssessment).toHaveBeenCalledWith(
                'assessment_123',
                'User requested cancellation'
            );
        });
    });

    describe('getRouter', () => {
        it('should return the router instance', () => {
            const router = assessmentController.getRouter();
            expect(router).toBeDefined();
            expect(typeof router).toBe('function');
        });
    });
});