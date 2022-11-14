import shutil

import cjkwrap
from ehforwarderbot.wizard import DataModel


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

    prerequisites_check()

    print_wrapped(
        "================================\n"
        "EFB Telegram Master Setup Wizard\n"
        "================================\n"
        "\n"
        "This wizard will guide you to setup your EFB Telegram Master channel "
        "(ETM). This would be really fast and simple."
    )
    print()

    print()
    print_wrapped(
        "Congratulations! You have finished the setup wizard for EFB Parabox "
        "Master Channel."
    )
