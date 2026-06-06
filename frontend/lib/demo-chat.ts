// Placeholder for demo chat utility
export interface DemoSession {
  sessionId: string;
  messageCount: number;
}

export function getDemoSession(): DemoSession {
  return { sessionId: '', messageCount: 0 };
}

export async function sendDemoMessage(
  message: string,
  onToken: (token: string) => void,
  onDone: (messageCount: number) => void,
  onError: (error: any) => void
): Promise<void> {
  // To be implemented in User Story 1
}
