# -*- coding: utf-8 -*-
"""Values written to the integer current_grade column."""
from c_step_intake.db import field_map
from c_step_intake.db.serializer import COERCE
from c_step_intake.db.serializer import grade_to_int

import unittest


class TestCoercion(unittest.TestCase):

    def test_blank_grade_is_null(self):
        self.assertIsNone(grade_to_int(None))
        self.assertIsNone(grade_to_int(''))

    def test_grade_is_an_int(self):
        self.assertEqual(11, grade_to_int('11'))

    def test_every_coerced_column_is_mapped_as_integer(self):
        types = {m.column: m.pg_type for m in field_map.APPLICATIONS}
        for column in COERCE:
            self.assertEqual('integer', types[column])
