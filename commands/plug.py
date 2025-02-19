from ipdb import launch_ipdb_on_exception
from zope.dottedname.resolve import resolve


class IPDBRun:
    def __init__(self, commands, args):
        self.commands = commands
        self.args = args

    def __call__(self, path, *args):
        with launch_ipdb_on_exception():
            code = resolve(path)
            return code(*args)

    @classmethod
    def execute(cls, commands, args):
        plugin = cls(commands, args)
        al = args.split()
        path, nargs = al[0], al[1:]
        return plugin(path, *nargs)

ipdb_run = IPDBRun.execute
