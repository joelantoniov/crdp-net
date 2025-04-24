docker cp ~/crdp-net/scripts/migrate_sensor_metrics.py spark-master:/opt/bitnami/spark/
docker exec -it spark-master spark-submit /opt/bitnami/spark/migrate_sensor_metrics.py
