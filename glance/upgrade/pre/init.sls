{%- from "glance/map.jinja" import server with context %}

include:
 - glance.upgrade.verify.api

glance_pre:
  test.show_notification:
    - text: "Running glance.upgrade.pre"
