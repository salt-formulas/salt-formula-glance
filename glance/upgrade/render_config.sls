{%- from "glance/map.jinja" import server with context %}

glance_render_config:
  test.show_notification:
    - text: "Running glance.upgrade.render_config"

{%- if server.enabled %}
/etc/glance/glance-api.conf:
  file.managed:
  - source: salt://glance/files/{{ server.version }}/glance-api.conf.{{ grains.os_family }}
  - template: jinja

/etc/glance/glance-registry.conf:
  file.managed:
  - source: salt://glance/files/{{ server.version }}/glance-registry.conf.{{ grains.os_family }}
  - template: jinja
{%- endif %}
