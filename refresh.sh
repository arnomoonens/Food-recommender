#!/bin/bash

rm output.ttl
java -jar db2triples-1.0.3-SNAPSHOT.jar -u root -p myfoodguru -l jdbc:mysql://198.199.127.25:3306/ -b myfoodguru -m r2rml -r mapping.ttl
scp output.ttl root@198.199.127.25:/root/
