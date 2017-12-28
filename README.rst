==============
Glance formula
==============

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
        - name: "CirrOS"
          format: qcow2
          file: cirros-0.4.0-x86_64-disk.img
          source: https://download.cirros-cloud.net/0.4.0/cirros-0.4.0-x86_64-disk.img
          visibility: true
        audit:
          enabled: false
        api_limit_max: 100
        limit_param_default: 50
        barbican:
          enabled: true

The pagination is controlled by the *api_limit_max* and *limit_param_default*
parameters as shown above:

* *api_limit_max* defines the maximum number of records that the server will
  return.

* *limit_param_default* is the default *limit* parameter that
  applies if the request didn't defined it explicitly.

Configuration of policy.json file

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

Configuring TLS communications
------------------------------


**Note:** by default system wide installed CA certs are used, so ``cacert_file`` param is optional, as well as ``cacert``.


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

Another way, which also supports multiple swift backends, can be configured like this:

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

Enable CORS parameters

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

Please note: the show_multiple_locations option is deprecated since Newton and is planned
             to be handled by policy files _only_ starting with the Pike release.

This feature is convenient in a scenario when you have swift and rbd configured and want to
benefit from rbd enhancements.


Barbican integration glance
---------------------------

.. code-block:: yaml

    glance:
      server:
          barbican:
            enabled: true


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


Usage
=====

Import new public image

.. code-block:: yaml

    glance image-create --name 'Windows 7 x86_64' --is-public true --container-format bare --disk-format qcow2  < ./win7.qcow2

Change new image's disk properties

.. code-block:: yaml

    glance image-update "Windows 7 x86_64" --property hw_disk_bus=ide

Change new image's NIC properties

.. code-block:: yaml

    glance image-update "Windows 7 x86_64" --property hw_vif_model=rtl8139


External links
==============

* http://ceph.com/docs/master/rbd/rbd-openstack/


Documentation and Bugs
======================

To learn how to deploy OpenStack Salt, consult the documentation available
online at:

    https://wiki.openstack.org/wiki/OpenStackSalt

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate bug tracker. If you obtained the software from a 3rd party
operating system vendor, it is often wise to use their own bug tracker for
reporting problems. In all other cases use the master OpenStack bug tracker,
available at:

    http://bugs.launchpad.net/openstack-salt

Developers wishing to work on the OpenStack Salt project should always base
their work on the latest formulas code, available from the master GIT
repository at:

    https://git.openstack.org/cgit/openstack/salt-formula-glance

Developers should also join the discussion on the IRC list, at:

    https://wiki.openstack.org/wiki/Meetings/openstack-salt

Documentation and Bugs
======================

To learn how to install and update salt-formulas, consult the documentation
available online at:

    http://salt-formulas.readthedocs.io/

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate issue tracker. Use Github issue tracker for specific salt
formula:

    https://github.com/salt-formulas/salt-formula-glance/issues

For feature requests, bug reports or blueprints affecting entire ecosystem,
use Launchpad salt-formulas project:

    https://launchpad.net/salt-formulas

You can also join salt-formulas-users team and subscribe to mailing list:

    https://launchpad.net/~salt-formulas-users

Developers wishing to work on the salt-formulas projects should always base
their work on master branch and submit pull request against specific formula.

    https://github.com/salt-formulas/salt-formula-glance

Any questions or feedback is always welcome so feel free to join our IRC
channel:

    #salt-formulas @ irc.freenode.net
