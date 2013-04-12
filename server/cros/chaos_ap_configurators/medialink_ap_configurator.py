# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Class to control MediaLink wapr150n router."""

import logging
import urlparse

import ap_configurator


class MediaLinkAPConfigurator(ap_configurator.APConfigurator):
    """Class to control MediaLink wapr150n router."""


    def __init__(self, ap_config=None):
        super(MediaLinkAPConfigurator, self).__init__(ap_config=ap_config)
        self.current_mode = self.mode_b
        self.add_item_to_command_list(self._set_mode, (self.current_mode, ),
                                      1, 500)


    def _alert_handler(self, alert):
        text = alert.text
        if 'Please input 10 or 26 characters of wep key1 !' in text:
            alert.accept()
            raise RuntimeError('We got an alert. %s' % text)
        elif 'turn on wireless' in text:
            alert.accept()
            raise RuntimeError('Please enable wireless. %s' % text)
        elif 'Invalid Wep key1 format' in text:
            alert.accept()
            raise RuntimeError('WEP key should be numbers. %s' % text)
        else:
            raise RuntimeError('We have an unhandled alert: %s' % text)


    def get_number_of_pages(self):
        return 2


    def get_supported_bands(self):
        return [{'band': self.band_2ghz,
                 'channels': ['AutoSelect', 1, 2, 3, 4, 5, 6, 7,
                              8, 9, 10, 11, 12, 13]}]


    def get_supported_modes(self):
        return [{'band': self.band_2ghz,
                 'modes': [self.mode_b, self.mode_g, self.mode_b |
                           self.mode_g, self.mode_b | self.mode_g |
                           self.mode_n]}]


    def is_security_mode_supported(self, security_mode):
        return security_mode in (self.security_type_disabled,
                                 self.security_type_wpapsk,
                                 self.security_type_wpa2psk,
                                 self.security_type_wep)


    def navigate_to_page(self, page_number):
        if page_number == 1:
            url = urlparse.urljoin(self.admin_interface_url,
                                   'wireless_basic.asp')
            self.get_url(url, page_title='wireless_basic.asp')
            self.wait_for_object_by_xpath('//input[@name="ssid"]')
        elif page_number == 2:
            url = urlparse.urljoin(self.admin_interface_url,
                                   'wireless_security.asp')
            self.get_url(url, page_title='wireless_security.asp')
            self.wait_for_object_by_xpath('//select[@name="security_mode"]')
        else:
            raise RuntimeError('Invalid page number passed.  Number of pages '
                               '%d, page value sent was %d' %
                               (self.get_number_of_pages(), page_number))


    def save_page(self, page_number):
        self.click_button_by_xpath('//input[@type="button" and @value="Apply"]',
                                   alert_handler=self._alert_handler)
        self.wait_for_object_by_xpath('//input[@type="button" and @value="OK"]')


    def set_mode(self, mode, band=None):
        self.add_item_to_command_list(self._set_mode, (mode, ), 1, 800)


    def _set_mode(self, mode):
        if mode == self.mode_b:
            mode_popup = '11b mode'
        elif mode == self.mode_g:
            mode_popup = '11g mode'
        elif mode == (self.mode_b | self.mode_g):
            mode_popup = '11b/g mixed mode'
        elif mode == (self.mode_b | self.mode_g | self.mode_n):
            mode_popup = '11b/g/n mixed mode'
        else:
            raise RuntimeError('Invalid mode passed: %x' % mode)
        self.current_mode = mode
        self._set_radio(enabled=True)
        xpath = '//select[@name="wirelessmode"]'
        self.select_item_from_popup_by_xpath(mode_popup, xpath)


    def set_radio(self, enabled=True):
        self.add_item_to_command_list(self._set_radio, (enabled, ), 1, 1000)


    def _set_radio(self, enabled=True):
        xpath = '//input[@name="enablewireless" and @type="checkbox"]'
        self.set_check_box_selected_by_xpath(xpath, selected=enabled,
                                             wait_for_xpath=None,
                                             alert_handler=self._alert_handler)


    def set_ssid(self, ssid):
        self.add_item_to_command_list(self._set_ssid, (ssid,), 1, 900)


    def _set_ssid(self, ssid):
        self._set_radio(enabled=True)
        xpath = '//input[@name="ssid"]'
        self.set_content_of_text_field_by_xpath(ssid, xpath)


    def set_channel(self, channel):
        self.add_item_to_command_list(self._set_channel, (channel,), 1, 900)


    def _set_channel(self, channel):
        position = self._get_channel_popup_position(channel)
        self._set_radio(enabled=True)
        channel_choices = ['AutoSelect', '2412MHz (Channel 1)',
                           '2417MHz (Channel 2)', '2422MHz (Channel 3)',
                           '2427MHz (Channel 4)', '2432MHz (Channel 5)',
                           '2437MHz (Channel 6)', '2442MHz (Channel 7)',
                           '2447MHz (Channel 8)', '2452MHz (Channel 9)',
                           '2457MHz (Channel 10)', '2462MHz (Channel 11)',
                           '2467MHz (Channel 12)', '2472MHz (Channel 13)']
        if self.current_mode == self.mode_b:
            xpath = '//select[@name="sz11bChannel"]'
        else:
            xpath = '//select[@name="sz11gChannel"]'
        self.select_item_from_popup_by_xpath(channel_choices[position], xpath,
                                             alert_handler=self._alert_handler)


    def set_band(self, band):
        logging.debug('This router %s does not support multiple bands.',
                      self.get_router_name())
        return None


    def set_security_disabled(self):
        self.add_item_to_command_list(self._set_security_disabled, (), 2, 900)


    def _set_security_disabled(self):
        xpath = '//select[@name="security_mode"]'
        self.select_item_from_popup_by_xpath('Disable', xpath)


    def set_security_wep(self, key_value, authentication):
        self.add_item_to_command_list(self._set_security_wep,
                                      (key_value, authentication), 2, 900)


    def _set_security_wep(self, key_value, authentication):
        logging.debug('This router %s does not support WEP authentication type:'
                      ' %s', self.get_router_name(), authentication)
        popup = '//select[@name="security_mode"]'
        text_field = '//input[@name="wep_key_1"]'
        self.select_item_from_popup_by_xpath('Mixed WEP', popup,
                                             wait_for_xpath=text_field)
        self.set_content_of_text_field_by_xpath(key_value, text_field,
                                                abort_check=True)


    def set_security_wpapsk(self, shared_key, update_interval=1800):
        self.add_item_to_command_list(self._set_security_wpapsk,
                                      (shared_key,update_interval,), 2, 900)


    def _set_security_wpapsk(self, shared_key, update_interval=1800):
        if update_interval < 600 | update_interval > 7200:
            logging.debug('Invalid update interval, setting it to 1800.')
            update_interval = 1800
        popup = '//select[@name="security_mode"]'
        key_field = '//input[@name="passphrase"]'
        self.select_item_from_popup_by_xpath('WPA - Personal', popup,
                                             wait_for_xpath=key_field)
        self.set_content_of_text_field_by_xpath(shared_key, key_field,
                                                abort_check=True)
        interval_field = ('//input[@name="keyRenewalInterval"]')
        self.set_content_of_text_field_by_xpath(str(update_interval),
                                                interval_field)


    def set_visibility(self, visible=True):
        self.add_item_to_command_list(self._set_visibility, (visible,), 1, 900)


    def _set_visibility(self, visible=True):
        self._set_radio(enabled=True)
        int_value = int(visible)
        xpath = '//input[@name="broadcastssid" and @value="%d"]' % int_value
        self.click_button_by_xpath(xpath)
