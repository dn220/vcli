#!/usr/bin/env python
'''
    VMware Command Line Interface (vcli) tool

    File name: VCLI.py
    Author: Dung Nguyen
    Date created: 12/28/2019
    Python Version: 2.7
'''
__author__ = 'Dung Nguyen'
__copyright__ = 'Copyright 2019, Dung Nguyen'
__credits__ = 'Dung Nguyen'
__license__ = 'GPLv3.0'
__version__ = '0.2.20'
__release__ = '12/30/2019'
__maintainer__ = 'Dung Nguyen'
__source__ = 'https://github.com/dn220/vcli'
__email__ = 'dn220@yahoo.com'

import os
import sys
import re

#
# VMware pyvmomi
#
import ssl
import requests

#
# VMware pyvmomi API 0:wbinding
#
from pyVim.connect import SmartConnect
from pyVmomi import vim
from vmware.vapi.lib.connect import get_requests_connector
from vmware.vapi.security.session import create_session_security_context
from vmware.vapi.security.user_password import create_user_password_security_context
from vmware.vapi.stdlib.client.factories import StubConfigurationFactory

#
# VMware pyvmomi vAPI 0:wbinding
#   For connectivity to Inventory Services for Tag
#
from com.vmware.cis.tagging_client import (Category, Tag, TagAssociation)
from com.vmware.cis_client import Session
from com.vmware.vapi.std_client import DynamicID

#
# Disable urllib warning
#
requests.packages.urllib3.disable_warnings()


