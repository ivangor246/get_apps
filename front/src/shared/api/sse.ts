import { API_BASE_URL } from '../config';

export type SseEventType = 'log' | 'progress' | 'status' | 'done' | 'error';

export interface SseEvent {
  type: SseEventType;
  ts: number;
  [key: string]: unknown;
}

export function openSse(
  path: string,
  onEvent: (event: SseEvent) => void,
  onClose?: () => void,
): () => void {
  const source = new EventSource(`${API_BASE_URL}${path}`);
  const types: SseEventType[] = ['log', 'progress', 'status', 'done', 'error'];
  for (const type of types) {
    source.addEventListener(type, (e) => {
      try {
        onEvent(JSON.parse((e as MessageEvent).data) as SseEvent);
      } catch {
        /* ignore malformed frames */
      }
    });
  }
  source.onerror = () => {
    source.close();
    onClose?.();
  };
  return () => source.close();
}
