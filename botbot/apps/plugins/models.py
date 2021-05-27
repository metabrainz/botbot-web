import inspect
from importlib import import_module

from django.core.cache import cache
from django.db import models
from django_jsonfield_backport.models import JSONField


class Plugin(models.Model):
    """A global plugin registered in botbot"""

    name = models.CharField(max_length=100)
    slug = models.SlugField()

    @property
    def user_docs(self):
        for mod_prefix in ("botbot_plugins.plugins.", "botbot.apps.plugins.core."):
            try:
                docs = import_module(mod_prefix + self.slug).Plugin.__doc__
                return inspect.cleandoc(docs)
            except (ImportError, AttributeError):
                continue
        return ""

    def __str__(self):
        return self.name


class ActivePlugin(models.Model):
    """An active plugin for a ChatBot"""

    plugin = models.ForeignKey("plugins.Plugin", on_delete=models.CASCADE)
    channel = models.ForeignKey("bots.Channel", on_delete=models.CASCADE)
    configuration = JSONField(
        blank=True,
        default=dict,
        help_text="User-specified attributes for this plugin " + '{"username": "joe", "api-key": "foo"}',
    )

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        # Let the plugin_runner auto-reload the new values
        cache.delete(self.channel.plugin_config_cache_key(self.plugin.slug))
        cache.delete(self.channel.active_plugin_slugs_cache_key)
        return obj

    def __str__(self):
        return f"{self.plugin.name} for {self.channel.name}"
