---
id: "20251225_react_context_prop_drilling"
source_url: "https://www.connerbush.com/react-advanced-state-management-context-and-custom-hooks/"
difficulty: "hard"
tags: ["react", "architecture", "context", "hooks", "refactoring"]
tech_stack: "React 18, TypeScript, Jest, React Testing Library"
---

# User Story
As a developer, I want to refactor a deeply nested component tree suffering from "prop drilling hell" into a maintainable Context + Custom Hooks pattern, so that state management is scalable and components remain decoupled.

# Context & Constraints
The current codebase has a 7-level component hierarchy where `user` and `theme` props are passed through every layer:

```
App → Layout → Sidebar → Navigation → MenuItem → ActionButton → Icon
```

**Current Anti-Pattern:**
Every intermediate component receives and forwards props it doesn't use:
```javascript
<Layout user={user} theme={theme}>
  <Sidebar user={user} theme={theme}>
    <Navigation user={user} theme={theme}>
      {/* ...6 more levels */}
    </Navigation>
  </Sidebar>
</Layout>
```

**Requirements:**
- Create `UserContext` and `ThemeContext` with TypeScript interfaces
- Implement custom hooks: `useUser()` and `useTheme()`
- Enforce "must be used within Provider" error handling
- Refactor all 7 components to consume context directly
- Maintain 100% behavioral compatibility (no UI changes)

**Performance Constraint:**
- Use `React.memo()` to prevent unnecessary re-renders
- Split contexts to avoid re-rendering theme consumers when user changes

# Acceptance Criteria
- [ ] **Context Creation:** Define `UserContext` and `ThemeContext` with proper TypeScript types
- [ ] **Custom Hooks:** Implement `useUser()` and `useTheme()` with error throwing if used outside Provider scope
- [ ] **Refactoring:** Remove ALL prop drilling - intermediate components should not receive `user` or `theme` props
- [ ] **Error Handling:** Attempting to use `useUser()` outside `<UserProvider>` throws descriptive error
- [ ] **Performance Test:** Verify changing `theme` does NOT re-render components only consuming `user` (use React DevTools Profiler)
- [ ] **Test Coverage:** Achieve >90% coverage with tests for both happy path and error cases
- [ ] **Type Safety:** No TypeScript `any` types - full inference for context values
