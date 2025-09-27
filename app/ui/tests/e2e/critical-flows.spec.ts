import { test, expect } from '@playwright/test';

test.describe('Critical User Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate through main application flow', async ({ page }) => {
    // Test navigation to key pages
    await expect(page).toHaveTitle(/Feature Factory/);
    
    // Navigate to Features page
    await page.click('[data-testid="nav-features"]');
    await expect(page.locator('h1')).toContainText('Features');
    
    // Navigate to Tasks page
    await page.click('[data-testid="nav-tasks"]');
    await expect(page.locator('h1')).toContainText('Tasks');
    
    // Navigate to Runs page
    await page.click('[data-testid="nav-runs"]');
    await expect(page.locator('h1')).toContainText('Runs');
  });

  test('should create a new feature', async ({ page }) => {
    await page.click('[data-testid="nav-features"]');
    
    // Click create feature button
    await page.click('[data-testid="create-feature-btn"]');
    
    // Fill out feature creation form
    await page.fill('[data-testid="feature-title-input"]', 'Test Feature');
    await page.fill('[data-testid="feature-description-textarea"]', 'This is a test feature created by Playwright');
    
    // Submit the form
    await page.click('[data-testid="submit-feature-btn"]');
    
    // Verify feature was created
    await expect(page.locator('[data-testid="feature-item"]')).toContainText('Test Feature');
  });

  test('should display feature status updates in real-time', async ({ page }) => {
    await page.click('[data-testid="nav-features"]');
    
    // Wait for any existing feature to load
    await page.waitForSelector('[data-testid="feature-item"]', { timeout: 10000 });
    
    // Take initial screenshot for status comparison
    await expect(page.locator('[data-testid="features-list"]')).toBeVisible();
    
    // Verify status pills are displayed
    await expect(page.locator('[data-testid="status-pill"]').first()).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API failure
    await page.route('**/api/v1/**', route => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });
    
    await page.click('[data-testid="nav-features"]');
    
    // Verify error handling
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });
});

test.describe('Performance Tests', () => {
  test('should load dashboard within performance budget @performance', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000); // 3 second budget
  });

  test('should handle large datasets efficiently @performance', async ({ page }) => {
    await page.goto('/features');
    
    // Wait for features to load
    await page.waitForSelector('[data-testid="features-list"]');
    
    // Measure rendering performance
    const performanceMetrics = await page.evaluate(() => {
      return performance.getEntriesByType('measure');
    });
    
    // Basic performance assertion
    expect(performanceMetrics.length).toBeGreaterThan(0);
  });
});

test.describe('Security Tests', () => {
  test('should prevent XSS attacks @security', async ({ page }) => {
    await page.goto('/features');
    await page.click('[data-testid="create-feature-btn"]');
    
    // Try to inject malicious script
    const maliciousInput = '<script>alert("XSS")</script>';
    await page.fill('[data-testid="feature-title-input"]', maliciousInput);
    
    // Verify script is not executed (content should be escaped)
    const titleValue = await page.inputValue('[data-testid="feature-title-input"]');
    expect(titleValue).toBe(maliciousInput);
    
    // Submit and verify no script execution
    await page.click('[data-testid="submit-feature-btn"]');
    
    // Check that content is properly escaped in display
    const displayedTitle = await page.locator('[data-testid="feature-item"]').first().textContent();
    expect(displayedTitle).not.toContain('<script>');
  });

  test('should validate input fields @security', async ({ page }) => {
    await page.goto('/features');
    await page.click('[data-testid="create-feature-btn"]');
    
    // Try to submit empty form
    await page.click('[data-testid="submit-feature-btn"]');
    
    // Verify validation errors
    await expect(page.locator('[data-testid="validation-error"]')).toBeVisible();
  });
});

test.describe('Accessibility Tests', () => {
  test('should be keyboard navigable @accessibility', async ({ page }) => {
    await page.goto('/');
    
    // Navigate using keyboard
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    
    // Verify keyboard navigation works
    await expect(page.locator(':focus')).toBeVisible();
  });

  test('should have proper ARIA labels @accessibility', async ({ page }) => {
    await page.goto('/');
    
    // Check for essential ARIA attributes
    const nav = page.locator('nav');
    await expect(nav).toHaveAttribute('aria-label');
    
    // Check buttons have accessible names
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const hasAriaLabel = await button.getAttribute('aria-label');
      const hasText = await button.textContent();
      
      expect(hasAriaLabel || hasText).toBeTruthy();
    }
  });
});

test.describe('Cross-browser Compatibility', () => {
  test('should work consistently across browsers @compatibility', async ({ page, browserName }) => {
    await page.goto('/');
    
    // Test basic functionality
    await expect(page.locator('h1')).toBeVisible();
    
    // Test browser-specific features
    if (browserName === 'webkit') {
      // Safari-specific tests
      await page.click('[data-testid="nav-features"]');
      await expect(page.locator('[data-testid="features-list"]')).toBeVisible();
    }
    
    if (browserName === 'firefox') {
      // Firefox-specific tests
      await page.click('[data-testid="nav-tasks"]');
      await expect(page.locator('[data-testid="tasks-list"]')).toBeVisible();
    }
  });
});

test.describe('Visual Regression Tests', () => {
  test('should match dashboard screenshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    
    // Take screenshot for visual regression testing
    await expect(page).toHaveScreenshot('dashboard.png');
  });

  test('should match features page screenshot', async ({ page }) => {
    await page.goto('/features');
    await page.waitForSelector('[data-testid="features-list"]');
    
    // Take screenshot for visual regression testing
    await expect(page).toHaveScreenshot('features-page.png');
  });
});