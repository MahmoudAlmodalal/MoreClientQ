import { test, expect } from '@playwright/test';

test.describe('Live Demo Chat Widget', () => {
  test('streams response and counts messages up to 5-message limit', async ({ page }) => {
    // 1. Visit landing page
    await page.goto('/');

    // 2. Mock success response for first message
    let chatRequestCount = 0;
    await page.route('**/api/v1/public/chat', async (route) => {
      chatRequestCount++;
      const reqBody = JSON.parse(route.request().postData() || '{}');
      expect(reqBody.message).toBe('Hello AI');
      expect(reqBody.session_id).toBeDefined();

      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'X-Accel-Buffering': 'no',
        },
        body: `data: {"type": "token", "content": "Hello! I am "}\n\ndata: {"type": "token", "content": "your assistant."}\n\ndata: {"type": "done", "message_count": ${chatRequestCount}}\n\n`,
      });
    });

    // Check that demo is visible
    const chatInput = page.locator('[data-testid="demo-chat-input"]');
    await expect(chatInput).toBeVisible();
    await expect(chatInput).toBeEnabled();

    // Send first message
    await chatInput.fill('Hello AI');
    await chatInput.press('Enter');

    // Verify message is sent and response streams in
    await expect(page.locator('text=Hello AI')).toBeVisible();
    await expect(page.locator('text=Hello! I am your assistant.')).toBeVisible();
    
    // Verify counter shows 1/5 messages
    await expect(page.locator('[data-testid="demo-counter"]')).toHaveText('1 / 5 messages');

    // Change route mock to simulate reaching the 5th message on subsequent calls
    await page.route('**/api/v1/public/chat', async (route) => {
      chatRequestCount++;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        headers: {
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
        body: `data: {"type": "token", "content": "This is message ${chatRequestCount}."}\n\ndata: {"type": "done", "message_count": ${chatRequestCount}}\n\n`,
      });
    });

    // Send 4 more messages to reach the cap
    for (let i = 2; i <= 5; i++) {
      await chatInput.fill('Hello AI');
      await chatInput.press('Enter');
      await expect(page.locator(`text=This is message ${i}.`)).toBeVisible();
      await expect(page.locator('[data-testid="demo-counter"]')).toHaveText(`${i} / 5 messages`);
    }

    // After 5 messages, the input should be disabled and the trial CTA should appear
    await expect(chatInput).toBeDisabled();
    const ctaButton = page.locator('[data-testid="demo-cta-trial"]');
    await expect(ctaButton).toBeVisible();
    await expect(ctaButton).toHaveAttribute('href', /.*\/register.*/);
  });

  test('gracefully handles 429 rate-limited quota exceeded', async ({ page }) => {
    await page.goto('/');

    await page.route('**/api/v1/public/chat', async (route) => {
      await route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'DEMO_QUOTA_EXCEEDED',
            message: 'You have reached the demo limit. Start your free trial to continue.',
            message_count: 5
          }
        })
      });
    });

    const chatInput = page.locator('[data-testid="demo-chat-input"]');
    await chatInput.fill('Let me in');
    await chatInput.press('Enter');

    // Check error message and input disabled
    await expect(page.locator('text=You have reached the demo limit.')).toBeVisible();
    await expect(chatInput).toBeDisabled();
    
    // Check trial CTA button
    const ctaButton = page.locator('[data-testid="demo-cta-trial"]');
    await expect(ctaButton).toBeVisible();
  });

  test('gracefully handles 503 service unavailable', async ({ page }) => {
    await page.goto('/');

    await page.route('**/api/v1/public/chat', async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'SERVICE_UNAVAILABLE',
            message: 'AI service temporarily unavailable. Please try again shortly.'
          }
        })
      });
    });

    const chatInput = page.locator('[data-testid="demo-chat-input"]');
    await chatInput.fill('Hello AI');
    await chatInput.press('Enter');

    // Check error fallback message
    await expect(page.locator('text=AI service temporarily unavailable')).toBeVisible();
    // Input should remain enabled for retries
    await expect(chatInput).toBeEnabled();
  });
});
