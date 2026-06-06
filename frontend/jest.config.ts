import type { Config } from "jest";

const config: Config = {
  testEnvironment: "node",
  transform: {
    "^.+\\.tsx?$": ["ts-jest", { tsconfig: { module: "commonjs", jsx: "react-jsx" } }],
  },
  testMatch: [
    "**/tests/**/*.test.ts",
    "**/tests/**/*.test.tsx",
    "**/__tests__/**/*.test.ts",
    "**/__tests__/**/*.test.tsx"
  ],
  moduleNameMapper: {
    // Map Next.js server imports to no-ops for unit testing
    "^next/server$": "<rootDir>/tests/__mocks__/next-server.ts",
  },
  extensionsToTreatAsEsm: [],
  clearMocks: true,
};

export default config;
