import { getApiBaseUrl } from './api';

export interface DemoSession {
  sessionId: string;
  messageCount: number;
}

function uuidv4() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0,
      v = c == 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function getDemoSession(): DemoSession {
  if (typeof window === 'undefined') {
    return { sessionId: '', messageCount: 0 };
  }
  const sessionStr = localStorage.getItem('demo_session');
  if (sessionStr) {
    try {
      const parsed = JSON.parse(sessionStr);
      if (parsed && typeof parsed.sessionId === 'string' && typeof parsed.messageCount === 'number') {
        return parsed;
      }
    } catch {
      // Ignored
    }
  }
  const newSession: DemoSession = {
    sessionId: uuidv4(),
    messageCount: 0,
  };
  localStorage.setItem('demo_session', JSON.stringify(newSession));
  return newSession;
}

export function updateDemoSessionCount(count: number): void {
  if (typeof window === 'undefined') return;
  const session = getDemoSession();
  session.messageCount = count;
  localStorage.setItem('demo_session', JSON.stringify(session));
}

export async function sendDemoMessage(
  message: string,
  onToken: (token: string) => void,
  onDone: (messageCount: number) => void,
  onError: (error: unknown) => void
): Promise<void> {
  try {
    const session = getDemoSession();
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/public/chat`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: session.sessionId,
      }),
    });

    if (!response.ok) {
      let errorData: unknown;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: `HTTP error ${response.status}` };
      }
      throw errorData;
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep the last incomplete line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        if (trimmed.startsWith('data: ')) {
          const dataStr = trimmed.slice(6);
          try {
            const parsed = JSON.parse(dataStr);
            if (parsed.type === 'token') {
              onToken(parsed.content);
            } else if (parsed.type === 'done') {
              const count = parsed.message_count;
              updateDemoSessionCount(count);
              onDone(count);
            }
          } catch (e) {
            console.error('Failed to parse SSE line data:', dataStr, e);
          }
        }
      }
    }
  } catch (err: unknown) {
    onError(err);
  }
}
