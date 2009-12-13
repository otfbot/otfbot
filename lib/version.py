from twisted.python import versions
import sys, os.path

class GitVersion(versions.Version):

    def _getSVNVersion(self):
        mod = sys.modules.get(self.__module__)
        if mod:
            f=os.path.dirname(mod.__file__)
            for i in range(1,2):
                f=os.path.split(f)[0]
            git = os.path.join(f,'.git')
            if not os.path.exists(git):
                print "no git dir"
                return None
            master=os.path.join(git,'refs','heads','master')
            if not os.path.exists(master):
                print "no masterref"
                return None
            f=open(master,'r')
            ver=f.readline().strip()
            return ver[:7]
        
    def _formatSVNVersion(self):
        ver = self._getSVNVersion()
        if ver is None:
            return ''
        return ' (Git commit %s)' % (ver,)

    def short(self):
        """
        from twisted.python.versions.Version
        Return a string in canonical short version format,
        <major>.<minor>.<micro>[+rSVNVer].
        """
        s = self.base()
        svnver = self._getSVNVersion()
        if svnver:
            s += "+" + str(svnver)
        return s


_version = GitVersion('OTFBot',1,0,0)