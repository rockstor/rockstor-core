This role has is a refactoring of the good work by Stephen Brown in his repo 
here: https://gitlab.com/StephenBrown2/rockstor-opensuse

Kudos to him for this excellent work.

## Main variables

There are some variables in default/main.yml which can (or need to) be overridden:

* `rs_inst_install_from_repo`: no[default] or yes. Install direct from testing repo.
* `rs_inst_experimental`: no[default] or yes. Controls whether the latest BTRFS is included.
* `rs_inst_set_root_pass`: no[default] or yes. Sometimes needed on first time installs of OpenSUSE.
* `rs_inst_root_password`: The root password to be set. Must be encrypted eg. 
    ```yaml
    rs_inst_root_password: "{{ 'root' | password_hash('sha512', 'mysecretsalt') }}"
    ```
* `rs_inst_update_os`: no[default] or yes. Choose to update the OS packages or not.
* `rs_inst_useful_server_packages`: A list of useful addition packages to install on the server (eg. to support a Rock-On).

## Vars in role configuration
Including an example of how to use your role (for instance, with variables passed in as parameters):
```yaml
---
- hosts: all
  become: yes
  become_user: root

  roles:
    - role: rockstor_installer
      vars:
        rs_inst_install_from_repo: yes
        rs_inst_set_root_pass: yes
        rs_inst_useful_server_packages:
            - ffmpeg
            - mediainfo
            - mosh
            - tmux
            - tree
```           
# rockstor-opensuse

1. A typical rockstor 'Built on OpenSUSE' host should be configure following the instructions 
here: https://forum.rockstor.com/t/built-on-opensuse-dev-notes-and-status/5662. 

    *This ansible role is intended to be aligned with those install instructions.*

2. After the install and initial reboot, create an SSH Key  and load it via `ssh-copy-id`. 
Make sure you can log in using it (ie. without needing a password.)

    *Note: if using vagrant this is typically already available for the vagrant user.*

3. Create an inventory file for ansible, something like the following in `hosts.yml`:
    ```yaml
    ---
    all:
        hosts:
            rockstor:
                # Use your server's IP
                ansible_ssh_host: 192.168.88.100
                # Use the path to your local SSH Private Key
                ansible_ssh_private_key_file: /home/youruser/.ssh/id_rsa_ansible
                ansible_user: root
    ```
4. Create a playbook called 'main.yml'
    ```yaml
    ---
    - hosts: rockstor
      become: yes
      become_user: root
    
      roles:
        - role: rockstor_installer
    ```
5. Run the ansible playbook:
    ```sh
    ansible-playbook -i hosts.yml main.yml
    ```
