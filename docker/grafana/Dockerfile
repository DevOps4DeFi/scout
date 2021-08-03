FROM grafana/grafana:8.0.6-ubuntu

# Disable Login form or not
ENV GF_AUTH_DISABLE_LOGIN_FORM=false

# Allow anonymous authentication or not
ENV GF_AUTH_ANONYMOUS_ENABLED=true

# Role of anonymous user
ENV GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer

# Install plugins here our in your own config file
ENV GF_INSTALL_PLUGINS="grafana-image-renderer"

# Add provisioning
ADD provisioning /etc/grafana/provisioning

# Add configuration file
ADD grafana.ini /etc/grafana/grafana.ini
ADD dashboards /etc/grafana/dashboards
