
TCP = 'tcp'
UDP = 'udp'
ONE_GB = 1073741824

openvpn = {u'containers': {u'openvpn': {'image': 'kylemanna/openvpn',
                                        'ports': {'1194':
                                                  {'protocol': 'udp',
                                                   'label': 'Server port',
                                                   'host_default': 1194,
                                                   'description': 'OpenVPN server listening port. You may need to open it on your firewall.',},},
                                        'launch_order': 2,
                                        u'opts': [['--cap-add=NET_ADMIN', ''],
                                                  ['--volumes-from', 'ovpn-data'], ],},
                           u'ovpn-data': {'image': 'busybox',
                                          'opts': [['-v', '/etc/openvpn'], ],
                                          'launch_order': 1,},},

           'custom_config': {'servername':
                             {'label': 'Server address',
                              'description': "Your Rockstor system's public ip address or hostname.",},},

           'description': 'Open Source VPN server',
           'website': 'https://openvpn.net/',
           'icon': 'https://openvpn.net/',
           'more_info': '<h4>Additional steps are required by this Rockon.</h4><p>Run these following commands as the<code>root</code>user on your Rockstor system.</p><h4><u>Initialize PKI</u>&nbsp;&nbsp;&nbsp;&nbsp;<i>Rock-on will not start without it.</i></h4><code>/opt/rockstor/bin/ovpn-initpki</code><h4><u>Generate a client certificate</u>&nbsp;&nbsp;&nbsp;&nbsp;<i>One for every client</i></h4><code>/opt/rockstor/bin/ovpn-client-gen</code><br><h4><u>Retrieve client configuration</u>&nbsp;&nbsp;&nbsp;&nbsp<i>For any one of your clients. The resulting .ovpn file can be used to connect.</i></h4><code>/opt/rockstor/bin/ovpn-client-print</code><h4><u>Configure firewall</u></h4><p>If your Rockstor system is behind a firewall, you will need to configure it to allow OpenVPN traffic to forward to your Rockstor system.</p>',}

owncloud = {'ui': {'slug': '',
                   'https': True,},
            'containers': {'owncloud': {'image': 'pschmitt/owncloud',
                                        'ports': {'443':
                                                  {'ui': True,
                                                   'host_default': 8080,
                                                   'protocol': 'tcp',
                                                   'label': 'WebUI port',
                                                   'description': 'OwnCloud WebUI port. Suggested default: 8080',},},
                                        'volumes': {'/var/www/owncloud/data':
                                                    {'description': 'Choose a Share for OwnCloud data. Eg: create a Share called owncloud-data for this purpose alone.',
                                                     'min_size': 1073741824,
                                                     'label': 'Data directory',},
                                                    '/var/www/owncloud/config':
                                                    {'description': 'Choose a Share for OwnCloud configuration. Eg: create a Share called owncloud-config for this purpose alone.',
                                                     'label': 'Config directory',
                                                     'min_size': 1073741824,},},
                                        'launch_order': 2,},
                           'owncloud-postgres': {'image': 'postgres',
                                                 'volumes': {'/var/lib/postgresql/data':
                                                             {'description': "Choose a Share for OwnCloud's postgresql database. Eg: create a Share called owncloud-db for this purpose alone.",
                                                              'label': 'Database',
                                                              'min_size': 1073741824, }, },
                                                 'launch_order': 1}, },
            'container_links': {'owncloud': [{'source_container': 'owncloud-postgres',
                                              'name': 'db'},]},
            'custom_config': {'db_user':
                              {'label': 'DB User',
                               'description': 'Choose a administrator username for the OwnCloud database.',},
                              'db_pw':
                              {'label': 'DB Password',
                               'description': 'Choose a secure password for the database admin user',},},
            'description': 'Secure file sharing and hosting',
            'website': 'https://owncloud.org/',
            'icon': 'https://owncloud.org/wp-content/themes/owncloudorgnew/assets/img/common/logo_owncloud.svg',
            'more_info': '<p>Default username for your OwnCloud UI is<code>admin</code>and password is<code>changeme</code></p>',}

