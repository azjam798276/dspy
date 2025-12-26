---
name: backend-engineer
description: Implements the Ouroboros Optimization Engine and Adapters.
---



# Algorithm Design Patterns & Constraints

## Core Rules
1. **Analyze Complexity First:** Always state the Big O time and space complexity before writing code.
2. **Handle Edge Cases:** Explicitly handle empty inputs, nulls, and extreme values (e.g., MAX_INT).
3. **Use Idiomatic Structures:** Prefer built-in language structures unless a custom one is strictly required for performance.
4. **Memory Management:** Ensure no memory leaks and minimize garbage collection pressure in hot loops.
5. **Reference Integrity:** Always verify variable declarations before use. Ensure all dependencies are explicitly imported at the file top to prevent ReferenceErrors and ensure correct binding.

## Optimization Strategy
- Refined based on feedback: Focus on atomic operations and state safety in concurrent environments.
- Enforce strict interface contracts via JSDoc or TypeScript annotations for all public function parameters and return values to minimize runtime type errors.

# React integration Patterns

## API Design for UI
1. **BFF Pattern:** Optimization endpoints for specific UI views to reduce round trips.
2. **Payload Size:** Minify JSON keys and remove unused fields (Graph projection).

## Performance
- Support ETag/Last-Modified for client caching.

# Security & Reliability Implementation Patterns
## Input Validation
1. **Never Trust Input:** Validate all incoming data against strict schemas (Zod/Joi). 
2. **Acceptance Alignment:** Strictly cross-reference acceptance criteria from the story file before implementation to ensure all functional requirements and edge cases are addressed.
3. **Output Encoding:** Context-aware encoding to prevent XSS/Injection vulnerabilities.

## Workspace & Dependency Management
- **Dependency Safety:** Verify that all external modules are listed in `package.json` before importing. Always use relative paths for local module resolutions.
- **Persistence:** Never delete, move, or modify critical project configuration files (e.g., `package.json`, `.gitignore`, `.gemini/GEMINI.md`) unless explicitly instructed.

## Secrets Management
- Use environment variables or Vault; never hardcode secrets or API keys.
- Rotate keys automatically and ensure they are never committed to the repository.