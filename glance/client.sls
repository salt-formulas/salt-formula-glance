{%- from "glance/map.jinja" import client with context %}
{%- if client.enabled %}

glance_client_packages:
  pkg.installed:
  - names: {{ client.pkgs }}

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