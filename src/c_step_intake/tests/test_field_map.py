# -*- coding: utf-8 -*-
"""Self-consistency tests for the PostgreSQL field map.

field_map.py is plain data with no Plone imports, so these run standalone.
The companion tests that compare the map against the actual schemas live in
test_schema_coverage.py.
"""
import unittest

from c_step_intake.db import field_map


class TestFieldMap(unittest.TestCase):

    def test_no_duplicate_columns(self):
        columns = [m.column for m in field_map.APPLICATIONS]
        duplicates = {c for c in columns if columns.count(c) > 1}
        self.assertEqual(set(), duplicates)

    def test_every_mapping_declares_at_least_one_program(self):
        for mapping in field_map.APPLICATIONS:
            self.assertTrue(mapping.programs, mapping.column)

    def test_programs_are_known(self):
        for mapping in field_map.APPLICATIONS:
            for program in mapping.programs:
                self.assertIn(program, field_map.BOTH, mapping.column)

    def test_no_field_maps_to_two_columns(self):
        fields = [m.field for m in field_map.APPLICATIONS if m.field]
        self.assertEqual(len(fields), len(set(fields)))

    def test_mapped_fields_includes_derived_column_sources(self):
        # application_gpa and major_at_application have no `field` of their
        # own -- they read cumulative_gpa/gpa and major via source_fields.
        # mapped_fields() must still report those as accounted for, or
        # test_schema_coverage.py wrongly flags them as forgotten.
        for source in ('gpa', 'cumulative_gpa', 'major'):
            self.assertIn(source, field_map.mapped_fields())

    def test_columns_for_step_excludes_cstep_only_columns(self):
        step = {m.column for m in field_map.columns_for(field_map.STEP)}
        self.assertIn('school_name', step)
        self.assertNotIn('empl_id', step)

    def test_columns_for_cstep_excludes_step_only_columns(self):
        cstep = {m.column for m in field_map.columns_for(field_map.CSTEP)}
        self.assertIn('empl_id', cstep)
        self.assertNotIn('parent1_email', cstep)

    def test_both_programs_share_the_identity_block(self):
        step = {m.column for m in field_map.columns_for(field_map.STEP)}
        cstep = {m.column for m in field_map.columns_for(field_map.CSTEP)}
        for column in ('first_name', 'last_name', 'student_email', 'date_of_birth'):
            self.assertIn(column, step)
            self.assertIn(column, cstep)

    def test_decision_columns_apply_to_both_programs(self):
        for column in ('program_status', 'decision_reason', 'decided_at',
                       'rules_version'):
            mapping = self._by_column(column)
            self.assertEqual(field_map.BOTH, mapping.programs)

    def test_each_program_has_its_own_table(self):
        self.assertNotEqual(
            field_map.table_for(field_map.STEP),
            field_map.table_for(field_map.CSTEP),
        )

    def test_no_program_discriminator_column(self):
        # Each program writes to its own table, so a discriminator column
        # would be redundant -- and the live STEP table has none.
        columns = {m.column for m in field_map.APPLICATIONS}
        self.assertNotIn('program', columns)

    def test_gpa_columns_are_program_specific(self):
        # With one table per program there is no need to alias the two GPA
        # fields onto a shared column: each table uses its own field name.
        step = {m.column for m in field_map.columns_for(field_map.STEP)}
        cstep = {m.column for m in field_map.columns_for(field_map.CSTEP)}
        self.assertIn('cumulative_gpa', step)
        self.assertNotIn('cumulative_gpa', cstep)
        self.assertIn('gpa', cstep)
        self.assertNotIn('gpa', step)

    def test_income_is_flagged_as_pii(self):
        self.assertIn('household_income', field_map.pii_columns())

    def test_guardian_contact_is_flagged_as_pii(self):
        for column in ('parent1_email', 'parent1_phone', 'parent2_email'):
            self.assertIn(column, field_map.pii_columns())

    def test_application_id_is_not_pii(self):
        # The Plone UID is opaque by design so it can safely appear in URLs
        # and join keys.
        self.assertNotIn('application_id', field_map.pii_columns())

    def _by_column(self, column):
        for mapping in field_map.APPLICATIONS:
            if mapping.column == column:
                return mapping
        self.fail('No mapping for column {0}'.format(column))
