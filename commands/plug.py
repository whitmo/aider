# requires `pip install ipdb zope.dottedname`
import ipdb
from zope.dottedname.resolve import resolve


class IPDBRun:
    # somewhat limited due to arg handling and context
    # but demostrates a basic python plugin
    def __init__(self, commands, args):
        self.commands = commands
        self.args = args

    def __call__(self, path, *args):
        with ipdb.launch_ipdb_on_exception():
            code = resolve(path)
            return ipdb.runcall(code, args)

    @classmethod
    def execute(cls, commands, args):
        plugin = cls(commands, args)
        al = args.split()
        path, nargs = al[0], al[1:]
        return plugin(path, *nargs)

ipdb_run = IPDBRun.execute
