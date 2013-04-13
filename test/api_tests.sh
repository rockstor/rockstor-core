#!/bin/sh

echo "Disks"
curl -X GET http://localhost/api/disks/
echo "\nPools"
curl -X GET http://localhost/api/pools/
echo "\nShares"
curl -X GET http://localhost/api/shares/
echo "\nSetting up"
curl -X POST http://localhost/api/tools/sysdisks/

echo "\nCreating a pool"
curl -X POST -H 'Content-Type: application/json' --data-binary '{"disks": "sdb,sdc", "raid_level": "raid0", "name": "pool0"}' http://localhost/api/pools/
echo "\nPools"
curl -X GET http://localhost/api/pools/
echo "\nUsage of the pool
curl -X GET http://localhost/api/pools/pool0/usage/
echo "\nShares"
curl -X GET http://localhost/api/shares/
echo "\nCreating a share"
curl -X POST -H 'Content-Type: application/json' --data-binary '{"pool": "pool0", "name": "share0", "size": 12345}' http://localhost/api/shares/

echo "\nSnapshots"
curl -X GET http://localhost/api/shares/share0/snapshots/
echo "\nCreating a snapshot"
curl -X POST -H 'Content-Type: application/json' --data-binary '{"name": "snap0"}' http://localhost/api/shares/share0/snapshots/
echo "\nDeleting snapshots"
curl -X DELETE -H 'Content-Type: application/json' --data-binary '{"name": "snap0"}' http://localhost/api/shares/share0/snapshots/snap0/

echo "\nDeleting Share"
curl -X DELETE -H 'Content-Type: application/json' --data-binary '{"name": "share0", "pool": "pool0", "size": 10}' http://localhost/api/shares
echo "\nShares"
curl -X GET http://localhost/api/shares
echo "\nPools"
curl -X GET http://localhost/api/pools
echo "\nDeleting pool"
curl -X DELETE -H 'Content-Type: application/json' --data-binary '{"disks": "bla,bla", "name": "pool0", "raid_level": "raid0"}' http://localhost/api/pools
echo "\nPools"
curl -X GET http://localhost/api/pools
echo "\nDisks"
curl -X GET http://localhost/api/disks
echo "\nShares"
curl -X GET http://localhost/api/shares
echo ""
curl -X POST -H 'Content-Type: application/json' --data-binary '{"share": "share0", "name": "snap0"}' http://localhost/api/snapshots/
curl -X DELETE -H 'Content-Type: application/json' --data-binary '{"share": "share0", "name": "snap0"}' http://localhost/api/snapshots/
curl -X PUT -H 'Content-Type: application/json' --data-binary '{"disks": "sdd", "name": "pool1"}' http://localhost/api/pools/pool1/add/
curl -X PUT -H 'Content-Type: application/json' --data-binary '{"disks": "sdd", "name": "pool1"}' http://localhost/api/pools/pool1/remove/

curl -X PUT -H 'Content-Type: application/json' --data-binary '{"pool":
"pool1", "name": "share1", "size": 10, "mount": "/mnt2/share1", "host_str":
"example.com", "mod_choice": "rw", "sync_choice": "sync"}' http://localhost/api/shares/share1/nfs-export/

curl -X PUT -H 'Content-Type: application/json' --data-binary '{"name":
"share1"}' http://localhost/api/shares/share1/nfs-unexport/

curl -X PUT -H 'Content-Type: application/json' --data-binary '{"pool":
"pool1", "name": "share1", "size": 10, "mount": "/mnt2/share1", "browsable":
"yes"}' http://localhost/api/shares/share1/cifs-export/

curl -X PUT -H 'Content-Type: application/json' --data-binary '{"name":
"share1"}' http://localhost/api/shares/share1/cifs-unexport/