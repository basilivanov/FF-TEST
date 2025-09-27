# Critical Anti-Patterns to Avoid

## God Prompt Anti-Pattern ❌
**Problem**: Single massive prompt trying to handle everything
**Solution**: Modular, role-specific prompts with clear boundaries

## Vague Role Definition ❌  
**Problem**: "You are a developer" without specifics
**Solution**: Precise role boundaries with explicit do/don't lists

## Mock/Placeholder Pattern ❌
**CRITICAL**: NEVER use mocks, stubs, placeholders, TODO comments
- ❌ `YOUR_BOT_TOKEN` → ✅ Use actual tokens from requirements
- ❌ `# TODO: Implement` → ✅ Full implementation required  
- ❌ `mock_api_call()` → ✅ Real HTTP requests with httpx

## Missing Context Boundaries ❌
**Problem**: Instructions mixed with user data (prompt injection risk)
**Solution**: Clear separation between system instructions and input data

## Inconsistent Output Formats ❌
**Problem**: Different agents returning incompatible formats
**Solution**: Standardized YAML manifests + fenced code blocks

## Hallucinated Dependencies ❌
**Problem**: Assuming libraries/APIs that don't exist
**Solution**: Verify against actual tech stack before suggesting

## Over-Engineering ❌
**Problem**: Complex solutions when simple ones suffice  
**Solution**: Prefer standard patterns over custom implementations

## Insufficient Error Handling ❌
**Problem**: Code that fails silently or ungracefully
**Solution**: Explicit error handling with proper logging

## Security Vulnerabilities ❌
**Problem**: Exposing secrets, SQL injection, XSS vulnerabilities
**Solution**: Parameterized queries, input validation, secret masking