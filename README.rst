=====
Usage
=====

The Glance project provides services for discovering, registering, and
retrieving virtual machine images. Glance has a RESTful API that allows
querying of VM image metadata as well as retrieval of the actual image.

Sample pillars
==============

.. code-block:: yaml

    glance:
      server:
        enabled: true
        version: juno
        workers: 8
        glance_uid: 302
        glance_gid: 302
        policy:
          publicize_image:
            - "role:admin"
            - "role:image_manager"
        database:
          engine: mysql
          host: 127.0.0.1
          port: 3306
          name: glance
          user: glance
          password: pwd
        identity:
          engine: keystone
          host: 127.0.0.1
          port: 35357
          tenant: service
          user: glance
          password: pwd
        message_queue:
          engine: rabbitmq
          host: 127.0.0.1
          port: 5672
          user: openstack
          password: pwd
          virtual_host: '/openstack'
        storage:
          engine: file
        images:
        - name: "CirrOS 0.3.1"
          format: qcow2
          file: cirros-0.3.1-x86_64-disk.img
          source: http://cdn.download.cirros-cloud.net/0.3.1/cirros-0.3.1-x86_64-disk.img
          public: true
        audit:
          enabled: false
        api_limit_max: 100
        limit_param_default: 50
        barbican:
          enabled: true

The pagination is controlled by the ``api_limit_max`` and ``limit_param_default``
parameters as shown above:

* ``api_limit_max``
   Defines the maximum number of records that the server will return.

* ``limit_param_default``
   The default ``limit`` parameter that applies if the request didn't define
   it explicitly.

Configuration of the ``policy.json`` file:

.. code-block:: yaml

    glance:
      server:
        ....
        policy:
          publicize_image: "role:admin"
          # Add key without value to remove line from policy.json
          add_member:

Keystone and cinder region

.. code-block:: yaml

    glance:
      server:
        enabled: true
        version: kilo
        ...
        identity:
          engine: keystone
          host: 127.0.0.1
          region: RegionTwo
        ...

Ceph integration glance

.. code-block:: yaml

    glance:
      server:
        enabled: true
        version: juno
        storage:
          engine: rbd,http
          user: glance
          pool: images
          chunk_size: 8
          client_glance_key: AQDOavlU6BsSJhAAnpFR906mvdgdfRqLHwu0Uw==

VMWare integration:

.. code-block:: yaml

    glance:
      server
        storage:
          engine: vmware
          default_store: vsphere
          vmware:
            enabled: true
            server_host: 1.2.3.4
            server_username: vmware_username
            server_password: vmware_password
            datastores:
              data1:
                name: datastore_name1
                enabled: true
                path: datacenter_name
                weight: 10
              data2:
                name: datastore_name2
                enabled: true
                path: datacenter_name

RabbitMQ HA setup

.. code-block:: yaml

    glance:
      server:
        ....
        message_queue:
          engine: rabbitmq
          members:
            - host: 10.0.16.1
            - host: 10.0.16.2
            - host: 10.0.16.3
          user: openstack
          password: pwd
          virtual_host: '/openstack'
        ....

Quota Options

.. code-block:: yaml

    glance:
      server:
        ....
        quota:
          image_member: -1
          image_property: 256
          image_tag: 256
          image_location: 15
          user_storage: 0
        ....

Configuring TLS communications
------------------------------

.. note:: By default, system wide installed CA certs are used, so
          ``cacert_file`` param is optional, as well as ``cacert``.

- **RabbitMQ TLS**

  .. code-block:: yaml

   glance:
     server:
        message_queue:
          port: 5671
          ssl:
            enabled: True
            (optional) cacert: cert body if the cacert_file does not exists
            (optional) cacert_file: /etc/openstack/rabbitmq-ca.pem
            (optional) version: TLSv1_2

- **MySQL TLS**

  .. code-block:: yaml

   glance:
     server:
        database:
          ssl:
            enabled: True
            (optional) cacert: cert body if the cacert_file does not exists
            (optional) cacert_file: /etc/openstack/mysql-ca.pem

- **Openstack HTTPS API**

  Set the ``https`` as protocol at ``glance:server`` sections:

  .. code-block:: yaml

   glance:
     server:
        identity:
           protocol: https
           (optional) cacert_file: /etc/openstack/proxy.pem
        registry:
           protocol: https
           (optional) cacert_file: /etc/openstack/proxy.pem
        storage:
           engine: cinder, swift
           cinder:
              protocol: https
             (optional) cacert_file: /etc/openstack/proxy.pem
           swift:
              store:
                  (optional) cafile: /etc/openstack/proxy.pem

Enable Glance Image Cache:

.. code-block:: yaml

    glance:
      server:
        image_cache:
          enabled: true
          enable_management: true
          directory: /var/lib/glance/image-cache/
          max_size: 21474836480
      ....

Enable auditing filter (CADF):

.. code-block:: yaml

    glance:
      server:
        audit:
          enabled: true
      ....
          filter_factory: 'keystonemiddleware.audit:filter_factory'
          map_file: '/etc/pycadf/glance_api_audit_map.conf'
      ....

Swift integration glance

