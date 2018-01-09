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
    quota:
      image_member_quota: -1
      image_property_quota: 256
      image_tag_quota: 256
      image_location_quota: 15
      user_storage_quota: 0
