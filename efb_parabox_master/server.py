from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParaboxChannel


class ServerManager:

    def __init__(self, channel: 'ParaboxChannel'):
        self.channel: 'ParaboxChannel' = channel

    def pulling(self):
        pass

    def graceful_stop(self):
        pass
