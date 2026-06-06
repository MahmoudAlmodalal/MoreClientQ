import { test, expect } from '@playwright/test';

test.describe('Navigation and Redirection Flows', () => {
  test('sticky top navigation and footer sitemap links work', async ({ page }) => {
    await page.goto('/');

    // Check sticky Nav elements
    const navLogo = page.locator('[data-testid="nav-logo"]');
    const featuresLink = page.locator('[data-testid="nav-link-features"]');
    const pricingLink = page.locator('[data-testid="nav-link-pricing"]');
    const docsLink = page.locator('[data-testid="nav-link-docs"]');
    const loginLink = page.locator('[data-testid="nav-link-login"]');
    const registerCta = page.locator('[data-testid="nav-cta-register"]');

    await expect(navLogo).toBeVisible();
    await expect(featuresLink).toBeVisible();
    await expect(pricingLink).toBeVisible();
    await expect(docsLink).toBeVisible();
    await expect(loginLink).toBeVisible();
    await expect(registerCta).toBeVisible();

    // Check anchors & href attributes
    await expect(featuresLink).toHaveAttribute('href', '#features');
    await expect(pricingLink).toHaveAttribute('href', '#pricing');
    await expect(docsLink).toHaveAttribute('href', 'https://docs.example.com');
    await expect(loginLink).toHaveAttribute('href', '/login');
    await expect(registerCta).toHaveAttribute('href', '/register');

    // Check Footer sitemap links
    const footerDocsLink = page.locator('[data-testid="footer-link-docs"]');
    const footerPrivacyLink = page.locator('[data-testid="footer-link-privacy"]');
    
    await expect(footerDocsLink).toBeVisible();
    await expect(footerDocsLink).toHaveAttribute('href', 'https://docs.example.com');
    await expect(footerPrivacyLink).toBeVisible();
    await expect(footerPrivacyLink).toHaveAttribute('href', '/privacy');
  });
});
