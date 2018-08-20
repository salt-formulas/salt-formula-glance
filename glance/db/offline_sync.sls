{%- from "glance/map.jinja" import server with context %}

glance_syncdb:
  cmd.run:
  - name: glance-manage db_sync
  {%- if grains.get('noservices') or server.get('role', 'primary') == 'secondary' %}
  - onlyif: /bin/false
  {%- endif %}

glance_load_metadatafs:
  cmd.run:
  - name: glance-manage db_load_metadefs
  - require:
    - cmd: glance_syncdb
    {%- if grains.get('noservices') or server.get('role', 'primary') == 'secondary' %}
  - onlyif: /bin/false
    {%- endif %}