syncthing = {'ui': {'slug': '',
                    'https': True,},
             'containers': {'syncthing': {'image': 'istepanov/syncthing',
                                          'ports': {'8384':
                                                    {'ui': True,
                                                     'host_default': 8384,
                                                     'protocol': TCP,
                                                     'label': 'WebUI port',
                                                     'description': 'Syncthing WebUI port. Suggested default: 8384.',},
                                                    '22000':
                                                    {'host_default': 22000,
                                                     'protocol': TCP,
                                                     'label': 'Listening port',
                                                     'description': 'Port for incoming data. You may need to open it(protocol: tcp) on your firewall. Suggested default: 22000.',},
                                                    '21025':
                                                    {'host_default': 21025,
                                                     'protocol': UDP,
                                                     'label': 'Discovery port',
                                                     'description': 'Port for discovery broadcasts. You may need to open it(protocol: udp) on your firewall. Suggested default: 21025.',},},
                                          'volumes': {'/home/syncthing/.config/syncthing':
                                                      {'description': 'Choose a Share for configuration. Eg: create a Share called syncthing-config for this purpose alone.',
                                                       'min_size': ONE_GB,
                                                       'label': 'Config directory',},
                                                      '/home/syncthing/Sync':
                                                      {'label': 'Data directory',
                                                       'description': 'Choose a Share for all incoming data. Eg: create a Share called syncthing-data for this purpose alone.',},},
                                          'launch_order': 1,},},
             'description': 'Continuous File Synchronization',
             'website': 'https://syncthing.net/',}

transmission = {'ui': {'slug': '',},
                'containers': {'transmission': {'image': 'dperson/transmission',
                                                'ports': {'9091':
                                                          {'ui': True,
                                                           'host_default': 9091,
                                                           'protocol': TCP,
                                                           'label': 'WebUI port',
                                                           'description': 'Transmission WebUI port. Suggested default: 9091',},
                                                          '51413':
                                                          {'host_default': 51413,
                                                           'label': 'Sharing port',
                                                           'description': 'Port used to share the file being downloaded. You may need to open it(protocol: tcp and udp) on your firewall. Suggested default: 51413.',},},
                                                'volumes': {'/var/lib/transmission-daemon':
                                                            {'description': "Choose a Share where Transmission will save all of it's files including your downloads. Eg: create a Share called transmission-rockon.",
                                                             'label': 'Data directory',},},
                                                'launch_order': 1,},},
                'custom_config': {'TRUSER':
                                  {'label': 'WebUI username',
                                   'description': 'Choose a login username for Transmission WebUI.',},
                                  'TRPASSWD':
                                  {'label': 'WebUI password',
                                   'description': 'Choose a login password for the Transmission WebUI.',},},
                'description': 'Open Source BitTorrent client',
                'website': 'http://www.transmissionbt.com/',}

btsync = {'ui': {'slug': '',},
          'containers': {'btsync': {'image': 'aostanin/btsync',
                                    'ports': {'8888':
                                              {'ui': True,
                                               'host_default': 8888,
                                               'protocol': TCP,
                                               'label': 'WebUI port',
                                               'description': 'BTSync WebUI port. Suggested default: 8888',},
                                              '3369':
                                              {'host_default': 3369,
                                               'procotol': UDP,
                                               'label': 'Listening port',
                                               'description': 'Port for incoming data. You may need to open it(protocol: udp) on your firewall. Suggested default: 3369.',},},
                                    'volumes': {'/data':
                                                {'description': 'Choose a Share for all incoming data. Eg: create a Share called btsync-data for this purpose alone. It will be available as /data inside BTSync.',
                                                 'label': 'Data directory',},},
                                    'launch_order': 1,},},
          'description': 'BitTorrent Sync',
          'website': 'https://www.getsync.com/',
          'volume_add_support': True,
          'more_info': '<h4>Authentication</h4><p>Default username for your BTSync UI is<code>admin</code>and password is<code>password</code></p><h4>Storage</h4><p>We strongly recommend changing the Default folder location to<code>/data</code>in the UI preferences.</p><p>You can also assign additional Shares for custom organization of your data.</p>'}

plex = {'ui': {'slug': 'web',},
        'containers': {'plex': {'image': 'timhaak/plex',
                                'ports': {'32400':
                                          {'ui': True,
                                           'host_default': 32400,
                                           'protocol': TCP,
                                           'label': 'WebUI port',
                                           'description': 'Plex WebUI port. Suggested default: 32400',},},
                                'launch_order': 1,
                                'opts': [['--net=host', ''],],
                                'volumes': {'/config':
                                            {'description': 'Choose a Share for Plex configuration. Eg: create a Share called plex-config for this purpose alone.',
                                             'label': 'Config directory',},
                                            '/data':
                                            {'description': 'Choose a Share for Plex content(your media). Eg: create a Share called plex-data for this purpose alone. You can also assign other media Shares on the system after installation.',
                                             'label': 'Data directory',},},},},
        'description': 'Plex media server',
        'website': 'https://plex.tv/',
        'volume_add_support': True,
        'more_info': '<h4>Adding media to Plex.</h4><p>You can add more Shares(with media) from here</p><p>Then, from Plex WebUI, you can update and re-index your library.</p>'}

rockons = {'OpenVPN': openvpn,
           'OwnCloud': owncloud,
           'Syncthing': syncthing,
           'Transmission': transmission,
           'BTSync': btsync,
           'Plex': plex, }
