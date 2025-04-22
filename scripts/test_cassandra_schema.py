from cassandra.cluster import Cluster

cluster = Cluster(['localhost'])
session = cluster.connect('crdp')

session.execute("""
INSERT INTO sensor_metrics (region, timestamp, avg_temperature, avg_humidity, avg_pressure, flood_risk)
VALUES (%s, %s, %s, %s, %s, %s)
""", ("Jakarta", "2025-04-01 08:00:00", 31.8, 84.5, 1013.0, 0.9))

rows = session.execute("SELECT * FROM sensor_metrics WHERE region = 'Jakarta'")
for row in rows:
    print(row.region, row.timestamp, row.avg_temperature, row.flood_risk)

cluster.shutdown()
