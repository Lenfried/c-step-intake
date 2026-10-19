# -*- coding: utf-8 -*-
"""Value formatting for the live step_student table."""
from c_step_intake.db import field_map
from c_step_intake.db.serializer import COERCE
from c_step_intake.db.serializer import format_student_id
from c_step_intake.db.serializer import grade_to_int

import unittest


class TestCoercion(unittest.TestCase):

    def test_blank_grade_is_null(self):
        self.assertIsNone(grade_to_int(None))
        self.assertIsNone(grade_to_int(''))

    def test_student_id_is_dashed_like_the_existing_rows(self):
        self.assertEqual(
            '04e42317-bea7-44c6-964b-aa6944518988',
            format_student_id('04e42317bea744c6964baa6944518988'))

    def test_student_id_formatting_is_stable_and_null_safe(self):
        dashed = '04e42317-bea7-44c6-964b-aa6944518988'
        self.assertEqual(dashed, format_student_id(dashed))
        self.assertIsNone(format_student_id(None))

    def test_grade_is_an_int(self):
        self.assertEqual(11, grade_to_int('11'))

    def test_every_coerced_column_is_mapped_as_integer(self):
        types = {m.column: m.pg_type for m in field_map.APPLICATIONS}
        for column in COERCE:
            self.assertEqual('integer', types[column])
