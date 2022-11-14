import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise Exception("Python 3.6 or higher is required. Your version is %s." % sys.version)

__version__ = ""
exec(open("efb_parabox_master/__version__.py").read())

setup(
    name='efb_parabox_master',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    version=__version__,
    description='Parabox Master Channel for EH Forwarder Bot.',
    author='Ojhdt',
    license='AGPLv3+',
    include_package_data=True,
    python_requires='>=3.6',
    keywords=['ehforwarderbot', 'EH Forwarder Bot', 'EH Forwarder Bot Master Channel', 'Parabox'],
    classifiers=[
        "Development Status :: 1 - Alpha",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Communications :: Chat",
        "Topic :: Utilities"
    ],
    install_requires=[
        "ehforwarderbot>=2.0.0",
        "requests",
        "pillow",
        "retrying",
        "bullet>=2.2.0",
        "cjkwrap",
        "typing-extensions>=3.7.4.1",
    ],
    entry_points={
        "ehforwarderbot.master": "ojhdt.parabox = efb_parabox_master:ParaboxChannel",
        "ehforwarderbot.wizard": "ojhdt.parabox = efb_parabox_master.wizard:wizard"
    }
)