/**
 * Section heading for a fieldset merged into a single-page form.
 *
 * Rendered in place of a field; it has no value and never calls onChange,
 * so nothing it stands for is submitted.
 */
import React from 'react';
import { Segment } from 'semantic-ui-react';

const FieldsetHeadingWidget = ({ id, title, description }) => (
  <Segment
    secondary
    className="c-step-intake-fieldset-heading"
    id={`fieldset-heading-${id}`}
  >
    <h2 style={{ fontSize: '1.15em', margin: 0 }}>{title}</h2>
    {description && <p style={{ marginTop: '0.5em' }}>{description}</p>}
  </Segment>
);

export default FieldsetHeadingWidget;
