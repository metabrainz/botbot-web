"""
Channel sitemap
"""
from django.contrib.sitemaps import Sitemap

from .models import Channel


class ChannelSitemap(Sitemap):
    priority = 0.5

    def items(self):
        return Channel.objects.public()
