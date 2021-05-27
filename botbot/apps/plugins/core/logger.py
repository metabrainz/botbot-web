import re

import botbot_plugins.config as config
from botbot_plugins.base import BasePlugin

from botbot.apps.logs.models import Log


class Config(config.BaseConfig):
    ignore_prefixes = config.Field(
        default=["!-"],
        required=False,
        help_text="""
            Specify a list of regular expressions which match
            the start of messages to be ignored (excluded from the logs)
        """,
    )


def should_ignore_text(text, ignore_prefixes):
    return any((prefix and re.match(prefix, text, flags=re.IGNORECASE) is not None) for prefix in ignore_prefixes)


class Plugin(BasePlugin):
    """
    Logs all activity.

    I keep extensive logs on all the activity in `{{ channel.name }}`.
    You can read and search them at {{ SITE }}{{ channel.get_absolute_url }}.
    """

    config_class = Config

    def logit(self, line):
        """Log a message to the database"""
        # If the channel does not start with "#" that means the message
        # is part of a /query
        if line._channel_name.startswith("#"):
            ignore_prefixes = self.config["ignore_prefixes"]

            if ignore_prefixes:
                if not isinstance(ignore_prefixes, list):
                    ignore_prefixes = [ignore_prefixes]
            else:
                ignore_prefixes = []

            # Delete ACTION prefix created by /me
            text = line.text
            if text.startswith("ACTION "):
                text = text[7:]

            if not should_ignore_text(text, ignore_prefixes):
                Log.objects.create(
                    channel_id=line._channel.pk,
                    timestamp=line._received,
                    nick=line.user,
                    text=line.full_text,
                    room=line._channel,
                    host=line._host,
                    command=line._command,
                    raw=line._raw,
                )

    logit.route_rule = ("firehose", r"(.*)")
