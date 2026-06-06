/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import FooterCta from '../FooterCta';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

describe('FooterCta Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input, button and heading', () => {
    render(<FooterCta />);
    
    expect(screen.getByText(/Ready to scale your customer support/i)).toBeInTheDocument();
    expect(screen.getByTestId('footer-cta-email-input')).toBeInTheDocument();
    expect(screen.getByTestId('footer-cta-submit-btn')).toBeInTheDocument();
  });

  it('displays validation error for empty or invalid email', () => {
    render(<FooterCta />);
    
    const input = screen.getByTestId('footer-cta-email-input');
    const button = screen.getByTestId('footer-cta-submit-btn');

    // Test empty submit
    fireEvent.click(button);
    expect(screen.getByTestId('footer-cta-error')).toHaveTextContent(/Please enter a valid email address/i);
    expect(mockPush).not.toHaveBeenCalled();

    // Test invalid format
    fireEvent.change(input, { target: { value: 'invalid-email' } });
    fireEvent.click(button);
    expect(screen.getByTestId('footer-cta-error')).toHaveTextContent(/Please enter a valid email address/i);
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('redirects to register page with query parameters on successful submit', () => {
    render(<FooterCta />);
    
    const input = screen.getByTestId('footer-cta-email-input');
    const button = screen.getByTestId('footer-cta-submit-btn');

    fireEvent.change(input, { target: { value: 'user@example.com' } });
    fireEvent.click(button);

    expect(screen.queryByTestId('footer-cta-error')).not.toBeInTheDocument();
    expect(mockPush).toHaveBeenCalledWith('/register?email=user%40example.com&source=footer');
  });
});
