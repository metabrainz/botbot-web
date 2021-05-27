from django.core.management.base import BaseCommand

from botbot.apps.plugins import runner


class Command(BaseCommand):
    help = "Starts up all plugins in the botbot.apps.bots.plugins module"

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-gevent",
            action="store_true",
            dest="with_gevent",
            default=False,
            help="Use gevent for concurrency",
        )

    def handle(self, *args, **options):
        runner.start_plugins(use_gevent=options["with_gevent"])
