glance:
  server:
    enabled: true
    version: liberty
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
      engine: swift
      swift:
        store:
          # admin_tenants: 
          auth:
            address: http://127.0.0.1:5000/v2.0
            insecure: false
            version: 2
          cacert: /etc/ssl/certs/ca-certificates.crt
          # config_file: 
          container: glance
          create_container_on_put: true
          endpoint: swift
          endpoint_type: internalURL
          expire_soon_interval: 60
          key: someRandomPassword
          large_object_size: 5120
          large_object_chunk_size: 200
          multi_tenant: false
          multiple_containers_seed: 0
          retry_get_count: 5
          region: RegionOne
          service_type: object-store
          ssl_compression: false
          use_trusts: false
          user: 2ec7966596504f59acc3a76b3b9d9291:glance-user
