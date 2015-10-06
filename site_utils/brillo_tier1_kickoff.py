#!/usr/bin/python
# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
import httplib
import logging
import os
import sys
import urllib2

import common
from autotest_lib.client.common_lib import control_data
from autotest_lib.server import hosts
from autotest_lib.server.hosts import moblab_host
from autotest_lib.server.cros.dynamic_suite import control_file_getter


LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
MOBLAB_STATIC_DIR = '/mnt/moblab/static'
MOBLAB_TMP_DIR = os.path.join(MOBLAB_STATIC_DIR, 'tmp')
TARGET_IMAGE_NAME = 'brillo/target'
DEVSERVER_STAGE_URL_TEMPLATE = ('http://%(moblab)s:8080/stage?local_path='
                                '%(staged_dir)s&artifacts=full_payload')


class KickOffException(Exception):
    """Exception class for errors in the test kick off process."""


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print log statements.')
    parser.add_argument('-p', '--payload',
                        help='Path to the update payload for autoupdate '
                             'testing.')
    parser.add_argument('-m', '--moblab_host',
                        help='MobLab hostname or IP to launch tests.')
    parser.add_argument('-a', '--adb_host',
                        help='Hostname or IP of the adb_host connected to the '
                             'Brillo DUT. Default is to assume it is connected '
                             'directly to the MobLab.')
    return parser.parse_args()


def add_adbhost(moblab, adb_hostname):
    """Add the ADB host to the MobLab's host list.

    @param moblab: MoblabHost representing the MobLab being used to launch the
                   tests.
    @param adb_hostname: Hostname of the ADB Host.

    @returns The adb host to use for launching tests.
    """
    if not adb_hostname:
        adb_hostname = 'localhost'
        moblab.enable_adb_testing()
    if all([host.hostname != adb_hostname for host in moblab.afe.get_hosts()]):
        moblab.add_dut(adb_hostname)
    return adb_hostname


def stage_payload(moblab, payload):
    """Stage the payload on the MobLab.

    # TODO (sbasi): Add support to stage source payloads.

    @param moblab: MoblabHost representing the MobLab being used to launch the
                   testing.
    @param payload: Path to the Brillo payload that will be staged.
    """
    if not os.path.exists(payload):
        raise KickOffException('FATAL: payload %s does not exist!')
    stage_tmp_dir = os.path.join(MOBLAB_TMP_DIR, TARGET_IMAGE_NAME)
    stage_dest_dir = os.path.join(MOBLAB_STATIC_DIR, TARGET_IMAGE_NAME)
    stage_tmp_file = os.path.join(stage_tmp_dir, 'target_full_.bin')
    moblab.run('mkdir -p %s' % stage_tmp_dir)
    moblab.send_file(payload, stage_tmp_file)
    moblab.run('chown -R moblab:moblab %s' % MOBLAB_TMP_DIR)
    # Remove any artifacts that were previously staged.
    moblab.run('rm -rf %s' % stage_dest_dir)
    try:
        stage_url = DEVSERVER_STAGE_URL_TEMPLATE % dict(
                moblab=moblab.hostname, staged_dir=stage_tmp_dir)
        res = urllib2.urlopen(stage_url).read()
    except (urllib2.HTTPError, httplib.HTTPException, urllib2.URLError) as e:
        logging.error('Unable to stage payload on moblab. Error: %s', e)
    else:
        if res == 'Success':
            logging.debug('Payload is staged on Moblab as %s',
                          TARGET_IMAGE_NAME)
        else:
            logging.error('Staging failed. Error Message: %s', res)
    finally:
        moblab.run('rm -rf %s' % stage_tmp_dir)


def schedule_pts(moblab, host):
    """Schedule the Brillo PTS Sequence.

    @param moblab: MoblabHost representing the MobLab being used to launch the
                   testing.
    @param host: Hostname of the DUT.
    """
    getter = control_file_getter.FileSystemGetter(
            [os.path.dirname(os.path.dirname(os.path.realpath(__file__)))])
    pts_controlfile_conts = getter.get_control_file_contents_by_name(
            'control.brillo_pts')
    job_id = moblab.afe.create_job(
            pts_controlfile_conts, name='brillo pts sequence',
            control_type=control_data.CONTROL_TYPE_NAMES.SERVER,
            hosts=[host], require_ssp=False)
    return job_id


def main(args):
    """main"""
    args = parse_args()
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format=LOGGING_FORMAT)
    if not args.moblab_host:
        logging.error('FATAL: a MobLab IP/Hostname is required.')
        return 1

    # Create a MoblabHost to interact with the Moblab device.
    moblab = hosts.create_host(args.moblab_host,
                               host_class=moblab_host.MoblabHost)
    try:
        moblab.afe.get_hosts()
    except Exception as e:
        logging.error("Unable to communicate with the MobLab's web frontend. "
                      "Please verify the MobLab and its web frontend are up "
                      "running at http://%s/\nException:%s", args.moblab_host,
                      e)
        return 1
    # Add the adb host object to the MobLab.
    adb_host = add_adbhost(moblab, args.adb_host)
    # Stage the payload if provided.
    if args.payload:
        stage_payload(moblab, args.payload)
    # Launch PTS.
    sequence_jobid = schedule_pts(moblab, adb_host)
    # TODO (sbasi): Add job monitoring, and result collection.
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
