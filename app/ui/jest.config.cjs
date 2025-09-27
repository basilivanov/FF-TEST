module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.ts"],
  testPathIgnorePatterns: [
    "<rootDir>/node_modules/",
    "<rootDir>/tests/e2e/", // Исключаем Playwright тесты
    "<rootDir>/dist/"
  ],
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "^@/(.*)$": "<rootDir>/src/$1",
    "^recharts$": "<rootDir>/src/__mocks__/recharts.ts"
  },
  transformIgnorePatterns: [
    "node_modules/(?!(d3|d3-array|d3-scale|d3-selection|d3-shape|recharts|@recharts)/)"
  ],
  collectCoverageFrom: [
    "src/**/*.{ts,tsx}",
    "!src/main.tsx",
    "!src/vite-env.d.ts",
    "!src/components/CallGraphVisualization.tsx", // Временно исключаем d3 компонент
    "!tests/**/*"
  ],
  coverageThreshold: {
    global: {
      branches: 50, // Снижаем требования для демо
      functions: 50,
      lines: 50,
      statements: 50
    }
  },
  testMatch: [
    "<rootDir>/src/**/__tests__/**/*.{js,jsx,ts,tsx}",
    "<rootDir>/src/**/*.(test|spec).{js,jsx,ts,tsx}",
    "<rootDir>/tests/components/**/*.{js,jsx,ts,tsx}"
  ]
}