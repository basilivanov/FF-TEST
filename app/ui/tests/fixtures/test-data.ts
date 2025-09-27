export const mockFeature = {
  id: 1,
  title: "Sample Feature",
  description: "This is a sample feature for testing",
  status: "pending" as const,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  user_id: "test-user",
  priority: "medium" as const,
  tags: ["test", "sample"]
};

export const mockFeatures = [
  mockFeature,
  {
    id: 2,
    title: "Another Feature",
    description: "Another feature for testing lists",
    status: "in_progress" as const,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
    user_id: "test-user",
    priority: "high" as const,
    tags: ["important"]
  },
  {
    id: 3,
    title: "Completed Feature",
    description: "A completed feature",
    status: "completed" as const,
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-03T12:00:00Z",
    user_id: "test-user",
    priority: "low" as const,
    tags: ["done", "archived"]
  }
];

export const mockTask = {
  id: "task-1",
  feature_id: 1,
  title: "Implement API endpoint",
  description: "Create REST API endpoint for feature",
  status: "pending" as const,
  agent_type: "developer" as const,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  dependencies: [] as string[],
  files: ["app/api/endpoint.py"],
  dod: ["Endpoint responds correctly", "Tests pass"]
};

export const mockTasks = [
  mockTask,
  {
    id: "task-2",
    feature_id: 1,
    title: "Write tests",
    description: "Create comprehensive test suite",
    status: "in_progress" as const,
    agent_type: "validator" as const,
    created_at: "2024-01-01T01:00:00Z",
    updated_at: "2024-01-01T02:00:00Z",
    dependencies: ["task-1"],
    files: ["tests/test_endpoint.py"],
    dod: ["Tests pass", "Coverage ≥70%"]
  }
];

export const mockRun = {
  id: "run-1",
  feature_id: 1,
  status: "running" as const,
  started_at: "2024-01-01T00:00:00Z",
  completed_at: null,
  tasks_completed: 1,
  tasks_total: 3,
  current_task: "task-2",
  logs: [
    {
      timestamp: "2024-01-01T00:00:00Z",
      level: "info",
      message: "Started feature development",
      agent: "orchestrator"
    }
  ]
};

export const mockTokenBudget = {
  role: "developer",
  daily_limit: 100000,
  used: 45000,
  remaining: 55000,
  reset_time: "2024-01-02T00:00:00Z",
  provider: "openai"
};

export const mockApiResponses = {
  features: {
    list: mockFeatures,
    create: mockFeature,
    get: mockFeature
  },
  tasks: {
    list: mockTasks,
    get: mockTask
  },
  runs: {
    list: [mockRun],
    get: mockRun
  },
  tokens: {
    budget: mockTokenBudget
  }
};

// Utility function to create API route handlers
export const createApiHandler = (endpoint: string, data: any) => {
  return (route: any) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  };
};

// Error response templates
export const apiErrors = {
  notFound: {
    status: 404,
    body: JSON.stringify({ error: "Not Found", message: "Resource not found" })
  },
  serverError: {
    status: 500,
    body: JSON.stringify({ error: "Internal Server Error", message: "Something went wrong" })
  },
  unauthorized: {
    status: 401,
    body: JSON.stringify({ error: "Unauthorized", message: "Authentication required" })
  },
  rateLimited: {
    status: 429,
    body: JSON.stringify({ error: "Rate Limited", message: "Too many requests" })
  },
  badRequest: {
    status: 400,
    body: JSON.stringify({ error: "Bad Request", message: "Invalid request data" })
  }
};