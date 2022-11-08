/*
Informed by using Online PGTune https://pgtune.leopard.in.ua/
Resulting configuration is saved to /var/lib/pgsql/data/postgresql.auto.conf
Applied by initrock via its systemd rockstor-pre.servcie
#
# Parameters used in above online resource
# DB Version: 11 (max available)
# OS Type: linux
# DB Type: desktop
# Total Memory (RAM): 2 GB
# CPUs num: 2
# Connections num: 100
# Data Storage: ssd
#
wal_buffers & max_worker_processes require a server restart
 */

ALTER SYSTEM SET
 max_connections = '100';
ALTER SYSTEM SET
 shared_buffers = '128MB';
ALTER SYSTEM SET
 effective_cache_size = '512MB';
ALTER SYSTEM SET
 maintenance_work_mem = '128MB';
ALTER SYSTEM SET
 checkpoint_completion_target = '0.5';
-- ALTER SYSTEM SET
--  wal_buffers = '3932kB';  -- requires server restart
ALTER SYSTEM SET
 default_statistics_target = '100';
ALTER SYSTEM SET
 random_page_cost = '1.1';
ALTER SYSTEM SET
 effective_io_concurrency = '200';
ALTER SYSTEM SET
 work_mem = '1092kB';
ALTER SYSTEM SET
 min_wal_size = '100MB';
ALTER SYSTEM SET
 max_wal_size = '1GB';
-- ALTER SYSTEM SET
--  max_worker_processes = '2'; -- requires server restart
ALTER SYSTEM SET
 max_parallel_workers_per_gather = '1';
ALTER SYSTEM SET
 max_parallel_workers = '2';
ALTER SYSTEM SET
 password_encryption = 'scram-sha-256';
select pg_reload_conf();
