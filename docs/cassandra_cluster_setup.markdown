## Updated Cassandra Cluster Setup with Three Nodes

This section documents the final configuration for the Cassandra cluster with three nodes, each in a separate datacenter (`Asia`, `NorthAmerica`, `Europe`). These commands include optimizations for memory usage, JMX remote access, and custom `cassandra.yaml` settings.

### Node 1: cassandra-asia (Datacenter: Asia)

- **Purpose**: This node serves as the seed node for the cluster and is part of the `Asia` datacenter.
- **Command**:
  ```bash
  sudo docker run -d \
    --name cassandra-asia \
    --network crdp-cassandra-net \
    --memory="1g" \
    -e CASSANDRA_CLUSTER_NAME=CRDPCluster \
    -e CASSANDRA_DC=Asia \
    -e CASSANDRA_RACK=Rack1 \
    -e CASSANDRA_SEEDS=cassandra-asia \
    -e MAX_HEAP_SIZE="256M" \
    -e HEAP_NEWSIZE="50M" \
    -e JVM_OPTS="-Dcom.sun.management.jmxremote.port=7199 -Dcom.sun.management.jmxremote.rmi.port=7199 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Djava.rmi.server.hostname=172.21.0.2 -XX:MaxDirectMemorySize=512M" \
    -p 9042:9042 \
    -p 7199:7199 \
    -v cassandra-asia-data:/var/lib/cassandra \
    -v ~/crdp-net/cassandra-conf/cassandra.yaml:/etc/cassandra/cassandra.yaml \
    cassandra:latest
  ```
- **Notes**:
  - Uses the `crdp-cassandra-net` network for communication.
  - Memory limited to 1GB with a heap size of 256MB and direct memory of 512MB.
  - Exposes port 9042 for CQL clients and 7199 for JMX.
  - Mounts a custom `cassandra.yaml` for optimized settings (e.g., reduced cache sizes).

### Node 2: cassandra-na (Datacenter: NorthAmerica)

- **Purpose**: This node is part of the `NorthAmerica` datacenter and joins the cluster using `cassandra-asia` as the seed node.
- **Command**:
  ```bash
  sudo docker run -d \
    --name cassandra-na \
    --network crdp-cassandra-net \
    --memory="1g" \
    -e CASSANDRA_CLUSTER_NAME=CRDPCluster \
    -e CASSANDRA_DC=NorthAmerica \
    -e CASSANDRA_RACK=Rack1 \
    -e CASSANDRA_SEEDS=cassandra-asia \
    -e MAX_HEAP_SIZE="256M" \
    -e HEAP_NEWSIZE="50M" \
    -e JVM_OPTS="-Dcom.sun.management.jmxremote.port=7199 -Dcom.sun.management.jmxremote.rmi.port=7199 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Djava.rmi.server.hostname=172.21.0.3 -XX:MaxDirectMemorySize=512M" \
    -p 9043:9042 \
    -p 7200:7199 \
    -v cassandra-na-data:/var/lib/cassandra \
    -v ~/crdp-net/cassandra-conf/cassandra.yaml:/etc/cassandra/cassandra.yaml \
    cassandra:latest
  ```
- **Notes**:
  - Maps port 9043 on the host to 9042 in the container to avoid conflicts.
  - Maps JMX port 7200 on the host to 7199 in the container.
  - Uses the same memory and configuration settings as `cassandra-asia`.

### Node 3: cassandra-eu (Datacenter: Europe)

- **Purpose**: This node is part of the `Europe` datacenter and joins the cluster using `cassandra-asia` as the seed node.
- **Command**:
  ```bash
  sudo docker run -d \
    --name cassandra-eu \
    --network crdp-cassandra-net \
    --memory="1g" \
    -e CASSANDRA_CLUSTER_NAME=CRDPCluster \
    -e CASSANDRA_DC=Europe \
    -e CASSANDRA_RACK=Rack1 \
    -e CASSANDRA_SEEDS=cassandra-asia \
    -e MAX_HEAP_SIZE="256M" \
    -e HEAP_NEWSIZE="50M" \
    -e JVM_OPTS="-Dcom.sun.management.jmxremote.port=7199 -Dcom.sun.management.jmxremote.rmi.port=7199 -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote.authenticate=false -Djava.rmi.server.hostname=172.21.0.4 -XX:MaxDirectMemorySize=512M" \
    -p 9044:9042 \
    -p 7201:7199 \
    -v cassandra-eu-data:/var/lib/cassandra \
    -v ~/crdp-net/cassandra-conf/cassandra.yaml:/etc/cassandra/cassandra.yaml \
    cassandra:latest
  ```
- **Notes**:
  - Maps port 9044 on the host to 9042 in the container.
  - Maps JMX port 7201 on the host to 7199 in the container.
  - Same memory and configuration settings as the other nodes.

### Verification Steps

After starting all nodes, verify the cluster status:
```bash
sudo docker exec -it cassandra-asia nodetool status
```

**Expected Output**:
```
Datacenter: Asia
===============
Status=Up/Down
State=Normal/Leaving/Joining/Moving
--  Address     Load        Tokens  Owns (effective)  Host ID                               Rack
UN  172.21.0.2  124.48 KiB  16      ?                 <host-id>                            Rack1

Datacenter: NorthAmerica
===============
UN  172.21.0.3  124.48 KiB  16      ?                 <host-id>                            Rack1

Datacenter: Europe
===============
UN  172.21.0.4  124.48 KiB  16      ?                 <host-id>                            Rack1
```

Ensure all nodes are in the `UN` (Up, Normal) state and the datacenter names match the configuration.