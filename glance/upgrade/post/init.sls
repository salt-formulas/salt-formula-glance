{%- from "glance/map.jinja" import server with context %}

glance_post:
  test.show_notification:
    - text: "Running glance.upgrade.post"
