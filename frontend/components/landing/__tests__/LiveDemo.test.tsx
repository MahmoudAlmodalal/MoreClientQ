/**
 * @jest-environment jsdom
 */
import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import LiveDemo from '../LiveDemo';
import { getDemoSession, sendDemoMessage } from '../../../lib/demo-chat';

// Mock the demo-chat module
jest.mock('../../../lib/demo-chat', () => ({
  getDemoSession: jest.fn(),
  sendDemoMessage: jest.fn(),
}));

const mockGetDemoSession = getDemoSession as jest.MockedFunction<typeof getDemoSession>;
const mockSendDemoMessage = sendDemoMessage as jest.MockedFunction<typeof sendDemoMessage>;

describe('LiveDemo Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Default mock implementation
    mockGetDemoSession.mockReturnValue({ sessionId: 'mock-session-id', messageCount: 0 });
  });

  it('renders initial assistant greeting and enabled input', () => {
    render(<LiveDemo />);
    
    // Checks greeting message
    expect(screen.getByText(/Hi there! I'm the platform's demo assistant/)).toBeInTheDocument();
    
    // Checks counter
    expect(screen.getByTestId('demo-counter')).toHaveTextContent('0 / 5 messages');
    
    // Checks input
    const input = screen.getByTestId('demo-chat-input');
    expect(input).toBeEnabled();
    expect(input).toHaveAttribute('placeholder', 'Ask about our features, security, plans...');
  });

  it('handles user typing and successful streaming response', async () => {
    mockSendDemoMessage.mockImplementation(async (msg, onToken, onDone, onError) => {
      // Simulate tokens streaming
      onToken('Hello ');
      onToken('user!');
      // Update session mockup return to reflect 1 message
      mockGetDemoSession.mockReturnValue({ sessionId: 'mock-session-id', messageCount: 1 });
      onDone(1);
    });

    render(<LiveDemo />);
    
    const input = screen.getByTestId('demo-chat-input');
    const form = input.closest('form');

    fireEvent.change(input, { target: { value: 'Hello AI' } });
    
    await act(async () => {
      fireEvent.submit(form!);
    });

    // Verify sendDemoMessage was called
    expect(mockSendDemoMessage).toHaveBeenCalledWith(
      'Hello AI',
      expect.any(Function),
      expect.any(Function),
      expect.any(Function)
    );

    // Verify user message is displayed
    expect(screen.getByText('Hello AI')).toBeInTheDocument();
    
    // Verify streamed response is displayed
    expect(screen.getByText('Hello user!')).toBeInTheDocument();
    
    // Verify counter updated
    expect(screen.getByTestId('demo-counter')).toHaveTextContent('1 / 5 messages');
  });

  it('disables input and shows trial CTA when quota is exceeded', () => {
    mockGetDemoSession.mockReturnValue({ sessionId: 'mock-session-id', messageCount: 5 });
    
    render(<LiveDemo />);
    
    const input = screen.getByTestId('demo-chat-input');
    expect(input).toBeDisabled();
    
    const cta = screen.getByTestId('demo-cta-trial');
    expect(cta).toBeInTheDocument();
    expect(cta).toHaveAttribute('href', '/register?source=demo');
  });

  it('handles 429 quota exceeded error from API', async () => {
    mockSendDemoMessage.mockImplementation(async (msg, onToken, onDone, onError) => {
      // Simulate 429 error
      onError({
        error: {
          code: 'DEMO_QUOTA_EXCEEDED',
          message: 'You have reached the demo limit. Start your free trial to continue.',
          message_count: 5
        }
      });
    });

    render(<LiveDemo />);
    
    const input = screen.getByTestId('demo-chat-input');
    const form = input.closest('form');

    fireEvent.change(input, { target: { value: 'Hi' } });
    
    await act(async () => {
      fireEvent.submit(form!);
    });

    // Check error message and input disabled
    expect(screen.getByText(/You have reached the demo limit/)).toBeInTheDocument();
    expect(input).toBeDisabled();
    expect(screen.getByTestId('demo-cta-trial')).toBeInTheDocument();
  });

  it('handles 503 service unavailable error from API', async () => {
    mockSendDemoMessage.mockImplementation(async (msg, onToken, onDone, onError) => {
      // Simulate 503 error
      onError({
        error: {
          code: 'SERVICE_UNAVAILABLE',
          message: 'AI service temporarily unavailable. Please try again shortly.'
        }
      });
    });

    render(<LiveDemo />);
    
    const input = screen.getByTestId('demo-chat-input');
    const form = input.closest('form');

    fireEvent.change(input, { target: { value: 'Hi' } });
    
    await act(async () => {
      fireEvent.submit(form!);
    });

    // Check fallback message and input remains enabled
    expect(screen.getByText(/AI service temporarily unavailable/)).toBeInTheDocument();
    expect(input).toBeEnabled();
  });
});
