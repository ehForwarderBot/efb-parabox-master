import shutil
from typing import Optional

import cjkwrap
import random
from ehforwarderbot.types import ModuleID
from ehforwarderbot import coordinator, utils
from ehforwarderbot.wizard import DataModel
from ruamel.yaml import YAML

from efb_parabox_master import ParaboxChannel


class DataModel:
    data: dict
    building_default = False

    def __init__(self, profile: str, instance_id: str):
        print("==== epm_wizard, data mod, init", profile)
        coordinator.profile = profile
        self.profile = profile
        self.instance_id = instance_id
        self.channel_id = ParaboxChannel.channel_id

        if instance_id:
            self.channel_id = ModuleID(self.channel_id + "#" + instance_id)
        self.config_path = utils.get_config_path(self.channel_id)
        self.yaml = YAML()
        if not self.config_path.exists():
            self.build_default_config()
        else:
            self.data = self.yaml.load(self.config_path.open())

    def build_default_config(self):
        self.data = {
            "host": "0.0.0.0",
            "port": 8000,
            "token": ''.join(random.sample(
                ['z', 'y', 'x', 'w', 'v', 'u', 't', 's', 'r', 'q', 'p', 'o', 'n', 'm', 'l', 'k', 'j', 'i', 'h', 'g',
                 'f', 'e', 'd', 'c', 'b', 'a'], 10)),
            "sending_interval": 0,
            "compatibility_mode": False
        }

        self.building_default = True

    def save(self):
        if self.building_default:
            with self.config_path.open('w') as f:
                f.write(
                    # TRANSLATORS: This part of text must be formatted in a monospaced font and no line shall exceed the width of a 70-cell-wide terminal.
                    "# ======================================\n"
                    "# EFB Parabox Master Configuration file\n"
                    "# ======================================\n"
                    "#\n"
                    "# This file configures how EFB Parabox Master Channel (EPM) works, and\n"
                    "# Who it belongs to.\n"
                    "#\n"
                    "# Required items\n"
                    "# --------------\n"
                    "#\n"
                    "# [Server Host]\n"
                    "# 127.0.0.1 is used which allows connections only from the current machine. If "
                    "you wish to allow all network machines to connect, you need to pass 0.0.0.0 as hostname.\n "
                )
                f.write("\n")
                self.yaml.dump({"host": self.data['host']}, f)
                f.write("\n")
                f.write(
                    "# [Server Port]\n"
                    "# The port clients will need to connect to.\n"
                )
                f.write("\n")
                self.yaml.dump({"port": self.data['port']}, f)
                f.write("\n")
                f.write(
                    "# [Connection Token]\n"
                    "# The token used for verification.\n"
                )
                f.write("\n")
                self.yaml.dump({"token": self.data['token']}, f)
                f.write("\n")
                f.write(
                    "# [Message Sending Interval]\n"
                    "# The time interval for getting messages to send from the database. If the time is too short, \n"
                    "# it will cause high-frequency query of the database, if the time is too long, it will cause a \n"
                    "# long receiving delay. The unit is second.\n"
                )
                f.write("\n")
                self.yaml.dump({"sending_interval": self.data['sending_interval']}, f)
                f.write("\n")
                f.write(
                    "# [Compatibility Mode]\n"
                    "# Compatibility mode is used to enable compatibility with slaves that does not support the \n"
                    "# feature of obtaining group members' avatars.\n"
                    "# It SHOULD NOT be enabled most of the time.\n"
                )
                f.write("\n")
                self.yaml.dump({"compatibility_mode": self.data['compatibility_mode']}, f)
                f.write("\n")
            with self.config_path.open() as f:
                self.data = self.yaml.load(f)
            self.building_default = False
        else:
            with self.config_path.open('w') as f:
                self.yaml.dump(self.data, f)


def input_host(data: DataModel, default=None):
    prompt = "Your Host: "
    if default:
        prompt += f"[{default}] "
    while True:
        ans = input(prompt)
        if not ans:
            if default:
                return default
            else:
                print("Server host is required. Please try again.")
                continue
        else:
            return ans


def setup_host(data):
    print_wrapped(
        "1. Set up your Server Host\n"
        "---------------------------"
    )
    print()
    if data.data['host']:
        # Config has host ready.
        # Assuming user doesn't need help creating one
        data.data['host'] = input_host(data, data.data['host'])
    else:
        data.data['host'] = input_host(data)


