import shutil
import logging
import traceback
import configparser
import discord

LOG = logging.getLogger(__name__)


class PermissionsDefaults:
    """ TODO """
    perms_file = 'config/permissions.ini'

    DMCommandWhiteList = set()
    DMCommandBlackList = set()
    CommandWhiteList = set()
    CommandBlackList = set()
    IgnoreNonVoice = set()
    GrantToRoles = set()
    UserList = set()

    MaxSongs = 0
    MaxSongLength = 0
    MaxPlaylistLength = 0
    AllowPlaylists = True
    InstaSkip = False
    AllowHigherVolume = False


class Permissions:
    """ TODO """
    def __init__(self, config_file, grant_all=None):
        self.config_file = config_file
        self.config = configparser.ConfigParser(interpolation=None)

        if not self.config.read(config_file, encoding='utf-8'):
            LOG.info("Permissions file not found, \
            copying example_permissions.ini")

            try:
                shutil.copy('config/example_permissions.ini', config_file)
                self.config.read(config_file, encoding='utf-8')

            except Exception as error:
                traceback.print_exc()
                raise RuntimeError(
                    "Unable to copy config/example_permissions.ini to %s: %s",
                    (config_file, error))

        self.default_group = PermissionGroup('Default', self.config['Default'])
        self.groups = set()

        for section in self.config.sections():
            self.groups.add(PermissionGroup(section, self.config[section]))

        # Create a fake section to fallback onto the permissive default values
        # to grant to the owner
        # noinspection PyTypeChecker
        owner_group = PermissionGroup(
            "Owner (auto)", configparser.SectionProxy(self.config, None))
        if hasattr(grant_all, '__iter__'):
            owner_group.user_list = set(grant_all)

        self.groups.add(owner_group)

    async def async_validate(self, bot):
        """ TODO """
        LOG.debug("Validating permissions...")

        owner_groups = discord.utils.get(self.groups, name="Owner (auto)")
        if 'auto' in owner_groups.user_list:
            LOG.debug("Fixing automatic owner group")
            owner_groups .user_list = {bot.config.owner_id}

    def save(self):
        """ TODO """
        with open(self.config_file, 'w') as file_:
            self.config.write(file_)

    def for_user(self, user):
        """
        Returns the first PermissionGroup a user belongs to
        :param user: A discord User or Member object
        """

        for group in self.groups:
            if user.id in group.user_list:
                return group

        # The only way I could search for roles is if I add a `server=None`
        # param and pass that too
        if isinstance(user, discord.User):
            return self.default_group

        # We loop again so that we don't return a role based group before we
        # find an assigned one
        for group in self.groups:
            for role in user.roles:
                if role.id in group.granted_to_roles:
                    return group

        return self.default_group

    def create_group(self, name, **kwargs):
        """ TODO """
        self.config.read_dict({name: kwargs})
        self.groups.add(PermissionGroup(name, self.config[name]))
        # TODO: Test this


class PermissionGroup:
    """ TODO """
    def __init__(self, name, section_data):
        self.name = name

        self.dm_command_whitelist = section_data.get(
            'DMCommandWhiteList', fallback=PermissionsDefaults.DMCommandWhiteList)
        self.dm_command_blacklist = section_data.get(
            'DMCommandBlackList', fallback=PermissionsDefaults.DMCommandBlackList)
        self.command_whitelist = section_data.get(
            'CommandWhiteList', fallback=PermissionsDefaults.CommandWhiteList)
        self.command_blacklist = section_data.get(
            'CommandBlackList', fallback=PermissionsDefaults.CommandBlackList)
        self.ignore_non_voice = section_data.get(
            'IgnoreNonVoice', fallback=PermissionsDefaults.IgnoreNonVoice)
        self.granted_to_roles = section_data.get(
            'GrantToRoles', fallback=PermissionsDefaults.GrantToRoles)
        self.user_list = section_data.get(
            'UserList', fallback=PermissionsDefaults.UserList)
        self.max_songs = section_data.get(
            'MaxSongs', fallback=PermissionsDefaults.MaxSongs)
        self.max_song_length = section_data.get(
            'MaxSongLength', fallback=PermissionsDefaults.MaxSongLength)
        self.max_playlist_length = \
            section_data.get(
                'MaxPlaylistLength',
                fallback=PermissionsDefaults.MaxPlaylistLength)
        self.allow_playlists = section_data.get(
            'AllowPlaylists', fallback=PermissionsDefaults.AllowPlaylists)
        self.instaskip = section_data.get(
            'InstaSkip', fallback=PermissionsDefaults.InstaSkip)
        self.allow_higher_volume = \
            section_data.get(
                'AllowHigherVolume',
                fallback=PermissionsDefaults.AllowHigherVolume)

        self.validate()

    def validate(self):
        """ TODO """
        if self.dm_command_whitelist:
            self.dm_command_whitelist = set(
                self.dm_command_whitelist.lower().split())
        if self.dm_command_blacklist:
            self.dm_command_blacklist = set(
                self.dm_command_blacklist.lower().split())

        if self.command_whitelist:
            self.command_whitelist = set(
                self.command_whitelist.lower().split())

        if self.command_blacklist:
            self.command_blacklist = set(
                self.command_blacklist.lower().split())

        if self.ignore_non_voice:
            self.ignore_non_voice = set(self.ignore_non_voice.lower().split())

        if self.granted_to_roles:
            self.granted_to_roles = set(self.granted_to_roles.split())

        if self.user_list:
            self.user_list = set(self.user_list.split())

        try:
            self.max_songs = max(0, int(self.max_songs))
        except:
            self.max_songs = PermissionsDefaults.MaxSongs

        try:
            self.max_song_length = max(0, int(self.max_song_length))
        except:
            self.max_song_length = PermissionsDefaults.MaxSongLength

        try:
            self.max_playlist_length = max(0, int(self.max_playlist_length))
        except:
            self.max_playlist_length = PermissionsDefaults.MaxPlaylistLength

        self.allow_playlists = configparser.RawConfigParser.BOOLEAN_STATES.get(
            self.allow_playlists, PermissionsDefaults.AllowPlaylists
        )

        self.instaskip = configparser.RawConfigParser.BOOLEAN_STATES.get(
            self.instaskip, PermissionsDefaults.InstaSkip
        )

        self.allow_higher_volume = \
            configparser.RawConfigParser.BOOLEAN_STATES.get(
                self.allow_higher_volume, PermissionsDefaults.AllowHigherVolume
            )

    @staticmethod
    def _process_list(seq,
                      *,
                      split=' ',
                      lower=True,
                      strip=', ',
                      coerce=str,
                      rcoerce=list):
        lower = str.lower if lower else None
        _strip = (lambda x: x.strip(strip)) if strip else None
        coerce = coerce if callable(coerce) else None
        rcoerce = rcoerce if callable(rcoerce) else None

        for ch in strip:
            seq = seq.replace(ch, split)

        values = [i for i in seq.split(split) if i]
        for fn in (_strip, lower, coerce):
            if fn:
                values = map(fn, values)

        return rcoerce(values)

    def add_user(self, uid):
        """ TODO """
        self.user_list.add(uid)

    def remove_user(self, uid):
        """ TODO """
        if uid in self.user_list:
            self.user_list.remove(uid)

    def __repr__(self):
        return "<PermissionGroup: %s>" % self.name

    def __str__(self):
        return "<PermissionGroup: %s: %s>" % (self.name, self.__dict__)
