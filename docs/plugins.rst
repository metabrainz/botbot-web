.. role:: py(code)
   :language: python

Plugin API Documentation
=========================

You can write your own Botbot plugin by extending the core plugin class and providing one or more message handlers. A
message handler is a method on the plugin class that receives an object representing a user message that has been
posted to the IRC channel the plugin is associated with. The existing plugins in ``botbotme_plugins/plugins`` serve as good examples to follow. **ping** and **brain** are good ones to start with due to their simplicity.

Plugin Capabilities
--------------------

Plugins provide three basic capabilities:

1. Parse messages and optionally respond with an output message.
2. Associate configuration variables. Useful if your plugin needs to connect to external services.
3. Store and retrieve key/value pairs.

All plugins extend the BasePlugin class, providing them with the ability to utilize these capabilities.

Parsing and responding to messages
-----------------------------------

In the simplest case, a plugin will receive a message from an IRC channel and parse it based on a rule. When the parsed input
matches a rule, the plugin may return a response.

Additional methods should be defined on your ``Plugin`` class that will listen and optionally respond to incoming messages. They are registered with the app using one of the following decorators from ``botbotme_plugins.decorators``:

* :py:`listens_to_mentions(regex)`: A method that should be called only when the bot's nick prefixes the message and that message matches the regex pattern. For example, ``[o__o]: What time is it in Napier, New Zealand?``. The nick will be stripped prior to regex matching.
* :py:`listens_to_all(regex)`: A method that should be called on any line that matches the regex pattern.
* :py:`listens_to_command(cmd)`: A method that should be called on any line that starts with the command prefix, followed by :py:`cmd`. All further arguments are passed through in a list. For example, ``!list ops``.
* :py:`listens_to_regex_command(cmd, regex)`: :py:`listens_to_command`, with a regex check on all arguments. For a good example of this, see the ``metabrain`` plugin, which can do things like ``!remember jeff bezos=filthy rich`` by matching against ``some_key=some_value``.

The method should accept a ``line`` object as its first argument and any named matches from the regex as keyword args. Any text returned by the method will be echoed back to the channel.

The :py:`line` object has the following attributes:

* :py:`user`: The nick of the user who wrote the message
* :py:`text`: The text of the message (stripped of nick if addressed to the bot)
* :py:`full_text`: The text of the message

Configuration Metadata
-----------------------

Metadata can be associated with your plugin that can be referenced as needed in the message handlers. A common use case for
this is storing authentication credentials and/or API endpoint locations for external services. The ``github`` plugin is an example that uses configuration for the ability to query a Github repository.

To add configuration to your plugin, define a config class that inherits from :py:`config.BaseConfig`. Configuration values are
declared by adding instances of :py:`config.Field` as attributes of the class. You can validate that all required
fields have a value using the :py:`is_valid` method.

Once your config class is defined, you associate it with the plugin via the :py:`config_class` attribute:

.. code-block:: python

    class MyConfig(BaseConfig):
        unwarranted_comments = Field(
            required=False,
            help_text="Responds to every message with sarcastic comment",
            default=True)

    class Plugin(BasePlugin):
        config_class = MyConfig

        @listens_to_all
        def peanut_gallery(self, line):
            if self.config.unwarranted_comments:
                return "Good one!"


Storage / Persisting Data
--------------------------

BasePlugin provides a simple wrapper around the Redis API that Plugins should use for storage - it'll handle namespacing the key in the format "<bot_id>:<channel_id>:<plugin_slug>:<key_name_stripped>". This ensures that there's no collisions.

There are four methods:

* :py:`store(key, value)`: Sets :py:`key` to :py:`value`. Importantly, :py:`value` is encoded in ``utf-8`` before being stored.
* :py:`retrieve(key)`: Gets the value corresponding to :py:`key`. Returns a ``utf-8``-encoded string.
* :py:`delete(key)`: Removes the stored :py:`key`.
* :py:`incr(key)`: Increments the counter specified by :py:`key`. This is really just a special-case version of :py:`set`, but the counter is set to :py:`0` if it does not exist, and there's no need to :py:`retrieve` the existing value beforehand.


Testing Your Plugins
---------------------

In order to simulate the plugin running in its normal environment, an app instance must be instantiated. See the current
tests for examples. This may change with subsequent releases.
