---
id: "20260102_dashboard_session_list"
difficulty: "medium"
tags: ["dashboard", "react", "graphql", "qlkube", "ui"]
tech_stack: "React 18, TypeScript, Apollo Client, qlkube"
---

# User Story
As an end user, I want a dashboard showing my active VDI sessions with status and connect buttons, so I can manage my desktop sessions.

# Context & Constraints
**GraphQL Query:**
```graphql
query GetMySessions($user: String!) {
  vdisessions(namespace: "vdi", labelSelector: {user: $user}) {
    metadata { name, creationTimestamp }
    spec { template, resources { gpu, memory } }
    status { phase, url, podName }
  }
}
```

**Component Structure:**
```tsx
const SessionList: React.FC = () => {
  const { data, loading, error } = useQuery(GET_SESSIONS, {
    variables: { user: currentUser.email },
    pollInterval: 5000,
  });

  return (
    <div className="session-grid">
      {data.vdisessions.map(session => (
        <SessionCard key={session.metadata.name} session={session} />
      ))}
    </div>
  );
};
```

**Session Card:**
| Element | Content |
|---------|---------|
| Header | Template name |
| Badge | Phase (color-coded) |
| Details | GPU, Memory, Age |
| Actions | Connect, Terminate |

# Acceptance Criteria
- [ ] **Query:** Fetch sessions filtered by current user
- [ ] **Polling:** Refresh every 5 seconds for status updates
- [ ] **Card:** Display SessionCard with phase badge
- [ ] **Connect:** Button linking to session.status.url
- [ ] **Terminate:** Button calling deleteVDISession mutation
- [ ] **Empty:** Show "No sessions" message when empty
- [ ] **Loading:** Show skeleton loader during fetch
