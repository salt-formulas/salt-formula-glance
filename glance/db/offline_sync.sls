{%- from "glance/map.jinja" import server with context %}

glance_syncdb:
  cmd.run:
  - name: glance-manage db_sync
  {%- if grains.get('noservices') or server.get('role', 'primary') == 'secondary' %}
  - onlyif: /bin/false
  {%- endif %}
