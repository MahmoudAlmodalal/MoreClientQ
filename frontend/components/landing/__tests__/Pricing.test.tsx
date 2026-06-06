/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Pricing from '../Pricing';

describe('Pricing Component', () => {
  it('renders all 4 pricing tiers with headings', () => {
    render(<Pricing />);

    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
    expect(screen.getByText('Business')).toBeInTheDocument();
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
  });

  it('renders CTAs with correct redirection links and test IDs', () => {
    render(<Pricing />);

    const starterCta = screen.getByTestId('pricing-cta-starter');
    const proCta = screen.getByTestId('pricing-cta-pro');
    const businessCta = screen.getByTestId('pricing-cta-business');
    const enterpriseCta = screen.getByTestId('pricing-cta-enterprise');

    expect(starterCta).toBeInTheDocument();
    expect(starterCta).toHaveAttribute('href', '/register?plan=starter');

    expect(proCta).toBeInTheDocument();
    expect(proCta).toHaveAttribute('href', '/register?plan=pro');

    expect(businessCta).toBeInTheDocument();
    expect(businessCta).toHaveAttribute('href', '/register?plan=business');

    expect(enterpriseCta).toBeInTheDocument();
    expect(enterpriseCta).toHaveAttribute('href', '/contact');
  });
});
