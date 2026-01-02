---
id: "20260102_launch_session"
difficulty: "medium"
tags: ["dashboard", "react", "mutation", "graphql", "modal"]
tech_stack: "React 18, TypeScript, Apollo Client"
---

# User Story
As an end user, I want to launch a new VDI session by selecting a template, so I can start a GPU-accelerated desktop.

# Context & Constraints
**GraphQL Mutation:**
```graphql
mutation CreateSession($input: VDISessionInput!) {
  createVDISession(input: $input) {
    metadata { name }
    status { phase, url }
  }
}

input VDISessionInput {
  user: String!
  template: String!
  resources: ResourceInput
}
```

**Template Query:**
```graphql
query GetTemplates {
  vditemplates {
    metadata { name }
    spec { displayName, description, image, resources { defaultGPU, defaultMemory } }
  }
}
```

**Launch Flow:**
1. User clicks "New Session"
2. Modal shows available templates
3. User selects template
4. Mutation creates VDISession
5. Redirect to session list (session shows as Pending)

# Acceptance Criteria
- [ ] **Modal:** Open template selection modal
- [ ] **Templates:** Display VDITemplates with displayName, description
- [ ] **Select:** Highlight selected template
- [ ] **Create:** Call createVDISession mutation on confirm
- [ ] **Loading:** Show spinner during creation
- [ ] **Error:** Display error toast on failure
- [ ] **Redirect:** Navigate to session list on success
