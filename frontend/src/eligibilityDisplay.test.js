import { describe, expect, it } from 'vitest';
import { overallColor, statusColor } from './eligibilityDisplay';

describe('statusColor', () => {
  it('colours each status', () => {
    expect(statusColor('met')).toBe('green');
    expect(statusColor('not met')).toBe('red');
    expect(statusColor('undetermined')).toBe('yellow');
  });
});

describe('overallColor', () => {
  // The conclusions step_criteria._overall produces.
  it.each([
    ['meets the criteria (1, 2 and 3a)', 'green'],
    [
      'meets the criteria only if staff judge the STEM statement shows need (3b)',
      'yellow',
    ],
    ['does not meet the criteria (condition 1 not met)', 'red'],
    ['undetermined: staff to check income (3a)', 'yellow'],
    [undefined, 'grey'],
  ])('%s -> %s', (overall, color) => {
    expect(overallColor(overall)).toBe(color);
  });
});
