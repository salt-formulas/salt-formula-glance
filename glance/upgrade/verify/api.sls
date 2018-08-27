{%- from "glance/map.jinja" import server with context %}
{%- from "keystone/map.jinja" import client as kclient with context %}


glance_upgrade_verify_api:
  test.show_notification:
    - text: "Running glance.upgrade.verify.api"

{%- if kclient.enabled and kclient.get('os_client_config', {}).get('enabled', False)  %}

  {%- if server.get('version') not in ('mitaka', 'newton') %}
    {%- set image_name = 'TestImage' %}
    {%- set image_properties = "[{'op':'add', 'path':'/test_property', 'value': 'test'},]" %}
glancev2_image_create:
  module.run:
    - name: glancev2.image_create
    - kwargs:
        container_format: bare
        disk_format: qcow2
        name: {{ image_name }}
        cloud_name: admin_identity

glancev2_image_list:
  module.run:
    - name: glancev2.image_list
    - kwargs:
        cloud_name: admin_identity
    - require:
      - glancev2_image_create

glancev2_image_get_details:
  module.run:
    - name: glancev2.image_get_details
    - args:
      - {{ image_name }}
    - kwargs:
        cloud_name: admin_identity
    - require:
      - glancev2_image_list

glancev2_image_update:
  module.run:
    - name: glancev2.image_update
    - args:
      - {{ image_name }}
      - {{ image_properties }}
    - kwargs:
        cloud_name: admin_identity
    - require:
      - glancev2_image_get_details

glancev2_image_delete:
  module.run:
    - name: glancev2.image_delete
    - args:
      - {{ image_name }}
    - kwargs:
        cloud_name: admin_identity
    - require:
      - glancev2_image_update
  {%- endif %}
{%- endif %}
