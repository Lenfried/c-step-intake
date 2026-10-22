import { describe, expect, it } from 'vitest';
import {
  HEADING_WIDGET,
  schemaTypeOf,
  singlePageFormsExtender,
  toSinglePage,
} from './singlePageForms';

const schema = {
  title: 'STEP Application',
  required: ['first_name'],
  properties: {
    first_name: { title: 'First name' },
    school_name: { title: 'School' },
    household_size: { title: 'Household size' },
  },
  fieldsets: [
    { id: 'default', title: 'Default', fields: ['first_name'] },
    { id: 'school', title: 'School', fields: ['school_name'] },
    {
      id: 'household',
      title: 'Household',
      description: 'Who lives with you',
      fields: ['household_size'],
    },
  ],
};

describe('toSinglePage', () => {
  it('merges every fieldset into one, keeping field order', () => {
    const result = toSinglePage(schema);
    expect(result.fieldsets).toHaveLength(1);
    expect(result.fieldsets[0].id).toBe('default');
    expect(result.fieldsets[0].fields).toEqual([
      'first_name',
      '__fieldset_school',
      'school_name',
      '__fieldset_household',
      'household_size',
    ]);
  });

  it('adds a read-only heading for each fieldset after the default one', () => {
    const { properties } = toSinglePage(schema);
    expect(properties.__fieldset_household).toEqual({
      title: 'Household',
      description: 'Who lives with you',
      widget: HEADING_WIDGET,
      readonly: true,
    });
    expect(properties.__fieldset_default).toBeUndefined();
  });

  it('leaves real fields and required untouched', () => {
    const result = toSinglePage(schema);
    expect(result.required).toEqual(['first_name']);
    expect(result.properties.school_name).toBe(schema.properties.school_name);
  });

  it('does not change the input schema', () => {
    const before = JSON.stringify(schema);
    toSinglePage(schema);
    expect(JSON.stringify(schema)).toBe(before);
  });

  it('returns a schema with one fieldset unchanged', () => {
    const single = { ...schema, fieldsets: [schema.fieldsets[0]] };
    expect(toSinglePage(single)).toBe(single);
  });
});

describe('schemaTypeOf', () => {
  it('reads the type from a getSchema request', () => {
    const action = { request: { path: '/folder/@types/step_application' } };
    expect(schemaTypeOf(action)).toBe('step_application');
  });

  it('returns null for other requests', () => {
    expect(schemaTypeOf({ request: { path: '/folder/@search' } })).toBeNull();
    expect(schemaTypeOf({})).toBeNull();
  });
});

describe('singlePageFormsExtender', () => {
  // Stand-in for Volto's api middleware: like the real one, it drops
  // `request` from the success action it dispatches.
  const fakeApi = () => (next) => (action) => {
    if (action.type !== 'GET_SCHEMA') return next(action);
    const { request, ...rest } = action;
    return next({ ...rest, result: schema, type: 'GET_SCHEMA_SUCCESS' });
  };

  function dispatchThrough(types, path) {
    const stack = singlePageFormsExtender('GET_SCHEMA', () => types)([
      fakeApi,
    ]);
    const seen = [];
    const dispatch = stack
      .map((middleware) => middleware({}))
      .reduceRight((next, mw) => mw(next), (action) => seen.push(action));
    dispatch({ type: 'GET_SCHEMA', request: { op: 'get', path } });
    return seen[0];
  }

  it('rewrites the schema of a configured type', () => {
    const action = dispatchThrough(['step_application'], '/@types/step_application');
    expect(action.result.fieldsets).toHaveLength(1);
  });

  it('leaves other types alone', () => {
    const action = dispatchThrough(['step_application'], '/@types/Document');
    expect(action.result).toBe(schema);
  });
});
