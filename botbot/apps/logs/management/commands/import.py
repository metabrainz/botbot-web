# MBChatLogger Plain Text -> BotBot Importer
# Copyright (C) 2015  Ben Ockmore
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
""" This script provides a command to import chatlogs in plain text format
output from MBChatLogger to a BotBot database. It also has some basic support
for detecting and removing duplicate messages on import.
"""
import datetime
import os
import re

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import reset_queries
from django.db import transaction

from botbot.apps.bots.models import Channel
from botbot.apps.bots.models import ChatBot
from botbot.apps.logs.models import Log


def _get_channel(channel_name):
    """Attempts to locate a channel with the given name in the BotBot database."""

    try:
        return Channel.objects.get(name=channel_name)
    except Channel.DoesNotExist:
        raise CommandError(f"Channel {channel_name} not found.")


def _path(directory, filenames):
    """Combines each provided filename with the given directory using
    os.path.join.
    """
    for f in filenames:
        yield os.path.join(directory, f)


def _get_existing_entries(parsed_log, timestamp, nick, channel):
    """Gets entries within 1 second of the parsed log information, to avoid
    creating duplicate entries when timestamps differ slightly.
    """

    dt1 = datetime.timedelta(seconds=3)
    earliest = timestamp - dt1
    latest = timestamp + dt1
    return Log.objects.filter(
        channel=channel, timestamp__gte=earliest, timestamp__lte=latest, nick=nick, text=parsed_log["text"]
    ).all()


class Command(BaseCommand):
    help = "Imports logs from the specified channel on" "chatlogs.musicbrainz.org"

    def __init__(self, *args, **kwargs):
        self.bot = None
        self.channel = None

        self.date_regex = re.compile(r"(\d{2}:\d{2}:\d{2})")
        self.user_regex = re.compile(r"<(.+?)>")

        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument("channel", type=str)
        parser.add_argument("source_dir", type=str)

    def handle(self, *args, **options):
        if "channel" not in options or "source_dir" not in options:
            raise CommandError("Channel name and source" " directory are required.")

        self.bot = ChatBot.objects.get(nick="BrainzBot")

        channel_name = "#" + options["channel"]
        self.channel = _get_channel(channel_name)

        print(
                'About to import logs from {} to Channel "{}" with Bot "{}"'.format(
                    options["source_dir"], channel_name, self.bot.nick
                )
        )

        prompt = input("Continue? (Y/n) ")
        if prompt and prompt.lower() != "y":
            raise CommandError("User aborted import.")

        self._import_channel(options["source_dir"])

    def _import_channel(self, root):
        for directory, _, filenames in os.walk(root):
            for path in _path(directory, filenames):
                if os.path.splitext(path)[1] == ".txt":
                    self._import_file(path)
                    reset_queries()

    @transaction.atomic
    def _import_file(self, path):
        print(f"Importing {path}")
        date = os.path.splitext(os.path.basename(path))[0]
        with open(path) as f:
            for line in f:
                line = line.decode("utf8", errors="replace")
                self._import_line(date, line)

    def _import_line(self, date, line):
        date_match = self.date_regex.match(line)
        if date_match is None:
            raise CommandError(f"Bad line format - no date: {line}")
        line = line[date_match.end() :].strip()

        user_match = self.user_regex.match(line)
        if user_match is None:
            raise CommandError(f"Bad line format - no user: {line}")

        content = line[user_match.end() :].strip()

        msg_time = date_match.groups()[0]
        user = user_match.groups()[0]
        timestamp = datetime.datetime.strptime(date + "T" + msg_time, "%Y-%m-%dT%H:%M:%S")

        result = self._parse_message(user, content)

        if result is not None:
            existing_entries = _get_existing_entries(result, timestamp, user, self.channel)
            if len(existing_entries) > 1:
                # Delete the duplicate with the least precise timestamp
                most_precise = [entry for entry in existing_entries if entry.timestamp.microsecond]
                if most_precise:
                    for entry in existing_entries:
                        if entry not in most_precise:
                            entry.delete()
                    existing_entries = most_precise
            elif existing_entries:
                for key, value in result.items():
                    setattr(existing_entries[0], key, value)
            else:
                result.update({"bot": self.bot, "channel": self.channel, "timestamp": timestamp, "nick": user})
                existing_entries = [Log(**result)]

            existing_entries[0].save()

    def _parse_message(self, nick, content):
        if content.startswith(f"{nick} has joined {self.channel.name}"):
            # JOIN
            return {"room": self.channel.name, "command": "JOIN", "text": ""}
        elif content.startswith(f"{nick} has left {self.channel.name}"):
            # PART
            return {"room": self.channel.name, "command": "PART", "text": ""}
        elif content.startswith(f"{nick} has quit"):
            # QUIT
            return {"room": self.channel.name, "command": "QUIT", "text": ""}
        elif content.startswith(f"* {nick} "):
            # ACTION
            nick_length = len(nick) + 3
            return {"room": self.channel.name, "command": "ACTION", "text": content[nick_length:]}
        elif content.startswith("{} has changed"):
            # Haven't yet worked out how to handle topic change
            return None
        else:
            # PRIVMSG
            return {"room": self.channel.name, "command": "PRIVMSG", "text": content}
