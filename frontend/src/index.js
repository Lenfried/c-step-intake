import { GET_SCHEMA } from '@plone/volto/constants/ActionTypes';
import ApplicationView from './ApplicationView';
import FieldsetHeadingWidget from './FieldsetHeadingWidget';
import { HEADING_WIDGET, singlePageFormsExtender } from './singlePageForms';

/** Types whose add and edit forms show every fieldset on one page. */
const SINGLE_PAGE_FORM_TYPES = ['step_application', 'cstep_application'];

export default function applyConfig(config) {
  config.settings.cStepIntakeSinglePageFormTypes = SINGLE_PAGE_FORM_TYPES;
  config.widgets.widget[HEADING_WIDGET] = FieldsetHeadingWidget;
  config.settings.storeExtenders = [
    ...(config.settings.storeExtenders || []),
    singlePageFormsExtender(
      GET_SCHEMA,
      () => config.settings.cStepIntakeSinglePageFormTypes || [],
    ),
  ];
  // Section headings, plus the staff-only eligibility panel.
  config.views.contentTypesViews = {
    ...config.views.contentTypesViews,
    step_application: ApplicationView,
    cstep_application: ApplicationView,
  };
  return config;
}
