import enum

from pynicotine.pluginsystem import BasePlugin
from pynicotine.events import events

@enum.unique
class STATUS(enum.StrEnum):
    PENDING = enum.auto()
    OK = enum.auto()

# REFERENCE: https://github.com/nicotine-plus/nicotine-plus/blob/master/pynicotine/uploads.py#L836
# In-progress uploads are cancelled on user ban.

WHITELISTED_USERS = {
    "awesomeme" # covers.musichoarders.xyz bot
}

class Plugin(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = {
            "message": "You seem to have a lot of private folders, please message to ask for an unban if you are not a trader.",
            "open_private_chat": True,
            "ban_in_searches": True,
            "message_in_searches": False
        }

        self.metasettings = {
            "message": {
                "description": "Private chat message to send to traders.\nEach line is sent as a separate message, too many message lines may get you temporarily banned for spam!",
                "type": "textview"
            },
            "open_private_chat": {
                "description": "Open chat tabs when sending private messages to traders",
                "type": "bool"
            },
            "ban_in_searches": {
                "description": "Autoban users with fully private shares in searches",
                "type": "bool"
            },
            "message_in_searches": {
                "description": "Send a message to users banned via searches (may cause rate-limiting)",
                "type": "bool"
            }
        }

        self.Probed: dict[str, STATUS] = {}

        events.connect("file-search-response", self._file_search_response)

    def check_user(self, user: str, public_folders: dict, private_folders: dict):
        self.Probed[user] = STATUS.OK

        if user in WHITELISTED_USERS:
            return

        # buddies are whitelisted :)
        if user in self.core.buddies.users:
            return

        publicCount, privateCount = len(public_folders), len(private_folders)

        # nothing private here, yay
        if privateCount == 0:
            self.log("user '%s' has no private folders, not a trader.", user)
            return

        # traders have a few public files sometimes
        if publicCount >= 1 and privateCount / (publicCount + privateCount) <= 0.05:
            self.log("user '%s' has some private folders but less than 5%. most likely not a trader", user)
            return

        # user already banned? ignore them
        if self.core.network_filter.is_user_banned(user):
            self.log("user '%s' is already banned.", user)
            return

        banMsg: str = self.settings["message"]

        if banMsg:
            for line in banMsg.splitlines():
                self.send_private(user, line, show_ui = self.settings["open_private_chat"], switch_page = False)

        self.core.network_filter.ban_user(user)

        self.log("Banned user '%s' for being a trader with <= 95 percent private shares ratio.", user)

    def upload_queued_notification(self, user: str, virualfile, realfile):
        if user in self.Probed:
            return

        self.Probed[user] = STATUS.PENDING

        browsedUser = self.core.userbrowse.users.get(user)

        if browsedUser:
            self.log("BrowseUser object of user '%s' found.", user)
            self.check_user(user, browsedUser.public_folders, browsedUser.private_folders)
        else:
            # No BrowseUser object, so their file list hasn't been networked yet.
            self.log("BrowseUser object of user '%s' not found. Requesting user shares...", user)

            self.core.userbrowse.browse_user(user, switch_page = False)

    def user_stats_notification(self, user: str, stats: dict):
        if user in self.Probed and self.Probed[user] != STATUS.PENDING:
            return

        if stats["source"] != "peer":
            return

        self.log("Peer stats of user '%s' received.", user)

        browsedUser = self.core.userbrowse.users.get(user)

        # Check if this event originates from the browse_user call in upload_queued_notification.
        originFromPlugin = user in self.Probed and self.Probed[user] == STATUS.PENDING

        if browsedUser:
            self.log("BrowseUser object of user '%s' found.", user)
            self.check_user(user, browsedUser.public_folders, browsedUser.private_folders)
        else:
            # No BrowseUser object? Something has gone wrong and we can't recover.
            self.log("BrowseUser object of user '%s' not found.", user)
            pass

        # Try to only close the browse page if it originates from our plugin.
        if originFromPlugin:
            self.core.userbrowse.remove_user(user)

        self.Probed[user] = STATUS.OK

    def _file_search_response(self, msg):
        if not self.settings["ban_in_searches"]:
            return

        user: str = msg.username

        if user in WHITELISTED_USERS:
            return

        # buddies are whitelisted :)
        if user in self.core.buddies.users:
            return

        if msg.list or not msg.privatelist:
            return

        # user already banned? ignore them
        if self.core.network_filter.is_user_banned(user):
            self.log("user '%s' is already banned.", user)
            return

        banMsg: str = self.settings["message"]

        # TODO: check if this gets you temp banned or rate limited
        if banMsg and self.settings["message_in_searches"]:
            for line in banMsg.splitlines():
                self.send_private(user, line, show_ui = self.settings["open_private_chat"], switch_page = False)

        self.core.network_filter.ban_user(user)

        self.log("Banned user '%s' for having completely private shares found by a search query.", user)