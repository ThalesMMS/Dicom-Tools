export type LogLevel = 'info' | 'error';

export function logMessage(level: LogLevel, message: string, error?: unknown) {
  if (level === 'error') {
    console.error(message, error);
  } else {
    console.info(message);
  }
}

export function setStatus(element: HTMLElement, message: string, level: LogLevel = 'info') {
  element.textContent = message;
  element.dataset.statusLevel = level;
}

export function reportStatus(element: HTMLElement, level: LogLevel, message: string, error?: unknown) {
  logMessage(level, message, error);
  setStatus(element, message, level);
}
