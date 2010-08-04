class Plugin:
    """ Basic plugin for services inside OTFBot

        Inherit from this class if you want
        to write your plugin
    """

    def __init__(self, root, parent):
        self.root = root
        self.parent = parent

    def register_ctl_command(self, f, namespace=None, name=None):
        """ register commands in control service """
        if namespace is None:
            namespace = []
        if not type(namespace) == list:
            namespace = list(namespace)
        namespace.insert(0, self.name.split(".")[-1])
        self.bot.register_ctl_command(f, namespace, name)

    def setLogger(self, logger):
        """ set the logger """
        self.logger = logger

    class Meta:
        """ Provide some meta data for the plugin

            @ivar name: Identifier of the plugin
            @ivar description: short description
                                of the functionality
                                of the plugin
            @ivar serviceDepends: a list of services
                                needed by the plugin
            @ivar pluginDepends: a list of plugins
                                needed by the plugin
        """
        name = __module__
        description = "Basic Plugin"
        serviceDepends = []
        #serviceDepends.append("control")
        pluginDepends = []
        #pluginDepends.append("something")

