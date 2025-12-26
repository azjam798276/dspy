# Architectural Decision Patterns

## Governance
1. **Trade-off Analysis:** Document decision matrices (CAP theorem, Time vs Space).
2. **Scalability:** Design for horizontal scaling and statelessness.
3. **Maintainability:** Enforce modularity and separation of concerns.

## Review Standards
- Reject complexity without justification.
- Enforce observability integration.

## Optimization Strategy
- Refined based on feedback: Prioritize system stability over micro-optimizations.

# React Architecture Patterns

## Component Composition
1. **Composition over Inheritance:** Use props.children for layout wrappers.
2. **Container/Presentational:** Separate data fetching from rendering logic.

## State Management
- Lift state up only as far as needed.
- Use Context for global themes/auth only, avoid prop drilling.

# Security Architecture Patterns
## Threat Modeling
1. **STRIDE Analysis:** Perform per-component threat modeling during design.
2. **Defense in Depth:** Multiple layered controls (e.g., WAF + App Auth + DB Firewall).

## Governance
- Enforce "Secure by Design" principles in all ADRs.
- Require security reviews for any PI handling changes.