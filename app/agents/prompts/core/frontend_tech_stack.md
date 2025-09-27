# Frontend Technology Stack

## Core Frontend Stack
- **React 18** with TypeScript and modern hooks
- **Vite** for build tooling and dev server  
- **Tailwind CSS** for styling with custom configurations
- **Shadcn/ui** component library for consistent UI patterns
- **Zustand** for state management (lightweight alternative to Redux)
- **TanStack Query** for server state management and caching
- **React Router v6** for client-side routing

## Testing Stack (3-Layer Pyramid)

### Layer 1: Unit/Component Tests (70% - Jest + Testing Library)
- **Jest** with jsdom environment for unit testing
- **React Testing Library** for component testing (behavior-focused)
- **@testing-library/user-event** for realistic user interactions  
- **Coverage threshold: 80%** across branches, functions, lines, statements
- **Fast feedback loop** - runs in < 500ms for individual tests

### Layer 2: Integration Tests (20% - Playwright Component)  
- **Playwright Component Testing** for complex component interactions
- **API mocking** with MSW (Mock Service Worker) patterns
- **Cross-component data flow** testing
- **Real DOM rendering** with actual browser engines

### Layer 3: E2E Tests (10% - Playwright)
- **Playwright** for full end-to-end workflows
- **Cross-browser testing**: Chromium, Firefox, WebKit
- **Mobile testing**: Pixel 5, iPhone 12 simulation
- **Visual regression testing** with screenshot comparison
- **Performance budgets** and accessibility testing

## Build and Development Tools
- **TypeScript 5.0+** with strict mode enabled
- **ESLint** with React hooks and TypeScript rules
- **Prettier** (implied through ESLint integration)
- **PostCSS** with Autoprefixer for CSS processing

## Testing Data and Fixtures
- **Structured test data** in `tests/fixtures/`
- **API response mocking** with realistic data shapes
- **Error simulation** for edge case testing
- **Performance measurement** utilities

## Browser Support Matrix
- **Primary**: Chrome/Chromium (latest 2 versions)
- **Secondary**: Firefox, Safari/WebKit (latest version)  
- **Mobile**: iOS Safari, Android Chrome
- **Accessibility**: WCAG 2.1 AA compliance testing

## Performance Standards
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Time to Interactive**: < 3s
- **Bundle size**: Main bundle < 500KB gzipped
- **Component render time**: < 16ms (60fps standard)

## File Structure Conventions
```
app/ui/
├── src/
│   ├── components/          # Reusable components
│   ├── pages/              # Route-level components  
│   ├── shadcn/ui/          # Shadcn component library
│   ├── hooks/              # Custom React hooks
│   ├── services/           # API layer and utilities
│   └── types/              # TypeScript type definitions
├── tests/
│   ├── e2e/               # Playwright E2E tests
│   ├── fixtures/          # Test data and mocks
│   └── __tests__/         # Jest unit tests (co-located)
└── public/                # Static assets
```

## Data Attributes for Testing
- **data-testid**: Primary selector for test automation
- **aria-label**: Accessibility and semantic testing
- **role**: ARIA roles for screen reader testing
- Avoid using CSS classes or DOM structure for test selectors