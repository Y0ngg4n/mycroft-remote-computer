# Copyright 2018 S. M. Estiaque Ahmed
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import sys
import paramiko
import ipaddress
from wakeonlan import send_magic_packet

from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill
from mycroft.skills.core import intent_handler


class RemoteComputerSkill(MycroftSkill):
    def __init__(self):
        super(RemoteComputerSkill, self).__init__(name="RemoteComputerSkill")

    @intent_handler(IntentBuilder("ComputerOnIntent").require("Computer")
                    .require("On").optionally("Turn"))
    def handle_turn_on_intent(self, message):
        self.log.info("Turning Computer on...")
        try:
            config = self.config_core.get("RemoteComputerSkill", {})

            if not config == {}:
                mac_address = str(config.get("mac_address"))

            else:
                mac_address = str(self.settings.get("mac_address"))

            if not mac_address:
                raise Exception("None found.")

        except Exception as e:
            self.speak_dialog("settings.error")
            self.log.error(e)
            return

        re_mac = "[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$"

        if re.match(re_mac, mac_address.lower()):
            if ':' in mac_address:
                mac_address.replace(':', '.')

            elif '-' in mac_address:
                mac_address.replace('-', '.')

        else:
            self.speak_dialog("invalid", {"word": "mac"})
            return

        prompt_response = self.ask_yesno("ask.confirmation.startup")
        if prompt_response == "yes":
            try:
                send_magic_packet(mac_address)
                self.speak_dialog("computer.on")

            except Exception as e:
                self.speak_dialog("connection.error")
                self.log.error(e)
        elif prompt_response == "no":
            self.speak_dialog("okay")

    @intent_handler(IntentBuilder("ComputerOffIntent").require("Computer")
                    .require("Off").optionally("Turn"))
    def handle_turn_off_intent(self, message):
        self.log.info("Turning Computer off...")
        try:
            config = self.config_core.get("RemoteComputerSkill", {})

            if not config == {}:
                ip_address = str(self.config.get("ip_address"))
                port = int(self.config.get("port"))
                user = str(self.config.get("user"))
                user_password = str(self.config.get("user_password"))
                sudo_password = str(self.config.get("sudo_password"))

            else:
                ip_address = str(self.settings.get("ip_address"))
                port = int(self.settings.get("port"))
                user = str(self.settings.get("user"))
                user_password = str(self.settings.get("user_password"))
                sudo_password = str(self.settings.get("sudo_password"))

            if not ip_address or not port or not user \
                    or not user_password or not sudo_password:
                raise Exception("None found.")

        except Exception as e:
            self.speak_dialog("settings.error")
            self.log.error(e)
            return

        try:
            ip = ipaddress.ip_address(ip_address)

        except ValueError:
            self.speak_dialog("invalid", {"word": "I.P"})
            return

        prompt_response = self.ask_yesno("ask.confirmation.shutdown")
        if prompt_response == "yes":
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(
                    hostname=str(ip),
                    port=port,
                    username=user,
                    password=user_password)

                transport = client.get_transport()

                try:
                    session = transport.open_session()
                    session.set_combine_stderr(True)
                    session.get_pty()
                    session.exec_command("sudo -k shutdown -h now")
                    stdin = session.makefile('wb', -1)
                    stdout = session.makefile('rb', -1)
                    stdin.write(sudo_password + '\n')
                    stdin.flush()
                    stdout.read()
                except Exception as e:
                    self.speak_dialog("connection.error")
                    self.log.error(e)
                try:
                    session = transport.open_session()
                    session.set_combine_stderr(True)
                    session.get_pty()
                    session.exec_command("shutdown /s")
                    stdin = session.makefile('wb', -1)
                    stdout = session.makefile('rb', -1)
                    stdin.write(sudo_password + '\n')
                    stdin.flush()
                    stdout.read()
                except Exception as e:
                    self.speak_dialog("connection.error")
                    self.log.error(e)

                client.close()

                self.speak_dialog("computer.off")

            except Exception as e:
                self.speak_dialog("connection.error")
                self.log.error(e)
        elif prompt_response == "no":
            self.speak_dialog("okay")

    def stop(self):
        pass


def create_skill():
    return RemoteComputerSkill()
