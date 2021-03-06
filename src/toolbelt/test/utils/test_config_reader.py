# -*- coding: utf-8 -*-
#
#     ||          ____  _ __
#  +------+      / __ )(_) /_______________ _____  ___
#  | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
#  +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
#   ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
#
# Toolbelt - a utility tu run tools in docker containers
# Copyright (C) 2016  Bitcraze AB
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
import unittest
from unittest.mock import patch, mock_open, MagicMock, call

from toolbelt.utils.bc_module import BcModule
from toolbelt.utils.config_reader import ConfigReader
from toolbelt.utils.file_wrapper import FileWrapper


class RunnerTest(unittest.TestCase):

    def setUp(self):
        self.file_wrapper_mock = MagicMock(FileWrapper)
        self.bc_module_mock = MagicMock(BcModule)

        self.default_config = {'some': 'data'}
        self.file_wrapper_mock.json_load.side_effect = [
            self.default_config, IOError()]

        self.bc_module_mock.enumerate_tools.return_value = []

        self.extensions_mock = MagicMock()
        self.extensions_mock.tools.return_value = []

        self.toolbelt_root = 'path'

        self.sut = ConfigReader(file_wrapper=self.file_wrapper_mock,
                                bc_module=self.bc_module_mock)

    def test_read_tb_config(self):
        # Fixture

        # Test
        actual = self.sut.get_tb_config(self.toolbelt_root,
                                        self.extensions_mock)

        # Assert
        self.assertEqual("data", actual['some'])
        self.file_wrapper_mock.json_load.assert_calls([
            call(self.toolbelt_root + '/config.json'),
            call(self.toolbelt_root + '/.toolbelt.json')])

    def test_read_tb_config_data_merged(self):
        # Fixture
        self.file_wrapper_mock.json_load.side_effect = [
            {'some': 'data'},
            {'more': 'info'}
        ]

        # Test
        actual = self.sut.get_tb_config(self.toolbelt_root,
                                        self.extensions_mock)

        # Assert
        self.assertEqual("data", actual['some'])
        self.assertEqual("info", actual['more'])

    def test_read_tb_config_data_replaced(self):
        # Fixture
        self.file_wrapper_mock.json_load.side_effect = [
            {'some': 'data'},
            {'some': 'info'}
        ]

        # Test
        actual = self.sut.get_tb_config(self.toolbelt_root,
                                        self.extensions_mock)

        # Assert
        self.assertEqual("info", actual['some'])

    def test_config_set_by_code_in_native_env(self):
        # Fixture
        currentDir = os.getcwd()

        # Test
        actual = self.sut.get_tb_config(self.toolbelt_root,
                                        self.extensions_mock)

        # Assert
        self.assertEqual('native', actual['host'])
        self.assertEqual(self.toolbelt_root, actual['root'])
        self.assertEqual(self.toolbelt_root + "/tmp", actual['tmpRoot'])
        self.assertEqual(currentDir, actual['module_root'])
        self.assertEqual(currentDir, actual['module_root_in_docker_host'])
        self.assertEqual([], actual['module_tools'])
        self.assertEqual(3, len(actual['tools']))

    def test_config_set_by_code_in_container_env(self):
        # Fixture
        path = "some/path"
        container_id = "someId"

        with patch.dict('os.environ', {'HOST_CW_DIR': path,
                                       "HOSTNAME": container_id}):

            # Test
            actual = self.sut.get_tb_config(self.toolbelt_root,
                                            self.extensions_mock)

            # Assert
            self.assertEqual('container', actual['host'])
            self.assertEqual(path, actual['module_root_in_docker_host'])
            self.assertEqual(container_id, actual['container_id'])

    def test_module_tools_added(self):
        # Fixture
        expected = ["nr1", "nr2"]
        self.bc_module_mock.enumerate_tools.return_value = expected

        # Test
        actual = self.sut.get_tb_config(self.toolbelt_root,
                                        self.extensions_mock)

        # Assert
        self.assertEqual(expected, actual['module_tools'])
