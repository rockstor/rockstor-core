Introduction
------------
You can use this vagrant environment to build a vagrant box VM of a confirmed working 
specification with rockstor for testing.

It will use the ansible playbooks and roles in this repository to perform the VM provisioning of Rockstor. Howver,
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

Both packages are available on Linux, Mac OSX and Windows.

It is also assumed that you have a local copy of this repository [rockstor-core](https://github.com/rockstor/rockstor-core) 
on your machine, see the top level README.md, and are currently within the 'vagrant_env' directory: where the 
Vagrantfile is located.

Vagrant Boxes for OpenSUSE Leap
-------------------------------

This vagrant file uses the vagrant box: [bento/opensuse-leap-15](https://app.vagrantup.com/bento/boxes/opensuse-leap-15) 

```
v.vm.box = bento/opensuse-leap-15 
```

Explanantion:

*Bento*: is a provider of many base boxes for vagrant, based on official images with the virtualisation tools added.  

*opensuse-leap-15*: is a 'tag' for 'Leap 15 latest' and will track the latest release of leap 15. Should you require 
a fixed version of leap there are specific tags available. eg. 

```
v.vm.box = bento/opensuse-leap-15.2 
```

Building the VM
-----------------------------------
On Mac OSX, Linux and Windows:

```shell script
vagrant up

```

This will also build and provision the vagrant box. It will then provision the VM with Rockstor as per the install 
guide in the top level README.md.

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

Managing the Virtual Machine
----------------------------
To manage the Vagrant box VM simple type the following from this directory...

- Bring up a vagrant box VM
```shell script
vagrant up
```

- Reconfigure the vagrant box VM following a change to the Vagrantfile:

```shell script
vagrant reload
```

- If you change the provisioner section of the Vagrantfile, you can rerun just that part as follows:

```shell script
vagrant provision
```

- Destroy the vagrant box VM:

```shell script
vagrant destroy
```

- If you wish to ssh into the vagrant box VM to poke around, try this:

```shell script
vagrant ssh
```
