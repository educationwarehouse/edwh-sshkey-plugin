# SPDX-FileCopyrightText: 2023-present Remco Boerma <remco.b@educationwarehouse.nl>
#
# SPDX-License-Identifier: MIT

from ..src.edwh_sshkey_plugin import fabfile
import unittest

import unittest
from src.edwh_sshkey_plugin import fabfile


class TestYourModule(unittest.TestCase):
    def test_create_new_keyholder(self):
        fabfile.YAML_KEYS_PATH.touch()
        # Assert that the file was created successfully
        self.assertTrue(fabfile.YAML_KEYS_PATH.exists())

    def test_create_new_yaml_file_if_not_exists(self):
        fabfile.create_new_yaml_file_if_not_exists()
        # Assert that the function created the file successfully
        self.assertTrue(fabfile.YAML_KEYS_PATH.exists())

    def test_open_new_keyholder(self):
        # Test the read mode
        with fabfile.open_new_keyholder(read=True) as f:
            # Assert that the file was opened successfully
            self.assertIsNotNone(f)
        # Test the write mode
        with fabfile.open_new_keyholder(read=False) as f:
            # Assert that the file was opened successfully
            self.assertIsNotNone(f)


