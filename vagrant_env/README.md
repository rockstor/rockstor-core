Introduction
------------
You can use this vagrant environment to build a vagrant box VM of a confirmed working 
specification with rockstor installed from source for testing.

It will use the ansible playbook and roles in this repository to perform the VM provisioning. However,
Vagrant generates it's own host inventory since it operates using the vagrant user. eg.

```yaml
ANSIBLE_GROUPS = {
  "all_groups" => ["rockstor"],
  "all_groups:vars" => {
        "rs_inst_set_root_pass" => "true"
        }
}
```

Pre-requesits
-------------
It is assumped that you have the follow software packages install on you host machine:
- Vagrant (https://www.vagrantup.com/downloads)
- VirtualBox (https://www.virtualbox.org/wiki/Downloads)
- Ansible - see this [README](../ansible/README.md) for download instructions.

All packages are available on Linux, Mac OSX and Windows.

It is also assumed that you have a local copy of this repository [rockstor-core](https://github.com/rockstor/rockstor-core) 
on your machine, see the top level README.md, and are currently within the 'vagrant_env' directory: where the 
Vagrantfile is located.

Vagrant Boxes
-------------

This Vagrantfile uses a number of vagrant box: 

- [bento/opensuse-leap-15](https://app.vagrantup.com/bento/boxes/opensuse-leap-15) 
- [opensuse/Tumbleweed.x86_64](https://app.vagrantup.com/opensuse/boxes/Tumbleweed.x86_64)
- [opensuse/Tumbleweed.aarch64](https://app.vagrantup.com/opensuse/boxes/Tumbleweed.aarch64)

Explanantion:

*Bento*: is a provider of many base boxes for vagrant, based on official images with the virtualisation tools added.  

*opensuse-leap-15*: is a 'tag' for 'Leap 15 latest' and will track the latest release of leap 15. Should you require 
a fixed version of leap there are specific tags available. eg. 

```
v.vm.box = bento/opensuse-leap-15.2 
```

The vagrant boxes for tumbleweed are from official OpenSUSE vagrant boxes.

Building an OpenSUSE Leap VM and installing Rockstor from source
----------------------------------------------------------------
On Mac OSX, Linux and Windows:

```shell script
./build.sh
```

This will, by default, build and provision an OpenSUSE Leap 15 vagrant box - including rsyncing the source to the 
VM in /root. It will then build and install Rockstor from source as per the install guide in the top level README.md.

The VM window should have popped up and show the usual Rockstor messages regarding how to reach the Web UI. eg.

```
Rockstor is successfully installed.

web-ui is accessible with the follow links:
https://127.0.0.1
https://10.0.2.15
https://172.28.128.101
https://172.28.128.100
rockstor login:
```  

Note: your IPs may well vary.

CAUTION: This command will ALWAYS do a clean build due to the nature of the vagran rsync which uses the rsync 
option --delete.

To do subsequent builds see the Aliases section that follows on how to login as root and run further operations.

Aliases
-------

Some aliases are define in the file 'alias_rc' to assist with some commands detailed in: 
http://rockstor.com/docs/contribute.html#developers

These are appended onto the file /root/.bashrc so that they are available 
when logged in as the root user. 

Typically in the world of vagrant you login as the user 'vagrant' and sudo operating. However, for ease in this case
and in line with the instruction you can also log in as root in one of the following ways:

```
host> vagrant ssh
:
vm> su root
password: vagrant
vm> cd
```

or

```
host> ssh root@<vm IP>
password: vagrant
```
If you have set the ansible option `rs_inst_set_root_pass: yes` then the root password will be defined in 
[ansible/defaults/main.yml](../ansible/defaults/main.yml) and defaults to 'password'

From here the aliases can used. Here is a summary of them:

```
build_init
build_all
build_ui
make_mig_stadm
apply_migrations_stadm
make_mig_smtmgr
apply_migrations_smtmgr
```
See [alias_rc](./alias_rc) for details

Deploy from Testing Channel
---------------------------

If you wish to deploy a VM from the Test Channel RPMs (rather than building from source) you need to update 
the ansible playbook 'ansible/Rockstor.yml' to set the variable 'rs_inst_install_from_repo:yes' as follows:

```
  roles:
    - role: rockstor_installer
      vars:
        rs_inst_install_from_repo: yes
```

Then simply bring up the VM using the command:
```
vagrant up
```

Do NOT run 'build.sh' in this scenario.

Building for Tumbleweed and Aarch64
-----------------------------------

To build for Tumbleweed x86_64:
```shell script
./build.sh tw
```

To build for Tumbleweed Aarch64:

[Work in progress... and only on libvirt]

<s>

```shell script
./build.sh pi
```

</s>

Managing the Virtual Machine
----------------------------
To manage the Vagrant box VM simple type the following from this directory...

- Enable disk management to allow creation of data disks requires the enablement 
of the experimental 'disk' feature:
    ```
    export VAGRANT_EXPERIMENTAL="disks"
    ```
  Note: This is enabled in 'build.sh' but needs external enablement if you wish to use descrete vagrant calls below.

- Bring up all vagrant box VMs
    ```shell script
    vagrant up
    ```
- Bring up a particular vagrant box VMs
    ```shell script
    vagrant up <box-name eg. rockstor-core>
    ```

- Reconfigure the vagrant box VM following a change to the Vagrantfile:
    ```shell script
    vagrant reload
    ```
    or
    ```shell script
    vagrant reload <box-name eg. rockstor-core>
    ```

- If you change the provisioner section of the Vagrantfile or update the ansible, you can rerun just that part as follows:
    ```shell script
    vagrant provision
    ```
    or
    ```shell script
    vagrant provision <box-name eg. rockstor-core>
    ```

- Destroy the vagrant box VM:
    ```shell script
    vagrant destroy
    ```
    or
    ```shell script
    vagrant destroy <box-name eg. rockstor-core>
    ```

- If you wish to ssh into the vagrant box VM to poke around, try this:
    ```shell script
    vagrant ssh
    ```
    or
    ```shell script
    vagrant ssh <box-name eg. rockstor-core>
    ```

- If you wish to re-rsync your source files (warning this will have the effect of cleaning the build too due 
to using the --delete options):
    ```
    vagrant rsync
    ```
    or
    ```shell script
    vagrant rsync <box-name eg. rockstor-core>
    ```
  
Debuging the Ansible
--------------------

If you need additional debug for the ansible add additional 'v' to the provisioners 
verbosity variable in the Vagrantfile. eg.
```
        config.vm.provision "rockstor", type: "ansible" do |ansible|
            ansible.config_file = "../ansible/ansible.cfg"
            ansible.playbook = "../ansible/Rockstor.yml"
            ansible.verbose = "vvvv"
            ansible.groups = ANSIBLE_GROUPS
        end
```