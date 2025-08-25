rc/database/migrations/001_enable_pg_tiktoken.sql</path>
<content-- Enable pg_tiktoken extension for fast, accurate token counting
-- This extension provides tiktoken_count function that aligns with OpenAI's models
-- Extension should be enabled by a superuser or user with CREATEDB privileges

-- Enable the extension
CREATE EXTENSION IF NOT EXISTS pg_tiktoken;

-- Verify the extension is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_tiktoken';

-- Test the tiktoken_count function is available
-- This should return a number representing the token count for the test text
SELECT tiktoken_count('This is a test to verify the pg_tiktoken extension is working correctly.');

-- Create a helper function to check if tiktoken is available
CREATE OR REPLACE FUNCTION is_tiktoken_available() RETURNS boolean AS $$
BEGIN
    -- Try to call tiktoken_count, return true if it succeeds
    PERFORM tiktoken_count('test');
    RETURN true;
EXCEPTION WHEN undefined_function THEN
    RETURN false;
END;
$$ LANGUAGE plpgsql;

-- Test the availability function
SELECT is_tiktoken_available() as tiktoken_extension_available;