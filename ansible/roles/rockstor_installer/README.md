This role has is a refactoring of the good work by Stephen Brown in his repo 
here: https://gitlab.com/StephenBrown2/rockstor-opensuse

Kudos to him for this excellent work.

## Main variables

There are some variables in default/main.yml which can (or need to) be overridden:

* `rs_inst_update_repo_key`: The URL for the Rockstor update repo GPG Key.
* `rs_inst_update_repo_url`: The URL for the Rockstor update repo"
* `rs_inst_update_repo_name`: The name of the Rockstor update repo"
* `rs_inst_useful_server_packages`: A list of useful addition packages to install on the server (eg. to support a Rock-On).
* `rs_inst_experimental`: no[default] or yes. Controls whether the latest BTRFS is included.
* `rs_inst_root_password`: The root password to be set. Must be encrypted eg. 
    ```yaml
    rs_inst_root_password: "{{ 'root' | password_hash('sha512', 'mysecretsalt') }}"
    ```
 * `rs_inst_set_root_pass`: false[default] or true. Sometimes needed on first time installs of OpenSUSE.

## Vars in role configuration
Including an example of how to use your role (for instance, with variables passed in as parameters):
```yaml
    - hosts: all
      roles:
         - role: rockstor-installer
           rs_inst_experimental: yes
           rs_inst_set_root_pass: true
```           
# rockstor-opensuse

1. A typical rockstor OpenSUSE Leap 15.x host should be configure following the "Installer options" instructions 
here: https://forum.rockstor.com/t/built-on-opensuse-dev-notes-and-status/5662. eg:
   - Use at least a 20 GB system disk, this auto enables boot to snapshot functionality.
   - Server (non transactional)
   - Default partitioning
   - Skip user creation (then only root password to enter and leaves all additional users as Rockstor managed)
   - (Optional) Load ssh key from thumb drive for root user access via ansible
*(Note: if using vagrant this is typically already available for the vagrant user)*
   - Click "Software" heading, then uncheck "AppArmor", then click Next or Apply (I forget which it is specifically)
   - Disable Firewall
   - Leave SSH service enabled
   - Switch to NetworkManager
2. After the install and initial reboot, make sure you can log in using the previously created SSH Key, or 
create one now and load it via `ssh-copy-id`
*(Note: if using vagrant this is typically already available for the vagrant user)*
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
6. Enjoy your OpenSUSE-based Rockstor!
