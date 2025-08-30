/* Dependency-Cruiser config for Feature Factory UI */
module.exports = {
  forbidden: [
    // no rules enforced at the moment; this file enables config-based resolution
  ],
  options: {
    includeOnly: '^src',
    exclude: {
      path: [
        'node_modules',
        'dist',
        'build',
        '\\.(spec|test)\\.(ts|tsx|js|jsx)$',
        '__tests__'
      ]
    },
    doNotFollow: {
      path: 'node_modules'
    },
    enhancedResolveOptions: {
      extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
      conditionNames: ['import', 'require', 'node']
    },
    tsConfig: {
      fileName: 'tsconfig.json'
    }
  }
};

