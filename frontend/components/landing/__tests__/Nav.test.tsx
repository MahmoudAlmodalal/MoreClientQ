/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Nav from '../Nav';

describe('Nav Component', () => {
  it('renders brand logo and desktop navigation links', () => {
    render(<Nav />);

    const logo = screen.getByTestId('nav-logo');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('href', '/');

    const featuresLink = screen.getByTestId('nav-link-features');
    expect(featuresLink).toBeInTheDocument();
    expect(featuresLink).toHaveAttribute('href', '#features');

    const pricingLink = screen.getByTestId('nav-link-pricing');
    expect(pricingLink).toBeInTheDocument();
    expect(pricingLink).toHaveAttribute('href', '#pricing');

    const docsLink = screen.getByTestId('nav-link-docs');
    expect(docsLink).toBeInTheDocument();
    expect(docsLink).toHaveAttribute('href', 'https://docs.example.com');
  });

  it('renders auth CTA links with correct paths', () => {
    render(<Nav />);

    const loginLink = screen.getByTestId('nav-link-login');
    expect(loginLink).toBeInTheDocument();
    expect(loginLink).toHaveAttribute('href', '/login');

    const registerCta = screen.getByTestId('nav-cta-register');
    expect(registerCta).toBeInTheDocument();
    expect(registerCta).toHaveAttribute('href', '/register');
  });
});
