import shutil
from typing import Optional

import cjkwrap
from ehforwarderbot.types import ModuleID
from ehforwarderbot import coordinator, utils
from ehforwarderbot.wizard import DataModel
from ruamel.yaml import YAML

from efb_parabox_master import ParaboxChannel


class DataModel:
    data: dict
    building_default = False

    def __init__(self, profile: str, instance_id: str):
        print("==== etm_wizard, data mod, init", profile)
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
            "host": "127.0.0.1",
            "port": "",
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
                    "# By default the 127.0.0.1 is used which allows connections only from the current machine. If "
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
        "---------------------------\n"
        "EPM requires you to have a Telegram bot ready with you to start with."
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
            return ans


def setup_port(data):
    print_wrapped(
        "1. Set up your Server Port\n"
        "---------------------------\n"
        "EPM requires you to have a Telegram bot ready with you to start with."
    )
    print()
    if data.data['port']:
        # Config has port ready.
        # Assuming user doesn't need help creating one
        data.data['port'] = input_port(data, data.data['port'])
    else:
        data.data['port'] = input_port(data)


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

    print("Saving configurations...", end="", flush=True)
    data.save()
    print("OK")

    print()
    print_wrapped(
        "Congratulations! You have finished the setup wizard for EFB Parabox "
        "Master Channel."
    )
