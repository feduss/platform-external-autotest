# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.server import autotest, test


class network_WiFiSimpleConnectionServer(test.test):
    """ Dynamic Chaos test. """

    version = 1


    def run_once(self, host, helper, ap_info, tries=1):
        """ Main entry function for autotest.

        @param host: an Autotest host object, DUT.
        @param helper: a WiFiChaosConnectionTest object, ready to use.
        @param ap_info: a dict of attributes of a specific AP.
        @param tries: an integer, number of connection attempts.
        """
        # Install all of the autotest libraries on the client
        client_at = autotest.Autotest(host)
        client_at.install()

        helper.run_ap_test(ap_info, tries, self.outputdir)

        logging.info('Client test complete, powering down router.')
        helper.power_down(ap_info['configurator'])
        helper.check_test_error()