.. code-block:: yaml

    glance:
      server:
        enabled: true
        version: mitaka
        storage:
          engine: swift,http
          swift:
            store:
              auth:
                address: http://keystone.example.com:5000/v2.0
                version: 2
              endpoint_type: publicURL
              container: glance
              create_container_on_put: true
              retry_get_count: 5
              user: 2ec7966596504f59acc3a76b3b9d9291:glance-user
              key: someRandomPassword

Another way, which also supports multiple swift backends, can be
configured like this:

.. code-block:: yaml

    glance:
      server:
        enabled: true
        version: mitaka
        storage:
          engine: swift,http
          swift:
            store:
              endpoint_type: publicURL
              container: glance
              create_container_on_put: true
              retry_get_count: 5
              references:
                my_objectstore_reference_1:
                  auth:
                    address: http://keystone.example.com:5000/v2.0
                    version: 2
                  user: 2ec7966596504f59acc3a76b3b9d9291:glance-user
                  key: someRandomPassword

Enable CORS parameters:

.. code-block:: yaml

    glance:
      server:
        cors:
          allowed_origin: https:localhost.local,http:localhost.local
          expose_headers: X-Auth-Token,X-Openstack-Request-Id,X-Subject-Token
          allow_methods: GET,PUT,POST,DELETE,PATCH
          allow_headers: X-Auth-Token,X-Openstack-Request-Id,X-Subject-Token
          allow_credentials: True
          max_age: 86400

Enable Viewing Multiple Locations
---------------------------------

If you want to expose all locations available (for example when you have
multiple backends configured), then you can configure this like so:

.. code-block:: yaml

    glance:
      server:
        show_multiple_locations: True
        location_strategy: store_type
        store_type_preference: rbd,swift,file

.. note:: The ``show_multiple_locations`` option is deprecated since
          Newton and is planned to be handled by policy files *only*
          starting with the Pike release.

This feature is convenient in a scenario when you have swift and rbd
configured and want to benefit from rbd enhancements.

Barbican integration glance
---------------------------

.. code-block:: yaml

    glance:
      server:
          barbican:
            enabled: true

Adding cron-job
---------------

.. code-block:: yaml

    glance:
      server:
        cron:
          cache_pruner:
            special_period: '@daily'
          cache_cleaner:
            hour: '5'
            minute: '30'
            daymonth: '*/2'


Image cache settings
--------------------

.. code-block:: yaml

    glance:
      server:
        image_cache:
          max_size: 10737418240
          stall_time: 86400
          directory: '/var/lib/glance/image-cache/'


Client role
-----------

Glance images

.. code-block:: yaml

  glance:
    client:
      enabled: true
      server:
        profile_admin:
          image:
            cirros-test:
              visibility: public
              protected: false
              location: http://download.cirros-cloud.net/0.3.4/cirros-0.3.4-i386-disk.img

Enhanced logging with logging.conf
----------------------------------

By default logging.conf is disabled.

That is possible to enable per-binary logging.conf with new variables:

* ``openstack_log_appender``
   Set to true to enable ``log_config_append`` for all OpenStack services

* ``openstack_fluentd_handler_enabled``
   Set to true to enable FluentHandler for all Openstack services

* ``openstack_ossyslog_handler_enabled``
   Set to true to enable OSSysLogHandler for all Openstack services

Only ``WatchedFileHandler``, ``OSSysLogHandler``, and ``FluentHandler``
are available.

Also, it is possible to configure this with pillar:

.. code-block:: yaml

  glance:
    server:
      logging:
        log_appender: true
        log_handlers:
          watchedfile:
            enabled: true
          fluentd:
            enabled: true
          ossyslog:
            enabled: true

Enable x509 and ssl communication between Glance and Galera cluster.
---------------------
By default communication between Glance and Galera is unsecure.

glance:
  server:
    database:
      x509:
        enabled: True

You able to set custom certificates in pillar:

glance:
  server:
    database:
      x509:
        cacert: (certificate content)
        cert: (certificate content)
        key: (certificate content)

You can read more about it here:
    https://docs.openstack.org/security-guide/databases/database-access-control.html

Usage
=====

#. Import new public image:

   .. code-block:: yaml

    glance image-create --name 'Windows 7 x86_64' --is-public true --container-format bare --disk-format qcow2  < ./win7.qcow2

#. Change new image's disk properties

   .. code-block:: yaml

    glance image-update "Windows 7 x86_64" --property hw_disk_bus=ide

#. Change new image's NIC properties

   .. code-block:: yaml

    glance image-update "Windows 7 x86_64" --property hw_vif_model=rtl8139


Read more
==========

* http://ceph.com/docs/master/rbd/rbd-openstack/

Documentation and Bugs
======================

* http://salt-formulas.readthedocs.io/
   Learn how to install and update salt-formulas

* https://github.com/salt-formulas/salt-formula-glance/issues
   In the unfortunate event that bugs are discovered, report the issue to the
   appropriate issue tracker. Use the Github issue tracker for a specific salt
   formula

* https://launchpad.net/salt-formulas
   For feature requests, bug reports, or blueprints affecting the entire
   ecosystem, use the Launchpad salt-formulas project

* https://launchpad.net/~salt-formulas-users
   Join the salt-formulas-users team and subscribe to mailing list if required

* https://github.com/salt-formulas/salt-formula-glance
   Develop the salt-formulas projects in the master branch and then submit pull
   requests against a specific formula

* #salt-formulas @ irc.freenode.net
   Use this IRC channel in case of any questions or feedback which is always
   welcome

