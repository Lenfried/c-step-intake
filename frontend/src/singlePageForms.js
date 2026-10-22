/**
 * Single-page add and edit forms.
 *
 * Volto draws a form as tabs whenever its schema has more than one fieldset,
 * and has no setting to turn that off. The backend's classic forms set
 * ``enable_form_tabbing = False``, but Volto never sees that: it builds its
 * forms from the ``@types`` schema alone.
 *
 * So for the configured types, the schema is rewritten as it arrives: all
 * fieldsets are merged into one, in order, and each former fieldset after the
 * first is introduced by a read-only heading field. With a single fieldset,
 * Volto's own form renders everything on one page. Nothing is sent to or
 * changed on the backend.
 *
 * This module has no Volto imports, so it can be tested on its own.
 */

/** Widget name the heading fields are rendered with. */
export const HEADING_WIDGET = 'c_step_intake_fieldset_heading';

/** Prefix of the heading field ids; never a real schema field. */
export const HEADING_PREFIX = '__fieldset_';

/**
 * Return a copy of ``schema`` with all fieldsets merged into one.
 *
 * The ``default`` fieldset gets no heading, because its fields are the
 * form's opening section.
 */
export function toSinglePage(schema) {
  if (!schema?.fieldsets || schema.fieldsets.length < 2) {
    return schema;
  }
  const properties = { ...schema.properties };
  const fields = [];
  schema.fieldsets.forEach((fieldset) => {
    if (fieldset.id !== 'default') {
      const headingId = `${HEADING_PREFIX}${fieldset.id}`;
      properties[headingId] = {
        title: fieldset.title,
        description: fieldset.description,
        widget: HEADING_WIDGET,
        readonly: true,
      };
      fields.push(headingId);
    }
    fields.push(...fieldset.fields);
  });
  return {
    ...schema,
    properties,
    fieldsets: [{ ...schema.fieldsets[0], id: 'default', fields }],
  };
}

/**
 * Return the content type a ``getSchema`` request is for, or null.
 *
 * ``getSchema`` requests ``<url>/@types/<type>``.
 */
export function schemaTypeOf(action) {
  const path = action?.request?.path;
  if (typeof path !== 'string') {
    return null;
  }
  const match = path.match(/\/@types\/([^/?]+)$/);
  return match ? match[1] : null;
}

/**
 * Build the store extender that applies ``toSinglePage``.
 *
 * Volto's api middleware drops ``request`` from the success action, so the
 * content type is gone by the time the schema arrives. Two middlewares work
 * around that: one placed before the api middleware tags the request with
 * the type, and one placed after it rewrites the tagged success action.
 *
 * ``getTypes`` is called on each request, so the list can be changed in
 * ``config.settings`` after this add-on is loaded.
 */
export function singlePageFormsExtender(getSchemaAction, getTypes) {
  const TAG = 'cStepIntakeSinglePage';
  const success = `${getSchemaAction}_SUCCESS`;

  const tag = () => (next) => (action) => {
    if (
      action?.type === getSchemaAction &&
      getTypes().includes(schemaTypeOf(action))
    ) {
      return next({ ...action, [TAG]: true });
    }
    return next(action);
  };

  const rewrite = () => (next) => (action) => {
    if (action?.type === success && action[TAG]) {
      return next({ ...action, result: toSinglePage(action.result) });
    }
    return next(action);
  };

  return (stack) => [tag, ...stack, rewrite];
}
