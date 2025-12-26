---
id: "prop_drilling_golden"
source_story: "stories/react/20251225_react_context_prop_drilling.story.md"
tags: ["react", "context", "hooks", "refactoring", "typescript"]
---

## Problem

Refactor 7-level prop drilling anti-pattern to Context + Custom Hooks.
Current structure passes `user` and `theme` through every component:
App → Layout → Sidebar → Navigation → Menu → Button → Icon

## Solution

// path: src/contexts/UserContext.tsx
import React, { createContext, useContext, useState, ReactNode } from 'react';

interface User { id: string; name: string; email: string; }
interface Theme { primaryColor: string; fontSize: string; }

const UserContext = createContext<User | null>(null);

export const UserProvider = ({ children }: { children: ReactNode }) => {
const [user, setUser] = useState<User | null>(null);

return (
<UserContext.Provider value={user}>
{children}
</UserContext.Provider>
);
};

// Custom hook with error boundary
export const useUser = (): User => {
const context = useContext(UserContext);
if (context === null) {
throw new Error('useUser must be used within a UserProvider');
}
return context;
};

text
undefined
// path: src/contexts/ThemeContext.tsx
const ThemeContext = createContext<Theme | null>(null);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
const [theme, setTheme] = useState<Theme>({
primaryColor: '#007bff',
fontSize: '16px'
});

return (
<ThemeContext.Provider value={theme}>
{children}
</ThemeContext.Provider>
);
};

export const useTheme = (): Theme => {
const context = useContext(ThemeContext);
if (context === null) {
throw new Error('useTheme must be used within a ThemeProvider');
}
return context;
};

text
undefined
// path: src/components/ActionButton.tsx (NO MORE PROP DRILLING!)
import React from 'react';
import { useUser } from '../contexts/UserContext';
import { useTheme } from '../contexts/ThemeContext';

const ActionButton = React.memo(() => {
const user = useUser();
const theme = useTheme();

return (
<button
style={{
color: theme.primaryColor,
fontSize: theme.fontSize
}}
>
Welcome, {user.name}!
</button>
);
});

export default ActionButton;

text
undefined
// path: src/App.tsx (Providers wrap entire tree)
function App() {
return (
<UserProvider>
<ThemeProvider>
<Layout>
<Sidebar>
<Navigation>
<ActionButton />
</Navigation>
</Sidebar>
</Layout>
</ThemeProvider>
</UserProvider>
);
}

text

## Key Techniques
- **Split Contexts**: User changes don't re-render Theme consumers
- **Custom Hooks**: `useUser()`, `useTheme()` with error boundaries
- **Zero Prop Drilling**: Deep components consume context directly
- **React.memo()**: Prevents unnecessary re-renders
