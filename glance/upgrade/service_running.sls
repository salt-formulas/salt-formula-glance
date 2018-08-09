{%- from "glance/map.jinja" import server,upgrade with context %}

glance_task_service_running:
  test.show_notification:
    - text: "Running glance.upgrade.service_running"

{%- if server.enabled %}
  {%- set gservices = server.services %}
  {%- if upgrade.new_release in ['newton','ocata'] %}
    {%- do gservices.append('glance-glare') %}
  {%- endif %}

  {%- for gservice in gservices %}
glance_running_stopped_{{ gservice }}:
  service.running:
  - name: {{ gservice }}
  - enable: True
  {%- endfor %}
{%- endif %}
