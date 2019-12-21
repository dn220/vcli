# vcli
VMware Command Line Interface Tool

This tool implements the common tasks associated with managing a virtual machine (vm) in the VMware environment.

The tool will be released on Saturday, December 28, 2019.

Sample Preview of the tool's top level help
-------------------------------------------


(vcli)$ vcli -h
usage: vcli [-h]

            {,info,list,add,backup,change,clone,destroy,migrate,remove,reboot,reset,resume,shutdown,start,stop,suspend,consolidate,merge,revert,snapshot,encrypt}
            ...

SYNOPSIS
    VMware Command Line Tool.

optional arguments:
  -h, --help            show this help message and exit

Action:
  {,info,list,add,backup,change,clone,destroy,migrate,remove,reboot,reset,resume,shutdown,start,stop,suspend,consolidate,merge,revert,snapshot,encrypt}
                        VM Informational Actions
                        ------------------------
    info                Display information about VM
    list                Display tabular list of object type

                        VM Common Actions
                        -----------------
    add                 Add resources to VM.
    backup              Create a clone backup of VM.
    change              Change property of VM.
    clone               Create new clone VM
    destroy             Destroy a VM
    migrate             Migrate VM to another hypervisor
    remove              Remove a resource from VM.

                        VM Power State Actions
                        ----------------------
    reboot              Gracefully reboot VM (shutdown then power on)
    reset               Forcefully reset a VM (power off then on)
    resume              Resume a suspended VM
    shutdown            Gracefully shutdown VM
    start               Start (power on) a VM
    stop                Stop (power off) a VM
    suspend             Suspend a running VM

                        VM Snapshot Actions
                        -------------------
    consolidate         Consolidate snapshot for VM
    merge               Merge snapshot files to VMDK file
    revert              Revert VM to current snapshot
    snapshot            Create snapshot for VM

                        VCLI Administrative Tasks
                        -------------------------
    encrypt             Encrypt a plaintext password for seamless execution,
                        see the help for further instruction.

DESCRIPTION
    VMware Command Line Tool.

EXAMPLES
    Example 1
    ---------
        Display all virtual machines.
        [user ~]$ vcli  list vm
        # VM            Pwr  CPU  Mem  Disks  Snap  Con  Description
        # --            ---  ---  ---  -----  ----  ---  -----------
        server1         On     1    2     40    No  No   Test server 1
        server2         On     1    2     40    No  No   Test server 2
        # Total:  2
        [user ~]$ vcli ...

(vcli)$
