/**
 * Colours for the eligibility panel. No Volto imports, so it is testable on
 * its own. Values are Semantic UI label colours.
 */

/** Colour of one condition's status. */
export function statusColor(status) {
  if (status === 'met') return 'green';
  if (status === 'not met') return 'red';
  return 'yellow';
}

/** Colour of the overall conclusion, from step_criteria._overall. */
export function overallColor(overall) {
  if (!overall) return 'grey';
  if (overall.startsWith('meets the criteria only if')) return 'yellow';
  if (overall.startsWith('meets the criteria')) return 'green';
  if (overall.startsWith('does not meet')) return 'red';
  return 'yellow';
}