def input_port(data: DataModel, default=None):
    prompt = "Your port: "
    if default:
        prompt += f"[{default}] "
    while True:
        ans = input(prompt)
        if not ans:
            if default:
                return default
            else:
                print("Server port is required. Please try again.")
                continue
        else:
            return int(ans)


def setup_port(data):
    print_wrapped(
        "2. Set up your Server Port\n"
        "---------------------------"
    )
    print()
    if data.data['port']:
        # Config has port ready.
        # Assuming user doesn't need help creating one
        data.data['port'] = input_port(data, data.data['port'])
    else:
        data.data['port'] = input_port(data)


def input_token(data: DataModel, default=None):
    prompt = "Your Token: "
    if default:
        prompt += f"[{default}] "
    while True:
        ans = input(prompt)
        if not ans:
            if default:
                return default
            else:
                print("Connection token is required. Please try again.")
                continue
        else:
            return ans


def setup_token(data):
    print_wrapped(
        "3. Set up your Connection Token\n"
        "---------------------------"
    )
    print()
    if data.data['token']:
        # Config has token ready.
        # Assuming user doesn't need help creating one
        data.data['token'] = input_token(data, data.data['token'])
    else:
        data.data['token'] = input_token(data)


def input_sending_interval(data: DataModel, default=None):
    prompt = "Message sending interval (seconds): "
    if default:
        prompt += f"[{default}] "
    while True:
        ans = input(prompt)
        if not ans:
            if default:
                return default
            else:
                print("Please try again.")
                continue
        else:
            return int(ans)


def setup_sending_interval(data):
    print_wrapped(
        "4. Set up Message sending interval\n"
        "---------------------------\n"
        "The time interval for querying messages to be sent from the database. If the time is too short, "
        "it will cause high-frequency query of the database, if the time is too long, it may cause a long receiving "
        "delay "
    )
    print()
    if data.data['sending_interval']:
        # Config has port ready.
        # Assuming user doesn't need help creating one
        data.data['sending_interval'] = input_sending_interval(data, data.data['sending_interval'])
    else:
        data.data['sending_interval'] = input_sending_interval(data)


def input_compatibility_mode(data: DataModel, default=None):
    prompt = "Enable compatibility mode? (y/n): "
    if default:
        prompt += f"[{default}] "
    while True:
        ans = input(prompt)
        if not ans:
            if default:
                return default.lower().strip() == 'y'
            else:
                print("No input detected. Please try again.")
                continue
        else:
            return ans.lower().strip() == 'y'


def setup_compatibility_mode(data):
    print_wrapped(
        "5. Enable compatibility mode\n"
        "---------------------------\n"
        "Compatibility mode is used to enable compatibility with slaves that does not support the feature of \n"
        "obtaining group members' avatars.\n"
        "It SHOULD NOT be enabled most of the time"
    )
    print()
    if data.data['compatibility_mode']:
        # Config has token ready.
        # Assuming user doesn't need help creating one
        data.data['compatibility_mode'] = input_compatibility_mode(data, 'n')
    else:
        data.data['compatibility_mode'] = input_compatibility_mode(data, 'n')


def print_wrapped(text):
    paras = text.split("\n")
    for i in paras:
        print(*cjkwrap.wrap(i), sep="\n")


def prerequisites_check():
    print("Checking ffmpeg installation...", end="", flush=True)
    if shutil.which('ffmpeg') is None:
        print("FAILED")
        print_wrapped("ffmpeg is not found in current $PATH.")
        exit(1)
    print("OK")

    print()


def wizard(profile, instance_id):
    data = DataModel(profile, instance_id)

    prerequisites_check()
    print_wrapped(
        "================================\n"
        "EFB Parabox Master Setup Wizard\n"
        "================================\n"
        "\n"
        "This wizard will guide you to setup your EFB Parabox Master channel "
        "(EPM). This would be really fast and simple."
    )

    print()
    setup_host(data)
    setup_port(data)
    setup_token(data)
    setup_sending_interval(data)
    setup_compatibility_mode(data)

    print("Saving configurations...", end="", flush=True)
    data.save()
    print("OK")

    print()
    print_wrapped(
        "Congratulations! You have finished the setup wizard for EFB Parabox "
        "Master Channel."
    )
