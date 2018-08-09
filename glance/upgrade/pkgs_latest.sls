{%- from "glance/map.jinja" import server,client,upgrade with context %}

glance_task_pkg_latest:
  test.show_notification:
    - text: "Running glance.upgrade.pkg_latest"

policy-rc.d_present:
  file.managed:
    - name: /usr/sbin/policy-rc.d
    - mode: 755
    - contents: |
        #!/bin/sh
        exit 101

{%- set pkgs = [] %}
{%- if server.enabled %}
  {%- do pkgs.extend(server.pkgs) %}
  {%- if upgrade.new_release in ['newton', 'ocata'] %}
    {%- do pkgs.append('glance-glare') %}
  {%- endif %}
{%- endif %}
{%- if client.enabled %}
  {%- do pkgs.extend(client.pkgs) %}
{%- endif %}

glance_pkg_latest:
  pkg.latest:
  - names: {{ pkgs|unique }}
  - require:
    - file: policy-rc.d_present
  - require_in:
    - file: policy-rc.d_absent

policy-rc.d_absent:
  file.absent:
    - name: /usr/sbin/policy-rc.d
