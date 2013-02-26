# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import mock
from mozpool.lifeguard import devicemachine
from mozpool.test.util import StateDriverMixin, DBMixin, PatchMixin, TestCase

class Tests(StateDriverMixin, DBMixin, PatchMixin, TestCase):

    driver_class = devicemachine.LifeguardDriver

    auto_patch = [
        ('start_ping', 'mozpool.bmm.api.API.start_ping'),
        ('set_pxe', 'mozpool.bmm.api.API.set_pxe'),
        ('start_powercycle', 'mozpool.bmm.api.API.start_powercycle'),
    ]

    def setUp(self):
        super(Tests, self).setUp()
        hw_id = self.add_hardware_type('test', 'test')
        self.add_device('dev1', hardware_type_id=hw_id,
                relayinfo='relayhost:bank1:relay2')

    def tearDown(self):
        super(Tests, self).tearDown()

    def set_state(self, state):
        self.db.devices.set_machine_state('dev1', state, None)

    def assert_state(self, state):
        self.assertEqual(self.db.devices.get_machine_state('dev1'), state)

    def test_free_ping_ok(self):
        self.set_state('free')
        self.driver.handle_timeout('dev1')
        self.start_ping.assert_called_with('dev1', mock.ANY)
        self.start_ping.call_args[0][1](True)
        self.assert_state('free')

    def test_ready_no_next_image(self):
        "entering ready does not change the image if there's no next_image"
        self.add_image('old_img')
        self.db.devices.set_image('dev1', 'old_img', '{bc}')
        self.set_state('sut_sdcard_verifying')
        self.driver.handle_event('dev1', 'sut_sdcard_ok', {})
        self.assert_state('ready')
        self.assertEqual(self.db.devices.get_image('dev1'),
                {'image': 'old_img', 'boot_config': '{bc}'})

    def test_ready_set_image(self):
        "entering ready changes the image if there is a next_image"
        self.add_image('old_img')
        self.add_image('new_img')
        self.db.devices.set_image('dev1', 'old_img', '{bc}')
        self.db.devices.set_next_image('dev1', 'new_img', '{bc2}')
        self.set_state('sut_sdcard_verifying')
        self.driver.handle_event('dev1', 'sut_sdcard_ok', {})
        self.assert_state('ready')
        self.assertEqual(self.db.devices.get_image('dev1'),
                {'image': 'new_img', 'boot_config': '{bc2}'})
