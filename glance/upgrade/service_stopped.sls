{%- from "glance/map.jinja" import server,upgrade with context %}

glance_task_service_stopped:
  test.show_notification:
    - text: "Running glance.upgrade.service_stopped"

{%- if server.enabled %}
  {%- set gservices = server.services %}
  {%- if upgrade.old_release in ['newton','ocata'] %}
    {%- do gservices.append('glance-glare') %}
  {%- endif %}

  {%- for gservice in gservices %}
glance_service_stopped_{{ gservice }}:
  service.dead:
  - name: {{ gservice }}
  - enable: False
  {%- endfor %}
{%- endif %}
