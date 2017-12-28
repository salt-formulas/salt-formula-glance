glance:
  server:
    enabled: true
    version: newton
    workers: 1
    database:
      engine: mysql
      host: localhost
      port: 3306
      name: glance
      user: glance
      password: password
    registry:
      host: 127.0.0.1
      port: 9191
    bind:
      address: 127.0.0.1
      port: 9292
    identity:
      engine: keystone
      host: 127.0.0.1
      port: 35357
      user: glance
      password: password
      region: RegionOne
      tenant: service
      endpoint_type: internalURL
    message_queue:
      engine: rabbitmq
      host: 127.0.0.1
      port: 5672
      user: openstack
      password: password
      virtual_host: '/openstack'
    storage:
      engine: file
    policy:
      publicize_image: "role:admin"
      add_member:
    images:
        - name: "CirrOS"
          format: qcow2
          file: cirros-0.4.0-x86_64-disk.img
          source: https://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img
          visibility: true
        - name: "CirrOS4"
          format: qcow2
          file: cirros-0.4.0-x86_64-disk.img
          source: https://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img
          # TODO:  for backward compatibility, test public option.
          public: true
