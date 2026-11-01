/**
 * View for STEP and CSTEP applications.
 *
 * Volto's DefaultView, with two changes:
 *
 * - the staff-only eligibility panel at the top;
 * - section headings from the single-page schema. DefaultView would render
 *   each heading field as an empty field, because the merged schema has
 *   only one fieldset.
 */
import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Container as SemanticContainer,
  Grid,
  Label,
  Segment,
} from 'semantic-ui-react';
import config from '@plone/volto/registry';
import { getSchema } from '@plone/volto/actions/schema/schema';
import { getWidget } from '@plone/volto/helpers/Widget/utils';
import { getBaseUrl } from '@plone/volto/helpers/Url/Url';
import EligibilityPanel from './EligibilityPanel';
import { sectionsOf } from './singlePageForms';

/** Sections DefaultView also leaves out. */
const HIDDEN_SECTIONS = ['categorization', 'dates', 'ownership', 'settings'];

const ApplicationView = ({ content, location }) => {
  const dispatch = useDispatch();
  const path = getBaseUrl(location?.pathname || '');
  const schema = useSelector((state) => state.schema?.schema);
  const { views } = config.widgets;

  useEffect(() => {
    if (content?.['@type']) {
      dispatch(getSchema(content['@type'], location.pathname));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content?.['@type']]);

  const Container =
    config.getComponent({ name: 'Container' }).component || SemanticContainer;

  if (!content?.['@type']) {
    return null;
  }

  const sections = sectionsOf(schema).filter(
    (section) => !HIDDEN_SECTIONS.includes(section.id),
  );

  return (
    <Container id="page-document">
      <EligibilityPanel
        path={path}
        reviewState={content.review_state}
        schema={schema}
      />
      {sections.map((section) => (
        <div className="fieldset" key={section.id}>
          {section.title && <h2>{section.title}</h2>}
          {section.fields.map((name) => {
            const field = {
              ...schema.properties[name],
              id: name,
              widget: getWidget(name, schema.properties[name]),
            };
            const Widget = views.getWidget(field);
            return (
              <Grid celled="internally" key={name}>
                <Grid.Row>
                  <Label title={name}>{field.title}:</Label>
                </Grid.Row>
                <Grid.Row>
                  <Segment basic>
                    <Widget value={content[name]} />
                  </Segment>
                </Grid.Row>
              </Grid>
            );
          })}
        </div>
      ))}
    </Container>
  );
};

export default ApplicationView;