class VCLI(object):
    '''
    VCLI Tool module.
    '''

    #
    # the argparse object
    #
    _args = None
    _conf = None

    #
    # VMware pyvmoni Service Interface
    #
    _stubConfig = None
    _si = None

    #
    # Environmental Information
    #
    _host = None
    _port = None
    _username = None
    _password = None

    #
    # timestamp
    #
    _ts = None

    #
    # if requested, CSV file writer
    #
    _csvWriter = None

    #
    # Help Text
    #

    ## ---------- ---------- ---------- ----------
    # vcli.py -h
    #    1         2         3         4         5         6         7         8
    # 78901234567890123456789012345678901234567890123456789012345678901234567890
    # ---1---------2---------3---------4---------5---------6---------7----------
    _helpSynopsis = '''SSYYNNOOPPSSIISS
    VMware Command Line Tool

    This tool implements the common tasks associated with managing a virtual
    machine (vm) in the VMware environment.'''
    _helpDescription = '''DDEESSCCRRIIPPTTIIOONN
    VMware Command Line Tool

    This tool implements the common tasks associated with managing a virtual
    machine (vm) in the VMware environment.

    Options and Arguments

    A convention for specifying options has been adopted in this tool.
    Lower case options, such as '-l', are used as flags to enable or disable features.
    Upper case options are used to input information and thus require a value, for example
    '-M 4' to specify 4GB of memory, for example, see vcli add -h.

    Options and arguments in square brackets are optional.
    Options and arguments without square brackets are required.
    Options can be given in any order.
    However, arguments must be given in the order specified.

        Sample 1: vcli clone -h
        usage: vcli clone [-h] [-x] [-D DESCRIPTION] [-M MEMORY] [-P CPU]
                          source vm-name [vm-name ...]

        Sample 2: vcli snapshot -h
        usage: vcli snapshot [-h] [-m] -D DESCRIPTION vm-name [vm-name ...]

    As shown above all options for the 'clone' action are optional while the
    '-D' option for the 'snapshot' action is required.

    As shown above the 'clone' action requires the first argument to be the
    source VM (or template) object used for the cloning process.  At lease
    one VM is required.  More can be provided if necessary.

    Detail help for each action is also available,
    for example, to get detail help for the 'add' action, run
        vcli add -h

    Some actions are layered, such as the 'list' command.
        Command             Description
        vcli list -h        help for the list action
        vcli list vm -h     help for vm listing
        vcli list nic -h    help for vm nic listing
    '''
    _helpExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all virtual machines.
        [user ~]$ vcli list vm
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server1         On     1    2     40    No  No   Test server 4
        server2         On     1    2     40    No  No   Test server 2
        # Total:  2
    '''
    _helpCredit = '''CCRREEDDIITTSS
    Author        {author}
    Copyright     {copyright}
    License       {license}
    Version       {version}
    Release Date  {release}
    Source Code   {source}
    E-Mail        {email}
    '''.format(author=__author__, copyright=__copyright__, license=__license__, release=__release__, version=__version__, source=__source__, email=__email__)

    ## ---------- ---------- ---------- ----------
    # VM Informational Actions

    ## ---------- ---------- ---------- ----------
    # vcli.py info -h
    #
    _helpInfoSynopsis = '''SSYYNNOOPPSSIISS
    Display detail information about VM.'''
    _helpInfoDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display detail information about VM.'''
    _helpInfoExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display detail information about server4
        [user ~]$ vcli info server4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list -h
    #
    _helpListSynopsis = '''SSYYNNOOPPSSIISS
    Display tabular listing of requested objects.'''
    _helpListDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display tabular listing of requested objects.'''
    _helpListExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all virtual machines (vm) with 'server' in its name.

        [user ~]$ vcli list vm server
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server2         On     1    4     74    No  No   Test server 2
        server3         Off    1    4     74    No  No   Test server 3
        server1         Off    1    4     74    No  No   Test server 1
        server4         On     2    8     66     3  No   Test server 4
        # Total:  4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list category -h
    #
    # ---1---------2---------3---------4---------5---------6---------7----------
    _helpListCategorySynopsis = '''SSYYNNOOPPSSIISS
    Display a listing of tag categories.'''
    _helpListCategoryDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display a listing of tag categories.'''
    _helpListCategoryExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display a list of tag categories.

        [user~]$ vcli list category
        # Category      Cardinality  Associable_Types    Tags     Description
        # --------      -----------  ----------------    ----     -----------
        Backup          SINGLE       ['VirtualMachine']  4        VM backup category
        # Total:  1
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list cluster -h
    #
    _helpListClusterSynopsis = '''SSYYNNOOPPSSIISS
    Display cluster.'''
    _helpListClusterDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display cluster.'''
    _helpListClusterExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all clusters

        [user ~]$ vcli list cluster
        # Cluster   Skts  Cores  CPUs  Used  Usage  Memory  Used  Usage  Hosts
        # -------   ----  -----  ----  ----  -----  ------  ----  -----  -----
        cluster1       4     32    64    32  50.0%     256   128  50.0%   4  ['host1', 'host2', 'host3', 'host4']
        cluster2       2    16    32    16   50.0%     256    64  25.0%   2  ['host5', 'host6']
        # Total:  2
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list datacenter -h
    #
    _helpListDatacenterSynopsis = '''SSYYNNOOPPSSIISS
    Display datacenter.'''
    _helpListDatacenterDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display datacenter.'''
    _helpListDatacenterExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all datacenters.

        [user ~]$ vcli list datacenter
        # Datacenter
        # ----------
        AU
        US
        # Total:  2
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list datastore -h
    #
    _helpListDatastoreSynopsis = '''SSYYNNOOPPSSIISS
    Display datastore.'''
    _helpListDatastoreDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display datastore.'''
    _helpListDatastoreExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display available datastores.

        [user ~]$ vcli list datastore
        # Datastore     Size  Free  Usage  VM
        # ---------     ----  ----  -----  --
        ds-02           4096  2125     49  4
        ds-01           4096  2061     50  4
        ds-22           4096   937     78  8
        ds-21           4096  1005     76  9
        # Total:  4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list disk -h
    #
    _helpListVmDiskSynopsis = '''SSYYNNOOPPSSIISS
    Display disk.'''
    _helpListVmDiskDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display disk.'''
    _helpListVmDiskExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all disks on VM server4.

        [user ~]$ vcli list disk server4
        # VM     HD  A  I  Size  Type   Mode  Share  UUID          Disk
        # --     --  -  -  ----  ----   ----  -----  ----          ----
        server4   1  0  0    60  thin      p   None  bc17dfc64c7e  [ds-01] server4/server4.vmdk
        server4   2  0  2     6  thin      p   None  1518ecd44854  [ds-01] server4/server4_1.vmdk
        # Total:  1
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list host -h
    #
    _helpListHostSynopsis = '''SSYYNNOOPPSSIISS
    Display host.'''
    _helpListHostDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display host.'''
    _helpListHostExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display ESXi hypervisors.

        [user ~]$ vcli list host
        # Host     Skts  Cores  CPUs  vCPUs  Memory  Cluster    VM
        # ----     ----  -----  ----  -----  ------  -------    --
        host4         2     12    24     48     256  cluster1   6
        host1         2     12    24     48     256  cluster1   8
        host2         2     12    24     48     256  cluster2   4
        host3         2     12    24     48     256  cluster2   2
        # Total:  4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list network -h
    #
    _helpListNetworkSynopsis = '''SSYYNNOOPPSSIISS
    Display network.'''
    _helpListNetworkDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display network.'''
    _helpListNetworkExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all networks with 'app' in its name
        [user ~]$ vcli list network app
        # Network         VLAN  VM   Hosts
        # -------         ----  --   -----
        AU|INT|DEV-APP     101  8    4
        AU|INT|TST-APP     102  6    4
        AU|INT|STG-APP     103  6    4
        AU|INT|PRD-APP     104  4    4
        AU|EXT|STG-APP     401  4    2
        AU|EXT|PRD-APP     402  4    2
        # Total:  6
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list nic -h
    #
    _helpListVmNicSynopsis = '''SSYYNNOOPPSSIISS
    Display nic.'''
    _helpListVmNicDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display nic.'''
    _helpListVmNicExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all network interface cards (nic) on server4.

        [user ~]$ vcli list nic server4
        # VM      Nic  NIC_Type  IP_Address      VLAN  Network           MAC_Address
        # --      ---  --------  ----------      ----  -------           -----------
        server4     1  Vmxnet3   10.0.0.1        101   AU|INT|DEV-APP    12:14:0B:02:25:DD
        server4     2  Vmxnet3   10.4.0.1        102   AU|INT|TST-APP    02:25:DD:12:14:0B
        # Total:  1
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list rpool -h
    #
    _helpListRpoolSynopsis = '''SSYYNNOOPPSSIISS
    Display rpool.'''
    _helpListRpoolDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display rpool.'''
    _helpListRpoolExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all resource pools.

        [user ~]$ vcli list rp
        # Res_Pool   Owner      Process  Alloc   Limit  Reservation  Memory  shares   Limit  Reservation  VM
        # --------   -----      ------   -----   -----  -----------  ------  ------   -----  -----------  --
        Resources    cluster1   normal      40  215232       215232  normal  163840  758791       758791  9
        Resources    cluster2   normal      60  215232       215232  normal  163840  758791       758791  9
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list snapshot -h
    #
    _helpListVmSnapshotSynopsis = '''SSYYNNOOPPSSIISS
    Display snapshot.'''
    _helpListVmSnapshotDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display snapshot.'''
    _helpListVmSnapshotExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display snapshots for VM server4.

        [user ~]$ vcli list snapshot server4
        # VM            Id    Created              By        Description
        # --            --    -------              --        -----------
        server4         1     2019-12-14 02:20:20  user1     test snapshot
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list tag -h
    #
    _helpListTagSynopsis = '''SSYYNNOOPPSSIISS
    Display a listing of tags.'''
    _helpListTagDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display a listing of tags.'''
    _helpListTagExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all backup tags.

        [user ~]$ vcli list tag -C backup
        # Tag     Cardinality  Category   Description      Attached_To
        # ---     -----------  --------   -----------      -----------
        policy4   SINGLE       Backup     Backup Policy 4  2
        policy3   SINGLE       Backup     Backup Policy 3  7
        policy2   SINGLE       Backup     Backup Policy 2  7
        policy1   SINGLE       Backup     Backup Policy 1  4
        # Total:  4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list template -h
    #
    _helpListTemplateSynopsis = '''SSYYNNOOPPSSIISS
    Display a listing of template.'''
    _helpListTemplateDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display a listing of template.'''
    _helpListTemplateExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all templates with 'gold' in its name.

        [user ~]$ vcli list template gold
        # Template         Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --------         ---  ---  ---  -----  ----  ---  -----------
        CentOs7-Gold-App   Off    1    4     60    No  No   CentOs7 Gold Template
        CentOs8-Gold-App   Off    1    4     60    No  No   CentOs8 Gold Template
        # Total:  2
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list vm -h
    #
    _helpListVmSynopsis = '''SSYYNNOOPPSSIISS
    Display a listing of vm.'''
    _helpListVmDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display a listing of vm.'''
    _helpListVmExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display all virtual machines (vm) with 'server' in its name.

        [user ~]$ vcli list vm server
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server4         Off    2    8     66     3  No   Test server 4
        server1         Off    1    4     74    No  No   Test server 1
        server2         Off    1    4     74    No  No   Test server 2
        server3         Off    1    4     74    No  No   Test server 3
        # Total:  4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py list vm-tag -h
    #
    _helpListVmTagSynopsis = '''SSYYNNOOPPSSIISS
    Display a listing of vm.'''
    _helpListVmTagDescription = '''DDEESSCCRRIIPPTTIIOONN
    Display a listing of vm.'''
    _helpListVmTagExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Display a listing of vm.
        [user ~]$ vcli list vm-tag

    Example 2
    ---------
        Display a listing of vm without backup (tag = no-backup).
        [user ~]$ vcli list vm-tag -l -T no-backup
    '''

    ## ---------- ---------- ---------- ----------
    # Common Actions

    ## ---------- ---------- ---------- ----------
    # vcli.py add -h
    #
    _helpAddSynopsis = '''SSYYNNOOPPSSIISS
    Add resources to VM.'''
    _helpAddDescription = '''DDEESSCCRRIIPPTTIIOONN
    Add resources to VM.'''
    _helpAddExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Add additional compute resources to VM server4.

        1. (optional)  Let's get server4 current compute allocation.
        [user ~]$ vcli list vm server4
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server4         On     1    4     66     3  No   Test server 4

        2.  Add the additional resources.
        [user ~]$ vcli add -P 2 -M 6 server4
        Changing compute resources
          CPU:  1 -> 3
          Memory:  4096.0 -> 10240.0
          Task completed successfully

        3.  (optional) Verify new compute allocation.
        [user ~]$ vcli list vm server4
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server4         On     3   10     66     3  No   Test server 4
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py backup -h
    #
    _helpBackupSynopsis = '''SSYYNNOOPPSSIISS
    Create a clone backup of VM.'''
    _helpBackupDescription = '''DDEESSCCRRIIPPTTIIOONN
    Create a clone backup of VM.'''
    _helpBackupExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        make a clone backup of VM server4.

        1.  Make a clone backup.
        [user ~]$ vcli backup server4
        Cloning server4 to server4.cloned.by.user1.20191214
          Task completed successfully

        2.  (optional) Verify backup.
        [user ~]$ vcli list vm server4
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server4         Off    2    8     66     3  No   Test server 4
        server4.cloned.by.user1.20191214  Off    2    8     66    No  No   Test server 4       4
        # Total:  2
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py change -h
    _helpChangeSynopsis = '''SSYYNNOOPPSSIISS
    Change VM's attribute.'''

    _helpChangeDescription = '''DDEESSCCRRIIPPTTIIOONN
    Change VM's attribute.'''

    _helpChangeExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Change VM's name from server1 to server2.
        [user ~]$ vcli change -N server2 server1

    Example 2
    ---------
        Add 'DR' to server server1.
        [user ~]$ vcli change -A 'DR' server1

        Note:
            You could have accomplished this with a new name change,
            as shown above in Example 1.
                [user ~]$ vcli change -N server1.DR server1

            However, if you needed to append 'DR' to a list of VM
            then a name change would not be possible.

    Example 3
    ---------
        Add 'DR' to a list of servers in file srvs.list
        [user ~]$ vcli change -A 'DR' srvs.list
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py clone -h
    _helpCloneSynopsis = '''SSYYNNOOPPSSIISS
    Clone a VM.'''

    _helpCloneDescription = '''DDEESSCCRRIIPPTTIIOONN
    Clone a VM.

    Two common use cases for cloning VM are:

    Build a new server based on an existing one or from a golden image.
    '''

    _helpCloneExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Application developer requests backup of the apache servers so they can
        test a new release.
        [user ~]$ vcli clone server1 server2 server3

    Example 2
    ---------
        Build new VM using CengOs7-Gold template
        Note:  DNS entries will be used to determine needed network interfaces.
        [user ~]$ vcli clone -S CengOs7-Gold server1 server2
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py destroy -h
    _helpDestroySynopsis = '''SSYYNNOOPPSSIISS
    Destroy a VM.'''
    _helpDestroyDescription = '''DDEESSCCRRIIPPTTIIOONN
    Destroy a VM.'''
    _helpDestroyExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        VM server1 is no longer needed and can be deleted from vcenter.
        [user ~]$ vcli destroy server1
    '''

    ## ---------- ---------- ---------- ----------

    ## ---------- ---------- ---------- ----------
    #  vcli.py migrate -h
    _helpMigrateSynopsis = '''SSYYNNOOPPSSIISS
    Migrate VM to another hypervisor and/or datastore.'''
    _helpMigrateDescription = '''DDEESSCCRRIIPPTTIIOONN
    Migrate VM to another hypervisor and/or datastore.'''
    _helpMigrateExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Migrate VM server1 and server2 to host host1
        [user ~]$ vcli migrate -H host1 server1 server2
    '''

    ## ---------- ---------- ---------- ----------
    # vcli.py remove -h
    #
    _helpRemoveSynopsis = '''SSYYNNOOPPSSIISS
    Remove a resource from VM.'''
    _helpRemoveDescription = '''DDEESSCCRRIIPPTTIIOONN
    Remove a resource from VM.'''
    _helpRemoveExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Remove computer resource from VM server4.

        1. (optional)  Let's get server4 current compute allocation.
        [user ~]$ vcli list vm server4
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server4         On     3   10     66     3  No   Test server 4

        2. Remove compute resources.
        [user ~]$
        vcli remove -P 1 -M 2 server4
        Cannot reduce CPU from 3 to 1 while VM is powered on.

        3. To remove compute resources, VM must be powered off.
           Note:  The shutdown action is preferred over the stop action.
        [user ~]$ vcli shutdown server4
        Shutting down server4
          VM shutdown successful

        (Repeat step 2)
        [user ~]$ vcli remove -P 1 -M 2 server4
        Changing compute resources
          CPU:  3 -> 2
          Memory:  10240.0 -> 8192.0
          Task completed successfully

        4.  (optional) Verify new compute allocation.
        [user ~]$ vcli list vm server4
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server4         Off    2    8     66     3  No   Test server 4
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py reboot -h
    _helpRebootSynopsis = '''SSYYNNOOPPSSIISS
    Reboot a VM.  This is implemented as a shutdown then a power on.'''
    _helpRebootDescription = '''DDEESSCCRRIIPPTTIIOONN
    Reboot a VM.  This is implemented as a shutdown then a power on.'''
    _helpRebootExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Reboot VM server4.
        [user ~]$ vcli reboot server4
        Shutting down server4
          VM shutdown successful
        Powering on server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py reset -h
    _helpResetSynopsis = '''SSYYNNOOPPSSIISS
    Reset a VM.  This is implemented as a shutdown then a power on.'''
    _helpResetDescription = '''DDEESSCCRRIIPPTTIIOONN
    Reset a VM.  This is implemented as a shutdown then a power on.'''
    _helpResetExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Reset server server1.
        [user ~]$ vcli reset server4
        Power reset server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py resume -h
    _helpResumeSynopsis = '''SSYYNNOOPPSSIISS
    Resume a suspended VM.'''
    _helpResumeDescription = '''DDEESSCCRRIIPPTTIIOONN
    Resume a suspended VM.'''
    _helpResumeExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Resume suspended VM server4.
        [user ~]$ vcli resume server4
        Power resume server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py shutdown -h
    _helpShutdownSynopsis = '''SSYYNNOOPPSSIISS
    Gracefully shut down a VM.'''

    _helpShutdownDescription = '''DDEESSCCRRIIPPTTIIOONN
    Gracefully shut down a VM.'''

    _helpShutdownExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Gracefully shutdown server lgsisa1.
        [user ~]$ vcli shutdown server4
        Shutting down server4
          VM shutdown successful
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py start -h
    _helpStartSynopsis = '''SSYYNNOOPPSSIISS
    Start a VM from a powered off state.'''
    _helpStartDescription = '''DDEESSCCRRIIPPTTIIOONN
    Start a VM from a powered off state.'''
    _helpStartExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        start server2.
        [user ~]$ vcli start server4
        Power start server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py stop -h
    _helpStopSynopsis = '''SSYYNNOOPPSSIISS
    Stop a VM.  This is implemented as a shutdown then a power on.'''

    _helpStopDescription = '''DDEESSCCRRIIPPTTIIOONN
    Stop a VM.  This is implemented as a shutdown then a power on.'''

    _helpStopExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Stop (power off) VM server4.
        [user ~]$ vcli stop server4
        Power stop server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py suspend -h
    _helpSuspendSynopsis = '''SSYYNNOOPPSSIISS
    Suspend a running VM.'''
    _helpSuspendDescription = '''DDEESSCCRRIIPPTTIIOONN
    Suspend a running VM.'''
    _helpSuspendExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Suspend running (powered on) VM server4
        [user ~]$ vcli suspend server4
        Power suspend server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  Snapshot Actions

    ## ---------- ---------- ---------- ----------
    #  vcli.py consolidate -h
    _helpConsolidateSynopsis = '''SSYYNNOOPPSSIISS
    Consolidate VM snapshots.'''
    _helpConsolidateDescription = '''DDEESSCCRRIIPPTTIIOONN
    Consolidate VM snapshots.'''
    _helpConsolidateExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Consolidate VM server4 snapshots.
        Note:  This is only application if the Vm needs consolidating.
        [user ~]$ vcli consolidate server4
        Consolidate snapshot for server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py rm-snapshot -h
    _helpRemoveSnapshotSynopsis = '''SSYYNNOOPPSSIISS
    Merge a VM snapshot VMDK.'''
    _helpRemoveSnapshotDescription = '''DDEESSCCRRIIPPTTIIOONN
    Merge a VM snapshot VMDK.'''
    _helpRemoveSnapshotExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Merge the snapshots into the primary VMDK.
        Note:  VMware GUI equivalent task:  remove snapshot
        [user ~]$ vcli rm-snapshot server4
        Merge snapshot for server4
        Remove all snapshots for server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py snapshot -h
    _helpSnapshotSynopsis = '''SSYYNNOOPPSSIISS
    Create a snapshot for VM.'''
    _helpSnapshotDescription = '''DDEESSCCRRIIPPTTIIOONN
    Create a snapshot for VM.'''
    _helpSnapshotExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Create a snapshot for VM server4.
        [user ~]$ vcli snapshot -D 'test snapshot' server4
        Add snapshot for server4
        Creating snapshot for server4 with memory(False) and quiesce(False)
          Task completed successfully

        Verify that snapshot was indeed created.
        [user ~]$ vcli list snapshot server4
        # VM            Id    Created              By        Description
        # --            --    -------              --        -----------
        server4         1     2019-12-14 02:20:20  user1     test snapshot
    '''

    ## ---------- ---------- ---------- ----------
    #  vcli.py revert -h
    _helpRevertSynopsis = '''SSYYNNOOPPSSIISS
    Revert a VM to a snapshot.'''
    _helpRevertDescription = '''DDEESSCCRRIIPPTTIIOONN
    Revert a VM to a snapshot.'''
    _helpRevertExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Revert VM server4 back to its last snapshot.
        [user ~]$ vcli revert server4
        Revert snapshot for server4
        Reverting to most recent snapshots for server4
          Task completed successfully
    '''

    ## ---------- ---------- ---------- ----------
    #  Administrative Tasks

    ## ---------- ---------- ---------- ----------
    #  vcli.py encrypt -h
    _helpEncryptSynopsis = '''SSYYNNOOPPSSIISS
    Encrypt a plaintext password for future use. '''
    _helpEncryptDescription = '''DDEESSCCRRIIPPTTIIOONN
    The encrypt command encodes a plaintext password into a cipher and stores
    it in a file for use in subsequent calls.

    The encrypted password can be stored in the your personal ~/.vcli.conf file
    or system /etc/.vcli.conf for seamless operations.'''
    _helpEncryptExample = '''EEXXAAMMPPLLEESS
    Example 1
    ---------
        Encrypt a plaintext password -- prompt me for password.
        [user ~]$ vcli encrypt
        Password to Encrypt: ********
        Encrypted ciphertext: tu7J5GCqy9407ikA1glYEFx9S1+Ebfs0G3lVMc7Cm4i9/4qmpHq+uYkbP91kKgb+

    '''


    #
    # class constructor
    #
    def __init__(self):
        _confs = ['{home}/.vcli.conf'.format(home=os.path.expanduser('~')), '/etc/.vcli.conf']
        for _conf in _confs:
            if os.path.isfile(_conf):
                try:
                    _stream = open(_conf, 'r')
                    break
                except IOError:
                    _conf = None
            else:
                _conf = None
        if _conf is None:
            self._print('Cannot open conf files {0}'.format(_confs))
            sys.exit(4)

        self._conf = _conf

        if self._host is None:
            self._host = self._getConf('host')
        if self._port is None:
            self._port = self._getConf('port')
        if self._username is None:
            self._username = self._getConf('username')
        if self._password is None:
            self._password = self._getConf('password')

        if self._host is None or self._host == '':
            self._print('VCenter host not defined in .vcli.conf config file.')
            sys.exit(4)

        if self._username is None:
            import subprocess
            try:
                self._username = subprocess.check_output('logname').rstrip('\n')
            except:
                pass

        if self._ts is None:
            from datetime import datetime
            self._ts = str(datetime.now()).replace('-', '').replace(':', '').split('.')[0].replace(' ', '.').split('.')[0]

    #
    # class desstructor
    #
    def __exit__(self, etype, evalue, traceback):
        self._print('[etype]  {0}'.format(etype))
        self._print('[evalue]  {0}'.format(evalue))
        self._print('[traceback]  {0}'.format(traceback))

    ## ---------- ---------- ---------- ----------
    #  private methods
    #

    #
    # Get YAML conf entry
    #
    def _getConf(self, field=None, group=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _group = group if group is not None else 'vcenter'
        _field = field

        # return value, default = None
        _value = None

        _conf = self._conf
        if os.path.isfile(_conf):
            try:
                import yaml
                _stream = open(_conf, 'r')
                _docs = yaml.load_all(_stream)
                for _doc in _docs:
                    if _group in _doc and _field in _doc[_group]:
                        _value = _doc[_group][_field]
                self._print('{0}.{1} = {2}'.format(_group, _field, _value), 3)
            except IOError:
                _value = None

        return _value

    ## ---------- ---------- ---------- ----------
    # Debug function
    def _printObject(self, obj, title=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        from pprint import pprint

        _title = title
        if _title is not None and _title != '':
            print
            print _title

        print 'dir(object)'
        pprint(dir(obj))

        if hasattr(object, '__dict__'):
            print 'vars(object)'
            pprint(vars(obj))
        else:
            print 'dir(object)'
            pprint(dir(obj))

    ## ---------- ---------- ---------- ----------
    #
    # define verbosity/debug level
    #
    # None :  quiet mode
    #    0 :  normal verbosity
    # >= 1 :  verbose mode for debugging
    #
    def _print(self, line=None, verbosity=0):
        _line = line if line is not None else ''
        _verbosity = verbosity

        _quiet = getattr(self._args, 'quiet') if hasattr(self._args, 'quiet') else None
        if _quiet is not None and _quiet:
            return None

        try:
            _verbose = getattr(self._args, 'verbose') if hasattr(self._args, 'verbose') else None
            if _verbosity == 0:
                print _line
            elif _verbose is not None and _verbose and _verbose >= _verbosity and _verbosity == 1:
                print _line
            elif _verbose is not None and _verbose and _verbose >= _verbosity:
                print '[{caller:<12}][{verbosity}]  {line}'.format(caller=sys._getframe(2).f_code.co_name + '()', verbosity=_verbosity, line=_line)

        except IOError:
            sys.exit(9)

    def _printCsv(self, row):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _row = row

        #
        # if not initalized
        #
        _csv = getattr(self._args, 'csv') if hasattr(self._args, 'csv') else None
        if _csv is not None and self._csvWriter is None:
            import csv
            _csvFile = open(_csv, 'w')
            self._csvWriter = csv.writer(_csvFile, dialect='excel', quotechar='"', quoting=True)

        if self._csvWriter is not None:
            self._csvWriter.writerow(_row)

    def _printRow(self, row=None, fmt=None, verbosity=0):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _row = row
        _fmt = fmt
        _verbosity = verbosity

        if _fmt is None:
            _colWidths = {
                #
                # Virtual Machines
                #
                'a:i': 3,
                'alloc': 5,
                'build': 8,
                'by': -8,
                'cluster': -12,
                'con': -3,
                'cores': 5,
                'created': -19,
                'cpu': 3,
                'cpus': 4,
                'datacenter': -12,
                'datastore': -23,
                'date/time': -19,
                'disks': 5,
                'free': 4,
                'from': -8,
                'guest_id': -8,
                'hd': 2,
                'host': -9,
                'hosts': -20,
                'id': -4,
                'ip_address': -14,
                'limit': 6,
                'mac_address': -16,
                'maint': 5,
                'mem': 3,
                'memory': 6,
                'mode': 4,
                'model': -24,
                'network': -20,
                'nic': 3,
                'net_type': -8,
                'nic_type': -8,
                'owner': -11,
                'pwr': -3,
                'pwr_pol': 7,
                'process': -7,
                'processor_type': -42,
                'reservation': 11,
                'res_pool': -12,
                'share': 5,
                'shares': 6,
                'size': 4,
                'skts': 4,
                'snap': 4,
                'template': -20,
                'to': -8,
                'tools_ver': 10,
                'type': -5,
                'usage': 5,
                'used': 4,
                'uuid': -12,
                'vcpus': 5,
                'version': 7,
                'vlan': 4,
                'vlan_name': -14,
                'vm': -14,
                'vms': -20,
                'vm_ver': 8,

                #
                # Tags
                #
                'attached_to': -20,
                'cardinality': -11,
                'category': -12,
                'description': -20,
                'associable_types': -18,
                'tag': -15,
                'tags': -30,
            }
            _widths = ()
            for _field in _row:
                _field = str(_field).lower()
                if _field.startswith('#'):
                    _field = _field.replace('# ', '')
                _width = _colWidths[_field] if _field in _colWidths else ''
                _widths += ('%{0}s'.format(_width),)
            _fmt = '  '.join(_widths)

        _line = _fmt % _row if _row is not None and _fmt is not None else None
        self._print(_line, verbosity)
        if _line.startswith('#'):
            self._print(re.sub('[0-z]', '-', _line))

        self._printCsv(_row)

        return _fmt

    def _confirm(self):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _proceed = None

        return _proceed

    #
    # Define the CLI arguments
    #
    def _parseArguments(self):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        import argparse

        # application parseri
        _parser = argparse.ArgumentParser(
            description=self._helpSynopsis,
            epilog='{description}\n\n{example}\n\n{credit}'.format(description=self._helpDescription, example=self._helpExample, credit=self._helpCredit),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _spAction = _parser.add_subparsers(title='Action', dest='action', help='VM Informational Actions')
        _grpSep = _spAction.add_parser('', help='------------------------')

        # option groups

        # general authentication options

        ## ---------- ---------- ---------- ----------
        # Global power options
        # option groups
        _optPower = argparse.ArgumentParser(add_help=False)

        _optPowerGroupHw = _optPower.add_argument_group(title='List Hardware Upgrade Options')
        _optPowerGroupHwMutex = _optPowerGroupHw.add_mutually_exclusive_group()
        _optPowerGroupHwMutex.add_argument('-u', '--upgrade-hw', dest='upgrade-hw', action='store_true', help='Upgrade vmx hardware to latest version.')
        _optPowerGroupHwMutex.add_argument('-V', '--hw-version', dest='hw-version', type=int, choices=xrange(10, 15), help='Change the hardware version.')

        ## ---------- ---------- ---------- ----------
        # Global cloning options
        # option groups
        _optClone = argparse.ArgumentParser(add_help=False)
        _optCloneGeneral = _optClone.add_argument_group(title='General Cloning Options')
        _optCloneGeneral.add_argument('-x', '--exclude-tag', dest='include-tag', default=True, action='store_false', help='Exclude tags from source VM')
        _optCloneGeneral.add_argument('-D', '--description', help='Clone description')

        ## ---------- ---------- ---------- ----------
        # Global compute options
        # option groups
        _optCompute = argparse.ArgumentParser(add_help=False)
        _optComputeGeneral = _optCompute.add_argument_group(title='General Compute Options')
        _optComputeGeneral.add_argument('-M', '--memory', type=int, help='Amount of memory (GB).')
        _optComputeGeneral.add_argument('-P', '--cpu', type=int, help='Number of CPU.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py info
        _grpInfo = _spAction.add_parser('info', help='Display information about VM',
            parents=[],
            description=self._helpInfoSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpInfoDescription, example=self._helpInfoExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpInfoOption = _grpInfo.add_argument_group(title='Info Options')
        _grpInfoOption.add_argument('-6', '--ipv6', action='store_true', help='Include IPv6 addresses.')

        _grpInfoArgument = _grpInfo.add_argument_group(title='Info Argument')
        _grpInfoArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to display info for.')

        ## ---------- ---------- ---------- ----------
        # vcli.py list -h
        #
        _grpList = _spAction.add_parser('list', help='Display tabular list of object type',
            parents=[],
            description=self._helpListSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListDescription, example=self._helpListExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _spList = _grpList.add_subparsers(title='Types of object to list', dest='object')

        ## ---------- ---------- ---------- ----------
        # Global list options
        # option groups
        _optList = argparse.ArgumentParser(add_help=False)

        # verbosity
        _optListGroupVerbosity = _optList.add_argument_group(title='List Verbosity Options')
        _optListGroupVerbosityMutex = _optListGroupVerbosity.add_mutually_exclusive_group()
        _optListGroupVerbosityMutex.add_argument('-q', '--quiet', action='store_true', help='Run in quiet mode')
        _optListGroupVerbosityMutex.add_argument('-v', '--verbose', default=0, action='count', help='increase verbosity')

        # power state
        _optListGroupPower = _optList.add_argument_group(title='List Power Options')
        _optListGroupPowerMutex = _optListGroupPower.add_mutually_exclusive_group()
        _optListGroupPowerMutex.add_argument('-0', '--off', dest='power', default=None, action='store_false', help='Powered off')
        _optListGroupPowerMutex.add_argument('-1', '--on', dest='power', default=None, action='store_true', help='Powered on')

        # general options
        _optListGeneral = _optList.add_argument_group(title='General List Options')
        _optListGeneral.add_argument('-l', '--long', default=None, action='store_true', help='Include detail information')
        _optListGeneral.add_argument('-m', '--match', default=None, action='store_true', help='Match argument')
        _optListGeneral.add_argument('-X', '--csv', metavar='OUTFILE', help='Write output in comma separated value (CSV) format to CSV file')

        _optListVm = argparse.ArgumentParser(add_help=False)
        _optListVmGeneral = _optListVm.add_argument_group(title='General VM List Options')
        _optListVmGeneral.add_argument('-C', '--cluster', help='Show Vms in CLUSTER')
        _optListVmGeneral.add_argument('-H', '--host', help='Show Vms in ESXi HOST')
        _optListVmGeneral.add_argument('-O', '--os', default='linux', choices=['all', 'linux', 'windows'], help='Where applicable, filter by Operating System (OS).  Default = linux')

        _grpSep = _spList.add_parser('', help=None)
        _grpSep = _spList.add_parser('', help='VCenter top level objects')
        _grpSep = _spList.add_parser('', help='-------------------------')
        ## ---------- ---------- ---------- ----------
        # vcli.py list category -h
        #
        _grpListCategory = _spList.add_parser('category', help='Tag categories',
            parents=[_optList],
            description=self._helpListCategorySynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListCategoryDescription, example=self._helpListCategoryExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListCategoryOption = _grpListCategory.add_argument_group(title='List Category Options')
        _grpListCategoryOption.add_argument('-A', '--associable-type', dest='associable-type', default='vm', choices=['all', 'vm', 'host', 'folder'], help='Type of object this category can be attached to.  Default=vm.')

        _grpListCategoryArgument = _grpListCategory.add_argument_group(title='List Category Argument')
        _grpListCategoryArgument.add_argument('names', metavar='category-name', nargs='?', help='Name of category')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list cluster -h
        _grpListCluster = _spList.add_parser('cluster', help='Clusters',
            parents=[_optList],
            description=self._helpListClusterSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListClusterDescription, example=self._helpListClusterExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListClusterArgument = _grpListCluster.add_argument_group(title='List Cluster Argument')
        _grpListClusterArgument.add_argument('names', metavar='cluster-name', nargs='?', help='Name of cluster')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list datacenter -h
        _grpListDatacenter = _spList.add_parser('datacenter', help='Datacenters',
            parents=[_optList],
            description=self._helpListDatacenterSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListDatacenterDescription, example=self._helpListDatacenterExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListDatacenterArgument = _grpListDatacenter.add_argument_group(title='List Datacenter Argument')
        _grpListDatacenterArgument.add_argument('names', metavar='datacenter-name', nargs='?', help='Name of datacenter.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list datastore -h
        _grpListDatastore = _spList.add_parser('datastore', help='Datastore',
            parents=[_optList],
            description=self._helpListDatastoreSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListDatastoreDescription, example=self._helpListDatastoreExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListDatastoreArgument = _grpListDatastore.add_argument_group(title='List Datastore Argument')
        _grpListDatastoreArgument.add_argument('names', metavar='datastore-name', nargs='?', help='Name of datastore.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list host -h
        _grpListHost = _spList.add_parser('host', help='Hypervisors / Hosts',
            parents=[_optList],
            description=self._helpListHostSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListHostDescription, example=self._helpListHostExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListHostOption = _grpListHost.add_argument_group(title='List Host Options')
        _grpListHostOption.add_argument('-C', '--cluster', help='Show Vms in CLUSTER')

        _grpListHostArgument = _grpListHost.add_argument_group(title='List Host Argument')
        _grpListHostArgument.add_argument('names', metavar='vm-name', nargs='?', help='Name of VM.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list network -h
        _grpListNetwork = _spList.add_parser('network', help='Networks',
            parents=[_optList],
            description=self._helpListNetworkSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListNetworkDescription, example=self._helpListNetworkExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListNetworkArgument = _grpListNetwork.add_argument_group(title='List Network Argument')
        _grpListNetworkArgument.add_argument('names', metavar='network-name', nargs='?', help='Name of network.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list resource-pool -h
        _grpListRpool = _spList.add_parser('rp', help='Resource Pools',
            parents=[_optList],
            description=self._helpListRpoolSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListRpoolDescription, example=self._helpListRpoolExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListRpoolArgument = _grpListRpool.add_argument_group(title='List Resource Pool Argument')
        _grpListRpoolArgument.add_argument('names', metavar='resource-pool-name', nargs='?', help='Name of resource pool.')

        ## ---------- ---------- ---------- ----------
        # vcli.py list tag -h
        #
        _grpListTag = _spList.add_parser('tag', help='Tag values',
            parents=[_optList],
            description=self._helpListTagSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListTagDescription, example=self._helpListTagExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListTagOption = _grpListTag.add_argument_group(title='List Tag Options')
        _grpListTagOption.add_argument('-A', '--associable-type', dest='associable-type', default='vm', choices=['all', 'vm', 'host', 'folder'], help='Type of object this category can be attached to.')
        _grpListTagOption.add_argument('-C', '--category', default=None, action='store', help='Show tag for category')

        _grpListTagArgument = _grpListTag.add_argument_group(title='List Tag Argument')
        _grpListTagArgument.add_argument('names', metavar='tag-name', nargs='?', help='Name of tag')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list template -h
        _grpListTemplate = _spList.add_parser('template', help='Virtual Machines template',
            parents=[_optList, _optListVm],
            description=self._helpListTemplateSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListTemplateDescription, example=self._helpListTemplateExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListTemplateOption = _grpListTemplate.add_argument_group(title='List Template Options')
        _grpListTemplateOption.add_argument('-V', '--hw-version', dest='hw-version', type=int, help='Hardware version.')

        _grpListTemplateArgument = _grpListTemplate.add_argument_group(title='List Template Argument')
        _grpListTemplateArgument.add_argument('names', metavar='template-name', nargs='*', help='Name of template')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list vm -h
        _grpListVirtualMachine = _spList.add_parser('vm', help='Virtual Machines',
            parents=[_optList, _optListVm],
            description=self._helpListVmSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListVmDescription, example=self._helpListVmExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListVirtualMachineOption = _grpListVirtualMachine.add_argument_group(title='List VM Options')
        _grpListVirtualMachineOption.add_argument('-c', '--consolidate', dest='consolidate', default=None, action='store_true', help='Show VM that needs consolidation')

        # snapshot is a tristate value: None, True or False
        _grpListVirtualMachineOptionSnapshotMutex = _grpListVirtualMachineOption.add_mutually_exclusive_group()
        _grpListVirtualMachineOptionSnapshotMutex.add_argument('-n', '--no-snapshot', dest='snapshot', default=None, action='store_false', help='Show VM that does not have snapshots')
        _grpListVirtualMachineOptionSnapshotMutex.add_argument('-s', '--snapshot', dest='snapshot', default=None, action='store_true', help='Show VM with snapshots')

        _grpListVirtualMachineOption.add_argument('-V', '--hw-version', dest='hw-version', type=int, help='Hardware version.')

        _grpListVirtualMachineArgument = _grpListVirtualMachine.add_argument_group(title='List VM Argument')
        _grpListVirtualMachineArgument.add_argument('names', metavar='vm-name', nargs='*', help='Name of VM')

        ## ---------- ---------- ---------- ----------
        #  VM resources
        _grpSep = _spList.add_parser('', help=None)
        _grpSep = _spList.add_parser('', help='Virtual Machine Resources')
        _grpSep = _spList.add_parser('', help='-------------------------')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list disk -h
        _grpListVmDisk = _spList.add_parser('disk', help='VM disks',
            parents=[_optList, _optListVm],
            description=self._helpListVmDiskSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListVmDiskDescription, example=self._helpListVmDiskExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListVmDiskOption = _grpListVmDisk.add_argument_group(title='List VM Disk Options')
        _grpListVmDiskOption.add_argument('-D', '--disk', dest='disk-id', type=int, help='Limit output to this disk')

        _grpListVmDiskArgument = _grpListVmDisk.add_argument_group(title='List VM Disk Argument')
        _grpListVmDiskArgument.add_argument('names', metavar='vm-name', nargs='*', help='Name of VM.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py list nic -h
        _grpListVmNic = _spList.add_parser('nic', help='VM network interface card (NIC)',
            parents=[_optList, _optListVm],
            description=self._helpListVmNicSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListVmNicDescription, example=self._helpListVmNicExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListVmNicOption = _grpListVmNic.add_argument_group(title='List VM NIC Options')
        _grpListVmNicOption.add_argument('-6', '--ipv6', action='store_true', help='Include IPv6 addresses.')
        _grpListVmNicOption.add_argument('-N', '--nic', dest='nic-id', type=int, help='Limit output to this NIC')

        _grpListVmNicArgument = _grpListVmNic.add_argument_group(title='List VM NIC Argument')
        _grpListVmNicArgument.add_argument('names', metavar='vm-name', nargs='*', help='Name of VM.')
        ## ---------- ---------- ---------- ----------
        #  vcli.py list snapshot -h
        _grpListVmSnapshot = _spList.add_parser('snapshot', help='VM snapshots',
            parents=[_optList, _optListVm],
            description=self._helpListVmSnapshotSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListVmSnapshotDescription, example=self._helpListVmSnapshotExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListVmSnapshotArgument = _grpListVmSnapshot.add_argument_group(title='List VM Snapshot Argument')
        _grpListVmSnapshotArgument.add_argument('names', metavar='vm-name', nargs='*', help='Name of VM.')

        ## ---------- ---------- ---------- ----------
        # vcli.py list vm-tag -h
        #
        _grpListVmTag = _spList.add_parser('vm-tag', help='VM and its tags',
            parents=[_optList, _optListVm],
            description=self._helpListVmTagSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpListVmTagDescription, example=self._helpListVmTagExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpListVmTagOption = _grpListVmTag.add_argument_group(title='List VM Tag Options')
        _grpListVmTagOption.add_argument('-T', '--tag', default=None, action='store', help='Show VM with specified tag.')

        _grpListVmTagArgument = _grpListVmTag.add_argument_group(title='List VM Tag Argument')
        _grpListVmTagArgument.add_argument('names', metavar='vm-name', nargs='*', help='Name of VM.  If one name is given than partial name search is done, unless the -m option is used.  If two or more VM are given then exact match is performed on all server names')

        ## ---------- ---------- ---------- ----------
        # Global task options
        # option groups
        _optTask = argparse.ArgumentParser(add_help=False)

        # general options
        _optTaskGeneral = _optTask.add_argument_group(title='General Task Options')
        _optTaskGeneral.add_argument('-W', '--wait', type=int, default=42, help='Number of seconds to wait task to complete.  Default=42.')

        ## ---------- ---------- ---------- ----------
        #  VM Common Actions
        _grpSep = _spAction.add_parser('', help=None)
        _grpSep = _spAction.add_parser('', help='VM Common Actions')
        _grpSep = _spAction.add_parser('', help='-----------------')

        ## ---------- ---------- ---------- ----------
        #  vcli.py add -h
        #
        _grpAdd = _spAction.add_parser('add', help='Add resources to VM.',
            parents=[_optCompute],
            description=self._helpAddSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpAddDescription, example=self._helpAddExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)


        _grpAddStorageOption = _grpAdd.add_argument_group(title='Add Storage Options')
        _grpAddStorageOption.add_argument('-S', '--storage', dest='storage-size', type=int, help='Size of additional storage in GB.')
        _grpAddStorageOptionMutex = _grpAddStorageOption.add_mutually_exclusive_group()
        _grpAddStorageOptionMutex.add_argument('-D', '--disk', dest='disk-id', type=int, help='Add storage to existing disk at disk-id.')
        _grpAddStorageOptionMutex.add_argument('-n', '--new-disk', dest='new-disk', action='store_true', help='Add storage to new disk')

        _grpAddStorageOption.add_argument('-i', '--independent', action='store_true', help='Make disk independent_persistent, only valid if creating new disk.')
        _grpAddStorageOption.add_argument('-t', '--thick', default=None, action='store_true', help='Override thick provision restriction, only valid if creating new disk.')

        _grpAddNicOption = _grpAdd.add_argument_group(title='Add NIC Options')
        _grpAddNicOptionMutex = _grpAddNicOption.add_mutually_exclusive_group()
        _grpAddNicOptionMutex.add_argument('-N', '--network', help='Add network by name.')
        _grpAddNicOptionMutex.add_argument('-V', '--vlan', dest='vlan-id', type=int, help='Add network by VLAN number.')

        _grpAddTagOption = _grpAdd.add_argument_group(title='Add Tag Options')
        _grpAddTagOption.add_argument('-T', '--tag', help='Add tag.')
        _grpAddTagOption.add_argument('-C', '--category', help='Add tag in this category.')

        _grpAddArgument = _grpAdd.add_argument_group(title='Add Resource Argument')
        _grpAddArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to add resource to.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py backup -h
        #
        _grpBackup = _spAction.add_parser('backup', help='Create a clone backup of VM.',
            parents=[_optClone, _optCompute],
            description=self._helpBackupSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpBackupDescription, example=self._helpBackupExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpBackupArgument = _grpBackup.add_argument_group(title='Backup Argument')
        _grpBackupArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to backup.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py change -h
        #
        _grpChange = _spAction.add_parser('change', help='Change property of VM.',
            parents=[_optPower, _optCompute],
            description=self._helpChangeSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpChangeDescription, example=self._helpChangeExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpChangeOption = _grpChange.add_argument_group(title='Change VM Options')
        _grpChangeOption.add_argument('-a', '--hot-add', dest='hot-add', action='store_true', help='Enable CPU and memory hot-add feature.')
        _grpChangeOptionTemplate = _grpChangeOption.add_mutually_exclusive_group()
        _grpChangeOptionTemplate.add_argument('-m', '--vm', dest='mark_as_template', default=None, action='store_false', help='Convert to VM.')
        _grpChangeOptionTemplate.add_argument('-t', '--template', dest='mark_as_template', default=None, action='store_true', help='Convert to template')

        _grpChangeOption.add_argument('-A', '--append', help='Append to VM name.')
        _grpChangeOption.add_argument('-D', '--description', help='New description/annotation to set for VM.')
        _grpChangeOption.add_argument('-N', '--new-name', dest='new-name', help='New name to change VM to.')
        _grpChangeOption.add_argument('-R', '--resource-pool', dest='resource-pool', help='Change the resource pool.')

        _grpChangeArgument = _grpChange.add_argument_group(title='Change VM Argument')
        _grpChangeArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to change.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py clone -h
        #
        _grpClone = _spAction.add_parser('clone', help='Create new clone VM',
            parents=[_optClone, _optCompute],
            description=self._helpCloneSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpCloneDescription, example=self._helpCloneExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpCloneArgument = _grpClone.add_argument_group(title='Clone Argument')
        _grpCloneArgument.add_argument('source', help='Clone source, can be a template or a VM.')
        _grpCloneArgument.add_argument('names', metavar='vm-name', nargs='+', help='New name of clone.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py destroy -h
        #
        _grpDestroy = _spAction.add_parser('destroy', help='Destroy a VM',
            parents=[],
            description=self._helpDestroySynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpDestroyDescription, example=self._helpDestroyExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpDestroyArgument = _grpDestroy.add_argument_group(title='Destroy Argument')
        _grpDestroyArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to destroy.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py migrate
        _grpMigrate = _spAction.add_parser('migrate', help='Migrate VM to another host',
            parents=[],
            description=self._helpMigrateSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpMigrateDescription, example=self._helpMigrateExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpMigrateOption = _grpMigrate.add_argument_group(title='Migrate Options')
        _grpMigrateOption.add_argument('-t', '--thin', action='store_true', help='Convert to thin provision disk')
        _grpMigrateOption.add_argument('-D', '--datastore', dest='to-datastore', help='Name of datastore to migrate VM disks to.')
        _grpMigrateOption.add_argument('-H', '--host', dest='to-host', help='Name of host to migrate VM to.')

        _grpMigrateArgument = _grpMigrate.add_argument_group(title='Migrate Argument')
        _grpMigrateArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to migrate.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py remove -h
        #
        _grpRemove = _spAction.add_parser('remove', help='Remove a resource from VM.',
            parents=[_optCompute],
            description=self._helpRemoveSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpRemoveDescription, example=self._helpRemoveExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)

        _grpRemoveComputeOption = _grpRemove.add_argument_group(title='Remove Compute Options')

        _grpRemoveStorageOption = _grpRemove.add_argument_group(title='Remove Storage Options')
        _grpRemoveStorageOption.add_argument('-D', '--disk', dest='disk-id', type=int, help='Remove disk by its id')

        _grpRemoveNicOption = _grpRemove.add_argument_group(title='Remove NIC Options')
        _grpRemoveNicOptionMutex = _grpRemoveNicOption.add_mutually_exclusive_group()
        _grpRemoveNicOptionMutex.add_argument('-N', '--network', help='Remove NIC specified by network name or adapter number.')
        _grpRemoveNicOptionMutex.add_argument('-V', '--vlan', dest='vlan-id', type=int, help='Remove NIC by VLAN number.')

        _grpRemoveTagOption = _grpRemove.add_argument_group(title='Remove NIC Options')
        _grpRemoveTagOption.add_argument('-T', '--tag', help='Remove tag.')
        _grpRemoveTagOption.add_argument('-C', '--category', help='Remove tag in this category.')

        _grpRemoveArgument = _grpRemove.add_argument_group(title='Remove Argument')
        _grpRemoveArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to add resource to.')

        ## ---------- ---------- ---------- ----------
        #  VM Power State Actions
        _grpSep = _spAction.add_parser('', help=None)
        _grpSep = _spAction.add_parser('', help='VM Power State Actions')
        _grpSep = _spAction.add_parser('', help='----------------------')

        ## ---------- ---------- ---------- ----------
        #  vcli.py reboot -h
        _grpReboot = _spAction.add_parser('reboot', help='Gracefully reboot VM (shutdown then power on)',
            parents=[_optPower, _optTask],
            description=self._helpRebootSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpRebootDescription, example=self._helpRebootExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpRebootArgument = _grpReboot.add_argument_group(title='Reboot Argument')
        _grpRebootArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to gracefully reboot.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py reset -h
        _grpReset = _spAction.add_parser('reset', help='Forcefully reset a VM (power off then on)',
            parents=[_optPower, _optTask],
            description=self._helpResetSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpResetDescription, example=self._helpResetExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpResetArgument = _grpReset.add_argument_group(title='Reset Snapshot Argument')
        _grpResetArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to forcecibly reset.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py resume -h
        _grpResume = _spAction.add_parser('resume', help='Resume a suspended VM',
            parents=[_optPower, _optTask],
            description=self._helpResumeSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpResumeDescription, example=self._helpResumeExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpResumeArgument = _grpResume.add_argument_group(title='Resume Argument')
        _grpResumeArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to gracefully resume.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py shutdown -h
        _grpShutdown = _spAction.add_parser('shutdown', help='Gracefully shutdown VM',
            parents=[_optPower, _optTask],
            description=self._helpShutdownSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpShutdownDescription, example=self._helpShutdownExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpShutdownOption = _grpShutdown.add_argument_group(title='Shutdown Options')
        _grpShutdownOption.add_argument('-r', '--reboot', action='store_true', help='Reboot VM after successful shutdown.')

        _grpShutdownArgument = _grpShutdown.add_argument_group(title='Shutdown Argument')
        _grpShutdownArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to gracefully shutdown.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py start -h
        _grpStart = _spAction.add_parser('start', help='Start (power on) a VM',
            parents=[_optPower, _optTask],
            description=self._helpStartSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpStartDescription, example=self._helpStartExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpStartArgument = _grpStart.add_argument_group(title='Start Argument')
        _grpStartArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to gracefully start.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py stop -h
        _grpStop = _spAction.add_parser('stop', help='Stop (power off) a VM',
            parents=[_optPower, _optTask],
            description=self._helpStopSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpStopDescription, example=self._helpStopExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpStopArgument = _grpStop.add_argument_group(title='Stop Argument')
        _grpStopArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to gracefully stop.')

        ## ---------- ---------- ---------- ----------
        #  vcli.py suspend -h
        _grpSuspend = _spAction.add_parser('suspend', help='Suspend a running VM',
            parents=[_optPower, _optTask],
            description=self._helpSuspendSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpSuspendDescription, example=self._helpSuspendExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpSuspendArgument = _grpSuspend.add_argument_group(title='Suspend Argument')
        _grpSuspendArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of VM to gracefully suspend.')

        ## ---------- ---------- ---------- ----------
        #  VM Snapshot Actions
        _grpSep = _spAction.add_parser('', help=None)
        _grpSep = _spAction.add_parser('', help='VM Snapshot Actions')
        _grpSep = _spAction.add_parser('', help='-------------------')

        ## ---------- ---------- ---------- ----------
        #  vcli.py consolidate -h
        _grpConsolidate = _spAction.add_parser('consolidate', help='Consolidate snapshot for VM',
            parents=[],
            description=self._helpConsolidateSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpConsolidateDescription, example=self._helpConsolidateExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpConsolidateOption = _grpConsolidate.add_argument_group(title='Consolidate Options')
        _grpConsolidateOption.add_argument('-m', '--match', default=None, action='store_true', help='Match VM name.')
        _grpConsolidateArgument = _grpConsolidate.add_argument_group(title='Consolidate Snapshot Argument')
        _grpConsolidateArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of vm to create a snapshot for')

        ## ---------- ---------- ---------- ----------
        #  vcli.py revert -h
        _grpRevert = _spAction.add_parser('revert', help='Revert VM to snapshot',
            parents=[],
            description=self._helpRevertSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpRevertDescription, example=self._helpRevertExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpRevertOption = _grpRevert.add_argument_group(title='Revert Snapshot Options')
        _grpRevertOption.add_argument('-I', '--id', dest='snapshot-id', type=int, help='Snapshot ID')

        _grpRevertArgument = _grpRevert.add_argument_group(title='Revert Snapshot Argument')
        _grpRevertArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of vm to create a snapshot for')

        ## ---------- ---------- ---------- ----------
        #  vcli.py rm-snapshot -h
        _grpRemoveSnapshot = _spAction.add_parser('rm-snapshot', help='Remove snapshot from VM',
            parents=[],
            description=self._helpRemoveSnapshotSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpRemoveSnapshotDescription, example=self._helpRemoveSnapshotExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpRemoveSnapshotOption = _grpRemoveSnapshot.add_argument_group(title='Merge Snapshot Options')
        _grpRemoveSnapshotOption.add_argument('-I', '--id', dest='snapshot-id', type=int, help='Snapshot ID')

        _grpRemoveSnapshotArgument = _grpRemoveSnapshot.add_argument_group(title='Merge Snapshot Argument')
        _grpRemoveSnapshotArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of vm to create a snapshot for')

        ## ---------- ---------- ---------- ----------
        #  vcli.py snapshot -h
        _grpSnapshot = _spAction.add_parser('snapshot', help='Create snapshot for VM',
            parents=[],
            description=self._helpSnapshotSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpSnapshotDescription, example=self._helpSnapshotExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpSnapshotAddOption = _grpSnapshot.add_argument_group(title='Create Snapshot Options')
        _grpSnapshotAddOption.add_argument('-m', '--match', default=None, action='store_true', help='Match VM name.')
        _grpSnapshotAddOption.add_argument('-D', '--description', required=True, help='Snapshot description')

        _grpSnapshotAddArgument = _grpSnapshot.add_argument_group(title='Create Snapshot Argument')
        _grpSnapshotAddArgument.add_argument('names', metavar='vm-name', nargs='+', help='Name of vm to create a snapshot for')

        ## ---------- ---------- ---------- ----------
        #  VCLI Administrative Tasks
        _grpSep = _spAction.add_parser('', help=None)
        _grpSep = _spAction.add_parser('', help='VCLI Administrative Tasks')
        _grpSep = _spAction.add_parser('', help='-------------------------')

        ## ---------- ---------- ---------- ----------
        # Global admin options
        # option groups
        _optCrypto = argparse.ArgumentParser(add_help=False)

        # general options
        _optCryptoGeneral = _optCrypto.add_argument_group(title='General Crypto Options')
        _optCryptoGeneral.add_argument('-O', '--outfile', help='Name of file to save result to')

        ## ---------- ---------- ---------- ----------
        # vcli.py encrypt
        #
        _grpEncrypt = _spAction.add_parser('encrypt', help='Encrypt a plaintext password for seamless execution, see the help for further instruction.',
            parents=[_optCrypto],
            description=self._helpEncryptSynopsis,
            epilog='{description}\n\n{example}'.format(description=self._helpEncryptDescription, example=self._helpEncryptExample),
            formatter_class=argparse.RawDescriptionHelpFormatter)
        _grpEncryptArgument = _grpEncrypt.add_argument_group(title='Encrypt Argument')
        _grpEncryptArgument.add_argument('password', nargs='?', help='Password to encrypt, plaintext or filename')


        _args = _parser.parse_args()

        return _args

    ## ---------- ---------- ---------- ----------
    # vcli.py encrypt ...
    # vcli.py decrypt ...
    #
    # AES 256 encryption/decryption using pycrypto library
    #
    def _decrypt(self, cipher):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        try:
            _cipher = cipher
            _action = 'decrypt'
            _password = self._encrypt(_cipher, _action)
        except ValueError:
            _password = cipher

        return _password

    def _encrypt(self, data, action='encrypt'):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        import base64
        from Crypto.Cipher import AES
        from Crypto import Random
        from Crypto.Protocol.KDF import PBKDF2

        _data = data
        _action = action
        _outfile = getattr(self._args, 'outfile') if hasattr(self._args, 'outfile') else None

        if _data is None:
            import getpass
            _prompt = 'Password to Encrypt:  ' if _action == 'encrypt' else 'Password:  '
            _data = getpass.getpass(_prompt)

        if os.path.isfile(_data):
            _data = open(_data, 'r').read()

        _bs = 32
        _pad = lambda _s: _s + (_bs - len(_s) % _bs) * chr(_bs - len(_s) % _bs)
        _unpad = lambda _s: _s[:-ord(_s[len(_s) - 1:])]

        _pwd = 'Pink is the new black'

        _salt = b'''Wife said your money is my money'''
        _kdf = PBKDF2(_pwd, _salt, 64, 2048)
        _key = _kdf[:32]


        if action == 'encrypt':
            _data = _pad(_data)
            _iv = Random.new().read(AES.block_size)
            _cipher = AES.new(_key, AES.MODE_CBC, _iv)
            _data = base64.b64encode(_iv + _cipher.encrypt(_data.encode('utf-8')))
        else:
            _data = base64.b64decode(_data)
            _iv = _data[:AES.block_size]
            _cipher = AES.new(_key, AES.MODE_CBC, _iv)
            _data = _unpad(_cipher.decrypt(_data[AES.block_size:]))
            _data = _data.rstrip('\n')

        if _outfile is not None:
            _hndl = open(_outfile, 'w')
            _hndl.write(_data)
            self._print('Result saved to {0}'.format(_outfile))

        #
        # Encryption/Decryption failed
        # return data passed in
        #
        if _data is None or _data == '':
            _data = data

        return _data

    def _loginVcenter(self):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        if self._si is not None:
            self._print('Already logged in', 1)
            return self._si

        #
        # get login info
        #
        _host = self._host
        _port = self._port

        _username = self._username
        _password = self._decrypt(self._password)


        #
        # prompt for password if not detectable
        #
        import getpass
        _prompt = 'VCenter Password:  '
        if _password is None:
            _password = getpass.getpass(_prompt)


        #
        # Let's log in
        #
        _attempt = 0
        while self._si is None and _attempt < 3:
            _attempt += 1
            try:






                _sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
                _sslContext.verify_mode = ssl.CERT_NONE
                _si = SmartConnect(host=_host, port=_port, user=_username, pwd=_password, sslContext=_sslContext)
                self._si = _si
            except:
                self._print('Login failed')
                _password = getpass.getpass(_prompt)


        if self._si is None:
            self._print('Login failed -- retry attempts exceeded')
            sys.exit(1)

        #
        # login successful
        #
        self._username = _username

        return self._si

    def _loginInventoryService(self):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        if self._stubConfig is not None:
            self._print('Already logged in', 1)
            return self._stubConfig

        #
        # get login info
        #
        _host = self._host
        _port = self._port

        _username = self._username
        _password = self._decrypt(self._password)


        #
        # prompt for password if not detectable
        #
        import getpass
        _prompt = 'VCenter Password:  '
        if _password is None:
            _password = getpass.getpass(_prompt)


        #
        # Let's log in
        #
        _url = 'https://{host}:{port}/api'.format(host=_host, port=_port)
        _attempt = 0
        while self._stubConfig is None and _attempt < 3:
            _attempt += 1
            try:

                _session = requests.Session()
                _session.verify = False
                _connector = get_requests_connector(session=_session, url=_url)
                _stubConfig = StubConfigurationFactory.new_std_configuration(_connector)

                # Pass user credentials (user/password) in the security context to authenticate.
                # login to vAPI endpoint
                _authContext = create_user_password_security_context(_username, _password)
                _stubConfig.connector.set_security_context(_authContext)

                # Create the stub for the session service and login by creating a session.
                _sessionService = Session(_stubConfig)
                _sessionId = _sessionService.create()

                # Successful authentication.  Store the session identifier in the security
                # context of the stub and use that for all subsequent remote requests
                _sessionContext = create_session_security_context(_sessionId)
                _stubConfig.connector.set_security_context(_sessionContext)

                self._stubConfig = _stubConfig

            except:
                self._print('Login failed')
                _password = getpass.getpass(_prompt)


        if self._stubConfig is None:
            self._print('Login failed -- retry attempts exceeded')
            sys.exit(0)

        #
        # login successful
        #
        self._username = _username

        return self._stubConfig

    def _logout(self):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

    def _getListVmRow(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm

        #
        # retrieve data row
        #
        _cpu = _vm.summary.config.numCpu
        _mem = int(_vm.summary.config.memorySizeMB) / 1024 if _vm.summary.config.memorySizeMB is not None else None
        _vmCon = 'Yes' if _vm.summary.runtime.consolidationNeeded else 'No'
        _guestId = _vm.summary.config.guestId.replace('Guest', '') if _vm.summary.config.guestId is not None else 'Unknown'

        if _vm.rootSnapshot:
            _vmSnap = 1
            _ss = _vm.snapshot.rootSnapshotList[0]
            while len(_ss.childSnapshotList) > 0:
                _vmSnap += 1
                _ss = _ss.childSnapshotList[0]
        else:
            _vmSnap = 'No'

        # calculate total disk usage
        _vmDisk = 0
        for _hw in _vm.config.hardware.device:
            if isinstance(_hw, vim.vm.device.VirtualDisk):
                _vmDisk += _hw.capacityInKB / 1024 / 1024

        _vmAnnotation = _vm.summary.config.annotation.replace(u'\u2019', u'\'').encode('ascii', 'ignore') if _vm.summary.config.annotation is not None else None

        #
        # these property takes more time
        #
        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None
        if _long is not None and _long:
            # Time Cost: Low
            _vmVersion = _vm.config.version
            _toolsVersion = _vm.guest.toolsVersion

            _vmHost = _vm.summary.runtime.host.summary.config.name.split('.')[0]
            _vmCluster = _vm.runtime.host.parent.name

            _row = (_vm.summary.config.name,
                    _vm.summary.runtime.powerState.replace('powered', ''),
                    _cpu, _mem, _vmDisk,
                    _vmSnap, _vmCon,
                    _vmVersion, _toolsVersion, _guestId,
                    _vmHost, _vmCluster,
                    _vmAnnotation)
        else:
            _row = (_vm.summary.config.name,
                    _vm.summary.runtime.powerState.replace('powered', ''),
                    _cpu, _mem, _vmDisk,
                    _vmSnap, _vmCon,
                    _vmAnnotation)

        return _row

    def _toList(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        if names is None:
            return None

        if isinstance(names, str):
            names = names.replace(',', ' ').split(' ')

        #
        # if any entry is a file, read it
        #
        _names = []
        for _name in names:
            if _name == '':
                continue

            if os.path.isfile(_name):
                _hFile = open(_name, 'r')
                for _line in iter(_hFile):
                    # Skip empty and commented lines
                    if len(_line.split()) == 0 or _line.startswith('#'):
                        continue
                    _names.append(_line.split()[0])
                _hFile.close()
            else:
                # Split comma delimited entries into list,
                # add to existing list
                _names += _name.split(',')

        #
        # change to lowercase
        #
        _names0 = []
        for _name in _names:
            _names0.append(_name.lower())
        _names = _names0

        #
        # return None if empty
        #
        if len(_names) == 0:
            _names = None

        return _names

    def _getObjects(self, otype, names=None, match=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _otype = otype
        _names = [names.lower()] if isinstance(names, str) else names
        _match = getattr(self._args, 'match') if hasattr(self._args, 'match') and match is not None else match


        # check for empty string and array/list
        if _names is not None and isinstance(_names, str) and _names == '':
            _names = None
        if _names is not None and not isinstance(_names, str) and len(_names) == 0:
            _names = None
        if _names is None:
            _match = None

        #
        # set view & spec types
        #
        if _otype in ['cluster', 'ClusterComputeResource']:
            _specType = vim.ClusterComputeResource
        elif _otype in ['datacenter', 'Datacenter']:
            _specType = vim.Datacenter
        elif _otype in ['datastore', 'Datastore']:
            _specType = vim.Datastore
        elif _otype in ['dvs', 'DistributedVirtualPortgroup']:
            _specType = vim.dvs.DistributedVirtualPortgroup
        elif _otype in ['host', 'HostSystem']:
            _specType = vim.HostSystem
        elif _otype in ['network', 'Network']:
            _specType = vim.Network
        elif _otype in ['pod', 'StoragePod']:
            _specType = vim.StoragePod
        elif _otype in ['rp', 'ResourcePool', 'pool']:
            _specType = vim.ResourcePool
        elif _otype in ['storage', 'StoragePod']:
            _specType = vim.StoragePod
        elif _otype in ['vm', 'VirtualMachine']:
            _specType = vim.VirtualMachine
        else:
            self._print('Unsupported object type')
            return None
        _viewType = [_specType]

        #
        # define properties to collect
        #
        _properties = ['name']

        if _otype in ['vm', 'VirtualMachine']:
            _properties.append('rootSnapshot')
            _properties.append('config.template')
            _properties.append('config.guestId')
            _properties.append('config.annotation')
            _properties.append('runtime.powerState')
            _properties.append('runtime.consolidationNeeded')
            _properties.append('summary.config.memorySizeMB')
            _properties.append('summary.config.numCpu')

            _properties.append('config.version')
            _properties.append('guest.toolsVersion')
            _properties.append('guest.ipAddress')

            # objects

        _si = self._loginVcenter()
        _content = _si.RetrieveContent()

        # Build a view and get basic properties for all Virtual Machines
        _containerView = _content.viewManager.CreateContainerView(_content.rootFolder, _viewType, recursive=True)

        _tSpec = vim.PropertyCollector.TraversalSpec(name='tSpecName', path='view', skip=False, type=vim.view.ContainerView)
        _pSpec = vim.PropertyCollector.PropertySpec(all=False, pathSet=_properties, type=_specType)
        _oSpec = vim.PropertyCollector.ObjectSpec(obj=_containerView, selectSet=[_tSpec], skip=False)
        _pfSpec = vim.PropertyCollector.FilterSpec(objectSet=[_oSpec], propSet=[_pSpec], reportMissingObjectsInResults=False)
        _retOptions = vim.PropertyCollector.RetrieveOptions()
        _totalProps = []
        _retProps = _content.propertyCollector.RetrievePropertiesEx(specSet=[_pfSpec], options=_retOptions)
        _totalProps += _retProps.objects
        while _retProps.token:
            _retProps = _content.propertyCollector.ContinueRetrievePropertiesEx(token=_retProps.token)
            _totalProps += _retProps.objects
        _containerView.Destroy()

        # Turn the output in _retProps into a usable dictionary of values
        _objects = {}
        for _eachProp in _totalProps:
            # match name
            if _match is not None and _match:
                if _names is not None and _eachProp.obj.name.lower() not in _names and _eachProp.obj._moId not in _names:
                    continue

            # partial/substring search
            if (_match is None or not _match) and _names is not None:
                _skip = True
                for _name in _names:
                    if _name.lower() in _eachProp.obj.name.lower() or _name.lower() == _eachProp.obj._moId.lower():
                        _skip = False
                        break
                if _skip:
                    continue

            _object = {'id': _eachProp.obj}
            _name = None
            for _pset in _eachProp.propSet:
                _object[_pset.name] = _pset.val
                if _pset.name == 'name':
                    _name = _pset.val
            try:
                if _name is not None:
                    _objects[_name] = _object
            except:
                pass


        return _objects

    def _getNetworkObjects(self, network=None, vlanId=None, pgkey=None, match=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _network = getattr(self._args, 'network') if hasattr(self._args, 'network') else network
        _vlanId = getattr(self._args, 'vlan-id') if hasattr(self._args, 'vlan-id') else vlanId
        _pgkey = getattr(self._args, 'pgkey') if hasattr(self._args, 'pgkey') else pgkey
        _match = match

        if _vlanId is None and _network is not None and _network.isdigit():
            _vlanId = int(_network)
            _network = None

        _objNetworks = self._getObjects('network', _network, match=_match)
        if _vlanId is not None or _pgkey is not None:
            _nws = {}
            for _key in _objNetworks:
                _dvs = _objNetworks[_key]['id']
                if _vlanId is not None and _dvs.config.defaultPortConfig.vlan.vlanId == _vlanId:
                    _nws[_key] = _objNetworks[_key]
                if _pgkey is not None and _dvs.key == _pgkey:
                    _nws[_key] = _objNetworks[_key]
            _objNetworks = _nws

        return _objNetworks

    def _getVmDiskObject(self, vm, diskId):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _diskId = diskId

        _label = 'Hard disk {diskId}'.format(diskId=_diskId)
        _vmDisk = None
        for _dev in _vm.config.hardware.device:
            if not isinstance(_dev, vim.vm.device.VirtualDisk):
                continue

            #
            # if disk id was not specified,
            # then set it to latest disk
            #
            if _diskId is None:
                _vmDisk = _dev
                continue

            #
            # found the disk we're looking for, let's stop
            #
            if _dev.deviceInfo.label == _label:
                _vmDisk = _dev
                break

        return _vmDisk

    def _getVmNicObject(self, vm, network):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _network = network

        _vlanId = getattr(self._args, 'vlan-id') if hasattr(self._args, 'vlan-id') else None
        _nicId = _network if _network is not None and _network.isdigit() else None
        _label = 'Network adapter {id}'.format(id=_network) if _network is not None and _network.isdigit() else None

        if _vlanId is None and _nicId is None:
            _objNetworks = self._getNetworkObjects(_network, match=True)
            self._print('[len(_objNetworks)]  {0}'.format(len(_objNetworks)))
            if len(_objNetworks) == 1:
                for _key in _objNetworks:
                    _dvs = _objNetworks[_key]['id']
                    _vlanId = _dvs.config.defaultPortConfig.vlan.vlanId
                    self._print('[_vlanId]  {0}'.format(_vlanId))

        if _label is None and _vlanId is None:
            return None


        _vmNic = None
        for _dev in _vm.config.hardware.device:
            if not isinstance(_dev, vim.vm.device.VirtualEthernetCard):
                continue

            if _label is not None and _dev.deviceInfo.label == _label:
                _vmNic = _dev
                break

            # find dvs
            _objNetworks = self._getNetworkObjects(pgkey=_dev.backing.port.portgroupKey)
            for _key in _objNetworks:
                _dvs = _objNetworks[_key]['id']
                if _vlanId is not None and _dvs.config.defaultPortConfig.vlan.vlanId == _vlanId:
                    _vmNic = _dev
                    break
            if _vmNic is not None:
                break

            if _vlanId is not None:
                # find dvs
                _objNetworks = self._getNetworkObjects(pgkey=_dev.backing.port.portgroupKey)
                for _key in _objNetworks:
                    _dvs = _objNetworks[_key]['id']
                    self._printObject(_dvs.config.defaultPortConfig.vlan)



        return _vmNic

    def _getVmObjects(self, names=None, match=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = self._toList(names)
        _match = match
        _objVms = self._getObjects('vm', _names, match=_match)

        # apply filters
        _consolidate = getattr(self._args, 'consolidate') if hasattr(self._args, 'consolidate') else None
        _power = getattr(self._args, 'power') if hasattr(self._args, 'power') else None
        _snapshot = getattr(self._args, 'snapshot') if hasattr(self._args, 'snapshot') else None
        _template = getattr(self._args, 'template') if hasattr(self._args, 'template') else None
        _host = getattr(self._args, 'host') if hasattr(self._args, 'host') else None
        _cluster = getattr(self._args, 'cluster') if hasattr(self._args, 'cluster') else None
        _vmx = getattr(self._args, 'hw-version') if hasattr(self._args, 'hw-version') else None
        if _vmx is not None:
            _vmx = 'vmx-{:02d}'.format(_vmx)

        #
        # if template is not specifically specified,
        # get only vm
        #
        if _template is None:
            _template = False

        _vms = {}
        for _key in _objVms:
            _os = getattr(self._args, 'os') if hasattr(self._args, 'os') else None
            if 'config.guestId' not in _objVms[_key]:
                continue

            if _os is not None and _os == 'linux' and 'win' in _objVms[_key]['config.guestId']:
                continue
            if _os is not None and _os == 'windows' and 'win' not in _objVms[_key]['config.guestId']:
                continue
            if _template is not None and _objVms[_key]['config.template'] != _template:
                continue

            if _vmx is not None and _vmx != _objVms[_key]['config.version']:
                continue

            if _snapshot is not None and _snapshot and not _objVms[_key]['rootSnapshot']:
                continue
            if _snapshot is not None and not _snapshot and _objVms[_key]['rootSnapshot']:
                continue

            if _consolidate is not None and _objVms[_key]['runtime.consolidationNeeded'] != _consolidate:
                continue
            if _power is not None and _power and _objVms[_key]['runtime.powerState'] == vim.VirtualMachinePowerState.poweredOff:
                continue
            if _power is not None and not _power and _objVms[_key]['runtime.powerState'] == vim.VirtualMachinePowerState.poweredOn:
                continue

            if _cluster is not None and _cluster.lower() not in _objVms[_key]['id'].runtime.host.parent.name.lower():
                continue

            try:
                if _host is not None and _host.lower() not in _objVms[_key]['id'].runtime.host.name.lower():
                    continue
            except:
                continue

            _vms[_key] = _objVms[_key]
        _objVms = _vms

        return _objVms

    def _waitOnTask(self, task, title=None, wait=42):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _task = task
        _title = title
        _wait = getattr(self._args, 'wait') if hasattr(self._args, 'wait') else wait
        if _task is None:
            return None


        if _title is not None and _title != '':
            self._print(_title)
        self._print('Waiting {0} seconds for task to complete'.format(_wait), 1)
        import time
        for _i in range(_wait):
            self._print('[_task.info.state]  {0}'.format(_task.info.state), 3)
            if _task.info.state in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
                break
            time.sleep(1)

        #
        # check task result
        #
        _state = _task.info.state
        if _state == vim.TaskInfo.State.success:
            self._print('  Task completed successfully')
        elif _state == vim.TaskInfo.State.error:
            self._print('  Task failed --  {0}'.format(_task.info.error.msg))
            for _fault in _task.info.error.faultMessage:
                self._print('    {0}'.format(_fault.message), 1)
        elif _state == vim.TaskInfo.State.running:
            self._print('  Task running')
        else:
            self._print('  Task state:  {0}'.format(_state))

        return _state

    ## ---------- ---------- ---------- ----------
    #  Informational

    ## ---------- ---------- ---------- ----------
    # vcli.py info ...
    #
    def _info(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            self._displayVmInfo(_vm)

    def _displayVmInfo(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm

        #
        # display VM information
        #
        self._print('VM Information')

        #
        # general/summary information
        #
        self._print()
        self._print('General/Summary Information')
        _label = '# Template' if _vm.summary.config.template else '# VM'
        _hdr = (_label, 'IP_Address', 'Host', 'Cluster')
        _row = (_vm.name.lower(), _vm.summary.guest.ipAddress, _vm.runtime.host.name.split('.')[0].lower(), _vm.runtime.host.parent.name)
        _fmt = self._printRow(_hdr)
        self._printRow(_row, _fmt)

        self._print()
        _hdr = ('# Pwr', 'CPU', 'Memory', 'VM Vers', 'Tools Vers', 'Guest ID')
        _row = (_vm.summary.runtime.powerState.replace('powered', ''), _vm.summary.config.numCpu, '{0} GB'.format(_vm.summary.config.memorySizeMB / 1024), _vm.config.version, _vm.guest.toolsVersion, _vm.summary.config.guestId)
        _fmt = self._printRow(_hdr)
        self._printRow(_row, _fmt)

        if _vm.summary.config.annotation is not None and _vm.summary.config.annotation != '':
            self._print()
            self._print('Annotation\n{0}'.format(_vm.summary.config.annotation.replace(u'\u2019', u'\'').encode('ascii', 'ignore')))

        self._print()
        self._print('Snapshots:')
        _total = self._listVmSnapshot(_vm)
        self._print('# Total snapshots:  {0}'.format(_total))

        self._print()
        self._print('NICs:')
        self._listVmNic(_vm)

        self._print()
        self._print('Disks:')
        self._listVmDisk(_vm)

        self._print()
        self._print('Migration History:')
        _total = self._displayVmotionEvents(_vm)
        self._print('# Total:  {0}'.format(_total))

    def _displayVmotionEvents(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _byEntity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion='self')
        _ids = ['VmRelocatedEvent', 'DrsVmMigratedEvent', 'VmMigratedEvent']
        _filterSpec = vim.event.EventFilterSpec(entity=_byEntity, eventTypeId=_ids)

        # Optionally filter by users

        _eventManager = self._si.content.eventManager
        _events = _eventManager.QueryEvent(_filterSpec)

        if len(_events) == 0:
            return None

        _hdr = ('# Date/Time', 'From', 'To', 'Datastore', 'By')
        _fmt = self._printRow(_hdr)

        for _event in _events:
            _ts = str(_event.createdTime).split('.')[0]
            _fromHost = _event.sourceHost.name.split('.')[0]
            _toHost = _event.host.name.split('.')[0]
            if _fromHost == _toHost:
                _toHost = 'same'

            _fromDs = _event.sourceDatastore.name
            _toDs = _event.ds.name
            if _fromDs == _toDs:
                _ds = _fromDs
            else:
                _ds = '{0}s -> {1}'.format(_fromDs, _toDs)

            _by = _event.userName if _event.userName != '' else _event._wsdlName

            _row = (_ts, _fromHost, _toHost, _ds, _by)
            self._printRow(_row, _fmt)

        return len(_events)

    ## ---------- ---------- ---------- ----------
    # vcli.py list ...
    #
    def _list(self, obj, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        _object = obj
        if _object in ['category', 'cat']:
            self._listCategory(_names)
        elif _object in ['cluster', 'clu']:
            self._listCluster(_names)
        elif _object in ['datacenter', 'dc']:
            self._listDatacenter(_names)
        elif _object in ['datastore', 'ds']:
            self._listDatastore(_names)
        elif _object in ['host']:
            self._listHost(_names)
        elif _object in ['network', 'net', 'nw']:
            self._listNetwork(_names)
        elif _object in ['resource-pool', 'respool', 'rp']:
            self._listResourcePool(_names)
        elif _object in ['tag']:
            self._listTag(_names)
        elif _object in ['template', 'temp', 'tmpl']:
            self._listTemplate(_names)
        elif _object in ['virtual-machine', 'vm']:
            self._listVirtualMachine(_names)

        elif _object in ['vm-disk', 'disk']:
            self._listVmResource('disk', _names)
        elif _object in ['vm-nic', 'nic']:
            self._listVmResource('nic', _names)
        elif _object in ['vm-snapshot', 'vm-snap', 'snapshot', 'snap']:
            self._listVmResource('snapshot', _names)

        elif _object in ['vm-tag']:
            self._listVmTag(_names)

    ## ---------- ---------- ---------- ----------
    #  vcli.py list ...
    #
    def _listCluster(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _hdr = ('# Cluster', 'Skts', 'Cores', 'CPUs', 'Used', 'Usage', 'Memory', 'Used', 'Usage', 'Hosts')
        _fmt = self._printRow(_hdr)

        _objClusters = self._getObjects('cluster', _names)
        for _key in _objClusters:
            _cluster = _objClusters[_key]['id']

            # get cluster info
            _cores = 0
            _cpus = 0
            _sockets = 0
            _cpuUsage = 0
            _memMb = 0
            _memUsage = 0
            _cpuAssigned = 0
            _memAssigned = 0

            _hosts = []
            for _host in _cluster.host:
                #
                # get VM cpu/memory allocation
                #
                _vmCpus = 0
                _vmMems = 0
                for _vm in _host.vm:
                    if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                        _cpu = _vm.summary.config.numCpu
                        _mem = _vm.summary.config.memorySizeMB
                        if _mem is not None:
                            _mem = int(_mem) / 1024
                        _vmCpus += _cpu
                        _vmMems += _mem

                _cpuAssigned += _vmCpus
                _memAssigned += _vmMems
                _cores += _host.summary.hardware.numCpuCores
                _sockets += _host.summary.hardware.numCpuPkgs
                _cpus += _host.summary.hardware.numCpuThreads

                _memMb += _host.summary.hardware.memorySize / 1024 / 1024 / 1024
                _hosts.append(_host.name.split('.')[0].upper())

            _cpuUsage = str(round(100 * _cpuAssigned / _cpus, 0)) + '%'
            _memUsage = str(round(100 * _memAssigned / _memMb, 0)) + '%'

            _row = (_cluster.name, _sockets, _cores, _cpus, _cpuAssigned, _cpuUsage, _memMb, _memAssigned, _memUsage, '{count:2}  {hosts}'.format(count=len(_hosts), hosts=_hosts))
            self._printRow(_row, _fmt)

        self._print('# Total:  {0}'.format(len(_objClusters)))

    def _listCategory(self, name=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None
        _atype = getattr(self._args, 'associable-type') if hasattr(self._args, 'associable-type') else None
        if _atype is not None:
            if _atype == 'vm':
                _atype = 'VirtualMachine'
            elif _atype == 'host':
                _atype = 'HostSystem'
            elif _atype == 'folder':
                _atype = 'Folder'

        _stubConfig = self._loginInventoryService()
        _catService = Category(_stubConfig)
        _tagService = Tag(_stubConfig)

        _categories = _catService.list()
        if len(_categories) == 0:
            self._print('No Tag Category Found...')
            return 0

        _hdr = ('# Category', 'Cardinality', 'Associable_Types', 'Tags', 'Description')
        _fmt = self._printRow(_hdr)

        _cnt = 0
        for _category in _categories:
            _objCat = _catService.get(_category)

            #
            # filter name?
            #
            if name is not None and name.lower() not in _objCat.name.lower():
                continue

            #
            # filter associable type?
            #
            if _atype is not None and _atype != 'all' and _atype not in _objCat.associable_types:
                continue

            _tagIds = _tagService.list_tags_for_category(_category)
            _tags = len(_tagIds)
            if _long is not None and _long and len(_tagIds) > 0:
                _tags = []
                for _tagId in _tagIds:
                    _tags.append(_tagService.get(_tagId).name)
                _tags.sort()

            _row = (_objCat.name, _objCat.cardinality, list(_objCat.associable_types), _tags, _objCat.description)
            self._printRow(_row, _fmt)

            _cnt += 1
        self._print('# Total:  {0}'.format(_cnt))

    def _listDatacenter(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _hdr = ('# Datacenter', '')
        _fmt = self._printRow(_hdr)
        _objDcs = self._getObjects('datacenter', _names)
        for _key in _objDcs:
            _datacenter = _objDcs[_key]['id']
            _row = (_datacenter.name, '')
            self._printRow(_row, _fmt)
        self._print('# Total:  {0}'.format(len(_objDcs)))

    def _listDatastore(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None

        _hdr = ('# Datastore', 'Size', 'Free', 'Usage', 'VM')
        _fmt = self._printRow(_hdr)
        _objDss = self._getObjects('datastore', _names)
        for _key in _objDss:
            _datastore = _objDss[_key]['id']

            #
            # get all VM using this datastyore
            #
            _capacity = _datastore.summary.capacity / 1024 / 1024 / 1024
            _freeSpace = _datastore.summary.freeSpace / 1024 / 1024 / 1024
            _usage = 100 - int(100 * _datastore.summary.freeSpace / _datastore.summary.capacity)
            if _long is not None and _long:
                _vms = []
                for _vm in _datastore.vm:
                    _vms.append(_vm.name)
                _vms = '{0}  {1}'.format(len(_vms), _vms)
            else:
                _vms = len(_datastore.vm)

            _row = (_datastore.name, _capacity, _freeSpace, _usage, _vms)
            self._printRow(_row, _fmt)
        self._print('# Total:  {0}'.format(len(_objDss)))

    def _listHost(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None
        if _long is None or not _long:
            # brief format
            _hdr = ('# Host', 'Skts', 'Cores', 'CPUs', 'vCPUs', 'Memory', 'Cluster', 'VM')
        else:
            # Detailed format
            _hdr = ('# Host', 'Skts', 'Cores', 'CPUs', 'vCPUs', 'Memory', 'Maint', 'Pwr_Pol', 'Version', 'Build', 'Model', 'Processor_Type', 'Cluster', 'VM')
        _fmt = self._printRow(_hdr)

        #
        # filter the hosts by namd and cluster
        #
        _objHosts = self._getObjects('host', _names)
        _hosts = {}
        _cluster = getattr(self._args, 'cluster') if hasattr(self._args, 'cluster') else None
        for _key in _objHosts:
            _host = _objHosts[_key]['id']
            if _cluster is not None and _cluster.lower() not in _host.parent.name.lower():
                continue
            _hosts[_key] = _objHosts[_key]

        #
        # display found hosts
        #
        for _key in _hosts:
            _host = _hosts[_key]['id']

            # get host info
            _name = _host.name.split('.')[0].upper()
            _cluster = _host.parent.name
            _sockets = _host.summary.hardware.numCpuPkgs
            _cpus = _host.summary.hardware.numCpuCores
            _vcpus = _host.summary.hardware.numCpuThreads
            _cores = _cpus / _sockets
            _mem = _host.summary.hardware.memorySize / 1024 / 1024 / 1024

            if _long is not None and _long:
                _vms = []
                for _vm in _host.vm:
                    _vms.append(_vm.name)
                _vms = '{count}  {vms}'.format(count=len(_vms), vms=_vms)
            else:
                _vms = len(_host.vm)

            if _long is None or not _long:
                _row = (_name, _sockets, _cores, _cpus, _vcpus, _mem, _cluster, _vms)
            else:
                _model = '{0} {1}'.format(_host.summary.hardware.vendor, _host.summary.hardware.model)
                _cpuType = _host.summary.hardware.cpuModel
                _powerPolicy = _host.config.powerSystemInfo.currentPolicy.shortName
                _maintenance = _host.runtime.inMaintenanceMode
                _version = _host.summary.config.product.version
                _build = _host.summary.config.product.build
                _row = (_name, _sockets, _cores, _cpus, _vcpus, _mem, _maintenance, _powerPolicy, _version, _build, _model, _cpuType, _cluster, _vms)
            self._printRow(_row, _fmt)

        self._print('# Total:  {0}'.format(len(_hosts)))

    def _listNetwork(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _os = getattr(self._args, 'os') if hasattr(self._args, 'os') else None
        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None

        _hdr = ('# Network', 'VLAN', 'VM', 'Hosts')
        if _long is not None and _long:
            _hdr = _hdr + ('VM', 'Hosts')
        _fmt = self._printRow(_hdr)
        _objNetworks = self._getNetworkObjects(_names)
        for _key in _objNetworks:
            _dvs = _objNetworks[_key]['id']
            _row = (_dvs.name, _dvs.config.defaultPortConfig.vlan.vlanId, len(_dvs.vm), len(_dvs.host))
            if _long is None or not _long:
                self._printRow(_row, _fmt)
                continue

            #
            # Detail display, show VM & hosts
            #
            # clusters
            _vms = []
            for _vm in _dvs.vm:
                if _os is not None and _os == 'linux' and 'win' in _vm.config.guestId:
                    continue
                if _os is not None and _os == 'windows' and 'win' not in _vm.config.guestId:
                    continue
                _vms.append(_vm.name)
            _row = _row + (_vms,)

            # hosts
            _hosts = []
            for _host in _dvs.host:
                _hosts.append(_host.name.split('.')[0])
            _row = _row + (_hosts,)

            self._printRow(_row, _fmt)
        self._print('# Total:  {0}'.format(len(_objNetworks)))

    def _listResourcePool(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None

        _hdr = ('# Res_Pool', 'Owner', 'Process', 'Alloc', 'Limit', 'Reservation', 'Memory', 'shares', 'Limit', 'Reservation', 'VM')
        _fmt = self._printRow(_hdr)

        _objResourcePools = self._getObjects('rp', _names)
        for _key in _objResourcePools:
            _rp = _objResourcePools[_key]['id']

            _cpuLevel = _rp.config.cpuAllocation.shares.level
            _cpuShare = _rp.config.cpuAllocation.shares.shares / 100
            _cpuLimit = _rp.config.cpuAllocation.limit
            _cpuRes = _rp.config.cpuAllocation.reservation

            _memLevel = _rp.config.memoryAllocation.shares.level
            _memShare = _rp.config.memoryAllocation.shares.shares
            _memLimit = _rp.config.memoryAllocation.limit
            _memRes = _rp.config.memoryAllocation.reservation

            _vms = len(_rp.vm)
            if _long is not None and _long:
                _vms = []
                for _vm in _rp.vm:
                    _vms.append(_vm.name)
                _vms = '{len}  {vms}'.format(len=len(_vms), vms=_vms)
            _row = (_rp.name, _rp.owner.name,
                    _cpuLevel, _cpuShare, _cpuLimit, _cpuRes,
                    _memLevel, _memShare, _memLimit, _memRes,
                    _vms)
            self._printRow(_row, _fmt)

    def _listTag(self, name=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None
        _category = getattr(self._args, 'category') if hasattr(self._args, 'category') else None
        _atype = getattr(self._args, 'associable-type') if hasattr(self._args, 'associable-type') else None
        if _atype is not None:
            if _atype == 'vm':
                _atype = 'VirtualMachine'
            elif _atype == 'host':
                _atype = 'HostSystem'
            elif _atype == 'folder':
                _atype = 'Folder'

        _stubConfig = self._loginInventoryService()
        _catService = Category(_stubConfig)
        _tagService = Tag(_stubConfig)
        _tagAssociation = TagAssociation(_stubConfig)

        _tags = _tagService.list()
        if len(_tags) == 0:
            self._print('No Tag Found...')
            return 0

        _hdr = ('# Tag', 'Cardinality', 'Category', 'Description', 'Attached_To')
        _fmt = self._printRow(_hdr)
        _cnt = 0
        for _tag in _tags:
            _objTag = _tagService.get(_tag)

            #
            # filter tag name
            #
            if name is not None and name.lower() not in _objTag.name.lower():
                continue

            #
            # filter category name
            #
            _objCat = _catService.get(_objTag.category_id)
            if _category is not None and _category.lower() not in _objCat.name.lower() and _objCat.name.lower() not in _category.lower():
                continue

            #
            # filter category associable type?
            #
            if _atype is not None and _atype != 'all' and _atype not in _objCat.associable_types:
                continue

            _associations = _tagAssociation.list_attached_objects(_tag)
            _values = len(_associations)
            if _long is not None and _long and len(_associations) > 0:
                _atype = None
                _moIds = []
                _association = None
                for _association in _associations:
                    _moIds.append(_association.id)
                if _association is not None:
                    _atype = _association.type

                _values = []
                _objs = self._getObjects(_atype, _moIds)
                for _key in _objs:
                    _values.append(_objs[_key]['id'].name)
                _values.sort()

            _row = (_objTag.name, _objCat.cardinality, _objCat.name, _objTag.description, _values)
            self._printRow(_row, _fmt)

            _cnt += 1
        self._print('# Total:  {0}'.format(_cnt))

    def _listTemplate(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        self._args.template = True
        self._listVirtualMachine(names)

    def _listVirtualMachine(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _template = getattr(self._args, 'template') if hasattr(self._args, 'template') else None
        _label = '# Template' if _template is not None and _template else '# VM'

        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None
        if _long is None or not _long:
            _hdr = (_label, 'Pwr', 'CPU', 'Mem', 'Disks', 'Snap', 'Con', 'Description')
        else:
            _hdr = (_label, 'Pwr', 'CPU', 'Mem', 'Disks', 'Snap', 'Con', 'VM_Ver', 'Tools_Ver', 'Guest_ID', 'Host', 'Cluster', 'Description')
        _fmt = self._printRow(_hdr)

        _i = 0
        _max = getattr(self._args, 'max') if hasattr(self._args, 'max') else None
        _objVms = self._getVmObjects(_names, match=None)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            _row = self._getListVmRow(_vm)
            if _row is None:
                continue

            self._printRow(_row, _fmt)

            _i += 1
            if _max is not None and _i >= _max:
                break

        self._print('# Total:  {0}'.format(_i))


    def _listVmResource(self, resource, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _resource = resource
        _names = names

        _header = True
        _total = 0
        _showName = True
        _objVms = self._getVmObjects(_names, match=None)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            if _resource in ['disk', 'vm-disk']:
                _diskId = getattr(self._args, 'disk-id') if hasattr(self._args, 'disk-id') else None
                _cnt = self._listVmDisk(_vm, _header, _showName, _diskId)
            elif _resource in ['nic', 'vm-nic']:
                _nicId = getattr(self._args, 'nic-id') if hasattr(self._args, 'nic-id') else None
                _cnt = self._listVmNic(_vm, _header, _showName, _nicId)
            elif _resource in ['snapshot', 'snap', 'vm-snapshot', 'vm-snap']:
                self._args.snapshot = True
                _cnt = self._listVmSnapshot(_vm, _header, _showName)
            _header = False
            if _cnt is not None and _cnt > 0:
                _total += 1
        self._print('# Total VMs:  {0}'.format(_total))

    def _listVmDisk(self, vm, header=True, showName=False, disk=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _header = header
        _showName = showName
        _disk = disk

        #
        # Disk information
        #
        if _header is not None and _header:
            _hdr = ('A', 'I', 'Size', 'Type', 'Mode', 'Share', 'UUID', 'Disk')
            if _showName is not None and _showName:
                _hdr = ('# VM', 'HD', ) + _hdr
            else:
                _hdr = ('# HD', ) + _hdr
            _fmt = self._printRow(_hdr)
        else:
            if _showName is not None and _showName:
                _fmt = '%-12s  %2s  %s:%-2s  %4s  %-5s  %5s  %5s  %-12s  %s'
            else:
                _fmt = '%-4s  %s:%-2s  %4s  %-5s  %5s  %5s  %-12s  %s'

        _total = 0
        for _hw in _vm.config.hardware.device:
            if not isinstance(_hw, vim.vm.device.VirtualDisk):
                continue
            if _disk is not None and _disk != int(_hw.deviceInfo.label.replace('Hard disk', '')):
                continue

            self._print('_hw.backing.diskMode:  {0}'.format(_hw.backing.diskMode), 1)
            self._print('vim.vm.device.VirtualDisk:  {0}'.format(_hw), 2)

            _mode = _hw.backing.diskMode
            if _mode == 'persistent':
                _mode = 'p'
            elif _mode == 'independent_persistent':
                _mode = 'ip'

            if _hw.backing.sharing is not None:
                _share = _hw.backing.sharing.replace('sharing', '')
            else:
                _share = ''
            if _share == 'MultiWriter':
                _share = 'Yes'

            _type = 'thin' if _hw.backing.thinProvisioned else 'thick'

            _row = (int(_hw.deviceInfo.label.replace('Hard disk', '')),
                    _hw.controllerKey - 1000, _hw.unitNumber,
                    _hw.capacityInKB / 1024 / 1024, _type,
                    _mode, _share, _hw.backing.uuid.split('-')[4],
                    _hw.backing.fileName)
            if _showName:
                _row = (_vm.name, ) + _row
            self._printRow(_row, _fmt)
            _total += 1

        return _total

    def _listVmNic(self, vm, header=True, showName=False, nic=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _header = header
        _showName = showName
        _nic = nic

        if _header is not None and _header:
            _hdr = ('NIC_Type', 'IP_Address', 'VLAN', 'Network', 'MAC_Address')
            if _showName is not None and _showName:
                _hdr = ('# VM', 'Nic', ) + _hdr
            else:
                _hdr = ('# Nic', ) + _hdr
            _fmt = self._printRow(_hdr)
        else:
            if _showName is not None and _showName:
                _fmt = '%-14s  %3s  %-7s  %-13s  %4s  %-16s  %s'
            else:
                _fmt = '%-5s  %-7s  %-13s  %4s  %-16s  %s'

        _pgKey = None
        _nicId = None
        if _nic is not None:
            if _nic < 10:
                _nicId = 'Network adapter {0}'.format(_nic)
            else:
                _dvsObjects = self._getObjects('dvs')
                for _key in _dvsObjects:
                    _dvs = _dvsObjects[_key]['id']
                    _vlanId = _dvs.config.defaultPortConfig.vlan.vlanId
                    if isinstance(_vlanId, int) and _vlanId == nic:
                        _pgKey = _dvs.key
                        break

        _ipv6 = getattr(self._args, 'ipv6') if hasattr(self._args, 'ipv6') else None
        _total = 0
        for _hw in _vm.config.hardware.device:
            if not isinstance(_hw, vim.vm.device.VirtualEthernetCard):
                continue
            if _nicId is not None and _nicId != _hw.deviceInfo.label:
                continue
            if _pgKey is not None and _hw.backing.port.portgroupKey != _pgKey:
                continue

            _ipAddress = None
            _vlanId = None
            _network = None
            for _net in _vm.guest.net:
                if _net.deviceConfigId != _hw.key or not hasattr(_net.ipConfig, 'ipAddress'):
                    continue
                _ipAddress = []
                for _addr in _net.ipConfig.ipAddress:
                    if (_ipv6 is None or not _ipv6) and ':' in _addr.ipAddress:
                        continue
                    _ipAddress.append('{0}/{1}'.format(_addr.ipAddress, _addr.prefixLength))
                _ipAddress = ', '.join(_ipAddress)
                _network = _net.network

            if _network is None and hasattr(_hw.backing, 'port'):
                _dvsObjects = self._getObjects('dvs')
                for _key in _dvsObjects:
                    _dvs = _dvsObjects[_key]['id']
                    if _dvs.key == _hw.backing.port.portgroupKey:
                        _network = _dvs.name
                        _vlanId = _dvs.config.defaultPortConfig.vlan.vlanId
                        break

            _row = (_hw.deviceInfo.label.replace('Network adapter', ''),
                    type(_hw).__name__.split('.')[3].replace('Virtual', ''),
                    _ipAddress, _vlanId, _network, _hw.macAddress)
            if _showName is not None and _showName:
                _row = (_vm.name, ) + _row
            self._printRow(_row, _fmt)
            _total += 1

        return _total

    def _listVmSnapshot(self, vm, header=True, showName=False):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _header = header
        _showName = showName

        if _header is not None and _header:
            _hdr = ('Created', 'By', 'Description')
            if _showName is not None and _showName:
                _hdr = ('# VM', 'Id', ) + _hdr
            else:
                _hdr = ('# Id', ) + _hdr
            _fmt = self._printRow(_hdr)
        else:
            if _showName is not None and _showName:
                _fmt = '%-12s  %3s  %-19s  %-22s  %s'
            else:
                _fmt = '%-4s  %-19s  %-22s  %s'

        if not _vm.rootSnapshot:
            return None

        _total = 0
        _ss = _vm.snapshot.rootSnapshotList[0]
        while True:
            _row = (_ss.id, str(_ss.createTime).split('.')[0], _ss.name, _ss.description)
            if _showName is not None and _showName:
                _row = (_vm.name, ) + _row
            self._printRow(_row, _fmt)
            _total += 1
            if len(_ss.childSnapshotList) == 0:
                break
            _ss = _ss.childSnapshotList[0]

        return _total

    ## ---------- ---------- ---------- ----------
    #  vcli.py list vm-tag ...
    #
    def _listVmTag(self, names=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _category = getattr(self._args, 'category') if hasattr(self._args, 'category') else None
        _tag = getattr(self._args, 'tag') if hasattr(self._args, 'tag') else None
        _long = getattr(self._args, 'long') if hasattr(self._args, 'long') else None

        _stubConfig = self._loginInventoryService()
        _catService = Category(_stubConfig)
        _tagService = Tag(_stubConfig)
        _tagAssociation = TagAssociation(_stubConfig)

        _objVms = self._getVmObjects(_names, match=True)

        #
        # Display VM
        #
        _cnt = 0
        if _long is not None and _long:
            _hdr = ('# VM', 'Tag', 'Cardinality', 'Category', 'Description')
        else:
            _hdr = ('# VM', 'Tags')
        _fmt = self._printRow(_hdr)

        for _key in _objVms:
            _vm = _objVms[_key]['id']

            _dynamicId = DynamicID(type='VirtualMachine', id=_vm._moId)
            _tagIds = _tagAssociation.list_attached_tags(_dynamicId)

            if _long is not None and _long:
                for _tagId in _tagIds:
                    _objTag = _tagService.get(_tagId)
                    if _tag is not None and _tag.lower() not in _objTag.name.lower():
                        continue

                    _objCat = _catService.get(_objTag.category_id)
                    if _category is not None and _category.lower() not in _objCat.name.lower():
                        continue

                    _row = (_vm.name, _objTag.name, _objCat.cardinality, _objCat.name, _objTag.description)
                    self._printRow(_row, _fmt)

                    _cnt += 1

            else:
                _tags = []
                for _tagId in _tagIds:
                    _tags.append(_tagService.get(_tagId).name)
                _tags.sort()

                _row = (_vm.name, _tags)
                self._printRow(_row, _fmt)
                _cnt += 1

        self._print('# Total:  {0}'.format(_cnt))

    ## ---------- ---------- ---------- ----------
    #  Common Actions

    ## ---------- ---------- ---------- ----------
    #  functions to support
    #    vcli.py add cpu,memory ...
    #    vcli.py remove cpu,memory ...
    #    vcli.py change --cpu,--memory ...
    #
    def _modifyCompute(self, vm, action, cpu=None, memory=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _action = action
        _cpu = getattr(self._args, 'cpu') if hasattr(self._args, 'cpu') else cpu
        _memory = getattr(self._args, 'memory') if hasattr(self._args, 'memory') else memory

        if _cpu is None and _memory is None:
            return None

        #
        # get current cpu/memory value
        #
        _cpuCurrent = int(_vm.summary.config.numCpu)
        _memCurrent = float(_vm.summary.config.memorySizeMB)

        #
        # determine cpu/memory changes
        #
        _cpuDelta = int(_cpu) if _cpu is not None else int(0)
        _memDelta = float(_memory * 1024) if _memory is not None else float(0)

        if _action in ['set']:
            _cpuNew = _cpuDelta if _cpuDelta is not None and _cpuDelta > 0 else _cpuCurrent
            _memNew = _memDelta if _memDelta is not None and _memDelta > 0 else _memCurrent
        elif _action in ['add']:
            _cpuNew = _cpuCurrent + _cpuDelta
            _memNew = _memCurrent + _memDelta
        elif _action in ['delete', 'del', 'remove', 'rm']:
            _cpuNew = _cpuCurrent - _cpuDelta if _cpuCurrent > _cpuDelta else _cpuDelta
            _memNew = _memCurrent - _memDelta if _memCurrent > _memDelta else _memDelta

        #
        # compute resource can only be reduced when VM is off
        #
        if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            if _cpuNew < _vm.summary.config.numCpu:
                self._print('Cannot reduce CPU from {0} to {1} while VM is powered on.'.format(_vm.summary.config.numCpu, _cpu))
                return None
            if _memNew < float(_vm.summary.config.memorySizeMB):
                self._print('Cannot reduce CPU from {0} to {1} while VM is powered on.'.format(_vm.summary.config.memorySizeMB, _memory))
                return None
        if _cpuCurrent == _cpuNew and _memCurrent == _memNew:
            self._print('No CPU or Memory change requested.')
            return None

        self._print('Changing compute resources')
        self._print('  CPU:  {0} -> {1}'.format(_cpuCurrent, _cpuNew))
        self._print('  Memory:  {0} -> {1}'.format(_memCurrent, _memNew))

        # VM config spec
        _spec = vim.vm.ConfigSpec()
        _spec.numCPUs = int(_cpuNew)
        _spec.memoryMB = int(_memNew)
        _spec.cpuHotAddEnabled = True
        _spec.memoryHotAddEnabled = True
        _task = _vm.Reconfigure(_spec)
        _state = self._waitOnTask(_task)

        return _state

    ## ---------- ---------- ---------- ----------
    #  vcli.py add ...
    def _add(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        # Compute resource
        _cpu = getattr(self._args, 'cpu') if hasattr(self._args, 'cpu') else None
        _memory = getattr(self._args, 'memory') if hasattr(self._args, 'memory') else None

        # Storage
        _storageSize = getattr(self._args, 'storage-size') if hasattr(self._args, 'storage-size') else None
        _newDisk = getattr(self._args, 'new-disk') if hasattr(self._args, 'new-disk') else None

        # NIC
        _network = getattr(self._args, 'network') if hasattr(self._args, 'network') else None
        _vlanId = getattr(self._args, 'vlan-id') if hasattr(self._args, 'vlan-id') else None

        # Tag
        _tag = getattr(self._args, 'tag') if hasattr(self._args, 'tag') else None

        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']

            if _cpu is not None or _memory is not None:
                _action = 'add'
                self._modifyCompute(_vm, _action)

            if _storageSize is not None and _storageSize > 0:
                if _newDisk is not None and _newDisk:
                    self._addVmDisk(_vm)
                else:
                    self._addVmStorage(_vm)

            if _network is not None or _vlanId is not None:
                self._addVmNic(_vm)

        if _tag is not None:
            self._addVmTag(_tag, _names)

    def _addVmDisk(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _diskSize = getattr(self._args, 'storage-size') if hasattr(self._args, 'storage-size') else 0

        _bus = getattr(self._args, 'controller') if hasattr(self._args, 'controller') else 0
        _independent = getattr(self._args, 'independent') if hasattr(self._args, 'independent') else False
        _thick = getattr(self._args, 'thick') if hasattr(self._args, 'thick') else False
        _mode = 'independent_persistent' if _independent is not None and _independent else 'persistent'

        _thin = not _thick
        _eager = _independent

        # get all disks on a VM, set _unitNumber to the next available
        _controller = None
        for _dev in _vm.config.hardware.device:
            if isinstance(_dev, vim.vm.device.VirtualDisk) and hasattr(_dev.backing, 'fileName'):
                self._print('[vim.vm.device.VirtualDisk]  {0}'.format(_dev), 2)
                self._print('[_dev.unitNumber]  {0}'.format(_dev.unitNumber), 1)
                self._print('[_dev.backing.fileName]  {0}'.format(_dev.backing.fileName), 1)

                _unitNumber = int(_dev.unitNumber) + 1
                # _unitNumber 7 reserved for scsi controller
                if _unitNumber == 7:
                    _unitNumber += 1
                elif _unitNumber >= 16:
                    self._print('The tool currently only supports adding disk to the first SCSI controller.')
                    return None
            if isinstance(_dev, vim.vm.device.VirtualSCSIController) and _dev.busNumber == _bus:
                _controller = _dev

        if _controller is None:
            self._print('Cannot find controller {0}'.format(_bus))
            return None

        # add disk here
        _devChanges = []
        _sizeKb = int(_diskSize) * 1024 * 1024
        _diskSpec = vim.vm.device.VirtualDeviceSpec()
        _diskSpec.fileOperation = 'create'
        _diskSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        _diskSpec.device = vim.vm.device.VirtualDisk()
        _diskSpec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()

        _diskSpec.device.backing.thinProvisioned = _thin
        _diskSpec.device.backing.diskMode = _mode
        _diskSpec.device.backing.eagerlyScrub = _eager

        _diskSpec.device.unitNumber = _unitNumber
        _diskSpec.device.capacityInKB = _sizeKb
        _diskSpec.device.controllerKey = _controller.key
        _devChanges.append(_diskSpec)
        self._print('[_diskSpec]  {0}'.format(_diskSpec), 1)

        _configSpec = vim.vm.ConfigSpec()
        _configSpec.deviceChange = _devChanges

        _title = 'Adding {0} GB disk to {1}'.format(_diskSize, _vm.name)
        _task = _vm.Reconfigure(_configSpec)
        _state = self._waitOnTask(_task, title=_title)
        if _state == vim.TaskInfo.State.success:
            # return controller & disk ID
            _state = '{0}:{1}'.format(_controller.busNumber, _unitNumber)

        return _state

    def _addVmNic(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _network = getattr(self._args, 'network') if hasattr(self._args, 'network') else None


        #
        # try exact match first,
        # if not found broaden search
        #
        _objNetworks = self._getNetworkObjects(_network, match=True)
        if len(_objNetworks) == 0:
            self._print('Unable to find exact match for network {0}.  Retrying with substring search'.format(_network))
            _objNetworks = self._getNetworkObjects(_network, match=False)
        if len(_objNetworks) != 1:
            self._print('Ambiguous network name, found {0} networks matching name {1}.'.format(len(_objNetworks), _network))
            return None


        for _key in _objNetworks:
            _dvs = _objNetworks[_key]['id']

        _dvsConnection = vim.dvs.PortConnection()
        _dvsConnection.portgroupKey = _dvs.key
        _dvsConnection.switchUuid = _dvs.config.distributedVirtualSwitch.uuid

        _nicSpec = vim.vm.device.VirtualDeviceSpec()
        _nicSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        _nicSpec.device = vim.vm.device.VirtualVmxnet3()
        _nicSpec.device.deviceInfo = vim.Description()

        _nicSpec.device.backing = vim.vm.device.VirtualEthernetCard.DistributedVirtualPortBackingInfo()
        _nicSpec.device.backing.port = _dvsConnection

        _nicSpec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        _nicSpec.device.connectable.startConnected = True
        _nicSpec.device.connectable.allowGuestControl = True

        _nicSpec.device.connectable.connected = False
        _nicSpec.device.connectable.status = 'untried'
        _nicSpec.device.wakeOnLanEnabled = True
        _nicSpec.device.addressType = 'assigned'

        # add nic here
        _devChanges = []
        _devChanges.append(_nicSpec)
        self._print('[_nicSpec]  {0}'.format(_nicSpec), 2)

        _configSpec = vim.vm.ConfigSpec()
        _configSpec.deviceChange = _devChanges

        _title = 'Adding {0} network to {1}'.format(_dvs.name, _vm.name)
        _task = _vm.Reconfigure(_configSpec)
        _state = self._waitOnTask(_task, title=_title)

        return _state

    ## ---------- ---------- ---------- ----------
    #  vcli.py add -S ...
    #
    def _addVmStorage(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _size = getattr(self._args, 'storage-size') if hasattr(self._args, 'storage-size') else 0
        _diskId = getattr(self._args, 'disk-id') if hasattr(self._args, 'disk-id') else None
        _thick = getattr(self._args, 'thick') if hasattr(self._args, 'thick') else False

        if _size == 0:
            self._print('Disk capacity is the same. No change needed.')
            return None
        elif _size < 0:
            self._print('Reducing Virtual Hard Disk Size is not supported at this time.')
            return None

        _vmDisk = self._getVmDiskObject(_vm, _diskId)
        if _vmDisk is None:
            self._print('Error adding storage to disk -- Hard disk {0} not found!'.format(_diskId))
            return None

        if not _vmDisk.backing.thinProvisioned and not _thick:
            self._print('Cannot add storage to thick provisioned disk')
            return None

        _newSize = _vmDisk.capacityInKB / 1024 / 1024 + abs(_size)

        _diskSpec = vim.vm.device.VirtualDeviceSpec()
        _diskSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
        _diskSpec.device = vim.vm.device.VirtualDisk()
        _diskSpec.device.key = _vmDisk.key
        _diskSpec.device.backing = _vmDisk.backing
        _diskSpec.device.backing.fileName = _vmDisk.backing.fileName
        _diskSpec.device.backing.diskMode = _vmDisk.backing.diskMode
        _diskSpec.device.controllerKey = _vmDisk.controllerKey
        _diskSpec.device.unitNumber = _vmDisk.unitNumber
        _diskSpec.device.capacityInKB = long(_newSize) * 1024 * 1024

        _devChanges = []
        _devChanges.append(_diskSpec)
        _configSpec = vim.vm.ConfigSpec()
        _configSpec.deviceChange = _devChanges

        _title = 'Extending {device} to {newSize} GB.'.format(device=_vmDisk.deviceInfo.label, newSize=_newSize)
        _task = _vm.Reconfigure(_configSpec)
        _state = self._waitOnTask(_task, title=_title)

        return _state

    ## ---------- ---------- ---------- ----------
    # vcli.py add -T  ...
    #
    def _addVmTag(self, tags, names=None, category=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _tags = self._toList(tags)
        _names = self._toList(names)
        _category = getattr(self._args, 'category') if hasattr(self._args, 'category') and category is None else category

        _stubConfig = self._loginInventoryService()
        _catService = Category(_stubConfig)
        _tagService = Tag(_stubConfig)
        _tagAssociation = TagAssociation(_stubConfig)


        _objTags = {}
        _tagIds = _tagService.list()
        for _tagId in _tagIds:
            #
            # does tag name match?
            #
            _objTag = _tagService.get(_tagId)
            if _objTag.name.lower() not in _tags:
                continue

            #
            # if specified, does category name match?
            #
            _objCat = _catService.get(_objTag.category_id)
            _cat = _objCat.name
            if _category is not None and _category.lower() not in _cat.lower():
                continue

            #
            # unique index key is category.tag
            #
            _key = '{cat}.{tag}'.format(cat=_category, tag=_objTag.name) if _category is not None else _objTag.name
            if _key in _objTags:
                self._print('Error -- More than one {tag} tag found.  Please use -C (or --category) option to clarify tag.'.format(tag=_key))
                return 0

            _objTags[_key] = _objTag

        if len(_objTags) == 0:
            self._print('Tag {0} not found.'.format(tags))
            return 0

        _objVms = self._getVmObjects(_names, match=True)
        if len(_objVms) == 0:
            self._print('VM {0} not found.'.format(names))
            return 0

        for _keyVm in _objVms:
            _vm = _objVms[_keyVm]['id']
            for _keyTag in _objTags:
                _objTag = _objTags[_keyTag]
                _name = _objTag.name
                _dynamicId = DynamicID(type='VirtualMachine', id=_vm._moId)

                _objCat = _catService.get(_objTag.category_id)
                _cat = _objCat.name
                _card = _objCat.cardinality
                if _card.lower() == 'single':
                    _dynamicId0 = DynamicID(type='VirtualMachine', id=_vm._moId)
                    _tagId0s = _tagAssociation.list_attached_tags(_dynamicId0)
                    for _tagId0 in _tagId0s:
                        _objTag0 = _tagService.get(_tagId0)
                        _name0 = _objTag0.name

                        _objCat0 = _catService.get(_objTag0.category_id)
                        _cat0 = _objCat0.name
                        _card0 = _objCat0.cardinality
                        if _cat0 == _cat and _card0 == _card and _name0 != _name:
                            self._print('Applying the Highlander Rule -- there can only be one')
                            self._print('Removing current conflicting tag {tag} from {vm}'.format(tag=_name0, vm=_vm.name))
                            _tagAssociation.detach(tag_id=_objTag0.id, object_id=_dynamicId0)
                            break

                self._print('Adding tag {tag} to {vm}'.format(tag=_objTag.name, vm=_vm.name))
                _tagAssociation.attach(tag_id=_objTag.id, object_id=_dynamicId)

    ## ---------- ---------- ---------- ----------
    #  vcli.py backup ...
    #
    def _backup(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        self._clone(_names)

    ## ---------- ---------- ---------- ----------
    #  vcli.py change ...
    #
    def _change(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _newName = getattr(self._args, 'new-name') if hasattr(self._args, 'new-name') else None
        _append = getattr(self._args, 'append') if hasattr(self._args, 'append') else None
        _description = getattr(self._args, 'description') if hasattr(self._args, 'description') else None
        _cpu = getattr(self._args, 'cpu') if hasattr(self._args, 'cpu') else None
        _memory = getattr(self._args, 'memory') if hasattr(self._args, 'memory') else None
        _template = getattr(self._args, 'mark_as_template') if hasattr(self._args, 'mark_as_template') else None
        _hotadd = getattr(self._args, 'hot-add') if hasattr(self._args, 'hot-add') else None
        _upgradeHw = getattr(self._args, 'upgrade-hw') if hasattr(self._args, 'upgrade-hw') else None
        _vmx = getattr(self._args, 'hw-version') if hasattr(self._args, 'hw-version') else None
        _rp = getattr(self._args, 'resource-pool') if hasattr(self._args, 'resource-pool') else None

        # if upgrading h/w then also enable hot-add

        #
        # if converting to template, only retrive vm
        # if converting to vm, only retrive template
        #
        if _template is not None:
            self._args.template = not _template

        _names = names
        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            if _newName is not None:
                _title = 'Changing VM name to: {0}'.format(_newName)
                _task = _vm.Rename(_newName)
                _state = self._waitOnTask(_task, title=_title)

            if _append is not None:
                _newName = '{0}.{1}'.format(_vm.name, _append)
                _title = 'Changing Vm name from {oldName} to {newName}'.format(oldName=_vm.name, newName=_newName)
                _task = _vm.Rename(_newName)
                _state = self._waitOnTask(_task, title=_title)

            if _description is not None:
                _spec = vim.vm.ConfigSpec()
                _spec.annotation = _description
                _title = 'Changing VM description/annotation to: {0}'.format(_description)
                _task = _vm.Reconfigure(_spec)
                _state = self._waitOnTask(_task, title=_title)

            if _rp is not None:
                _rpObjects = self._getObjects('rp', _rp)
                if len(_rpObjects) == 1:
                    _rp = None
                    for _key in _rpObjects:
                        _rp = _rpObjects[_key]['id']
                    _relocateSpec = vim.vm.RelocateSpec(pool=_rp)

                    _title = 'Moving {vm} to resource pool {rp}'.format(vm=_vm.name, rp=_rp)
                    _task = _vm.Relocate(spec=_relocateSpec)
                    _state = self._waitOnTask(_task, title=_title)
                else:
                    self._print('Resource pool not found or ambiguous.')

            if _template is not None and _template:
                if not _vm.summary.config.template:
                    _title = 'Marking {0} as a template'.format(_vm.name)
                    _task = _vm.MarkAsTemplate()
                    _state = self._waitOnTask(_task, title=_title)
                else:
                    self._print('{0} is a template'.format(_vm.name))

            if _template is not None and not _template:
                if _vm.summary.config.template:
                    _host = _vm.runtime.host
                    _cluster = _vm.runtime.host.parent
                    _title = 'Marking {0} as a virtual machine (VM)'.format(_vm.name)
                    _task = _vm.MarkAsVirtualMachine(pool=_cluster.resourcePool, host=_host)
                    _state = self._waitOnTask(_task, title=_title)
                else:
                    self._print('{0} is a virtual machine'.format(_vm.name))

            if _cpu is not None or _memory is not None:
                _action = 'set'
                self._modifyCompute(_vm, _action)

            # If VM is powered on, skip the rest
            if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                if _hotadd is not None and _hotadd:
                    self._print('Cannot enable cpu/memory hot-add on {name} while it is powered on.'.format(name=_vm.name))
                if (_upgradeHw is not None and _upgradeHw) or _vmx is not None:
                    self._print('Cannot upgrade hardware on {name} while it is powered on.'.format(name=_vm.name))
                continue

            # VM must be powered off for these changes

            # Enable hot add feature for CPU & memory
            if _hotadd is not None and _hotadd:
                _spec = vim.vm.ConfigSpec()
                _spec.cpuHotAddEnabled = True
                _spec.memoryHotAddEnabled = True
                _title = 'Enabling hot add CPU and memory'
                _task = _vm.Reconfigure(_spec)
                _state = self._waitOnTask(_task, title=_title)

            if _upgradeHw is not None and _upgradeHw:
                _title = 'Upgrade VM hardware to latest supported version'
                _task = _vm.UpgradeVM_Task()
                _state = self._waitOnTask(_task, title=_title)

            if _vmx is not None:
                _title = 'Changing VM hardware to version vmx-{0}'.format(_vmx)
                _task = _vm.UpgradeVM_Task('vmx-{0}'.format(_vmx))
                _state = self._waitOnTask(_task, title=_title)

    ## ---------- ---------- ---------- ----------
    #  vcli.py clone ...
    #
    def _cloneVm(self, objSrcVm, name):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _objSrcVm = objSrcVm
        _name = name


        #
        # determine folder to put VM into
        #

        # use current folder
        _destFolder = _objSrcVm.parent
        self._print('[_destFolder]  {0}'.format(_destFolder.name), 1)

        #
        # determine cluster to put VM into
        #
        _clusterName = getattr(self._args, 'cluster') if hasattr(self._args, 'cluster') else None
        if _clusterName is not None:
            _objClusters = self._getObjects('cluster', _clusterName)
            if len(_objClusters) != 1:
                self._print('Error -- {0} clusters found.'.format(len(_objClusters)))
                return None
            for _key in _objClusters:
                _cluster = _objClusters[_key]['id']
        else:
            _cluster = _objSrcVm.runtime.host.parent

        self._print('--cluster {0}'.format(_clusterName), 2)
        self._print('Cluster:  {0}'.format(_cluster.name), 1)

        # This constructs the reloacate spec needed
        # in a later step by specifying the default
        # resource pool (_name=Resource) of the Cluster
        # Alternatively one can specify a custom resource pool inside of a Cluster
        _relocateSpec = vim.vm.RelocateSpec(pool=_cluster.resourcePool)

        #
        # get CPU & memory setting
        #
        _configSpec = None
        _cpu = getattr(self._args, 'cpu') if hasattr(self._args, 'cpu') else None
        _memory = getattr(self._args, 'memory') if hasattr(self._args, 'memory') else None
        if _cpu is not None or _memory is not None:
            if _cpu is None:
                _cpu = _objSrcVm.summary.config.numCpu
            if _memory is None:
                _memory = _objSrcVm.summary.config.memorySizeMB
            else:
                _memory = int(_memory) * 1024
            if _configSpec is None:
                _configSpec = vim.vm.ConfigSpec()
            _configSpec.numCPUs = _cpu
            _configSpec.memoryMB = _memory
            _configSpec.cpuHotAddEnabled = True
            _configSpec.memoryHotAddEnabled = True

        _description = getattr(self._args, 'description') if hasattr(self._args, 'description') else None
        if _description is not None:
            if _configSpec is None:
                _configSpec = vim.vm.ConfigSpec()
            _configSpec.annotation = _description

        #
        # create CloneSpec
        #
        _cloneSpec = vim.vm.CloneSpec(powerOn=False, template=False)
        _cloneSpec.location = _relocateSpec
        if _configSpec is not None:
            _cloneSpec.config = _configSpec

        # perform the clone task
        _title = 'Cloning {srcVm} to {newName}'.format(srcVm=_objSrcVm.name, newName=_name)
        _wait = 1200
        _task = _objSrcVm.Clone(folder=_destFolder, name=_name, spec=_cloneSpec)
        _state = self._waitOnTask(_task, title=_title, wait=_wait)
        self._print('[_task.info]  {0}'.format(_task.info), 2)

        return _state

    def _getVmTag(self, vm):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm

        _stubConfig = self._loginInventoryService()
        _catService = Category(_stubConfig)
        _tagService = Tag(_stubConfig)
        _tagAssociation = TagAssociation(_stubConfig)

        _dynamicId = DynamicID(type='VirtualMachine', id=_vm._moId)
        _tagIds = _tagAssociation.list_attached_tags(_dynamicId)
        _tags = []
        for _tagId in _tagIds:

            _objTag = _tagService.get(_tagId)
            _objCat = _catService.get(_objTag.category_id)
            _tag = _objTag.name
            _cat = _objCat.name
            _tags.append([_cat, _tag])

        return _tags

    ## ---------- ---------- ---------- ----------
    #  vcli.py clone -h
    def _clone(self, names, source=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        _source = getattr(self._args, 'source') if hasattr(self._args, 'source') else source

        _includeTag = getattr(self._args, 'include-tag') if hasattr(self._args, 'include-tag') else None

        _username = self._username
        _ts = self._ts

        #
        # Are we cloning a new VM or backing up existing?
        #
        if _source is not None:
            #
            # Cloning a new VM
            #
            _objSrcVms = self._getVmObjects(_source, match=True)
            if len(_objSrcVms) != 1:
                self._print('Error -- clone source {0} not found.'.format(_source))
                return None
            _objSrcVm = _objSrcVms[_source]['id']
            self._print('****  Cloning from source {0}  ****'.format(_objSrcVm.name))


        #
        # get list of current VMs with _names
        #
        _objVms = self._getVmObjects(_names, match=True)

        #
        # 1.  Clone VMs
        #
        _vmClones = []
        for _name in _names:
            #
            # if not cloning from a source,
            # then we're making a clone for backup purposes
            #
            if _source is None:
                #
                # Backing up existing VM
                #
                if _name not in _objVms:
                    self._print('Error -- Cannot backup {0}, VM not found.'.format(_name))
                    continue
                _objSrcVm = _objVms[_name]['id']
                _name = '{name}.cloned.by.{username}.{ts}'.format(name=_name, username=_username, ts=_ts)

            if _name in _objVms:
                self._print('Error -- cannot clone to {0}, VM exists.'.format(_name))
                continue

            _state = self._cloneVm(_objSrcVm, _name)
            if _state != vim.TaskInfo.State.success:
                continue

            #
            # Find VM and power it on
            #
            _objClonedVms = self._getVmObjects(_name, match=True)
            if len(_objClonedVms) != 1:
                self._print('Cloning Error -- Cannot find clone {0}'.format(_name))
                continue

            #
            # if source not given, then we're doing a backup
            # so do not power on
            #
            if _source is None:
                continue

            #
            # Cloned VM
            #
            _vm = _objClonedVms[_name]['id']

            #
            # post clone
            #
            if _includeTag is not None and _includeTag:
                _tags = self._getVmTag(_objSrcVm)
                self._print('Adding tags {tags} to cloned VM {vm}'.format(vm=_vm.name, tags=_tags))
                for _cat, _tag in _tags:
                    self._addVmTag(_tag, _vm.name, _cat)

            #
            # power on successfully cloned VM
            #
            _title = 'Powering on cloned VM {0}'.format(_vm.name)
            _task = _vm.PowerOn()
            _state = self._waitOnTask(_task, title=_title)

            _vmClones.append(_vm.name)
            self._print()
        self._print('[_vmClones]  {0}'.format(_vmClones), 2)

    ## ---------- ---------- ---------- ----------
    #  vcli.py delete ...
    #
    def _destroy(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']

            if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                self._print('Remove VM Failed -- {0} is powered on.'.format(_vm.name))
                return None

            _title = 'Destroying {0}'.format(_vm.name)
            _task = _vm.Destroy()
            _state = self._waitOnTask(_task, title=_title)


    ## ---------- ---------- ---------- ----------
    #  vcli.py migrate -h
    def _migrate(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        _toHost = getattr(self._args, 'to-host') if hasattr(self._args, 'to-host') else None
        _toDatastore = getattr(self._args, 'to-datastore') if hasattr(self._args, 'to-datastore') else None
        _thin = getattr(self._args, 'thin') if hasattr(self._args, 'thin') else None

        if _toDatastore is None and _toHost is None:
            self._print('Migration Error -- destination host and/or datastore required')
            return None


        _objHost = None
        _objDatastore = None

        if _toHost is not None:
            _objHosts = self._getObjects('host', _toHost, match=True)
            if len(_objHosts) != 1:
                self._print('Migration Error -- ambiguous host')
                return None
            for _key in _objHosts:
                _objHost = _objHosts[_key]['id']
            _pool = _objHost.parent.resourcePool
            _priority = vim.VirtualMachine.MovePriority.defaultPriority

        if _toDatastore is not None:
            _objDatastores = self._getObjects('datastore', _toDatastore, match=True)
            if len(_objDatastores) != 1:
                self._print('Migration Error -- ambiguous datastore')
                return None
            for _key in _objDatastores:
                _objDatastore = _objDatastores[_key]['id']

        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            self._print('Migrating {0}'.format(_vm.name))

            if _objHost is not None:
                _title = '  from host {0} to {1}'.format(_vm.runtime.host.name.split('.')[0], _objHost.name.split('.')[0])

                _task = _vm.Migrate(pool=_pool, host=_objHost, priority=_priority)
                _state = self._waitOnTask(_task, title=_title)

            if _objDatastore is not None:
                # Live Migration :: Change both host and datastore
                _relSpec = vim.vm.RelocateSpec()

                _pool = _vm.runtime.host.parent.resourcePool
                _relSpec.pool = _pool

                if _thin is not None and _thin:
                    for _dev in _vm.config.hardware.device:
                        if not hasattr(_dev.backing, 'fileName'):
                            continue

                        # Convert to thin provision
                        _disk = vim.vm.RelocateSpec.DiskLocator()
                        _disk.diskBackingInfo = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                        _disk.diskBackingInfo.thinProvisioned = True
                        _disk.datastore = _objDatastore
                        _disk.diskId = _dev.key
                        _relSpec.disk.append(_disk)
                        self._print('''[diskId]  {0}'''.format(_dev.key), 1)

                # Assuming Migrating between local datastores
                _relSpec.datastore = _objDatastore


                _title = '  to datastore {0}'.format(_objDatastore.name)
                _wait = 300
                _task = _vm.Relocate(spec=_relSpec)
                _state = self._waitOnTask(_task, title=_title, wait=_wait)

    ## ---------- ---------- ---------- ----------
    #  vcli.py remove ...
    #
    def _remove(self, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names

        # Compute resource
        _cpu = getattr(self._args, 'cpu') if hasattr(self._args, 'cpu') else None
        _memory = getattr(self._args, 'memory') if hasattr(self._args, 'memory') else None

        # Storage/Disk
        _diskId = getattr(self._args, 'disk-id') if hasattr(self._args, 'disk-id') else None

        # NIC
        _network = getattr(self._args, 'network') if hasattr(self._args, 'network') else None
        _vlanId = getattr(self._args, 'vlan-id') if hasattr(self._args, 'vlan-id') else None

        # Tag
        _tag = getattr(self._args, 'tag') if hasattr(self._args, 'tag') else None

        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']

            if _cpu is not None or _memory is not None:
                _action = 'delete'
                self._modifyCompute(_vm, _action)

            if _diskId is not None:
                _dtype = 'disk'
                self._removeDevice(_vm, _dtype, _diskId)

            if _network is not None or _vlanId is not None:
                _dtype = 'nic'
                self._removeDevice(_vm, _dtype, _network)

        if _tag is not None:
            self._removeVmTag(_tag, _names)

    ## ---------- ---------- ---------- ----------
    #  vcli.py remove -D ...
    #  vcli.py remove -N ...
    #
    def _removeDevice(self, vm, dtype, devId):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _vm = vm
        _dtype = dtype
        _devId = devId

        if _dtype == 'disk':
            _device = self._getVmDiskObject(_vm, _devId)
        elif _dtype == 'nic':
            _device = self._getVmNicObject(_vm, _devId)
        else:
            _device = None


        if _device is None:
            self._print('Error removing {dtype} from {vm} -- {dtype} {devId} not found!'.format(vm=_vm.name, dtype=_dtype, devId=_devId))
            return None


        _devSpec = vim.vm.device.VirtualDeviceSpec()
        _devSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        _devSpec.device = _device

        _configSpec = vim.vm.ConfigSpec()
        _configSpec.deviceChange = [_devSpec]
        _title = 'Removing {label} from {vm}.'.format(vm=_vm.name, label=_device.deviceInfo.label)
        _task = _vm.Reconfigure(_configSpec)
        _state = self._waitOnTask(_task, title=_title)

        return _state

    ## ---------- ---------- ---------- ----------
    #  vcli.py remove -T ...
    #
    def _removeVmTag(self, tags, names=None, category=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _category = getattr(self._args, 'category') if hasattr(self._args, 'category') and category is None else category

        _stubConfig = self._loginInventoryService()
        _catService = Category(_stubConfig)
        _tagService = Tag(_stubConfig)
        _tagAssociation = TagAssociation(_stubConfig)

        _tags = self._toList(tags)
        _names = self._toList(names)

        _objVms = self._getVmObjects(_names, match=True)
        if len(_objVms) == 0:
            self._print('VM {0} not found.'.format(names))
            return 0

        for _keyVm in _objVms:
            _vm = _objVms[_keyVm]['id']

            _objTags = {}

            _dynamicId = DynamicID(type='VirtualMachine', id=_vm._moId)
            _tagIds = _tagAssociation.list_attached_tags(_dynamicId)
            for _tagId in _tagIds:
                _objTag = _tagService.get(_tagId)
                if _objTag.name.lower() not in _tags:
                    continue

                _objCat = _catService.get(_objTag.category_id)
                if _category is not None and _category.lower() not in _objCat.name.lower():
                    continue

                _key = '{cat}.{tag}'.format(cat=_category, tag=_objTag.name) if _category is not None else _objTag.name
                if _key in _objTags:
                    self._print('Skipping ambiguous tag {tag}.'.format(tag=_objTag.name))
                    _objTags[_key] = None
                    continue
                _objTags[_key] = _objTag

            #
            # cannot find specified tag
            #
            if len(_objTags) == 0:
                continue

            for _keyTag in _objTags:
                _objTag = _objTags[_keyTag]
                if _objTag is None:
                    continue

                self._print('Removing tag {tag} from {vm}'.format(tag=_objTag.name, vm=_vm.name))
                _tagAssociation.detach(tag_id=_objTag.id, object_id=_dynamicId)

    ## ---------- ---------- ---------- ----------
    #  Power Actions

    ## ---------- ---------- ---------- ----------
    #  vcli.py power ...
    #
    def _power(self, action, names):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _action = action
        _names = names

        #
        # Must be exact match, to prevent accidental outages
        #
        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            _task = None
            if _action in ['on', 'start'] and _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:

                _task = _vm.PowerOn()
            elif _action in ['resume'] and _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.suspended:
                _task = _vm.PowerOn()
            elif _action in ['off', 'stop'] and _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                _task = _vm.PowerOff()
            elif _action in ['pause', 'suspend'] and _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                _task = _vm.Suspend()
            elif _action in ['reset']:
                _task = _vm.Reset()

            if _task is not None:
                _title = 'Power {action} {vm}'.format(action=_action, vm=_vm.name)
                _state = self._waitOnTask(_task, title=_title)

    ## ---------- ---------- ---------- ----------
    #  vcli.py shutdown ...
    #
    def _shutdown(self, names, reboot=None):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        _wait = getattr(self._args, 'wait') if hasattr(self._args, 'wait') else 120
        _upgradeHw = getattr(self._args, 'upgrade-hw') if hasattr(self._args, 'upgrade-hw') else None
        _vmx = getattr(self._args, 'hw-version') if hasattr(self._args, 'hw-version') else None

        _reboot = getattr(self._args, 'reboot') if hasattr(self._args, 'reboot') and reboot is None else reboot
        _hotadd = getattr(self._args, 'hot-add') if hasattr(self._args, 'hot-add') else None

        import time

        _objVms = self._getVmObjects(_names, match=True)
        for _key in _objVms:
            _vm = _objVms[_key]['id']

            if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                self._print('Shutdown failed -- {0}s is powered off'.format(_vm.name))
                continue

            try:
                self._print('Shutting down {0}'.format(_vm.name))
                _task = _vm.ShutdownGuest()
                _state = self._waitOnTask(_task)
            except:
                self._print('Error Tools Unavailable -- Cannot issue shutdown request to {0}.'.format(_vm.name))
                continue

            _i = 0
            while _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn and _i < _wait:
                time.sleep(1)
                _i += 1
            if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
                self._print('  Unable to shutdown VM.')
                continue

            if _vm.summary.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
                self._print('  VM shutdown successful')

            if _hotadd is not None and _hotadd:
                # Enable hot add feature for CPU & memory
                _spec = vim.vm.ConfigSpec()
                _spec.cpuHotAddEnabled = True
                _spec.memoryHotAddEnabled = True
                _title = 'Enabling host add CPU and memory'
                _task = _vm.Reconfigure(_spec)
                _state = self._waitOnTask(_task, title=_title)

            if _upgradeHw is not None and _upgradeHw:
                _title = 'Upgrade VM hardware to latest supported version'
                _task = _vm.UpgradeVM_Task()
                _state = self._waitOnTask(_task, title=_title)

            if _vmx is not None:
                _title = 'Changing VM hardware to version vmx-{0}'.format(_vmx)
                _task = _vm.UpgradeVM_Task('vmx-{0}'.format(_vmx))
                _state = self._waitOnTask(_task, title=_title)

            if _reboot is not None and _reboot:
                _title = 'Powering on {0}'.format(_vm.name)
                _task = _vm.PowerOn()
                _state = self._waitOnTask(_task, title=_title, wait=_wait)

    ## ---------- ---------- ---------- ----------
    #  Snapshot Actions

    ## ---------- ---------- ---------- ----------
    #  vcli.py rm-snapshot -h

    ## ---------- ---------- ---------- ----------
    #  vcli.py consolidate ...
    #  vcli.py rm-snapshot ...
    #  vcli.py revert ...
    #  vcli.py snapshot ...
    #
    def _snapshot(self, names, action='add'):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)

        _names = names
        _action = action

        _match = None
        _id = getattr(self._args, 'snapshot-id') if hasattr(self._args, 'snapshot-id') else None
        # info for adding/creating a new snpshot
        _description = getattr(self._args, 'description') if hasattr(self._args, 'description') else None

        #
        # if merge/remove or rever, force exact match
        # set filter option to speed up search
        #
        if _action in ['remove', 'revert', 'merge']:
            _match = True
            self._args.snapshot = True
        if _action in ['consolidate']:
            self._args.consolidate = True


        _objVms = self._getVmObjects(_names, match=_match)
        for _key in _objVms:
            _vm = _objVms[_key]['id']
            self._print('{action} snapshot for {vm}'.format(vm=_vm.name, action=_action.capitalize()))

            #
            # Find specified ID _id
            #
            _ss = None
            if _id is not None:
                _ss = _vm.snapshot.rootSnapshotList[0]
                # Find snapshot with ID _id
                while True:
                    if _ss.id == _id:
                        # found it
                        break
                    if len(_ss.childSnapshotList) == 0:
                        self._print('Unable to find snapshot ID {id} for {vm}.'.format(vm=_vm.name, id=_id))
                        _ss = None
                        break
                    _ss = _ss.childSnapshotList[0]

            _title = None
            _task = None
            if _action in ['add', 'create']:
                _username = self._username if self._username is not None else 'unknown'
                _memory = False
                _quiesce = False
                _title = 'Creating snapshot for {vm} with memory({memory}) and quiesce({quiesce})'.format(vm=_vm.name, memory=_memory, quiesce=_quiesce)
                _task = _vm.CreateSnapshot(_username, _description, _memory, _quiesce)
            elif _action in ['consolidate']:
                _title = 'Consolidate snapshot for {vm}'.format(vm=_vm.name)
                _task = _vm.ConsolidateDisks()
            elif _action in ['remove', 'merge']:
                if _id is not None and _ss is not None and _ss.id == _id:
                    _title = 'Remove snapshot ID {id} from {vm}'.format(vm=_vm.name, id=_id)
                    _task = _ss.snapshot.RemoveSnapshot_Task(removeChildren=True)
                else:
                    _title = 'Remove all snapshots for {0}'.format(_vm.name)
                    _task = _vm.RemoveAllSnapshots()
            elif _action in ['revert']:
                if _id is not None and _ss is not None and _ss.id == _id:
                    _title = 'Reverting to snapshot ID {0} for {1}'.format(_id, _vm.name)

                    _task = _ss.snapshot.RevertToSnapshot_Task()
                else:
                    _title = 'Reverting to most recent snapshots for {0}'.format(_vm.name)
                    _task = _vm.RevertToCurrentSnapshot()
            else:
                _task = None

            if _task is not None:
                _state = self._waitOnTask(_task, title=_title)

    ## ---------- ---------- ---------- ----------
    # vcli.py ...
    #
    def main(self):
        self._print('{func}({args})'.format(func=sys._getframe(0).f_code.co_name, args=re.sub('^, ', '', ', '.join(['''{0}="{1}"'''.format(_arg, _value) if _arg != 'self' else '' for _arg, _value in zip(locals().keys(), locals().values())]))), 3)
        self._print('main()', 3)

        try:
            _args = self._parseArguments()
            self._args = _args

            self._si = self._loginVcenter()
            self._stubConfig = self._loginInventoryService()

            # VCLI application
            _action = _args.action

            #
            # Informational actions
            #
            if _action in ['information', 'info']:
                self._info(_args.names)
            elif _action in ['list', 'ls']:
                self._list(_args.object, _args.names)

            #
            # Common actions
            #
            elif _action in ['add']:
                self._add(_args.names)
            elif _action in ['backup']:
                self._backup(_args.names)
            elif _action in ['change']:
                self._change(_args.names)
            elif _action in ['clone']:
                self._clone(_args.names)
            elif _action in ['destroy']:
                self._destroy(_args.names)
            elif _action in ['migrate']:
                self._migrate(_args.names)
            elif _action in ['remove']:
                self._remove(_args.names)

            #
            # Power State actions
            #
            elif _action in ['reboot', 'shutdown']:
                _reboot = True if _action == 'reboot' else False
                self._shutdown(_args.names, _reboot)
            elif _action in ['reset', 'resume', 'start', 'stop', 'suspend']:
                self._power(_action, _args.names)

            #
            # Snapshot actions
            #
            elif _action in ['consolidate']:
                _action = 'consolidate'
                self._snapshot(_args.names, _action)
            elif _action in ['rm-snapshot', 'merge']:
                _action = 'remove'
                self._snapshot(_args.names, _action)
            elif _action in ['revert']:
                _action = 'revert'
                self._snapshot(_args.names, _action)
            elif _action in ['snapshot']:
                _action = 'add'
                self._snapshot(_args.names, _action)

            #
            # Administrative actions
            # Password encryption/decryption
            #
            elif _action in ['encrypt', 'enc']:
                _cipher = self._encrypt(_args.password)
                self._print('Encrypted ciphertext: {0}'.format(_cipher))
            elif _action in ['decrypt', 'dec']:
                _password = self._decrypt(_args.password)
                self._print('Decrypted password: {0}'.format(_password))

        except KeyboardInterrupt:
            print 'Aborting'
            sys.exit(9)
        except IOError:
            sys.exit(8)

        sys.exit(0)
