import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  test('should handle feature creation API flow', async ({ page }) => {
    // Mock successful API response
    await page.route('**/api/v1/features', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 123,
            title: 'Test Feature',
            description: 'Test Description',
            status: 'pending',
            created_at: new Date().toISOString()
          })
        });
      }
    });

    // Mock GET request for features list
    await page.route('**/api/v1/features', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 123,
              title: 'Test Feature',
              description: 'Test Description',
              status: 'pending',
              created_at: new Date().toISOString()
            }
          ])
        });
      }
    });

    await page.goto('/features');
    
    // Create new feature
    await page.click('[data-testid="create-feature-btn"]');
    await page.fill('[data-testid="feature-title-input"]', 'Test Feature');
    await page.fill('[data-testid="feature-description-textarea"]', 'Test Description');
    await page.click('[data-testid="submit-feature-btn"]');

    // Verify feature appears in list
    await expect(page.locator('[data-testid="feature-item"]')).toContainText('Test Feature');
  });

  test('should handle API rate limiting', async ({ page }) => {
    // Mock rate limit response
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Rate limit exceeded',
          retry_after: 60
        })
      });
    });

    await page.goto('/features');
    
    // Verify rate limit handling
    await expect(page.locator('[data-testid="rate-limit-message"]')).toBeVisible();
  });

  test('should handle network timeouts', async ({ page }) => {
    // Mock timeout
    await page.route('**/api/v1/**', async route => {
      // Delay response to simulate timeout
      await new Promise(resolve => setTimeout(resolve, 35000));
      await route.fulfill({ status: 200, body: '{}' });
    });

    await page.goto('/features');
    
    // Verify timeout handling (should show loading state initially, then error)
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    await expect(page.locator('[data-testid="timeout-error"]')).toBeVisible({ timeout: 40000 });
  });

  test('should handle malformed API responses', async ({ page }) => {
    // Mock malformed JSON response
    await page.route('**/api/v1/features', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'invalid json content'
      });
    });

    await page.goto('/features');
    
    // Verify error handling for malformed responses
    await expect(page.locator('[data-testid="parse-error"]')).toBeVisible();
  });

  test('should retry failed requests', async ({ page }) => {
    let requestCount = 0;
    
    // Mock failing requests that succeed on retry
    await page.route('**/api/v1/features', route => {
      requestCount++;
      
      if (requestCount === 1) {
        // First request fails
        route.fulfill({ status: 500, body: 'Server Error' });
      } else {
        // Subsequent requests succeed
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([])
        });
      }
    });

    await page.goto('/features');
    
    // Wait for retry mechanism to work
    await page.waitForTimeout(2000);
    
    // Verify that data loads after retry
    await expect(page.locator('[data-testid="features-list"]')).toBeVisible();
    expect(requestCount).toBeGreaterThan(1);
  });

  test('should handle concurrent API requests', async ({ page }) => {
    let requestCount = 0;
    
    // Track concurrent requests
    await page.route('**/api/v1/**', async route => {
      requestCount++;
      
      // Add delay to simulate real API
      await new Promise(resolve => setTimeout(resolve, 100));
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([])
      });
    });

    await page.goto('/');
    
    // Navigate to multiple pages quickly to trigger concurrent requests
    await page.click('[data-testid="nav-features"]');
    await page.click('[data-testid="nav-tasks"]');
    await page.click('[data-testid="nav-runs"]');
    
    // Wait for requests to complete
    await page.waitForTimeout(1000);
    
    // Verify requests were made
    expect(requestCount).toBeGreaterThan(2);
  });

  test('should handle authentication errors', async ({ page }) => {
    // Mock authentication failure
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Unauthorized',
          message: 'Authentication required'
        })
      });
    });

    await page.goto('/features');
    
    // Verify authentication error handling
    await expect(page.locator('[data-testid="auth-error"]')).toBeVisible();
  });

  test('should handle server maintenance mode', async ({ page }) => {
    // Mock maintenance mode
    await page.route('**/api/v1/**', route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Service Unavailable',
          message: 'System is under maintenance'
        })
      });
    });

    await page.goto('/');
    
    // Verify maintenance mode handling
    await expect(page.locator('[data-testid="maintenance-notice"]')).toBeVisible();
  });
});