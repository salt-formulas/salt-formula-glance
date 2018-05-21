{%- from "glance/map.jinja" import client with context %}
{%- if client.enabled %}

glance_client_packages:
  pkg.installed:
  - names: {{ client.pkgs }}

{%- if client.cloud_name is defined %}

{%- for identity_name, identity in client.identity.items() %}
{%- for image_name, image in identity.image.items() %}

{%- set _image_properties = {} %}
{%- do _image_properties.update({'container_format': image.container_format}) %}
{%- do _image_properties.update({'disk_format': image.disk_format}) %}
{%- do _image_properties.update({'protected': 'false'}) %}
{%- do _image_properties.update({'tags': image.tags}) %}
{%- do _image_properties.update({'visibility': image.visibility}) %}

glance_openstack_image_{{ image_name }}:
  glancev2.image_present:
    - cloud_name: {{ client.cloud_name }}
    - name: {{ image.get('name', image_name) }}
    - image_properties: {{ _image_properties }}
    {%- if image.import_from_format is defined %}
    - import_from_format: {{ image.import_from_format }}
    {%- endif %}
    {%- if image.location is defined %}
    - location: {{ image.location }}
    {%- endif %}
    {%- if image.wait_timeout is defined %}
    - timeout: {{ image.wait_timeout }}
    {%- endif %}
    {%- if image.checksum is defined %}
    - checksum: {{ image.checksum }}
    {%- endif %}
{%- endfor %}
{%- endfor %}


{%- else %}
{%- for identity_name, identity in client.identity.items() %}

{%- for image_name, image in identity.image.items() %}

glance_openstack_image_{{ image_name }}:
  glanceng.image_import:
    - name: {{ image.get('name', image_name) }}
    - profile: {{ identity_name }}
    {%- if image.import_from_format is defined %}
    - import_from_format: {{ image.import_from_format }}
    {%- endif %}
    {%- if image.visibility is defined %}
    - visibility: {{ image.visibility }}
    {%- endif %}
    {%- if image.protected is defined %}
    - protected: {{ image.protected }}
    {%- endif %}
    {%- if image.location is defined %}
    - location: {{ image.location }}
    {%- endif %}
    {%- if image.tags is defined %}
    - tags: {{ image.tags }}
    {%- endif %}
    {%- if image.disk_format is defined %}
    - disk_format: {{ image.disk_format }}
    {%- endif %}
    {%- if image.container_format is defined %}
    - container_format: {{ image.container_format }}
    {%- endif %}
    {%- if image.wait_timeout is defined %}
    - timeout: {{ image.wait_timeout }}
    {%- endif %}
    {%- if image.checksum is defined %}
    - checksum: {{ image.checksum }}
    {%- endif %}

{%- endfor %}
{%- endfor %}

{%- endif %}

{%- endif %}
