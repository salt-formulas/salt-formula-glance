{%- from "glance/map.jinja" import server with context %}

glance_ssl_rabbitmq:
  test.show_notification:
    - text: "Running glance._ssl.rabbitmq"

{%- if server.message_queue.get('x509',{}).get('enabled',False) %}

  {%- set ca_file=server.message_queue.x509.ca_file %}
  {%- set key_file=server.message_queue.x509.key_file %}
  {%- set cert_file=server.message_queue.x509.cert_file %}

rabbitmq_glance_ssl_x509_ca:
  {%- if server.message_queue.x509.cacert is defined %}
  file.managed:
    - name: {{ ca_file }}
    - contents_pillar: glance:server:message_queue:x509:cacert
    - mode: 444
    - user: glance
    - group: glance
    - makedirs: true
  {%- else %}
  file.exists:
    - name: {{ ca_file }}
  {%- endif %}

rabbitmq_glance_client_ssl_cert:
  {%- if server.message_queue.x509.cert is defined %}
  file.managed:
    - name: {{ cert_file }}
    - contents_pillar: glance:server:message_queue:x509:cert
    - mode: 440
    - user: glance
    - group: glance
    - makedirs: true
  {%- else %}
  file.exists:
    - name: {{ cert_file }}
  {%- endif %}

rabbitmq_glance_client_ssl_private_key:
  {%- if server.message_queue.x509.key is defined %}
  file.managed:
    - name: {{ key_file }}
    - contents_pillar: glance:server:message_queue:x509:key
    - mode: 400
    - user: glance
    - group: glance
    - makedirs: true
  {%- else %}
  file.exists:
    - name: {{ key_file }}
  {%- endif %}

rabbitmq_glance_ssl_x509_set_user_and_group:
  file.managed:
    - names:
      - {{ ca_file }}
      - {{ cert_file }}
      - {{ key_file }}
    - user: glance
    - group: glance

{% elif server.message_queue.get('ssl',{}).get('enabled',False) %}
rabbitmq_ca_glance_client:
  {%- if server.message_queue.ssl.cacert is defined %}
  file.managed:
    - name: {{ server.message_queue.ssl.cacert_file }}
    - contents_pillar: glance:server:message_queue:ssl:cacert
    - mode: 0444
    - makedirs: true
  {%- else %}
  file.exists:
    - name: {{ server.message_queue.ssl.get('cacert_file', server.cacert_file) }}
  {%- endif %}

{%- endif %}
