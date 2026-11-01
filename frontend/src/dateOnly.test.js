import { describe, expect, it } from 'vitest';
import { formatDateOnly, isDateOnly } from './dateOnly';

describe('formatDateOnly', () => {
  it('shows the day entered, in a time zone west of UTC', () => {
    expect(formatDateOnly('2011-05-01')).toBe('May 1, 2011');
  });

  it('would be a day early in New York without it', () => {
    const naive = new Intl.DateTimeFormat('en', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'America/New_York',
    }).format(new Date('2011-05-01'));
    expect(naive).toBe('Apr 30, 2011');
  });

  it('handles the first day of a year', () => {
    expect(formatDateOnly('2012-01-01')).toBe('Jan 1, 2012');
  });

  it('formats in the given locale', () => {
    expect(formatDateOnly('2011-05-01', 'de')).toBe('1. Mai 2011');
  });

  it('leaves anything that is not a date-only string unchanged', () => {
    expect(formatDateOnly('2011-05-01T12:00:00Z')).toBe('2011-05-01T12:00:00Z');
    expect(formatDateOnly(null)).toBeNull();
  });
});

describe('isDateOnly', () => {
  it('recognises YYYY-MM-DD only', () => {
    expect(isDateOnly('2011-05-01')).toBe(true);
    expect(isDateOnly('2011-5-1')).toBe(false);
    expect(isDateOnly(undefined)).toBe(false);
  });
});
