---
name: dashboard-developer
description: Expert in building React-based VDI dashboards using qlkube for GraphQL interactions with Kubernetes CRDs (VDISession, VDITemplate).
---

# Dashboard Development: React + qlkube GraphQL Integration

## Core Principles
1. **Real-Time Visibility:** Implement 5-second polling (`pollInterval: 5000`) for session phase transitions to reflect Operator updates.
2. **Identity-Bound Filtering:** MANDATORY: Always filter `vdisessions` using `labelSelector: {user: currentUser.email}` to ensure multi-tenant isolation.
3. **Optimistic Feedback:** Show immediate loading spinners on mutations and skeleton loaders for initial data fetches.
4. **Resilient Connectivity:** Use the `status.url` field for the "Connect" button, only enabling it when `phase === 'Running'`.

## GraphQL Schema Operations
Utilize these exact patterns for `qlkube` interactions:

```graphql
# 1. Fetch user's active sessions
query GetMySessions($user: String!) {
  vdisessions(namespace: "vdi", labelSelector: {user: $user}) {
    metadata { name, creationTimestamp }
    spec { template, resources { gpu, memory } }
    status { phase, url, podName }
  }
}

# 2. Get templates for Launch Modal
query GetTemplates {
  vditemplates {
    metadata { name }
    spec { displayName, description, image, resources { defaultGPU, defaultMemory } }
  }
}

# 3. Launch Session Mutation
mutation CreateSession($input: VDISessionInput!) {
  createVDISession(input: $input) {
    metadata { name }
    status { phase, url }
  }
}

# 4. Terminate Session Mutation
mutation TerminateSession($name: String!) {
  deleteVDISession(name: $name) {
    metadata { name }
  }
}
```

## Component & State Architecture
- **State Management:** Use `Apollo Client` for GraphQL and `React Context` for OIDC User Identity.
- **SessionList:** Grid layout (CSS Grid) with 1/2/3 column breakpoints for Mobile/Tablet/Desktop.
- **SessionCard:** Must display:
  - **Header:** `session.spec.template` name.
  - **Badge:** Color-coded Phase (`Running`: Green, `Pending`: Yellow, `Failed`: Red).
  - **Details:** GPU (`spec.resources.gpu`), Memory (`spec.resources.memory`), and Age (calculated from `metadata.creationTimestamp`).
  - **Actions:** "Connect" (primary, external link) and "Terminate" (danger, calls mutation).

## Critical UI/UX Lifecycle
- **Launch Flow:** Modal Open -> Template Selection (with visual highlight) -> Confirm (show Spinner) -> Mutation -> Redirect to Dashboard on success.
- **Empty State:** If `vdisessions` is empty, show a "No active sessions" message with a primary "Launch Desktop" call-to-action.
- **Error Handling:** Use a Toast provider to display `error.message` for mutation failures (e.g., quota exceeded).

## Performance & Accessibility
- **Target:** Initial dashboard load < 2 seconds.
- **Accessibility:** Ensure all buttons have `aria-label` and use `aria-live` regions for status phase updates (e.g., "Session is now Running").
- **OIDC:** Inject the OIDC `access_token` into Apollo headers via `setContext` for every request.