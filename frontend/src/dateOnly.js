/**
 * Display a date-only value ("2011-05-01") as the same calendar day
 * everywhere.
 *
 * Volto's date view widget turns the value into a JavaScript Date, which
 * reads a date-only string as midnight UTC, then formats it in the browser's
 * time zone. West of UTC that is the evening before: a date of birth of
 * May 1 shows as April 30 in New York. Formatting in UTC keeps the day the
 * applicant entered. No Volto imports, so it is testable on its own.
 */

const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

/** Same format as Volto's default 'll', e.g. "May 1, 2011". */
const FORMAT = { year: 'numeric', month: 'short', day: 'numeric' };

export function isDateOnly(value) {
  return typeof value === 'string' && DATE_ONLY.test(value);
}

/** Format a "YYYY-MM-DD" value; anything else is returned unchanged. */
export function formatDateOnly(value, locale = 'en') {
  if (!isDateOnly(value)) {
    return value;
  }
  return new Intl.DateTimeFormat(locale, {
    ...FORMAT,
    timeZone: 'UTC',
  }).format(new Date(value));
}
