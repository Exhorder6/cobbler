"""
A Cobbler Profile.  A profile is a reference to a distribution, possibly some kernel options, possibly some Virt options, and some kickstart data.

Copyright 2006, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import utils
import item
import cexceptions

class Profile(item.Item):

    def __init__(self,config):
        """
        Constructor.  Requires a backreference to Config.
        """
        self.config = config
        self.settings = self.config.settings()
        self.clear()

    def clear(self):
        """
        Reset this object.
        """
        self.name = None
        self.distro = None # a name, not a reference
        self.kickstart = self.settings.default_kickstart
        self.kernel_options = ''
        self.ks_meta = ''
        self.virt_name = 'virtguest'
        self.virt_file_size = 5    # GB.  5 = Decent _minimum_ default for FC5.
        self.virt_ram = 512        # MB.  Install with 256 not likely to pass
        self.virt_paravirt = True  # hvm support is *NOT* in Koan (now)
        self.repos = ""            # names of cobbler repo definitions

    def from_datastruct(self,seed_data):
        """
        Load this object's properties based on seed_data
        """
        self.name            = self.load_item(seed_data,'name')
        self.distro          = self.load_item(seed_data,'distro')
        self.kickstart       = self.load_item(seed_data,'kickstart')
        self.kernel_options  = self.load_item(seed_data,'kernel_options')
        self.ks_meta         = self.load_item(seed_data,'ks_meta')
        self.repos           = self.load_item(seed_data,'repos', "")       

        # virt specific 
        self.virt_name       = self.load_item(seed_data,'virt_name')
        if not self.virt_name or self.virt_name == '':
            self.virt_name    = self.name
        self.virt_ram        = self.load_item(seed_data,'virt_ram')
        self.virt_file_size  = self.load_item(seed_data,'virt_file_size')
        self.virt_paravirt   = self.load_item(seed_data,'virt_paravirt')

        return self

    def set_distro(self,distro_name):
        """
	Sets the distro.  This must be the name of an existing
	Distro object in the Distros collection.
	"""
        if self.config.distros().find(distro_name):
            self.distro = distro_name
            return True
        raise cexceptions.CobblerException("no_distro")

    def set_repos(self,repos):
        repolist = repos.split(" ")
        ok = True
        for r in repolist:
            if not self.config.repos().find(r):
                ok = False 
                break
        if ok:
            self.repos = repos
        else:
            raise cexceptions.CobblerException("no_repos")

    def set_kickstart(self,kickstart):
        """
	Sets the kickstart.  This must be a NFS, HTTP, or FTP URL.
	Minor checking of the URL is performed here.
	"""
        if utils.find_kickstart(kickstart):
            self.kickstart = kickstart
            return True
        raise cexceptions.CobblerException("no_kickstart")

    def set_virt_name(self,str):
        """
	For Virt only.
	Specifies what virt install should use for --name.
        virt install may do conflict resolution, so this is mostly
        a hint...  To keep the shell happy, the 'str' cannot
	contain wildcards or slashes and may be subject to some other
        untainting later.
	"""
        # no slashes or wildcards
        for bad in [ '/', '*', '?' ]:
            if str.find(bad) != -1:
                raise cexceptions.CobblerException("exc_virt_name")
        self.virt_name = str
        return True
    
    def set_virt_file_size(self,num):
        """
	For Virt only.
	Specifies the size of the virt image in gigabytes.  koan
	may contain some logic to ignore 'illogical' values of this size,
	though there are no guarantees.  0 tells koan to just
	let it pick a semi-reasonable size.  When in doubt, specify the
	size you want.
	"""
        # num is a non-negative integer (0 means default)
        try:
            inum = int(num)
            if inum != float(num):
                return cexceptions.CobblerException("exc_virt_file")
            if inum >= 0:
                self.virt_file_size = inum
                return True
            return cexceptions.CobblerException("exc_virt_file")
        except:
            return cexceptions.CobblerException("exc_virt_file")

    def set_virt_ram(self,num):
        """
        For Virt only.
        Specifies the size of the Virt RAM in MB.
        0 tells Koan to just choose a reasonable default.
        """
        # num is a non-negative integer (0 means default)
        try:
            inum = int(num)
            if inum != float(num):
                return cexceptions.CobblerException("exc_virt_ram")
            if inum >= 0:
                self.virt_ram = inum
                return True
            return cexceptions.CobblerException("exc_virt_ram")
        except:
            return cexceptions.CobblerException("exc_virt_ram")

    def set_virt_paravirt(self,truthiness):
        """
	For Virt only.
	Specifies whether the system is a paravirtualized system or not.
	For ordinary computers, you want to pick 'true'.  Method accepts string
	'true'/'false' in all cases, or Python True/False.
	"""
        # truthiness needs to be True or False, or (lcased) string equivalents
        # yes, we *do* want to explicitly test against True/False
        # the string "foosball" is True, and that is not a valid argument for this function
        try:
            if (not truthiness or truthiness.lower() == 'false'):
                self.virt_paravirt = False
            elif (truthiness or truthiness.lower() == 'true'):
                self.virt_paravirt = True
            else:
                return cexceptions.CobblerException("exc_virt_para")
        except:
            return cexceptions.CobblerException("exc_virt_para")
        return True

    def is_valid(self):
        """
	A profile only needs a name and a distro.  Kickstart info,
	as well as Virt info, are optional.  (Though I would say provisioning
	without a kickstart is *usually* not a good idea).
	"""
        for x in (self.name, self.distro):
            if x is None:
                return False
        return True

    def to_datastruct(self):
        """
        Return hash representation for the serializer
        """
        return {
            'name'             : self.name,
            'distro'           : self.distro,
            'kickstart'        : self.kickstart,
            'kernel_options'   : self.kernel_options,
            'virt_name'        : self.virt_name,
            'virt_file_size'   : self.virt_file_size,
            'virt_ram'         : self.virt_ram,
            'virt_paravirt'    : self.virt_paravirt,
            'ks_meta'          : self.ks_meta,
            'repos'            : self.repos
        }

    def printable(self,id):
        """
        A human readable representaton
        """
        buf =       "profile %-4s    : %s\n" % (id, self.name)
        buf = buf + "distro          : %s\n" % self.distro
        buf = buf + "kickstart       : %s\n" % self.kickstart
        buf = buf + "kernel options  : %s\n" % self.kernel_options
        buf = buf + "ks metadata     : %s\n" % self.ks_meta
        buf = buf + "virt name        : %s\n" % self.virt_name
        buf = buf + "virt file size   : %s\n" % self.virt_file_size
        buf = buf + "virt ram         : %s\n" % self.virt_ram
        buf = buf + "virt paravirt    : %s\n" % self.virt_paravirt
        buf = buf + "repos            : %s\n" % self.repos
        return buf

