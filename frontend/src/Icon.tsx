import type { ReactNode } from 'react';

const paths = {
  location: <><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/></>,
  storm: <><path d="M6 15a4 4 0 0 1 0-8 6 6 0 0 1 11-1 4.5 4.5 0 0 1 1 9h-2"/><path d="m12 11-3 6h4l-2 5"/></>,
  shield: <><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/></>,
  network: <><rect x="8" y="2" width="8" height="5" rx="1"/><path d="M12 7v5M4 16v-4h16v4"/><rect x="1" y="16" width="6" height="5" rx="1"/><rect x="17" y="16" width="6" height="5" rx="1"/></>,
  crew: <><circle cx="9" cy="7" r="3"/><path d="M3 21v-4a6 6 0 0 1 12 0v4M17 4a3 3 0 0 1 0 6m1 3a5 5 0 0 1 3 5v3"/></>,
  access: <><path d="M5 21 9 3m6 0 4 18M12 4v3m0 4v3m0 4v3"/></>,
  critical: <><path d="M4 21V5h16v16M2 21h20M9 21v-5h6v5M12 7v6m-3-3h6"/></>,
  fire: <><path d="M12 2c1 6 6 7 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 3 1 4 2 4 1-3 2-6 1-10Z"/><path d="M12 15c-4 4 2 7 3 3"/></>,
  check: <path d="m5 12 4 4L19 6"/>,
  alert: <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 8 3 8H3s3-1 3-8ZM9 20h6"/></>,
  sms: <><path d="M3 4h18v13H9l-6 4V4Z"/><path d="M7 9h10M7 13h6"/></>,
  evidence: <><path d="M5 3h10l4 4v14H5V3Zm10 0v5h4M8 11h8M8 15h5"/></>,
  model: <><path d="m12 2 10 6-10 6L2 8l10-6Zm-9 11 9 5 9-5M3 18l9 5 9-5"/></>,
  spatial: <><circle cx="12" cy="12" r="9" strokeDasharray="2 3"/><circle cx="12" cy="12" r="3"/><path d="M12 1v3m0 16v3M1 12h3m16 0h3"/></>,
  unknown: <><circle cx="12" cy="12" r="9"/><path d="M9 8a3 3 0 1 1 5 2c-2 1-2 2-2 3M12 17h.01"/></>,
  explain: <><path d="M3 3h18v14H10l-5 4v-4H3V3Z"/><path d="M8 8h8M8 12h5"/></>,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6"/>,
  chevron: <path d="m6 9 6 6 6-6"/>,
  close: <path d="m6 6 12 12M6 18 18 6"/>,
  fuse: <><path d="M12 1v5m0 12v5M7 6h10v12H7z"/><path d="m14 8-4 4h4l-3 4"/></>,
  transformer: <><path d="M7 4h10v16H7zM10 1v3m4-3v3M4 8h3m10 0h3M4 16h3m10 0h3"/><path d="M10 8h4m-4 4h4m-4 4h4"/></>,
  home: <><path d="m2 11 10-9 10 9M5 9v12h14V9M9 21v-8h6v8"/></>,
  repair: <><path d="M14 3a6 6 0 0 0-7 8l-5 7 4 4 7-6a6 6 0 0 0 8-7l-4 4-5-5 4-4Z"/></>,
  medical: <><path d="M8 3h8v5h5v8h-5v5H8v-5H3V8h5V3Z"/></>,
  accessibility: <><circle cx="12" cy="4" r="2"/><path d="m4 9 8 2 8-2M12 11v5m0 0-5 6m5-6 5 6"/></>,
  book: <><path d="M12 5c-3-2-7-2-10-1v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1Zm0 0v15"/></>,
} satisfies Record<string, ReactNode>;
export type IconName = keyof typeof paths;
export function Icon({ name, className = '' }: { name: IconName; className?: string }) {
  return <svg className={`icon ${className}`} width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">{paths[name]}</svg>;
}
