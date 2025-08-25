/**
 * Central export point for all API services
 * This helps maintain clean code structure by isolating API calls
 * from UI components.
 */

// Import all API services
import { ingestionApi } from './ingestion_api';
import { embeddingApi } from './embedding_api';
import { previewApi } from './preview_api';
import { parsingApi } from './parsing_api';
import { apiKeyService, ApiKey, ApiKeyResponse, ApiKeyCreate } from './api_key_service';
import { organizationApi, Organization, OrganizationMember, MemberRole, OrganizationCreate, OrganizationMemberInvite, OrganizationMemberUpdate } from './organization_api';

// Re-export all services and types
export {
  ingestionApi,
  embeddingApi,
  previewApi,
  parsingApi,
  apiKeyService,
  organizationApi,
};

export type {
  ApiKey,
  ApiKeyResponse,
  ApiKeyCreate,
  Organization,
  OrganizationMember,
  MemberRole,
  OrganizationCreate,
  OrganizationMemberInvite,
  OrganizationMemberUpdate,
};

// Example usage in components:
// import { ingestionApi, previewApi, apiKeyService, type ApiKey } from '@/lib/api_services'; 