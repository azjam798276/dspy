---
name: dashboard-developer
description: React Dashboard Developer for VDI Session Management with GraphQL
---



---
name: dashboard-developer
description: Expert in building React-based VDI dashboards using qlkube for GraphQL interactions with Kubernetes CRDs.
---

# Dashboard Development: React + qlkube GraphQL Integration

## Core Principles
1. **Real-Time Updates:** Use GraphQL subscriptions for live session status.
2. **Optimistic UI:** Update UI immediately, rollback on mutation failure.
3. **OIDC Integration:** Handle auth tokens transparently; refresh before expiry.
4. **Responsive Design:** Support desktop and tablet form factors.

## Technology Stack
- **Frontend:** React 18 + TypeScript
- **State:** React Query (TanStack Query) for server state
- **GraphQL:** Apollo Client or urql
- **API Gateway:** qlkube (K8s API → GraphQL)
- **Auth:** OIDC via Keycloak/Dex

## qlkube Query Patterns
```graphql
# List user's sessions
query GetMySessions($user: String!) {
  vdisessions(namespace: "vdi", labelSelector: {user: $user}) {
    metadata { name, creationTimestamp }
    spec { template, resources { gpu, memory } }
    status { phase, url, podName }
  }
}

# Create new session
mutation CreateSession($input: VDISessionInput!) {
  createVDISession(input: $input) {
    metadata { name }
    status { url }
  }
}

# Subscribe to status changes
subscription WatchSession($name: String!) {
  watchVDISession(name: $name) {
    status { phase, url, message }
  }
}
```

## Component Architecture
```
App
├── AuthProvider (OIDC context)
├── QueryProvider (React Query)
├── Layout
│   ├── Header (user info, logout)
│   ├── Sidebar (template list)
│   └── Main
│       ├── SessionList (active sessions)
│       ├── SessionCard (status, controls)
│       └── LaunchModal (template selection)
```

## Session Card Component
```tsx
interface SessionCardProps {
  session: VDISession;
  onTerminate: () => void;
}

const SessionCard: React.FC<SessionCardProps> = ({ session, onTerminate }) => {
  const phaseColor = {
    Running: 'green',
    Pending: 'yellow',
    Creating: 'blue',
    Failed: 'red',
  }[session.status.phase];

  return (
    <Card>
      <Badge color={phaseColor}>{session.status.phase}</Badge>
      <Text>{session.spec.template}</Text>
      {session.status.url && (
        <Button as="a" href={session.status.url} target="_blank">
          Connect
        </Button>
      )}
      <Button variant="danger" onClick={onTerminate}>
        Terminate
      </Button>
    </Card>
  );
};
```

## Authentication Flow
```typescript
// OIDC configuration
const oidcConfig = {
  authority: 'https://keycloak.example.com/realms/vdi',
  client_id: 'vdi-dashboard',
  redirect_uri: window.location.origin + '/callback',
  scope: 'openid profile email',
};

// Attach token to GraphQL requests
const authLink = setContext((_, { headers }) => ({
  headers: {
    ...headers,
    authorization: `Bearer ${getAccessToken()}`,
  },
}));
```

## Error Handling
```tsx
const { data, error, isLoading } = useQuery('sessions', fetchSessions);

if (error?.status === 401) {
  // Token expired, trigger refresh
  return <RedirectToLogin />;
}

if (error?.status === 403) {
  return <AccessDenied />;
}
```

## Template Selection UI
- Display available VDITemplates with icons
- Show resource requirements (GPU, memory)
- Estimate queue position if resources exhausted
- Disable launch if user quota exceeded

## Responsive Breakpoints
```css
/* Mobile first */
.session-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

 @media (min-width: 768px) {
  .session-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

 @media (min-width: 1200px) {
  .session-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

## Performance Targets
| Metric | Threshold |
|--------|-----------|
| Initial load | < 2s |
| Session list refresh | < 500ms |
| Launch to URL | < 30s |
| Status update | Real-time |

## Accessibility
- All interactive elements keyboard accessible
- ARIA labels for session status
- Color-blind safe status indicators
- Screen reader announcements for phase changes