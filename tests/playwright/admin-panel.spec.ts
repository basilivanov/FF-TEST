// tests/playwright/admin-panel.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Admin Panel', () => {
  test('should display dashboard with features, tasks, and runs', async ({ page }) => {
    // Navigate to the dashboard
    await page.goto('/')
    
    // Check if dashboard elements are present
    await expect(page.getByText('System Health')).toBeVisible()
    await expect(page.getByText('Backlog')).toBeVisible()
    await expect(page.getByText('Runs')).toBeVisible()
    await expect(page.getByText('LLM Budgets')).toBeVisible()
    await expect(page.getByText('Errors')).toBeVisible()
    await expect(page.getByText('Docs')).toBeVisible()
  })
  
  test('should display features list', async ({ page }) => {
    // Navigate to features page
    await page.goto('/features')
    
    // Check if features table is present
    await expect(page.getByText('Features')).toBeVisible()
    await expect(page.getByRole('table')).toBeVisible()
    
    // Check if at least one feature is displayed (we assume there's at least one feature in the DB)
    // This test might need to be adjusted based on the actual data in the DB
    // For now, we just check if the table structure is correct
    const table = page.getByRole('table')
    await expect(table.getByRole('row').first()).toBeVisible()
  })
  
  test('should display tasks list', async ({ page }) => {
    // Navigate to tasks page
    await page.goto('/tasks')
    
    // Check if tasks table is present
    await expect(page.getByText('Tasks')).toBeVisible()
    await expect(page.getByRole('table')).toBeVisible()
    
    // Check if at least one task is displayed (we assume there's at least one task in the DB)
    const table = page.getByRole('table')
    await expect(table.getByRole('row').first()).toBeVisible()
  })
  
  test('should display runs list', async ({ page }) => {
    // Navigate to runs page
    await page.goto('/runs')
    
    // Check if runs table is present
    await expect(page.getByText('Runs')).toBeVisible()
    await expect(page.getByRole('table')).toBeVisible()
    
    // Check if at least one run is displayed (we assume there's at least one run in the DB)
    const table = page.getByRole('table')
    await expect(table.getByRole('row').first()).toBeVisible()
  })
  
  test('should display logs with SSE streaming', async ({ page }) => {
    // Navigate to logs page
    await page.goto('/logs')
    
    // Check if logs viewer is present
    await expect(page.getByText('Logs')).toBeVisible()
    await expect(page.getByText('Поток логов в реальном времени с фильтрацией')).toBeVisible()
    
    // Check if SSE connection is established and logs are streaming
    // This is a bit tricky to test, as it depends on the SSE server
    // We can check if the "Пауза" button is present, which indicates that streaming is active
    await expect(page.getByText('Пауза')).toBeVisible()
  })
  
  test('should display chat pane', async ({ page }) => {
    // Navigate to chat page
    await page.goto('/chat')
    
    // Check if chat pane is present
    await expect(page.getByText('Chat')).toBeVisible()
    await expect(page.getByPlaceholder('Введите команду или вопрос...')).toBeVisible()
  })
})