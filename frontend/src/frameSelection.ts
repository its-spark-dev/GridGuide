import type { PathFrame } from './offline';

// Only an exact approved frame can be selected from a link. No scenario data,
// declarations or source identifiers enter a URL or persistent storage.
export const frameHash = (frame: PathFrame) => '#' + frame.scenario_id + '/' + frame.step;
export function linkedFrame(frames: PathFrame[], hash: string): PathFrame | undefined {
  return frames.find(frame => frameHash(frame) === hash);
}
