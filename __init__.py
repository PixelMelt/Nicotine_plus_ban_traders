import enum
import os

from pynicotine.pluginsystem import BasePlugin
from pynicotine.events import events


@enum.unique
class STATUS(enum.Enum):
    PENDING = "pending"
    OK = "ok"


# REFERENCE: https://github.com/nicotine-plus/nicotine-plus/blob/master/pynicotine/uploads.py#L836
# In-progress uploads are cancelled on user ban.

# TODO: Ignore users with no user info?

WHITELISTED_USERS = {
    "awesomeme"  # covers.musichoarders.xyz bot
}

# Common music file extensions
MUSIC_EXTENSIONS = {
    '.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma', '.opus', '.ape',
    '.mpc', '.mp4', '.m4p', '.3gp', '.aiff', '.au', '.ra', '.ac3', '.dts',
    '.tta', '.wv', '.mka', '.dsf', '.dff', '.mp2', '.amr', '.m4r', '.caf',
    '.tak', '.aifc', '.mod', '.s3m', '.xm', '.it'
}

# Detection thresholds
MINIMUM_PUBLIC_FILES = 1

class Plugin(BasePlugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.settings = {
            "ban_uploads": True,
            "ban_searches": True,
            "send_messages": False,
            "send_search_messages": False,
            "upload_message":
            "You seem to have a lot of private music files, please message to ask for an unban if you are not a trader.",
            "search_message":
            "You seem to have a lot of private music files, please message to ask for an unban if you are not a trader.",
            "open_private_chat": True,
            "debug_logging": False,
            "private_threshold": 95
        }

        self.metasettings = {
            "ban_uploads": {
                "description":
                "Ban users with predominantly private music files from uploads",
                "type": "bool"
            },
            "ban_searches": {
                "description":
                "Ban users with fully private music shares in searches",
                "type": "bool"
            },
            "private_threshold": {
                "description":
                "Percentage threshold for private music files (0-100). Users with this percentage or higher of private music files will be banned.",
                "type": "int"
            },
            "send_messages": {
                "description": "Send messages to users banned from uploads",
                "type": "bool"
            },
            "send_search_messages": {
                "description": "Send messages to users banned from searches",
                "type": "bool"
            },
            "upload_message": {
                "description":
                "Private chat message to send to traders banned from uploads.\nEach line is sent as a separate message, too many message lines may get you temporarily banned for spam!",
                "type": "textview"
            },
            "search_message": {
                "description":
                "Private chat message to send to traders banned from searches.\nEach line is sent as a separate message, too many message lines may get you temporarily banned for spam!",
                "type": "textview"
            },
            "open_private_chat": {
                "description": "Open chat tabs when sending private messages",
                "type": "bool"
            },
            "debug_logging": {
                "description": "Enable verbose debug logging",
                "type": "bool"
            }
        }

        self.probed: dict[str, STATUS] = {}

        events.connect("file-search-response", self._file_search_response)

    def count_music_files(self, folders: dict) -> int:
        """Count music files in the given folder structure."""
        music_count = 0

        for files in folders.values():
            for file_info in files:
                try:
                    # file_info is a tuple: (file_id, filename, size, None, {})
                    if isinstance(file_info,
                                  (list, tuple)) and len(file_info) > 1:
                        filename = str(
                            file_info[1])  # filename is second element
                    elif isinstance(file_info, str):
                        filename = file_info
                    else:
                        continue

                    file_ext = os.path.splitext(filename.lower())[1]
                    if file_ext in MUSIC_EXTENSIONS:
                        music_count += 1
                except (AttributeError, IndexError, TypeError):
                    continue

        return music_count

    def _is_whitelisted(self, user: str) -> bool:
        """Check if user is whitelisted."""
        return user in WHITELISTED_USERS or user in self.core.buddies.users

    def _send_upload_ban_message(self, user: str) -> None:
        """Send upload ban message to user if enabled."""
        ban_msg: str = self.settings["upload_message"]

        if ban_msg:
            for line in ban_msg.splitlines():
                self.send_private(user,
                                  line,
                                  show_ui=self.settings["open_private_chat"],
                                  switch_page=False)

    def _send_search_ban_message(self, user: str) -> None:
        """Send search ban message to user if enabled."""
        ban_msg: str = self.settings["search_message"]

        if ban_msg:
            for line in ban_msg.splitlines():
                self.send_private(user,
                                  line,
                                  show_ui=self.settings["open_private_chat"],
                                  switch_page=False)

    def check_user(self, user: str, public_folders: dict,
                   private_folders: dict):
        self.probed[user] = STATUS.OK

        if self._is_whitelisted(user):
            return

        public_music_count = self.count_music_files(public_folders)
        private_music_count = self.count_music_files(private_folders)

        if self.settings["debug_logging"]:
            self.log(
                f"user '{user}' has {public_music_count} public music files, {private_music_count} private music files"
            )

        # nothing private here, yay
        if private_music_count == 0:
            self.log(
                f"user '{user}' has no private music files, not a trader.")
            return

        # no music files at all
        if public_music_count == 0 and private_music_count == 0:
            if self.settings["debug_logging"]:
                self.log(
                    f"user '{user}' has no music files at all, not a music trader."
                )
            return

        # traders have a few public files sometimes
        total_files = public_music_count + private_music_count
        private_ratio = private_music_count / total_files
        threshold_ratio = self.settings["private_threshold"] / 100.0

        if public_music_count >= MINIMUM_PUBLIC_FILES or private_ratio < threshold_ratio:
            if self.settings["debug_logging"]:
                self.log(
                    f"user '{user}' has some private music files but less than {self.settings['private_threshold']}%. most likely not a trader"
                )
            return

        # user already banned? ignore them
        if self.core.network_filter.is_user_banned(user):
            if self.settings["debug_logging"]:
                self.log(f"user '{user}' is already banned.")
            return

        if self.settings["send_messages"]:
            self._send_upload_ban_message(user)

        self.core.network_filter.ban_user(user)

        self.log(
            f"Banned user '{user}' for being a trader with >= {self.settings['private_threshold']}% private music files ratio."
        )

    def upload_queued_notification(self, user: str, _virtualfile, _realfile):
        if not self.settings["ban_uploads"]:
            return

        if user in self.probed:
            return

        self.probed[user] = STATUS.PENDING

        browsed_user = self.core.userbrowse.users.get(user)

        if browsed_user:
            if self.settings["debug_logging"]:
                self.log(f"BrowseUser object of user '{user}' found.")
            self.check_user(user, browsed_user.public_folders,
                            browsed_user.private_folders)
        else:
            # No BrowseUser object, so their file list hasn't been networked yet.
            if self.settings["debug_logging"]:
                self.log(
                    f"BrowseUser object of user '{user}' not found. Requesting user shares..."
                )

            self.core.userbrowse.browse_user(user, switch_page=False)

    def user_stats_notification(self, user: str, stats: dict):
        if user in self.probed and self.probed[user] != STATUS.PENDING:
            return

        if stats["source"] != "peer":
            return

        if self.settings["debug_logging"]:
            self.log(f"Peer stats of user '{user}' received.")

        browsed_user = self.core.userbrowse.users.get(user)

        # Check if this event originates from the browse_user call in upload_queued_notification.
        origin_from_plugin = user in self.probed and self.probed[
            user] == STATUS.PENDING

        if browsed_user:
            if self.settings["debug_logging"]:
                self.log(f"BrowseUser object of user '{user}' found.")
            self.check_user(user, browsed_user.public_folders,
                            browsed_user.private_folders)
        else:
            # No BrowseUser object? Something has gone wrong and we can't recover.
            if self.settings["debug_logging"]:
                self.log(f"BrowseUser object of user '{user}' not found.")

        # Try to only close the browse page if it originates from our plugin.
        if origin_from_plugin:
            self.core.userbrowse.remove_user(user)

        self.probed[user] = STATUS.OK

    def _file_search_response(self, msg):
        if not self.settings["ban_searches"]:
            return

        user: str = msg.username

        if self._is_whitelisted(user):
            return

        # only ban for completely private shares
        if msg.list or not msg.privatelist:
            return

        # user already banned? ignore them
        if self.core.network_filter.is_user_banned(user):
            if self.settings["debug_logging"]:
                self.log(f"user '{user}' is already banned.")
            return

        # TODO: check if this gets you temp banned or rate limited
        if self.settings["send_search_messages"]:
            self._send_search_ban_message(user)

        self.core.network_filter.ban_user(user)

        self.log(
            f"Banned user '{user}' for having completely private music shares found by a search query."
        )
