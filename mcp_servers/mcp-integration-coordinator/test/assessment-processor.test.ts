/**
 * MCP Integration Coordinator - Assessment Processor Tests
 * 
 * Simple tests for the AssessmentProcessor service (without test runner dependencies).
 */

import { AssessmentProcessor } from '../src/services/assessment-processor';
import { AssessmentProcessorConfig, AssessmentState } from '../src/types';

// Mock dependencies
const mockLogger = {
    info: () => { },
    warn: () => { },
    error: () => { },
    debug: () => { },
    child: () => mockLogger
};

const mockDatabaseService = {
    query: async () => ({ rows: [] }),
    initialize: async () => { },
    close: async () => { },
    isConnectionActive: () => true
};

const mockAuditService = {
    log: async () => { }
};

// Simple test runner
function runTest(name: string, testFn: () => void | Promise<void>) {
    console.log(`Running test: ${name}`);
    try {
        const result = testFn();
        if (result instanceof Promise) {
            result.then(() => {
                console.log(`✓ Test passed: ${name}`);
            }).catch((error) => {
                console.error(`✗ Test failed: ${name}`, error);
            });
        } else {
            console.log(`✓ Test passed: ${name}`);
        }
    } catch (error) {
        console.error(`✗ Test failed: ${name}`, error);
    }
}

// Simple assertion functions
const assert = {
    equals: (actual: any, expected: any, message?: string) => {
        if (actual !== expected) {
            throw new Error(message || `Expected ${expected}, got ${actual}`);
        }
    },
    instanceOf: (actual: any, expected: any, message?: string) => {
        if (!(actual instanceof expected)) {
            throw new Error(message || `Expected instance of ${expected.name}, got ${typeof actual}`);
        }
    },
    throws: (fn: () => void, message?: string) => {
        try {
            fn();
            throw new Error(message || 'Expected function to throw');
        } catch (error) {
            // Expected
        }
    },
    hasProperty: (obj: any, prop: string, message?: string) => {
        if (!(prop in obj)) {
            throw new Error(message || `Expected object to have property ${prop}`);
        }
    }
};

// Test suite
console.log('=== AssessmentProcessor Test Suite ===\n');

// Basic functionality tests
runTest('should create an AssessmentProcessor instance', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    assert.instanceOf(assessmentProcessor, AssessmentProcessor);
});

runTest('should initialize with default metrics', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const metrics = assessmentProcessor.getMetrics();
    assert.equals(metrics.totalProcessed, 0);
    assert.equals(metrics.successful, 0);
    assert.equals(metrics.failed, 0);
    assert.equals(metrics.retryCount, 0);
    assert.equals(metrics.averageProcessingTime, 0);
    assert.equals(metrics.queueSize, 0);
});

runTest('should start and stop successfully', async () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    await assessmentProcessor.start();
    await assessmentProcessor.stop();
});

runTest('should add assessment to processing queue', async () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const assessmentId = 'test-assessment-123';
    await assessmentProcessor.processAssessment(assessmentId);

    const queueStatus = assessmentProcessor.getQueueStatus();
    assert.equals(queueStatus.queueSize, 1);
});

runTest('should return current metrics', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const metrics = assessmentProcessor.getMetrics();
    assert.hasProperty(metrics, 'totalProcessed');
    assert.hasProperty(metrics, 'successful');
    assert.hasProperty(metrics, 'failed');
    assert.hasProperty(metrics, 'retryCount');
    assert.hasProperty(metrics, 'averageProcessingTime');
    assert.hasProperty(metrics, 'queueSize');
    assert.hasProperty(metrics, 'circuitBreakerState');
    assert.hasProperty(metrics, 'lastProcessedAt');
});

runTest('should return current queue status', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const status = assessmentProcessor.getQueueStatus();
    assert.hasProperty(status, 'queueSize');
    assert.hasProperty(status, 'activeAssessments');
    assert.hasProperty(status, 'isProcessing');
    assert.hasProperty(status, 'circuitBreakerState');
});

runTest('should calculate retry delay with exponential backoff', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const processor = assessmentProcessor as any;
    const delay1 = processor.calculateRetryDelay(1);
    const delay2 = processor.calculateRetryDelay(2);
    const delay3 = processor.calculateRetryDelay(3);

    assert.equals(delay1 > 0, true);
    assert.equals(delay2 > delay1, true);
    assert.equals(delay3 > delay2, true);
});

runTest('should cap retry delay at maximum', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const processor = assessmentProcessor as any;
    const delay = processor.calculateRetryDelay(10);
    assert.equals(delay <= 300000, true); // 5 minutes
});

runTest('should handle processing errors and retry', async () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const assessmentId = 'test-assessment-123';
    const error = new Error('Test error');

    const shouldRetry = await (assessmentProcessor as any).handleProcessingError(
        assessmentId,
        error,
        1
    );

    assert.equals(shouldRetry, true);
});

runTest('should not retry after max retries', async () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const assessmentId = 'test-assessment-123';
    const error = new Error('Test error');

    const shouldRetry = await (assessmentProcessor as any).handleProcessingError(
        assessmentId,
        error,
        10
    );

    assert.equals(shouldRetry, false);
});

runTest('should open circuit breaker after threshold failures', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const processor = assessmentProcessor as any;

    // Simulate failures
    for (let i = 0; i < 5; i++) {
        processor.updateCircuitBreakerFailure();
    }

    assert.equals(processor.circuitBreaker.state, 'open');
    assert.equals(processor.circuitBreaker.failureCount, 5);
});

runTest('should close circuit breaker after successful request', () => {
    const config: AssessmentProcessorConfig = {
        assessmentStore: {
            database: {
                host: 'localhost',
                port: 5432,
                database: 'test',
                username: 'test',
                password: 'test',
                ssl: false
            },
            complianceServer: {
                baseUrl: 'http://localhost:3000',
                apiKey: 'test-key',
                timeout: 30000,
                maxConcurrent: 5
            },
            processing: {
                timeout: 30000,
                maxRetries: 3,
                retryDelay: 5000,
                queueSize: 100
            }
        },
        processing: {
            timeout: 30000,
            maxRetries: 3,
            retryDelay: 5000,
            retryBackoff: 2,
            queueSize: 100,
            batchSize: 5,
            processingInterval: 1000
        },
        circuitBreaker: {
            failureThreshold: 5,
            resetTimeout: 60000,
            monitoringInterval: 30000
        },
        logging: {
            level: 'info',
            enableMetrics: true
        }
    };

    const assessmentProcessor = new AssessmentProcessor(
        config,
        mockLogger as any,
        mockDatabaseService as any,
        mockAuditService as any
    );

    const processor = assessmentProcessor as any;

    // Open circuit breaker
    processor.circuitBreaker.state = 'open';
    processor.updateCircuitBreakerSuccess();

    assert.equals(processor.circuitBreaker.state, 'closed');
    assert.equals(processor.circuitBreaker.failureCount, 0);
});

console.log('\n=== Test Suite Complete ===');