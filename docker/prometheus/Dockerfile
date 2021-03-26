FROM prom/prometheus
ADD prometheus.yml /etc/prometheus/
CMD ["--config.file=/etc/prometheus/prometheus.yml", "--storage.tsdb.path=/prometheus", "--web.console.libraries=/usr/share/prometheus/console_libraries", "--storage.tsdb.retention.time=800d"]