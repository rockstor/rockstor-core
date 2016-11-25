# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'NFSDShareDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_commit', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_remove', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'sum_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'sum_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_lookup', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_create', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_commit', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_remove', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'sum_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'sum_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_lookup', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_create', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.swap_free'
        db.alter_column(u'smart_manager_meminfo', 'swap_free', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.cached'
        db.alter_column(u'smart_manager_meminfo', 'cached', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.free'
        db.alter_column(u'smart_manager_meminfo', 'free', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.swap_total'
        db.alter_column(u'smart_manager_meminfo', 'swap_total', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.inactive'
        db.alter_column(u'smart_manager_meminfo', 'inactive', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.dirty'
        db.alter_column(u'smart_manager_meminfo', 'dirty', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.active'
        db.alter_column(u'smart_manager_meminfo', 'active', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.total'
        db.alter_column(u'smart_manager_meminfo', 'total', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'MemInfo.buffers'
        db.alter_column(u'smart_manager_meminfo', 'buffers', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'ServiceStatus.count'
        db.alter_column(u'smart_manager_servicestatus', 'count', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_commit', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_remove', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'sum_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_read'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'sum_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_lookup', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_create'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_create', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_write'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'PoolUsage.usage'
        db.alter_column(u'smart_manager_poolusage', 'usage', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'PoolUsage.count'
        db.alter_column(u'smart_manager_poolusage', 'count', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_commit', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_remove', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'sum_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'sum_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_lookup', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDCallDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_create', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_commit', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_remove', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'sum_write', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'sum_read', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_lookup', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NFSDClientDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_create', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.errs_tx'
        db.alter_column(u'smart_manager_netstat', 'errs_tx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.compressed_tx'
        db.alter_column(u'smart_manager_netstat', 'compressed_tx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.compressed_rx'
        db.alter_column(u'smart_manager_netstat', 'compressed_rx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.drop_rx'
        db.alter_column(u'smart_manager_netstat', 'drop_rx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.fifo_rx'
        db.alter_column(u'smart_manager_netstat', 'fifo_rx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.carrier'
        db.alter_column(u'smart_manager_netstat', 'carrier', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.colls'
        db.alter_column(u'smart_manager_netstat', 'colls', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.multicast_rx'
        db.alter_column(u'smart_manager_netstat', 'multicast_rx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.packets_tx'
        db.alter_column(u'smart_manager_netstat', 'packets_tx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.drop_tx'
        db.alter_column(u'smart_manager_netstat', 'drop_tx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.fifo_tx'
        db.alter_column(u'smart_manager_netstat', 'fifo_tx', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'NetStat.frame'
        db.alter_column(u'smart_manager_netstat', 'frame', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'VmStat.free_pages'
        db.alter_column(u'smart_manager_vmstat', 'free_pages', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'ReceiveTrail.kb_received'
        db.alter_column(u'smart_manager_receivetrail', 'kb_received', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'ShareUsage.count'
        db.alter_column(u'smart_manager_shareusage', 'count', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'ShareUsage.r_usage'
        db.alter_column(u'smart_manager_shareusage', 'r_usage', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'ShareUsage.e_usage'
        db.alter_column(u'smart_manager_shareusage', 'e_usage', self.gf('django.db.models.fields.BigIntegerField')())

        # Changing field 'ReplicaTrail.kb_sent'
        db.alter_column(u'smart_manager_replicatrail', 'kb_sent', self.gf('django.db.models.fields.BigIntegerField')())

    def backwards(self, orm):

        # Changing field 'NFSDShareDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_commit', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_remove', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'sum_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'sum_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_lookup', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdsharedistribution', 'num_create', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_commit', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_remove', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'sum_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'sum_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_lookup', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDShareClientDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdshareclientdistribution', 'num_create', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.swap_free'
        db.alter_column(u'smart_manager_meminfo', 'swap_free', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.cached'
        db.alter_column(u'smart_manager_meminfo', 'cached', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.free'
        db.alter_column(u'smart_manager_meminfo', 'free', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.swap_total'
        db.alter_column(u'smart_manager_meminfo', 'swap_total', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.inactive'
        db.alter_column(u'smart_manager_meminfo', 'inactive', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.dirty'
        db.alter_column(u'smart_manager_meminfo', 'dirty', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.active'
        db.alter_column(u'smart_manager_meminfo', 'active', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.total'
        db.alter_column(u'smart_manager_meminfo', 'total', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'MemInfo.buffers'
        db.alter_column(u'smart_manager_meminfo', 'buffers', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'ServiceStatus.count'
        db.alter_column(u'smart_manager_servicestatus', 'count', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_commit', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_remove', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'sum_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_read'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'sum_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_lookup', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_create'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_create', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDUidGidDistribution.num_write'
        db.alter_column(u'smart_manager_nfsduidgiddistribution', 'num_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'PoolUsage.usage'
        db.alter_column(u'smart_manager_poolusage', 'usage', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'PoolUsage.count'
        db.alter_column(u'smart_manager_poolusage', 'count', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_commit', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_remove', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'sum_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'sum_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_lookup', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDCallDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdcalldistribution', 'num_create', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.num_write'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.num_commit'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_commit', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.num_remove'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_remove', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.sum_write'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'sum_write', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.num_read'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.sum_read'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'sum_read', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.num_lookup'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_lookup', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NFSDClientDistribution.num_create'
        db.alter_column(u'smart_manager_nfsdclientdistribution', 'num_create', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.errs_tx'
        db.alter_column(u'smart_manager_netstat', 'errs_tx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.compressed_tx'
        db.alter_column(u'smart_manager_netstat', 'compressed_tx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.compressed_rx'
        db.alter_column(u'smart_manager_netstat', 'compressed_rx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.drop_rx'
        db.alter_column(u'smart_manager_netstat', 'drop_rx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.fifo_rx'
        db.alter_column(u'smart_manager_netstat', 'fifo_rx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.carrier'
        db.alter_column(u'smart_manager_netstat', 'carrier', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.colls'
        db.alter_column(u'smart_manager_netstat', 'colls', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.multicast_rx'
        db.alter_column(u'smart_manager_netstat', 'multicast_rx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.packets_tx'
        db.alter_column(u'smart_manager_netstat', 'packets_tx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.drop_tx'
        db.alter_column(u'smart_manager_netstat', 'drop_tx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.fifo_tx'
        db.alter_column(u'smart_manager_netstat', 'fifo_tx', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'NetStat.frame'
        db.alter_column(u'smart_manager_netstat', 'frame', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'VmStat.free_pages'
        db.alter_column(u'smart_manager_vmstat', 'free_pages', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'ReceiveTrail.kb_received'
        db.alter_column(u'smart_manager_receivetrail', 'kb_received', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'ShareUsage.count'
        db.alter_column(u'smart_manager_shareusage', 'count', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'ShareUsage.r_usage'
        db.alter_column(u'smart_manager_shareusage', 'r_usage', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'ShareUsage.e_usage'
        db.alter_column(u'smart_manager_shareusage', 'e_usage', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'ReplicaTrail.kb_sent'
        db.alter_column(u'smart_manager_replicatrail', 'kb_sent', self.gf('django.db.models.fields.IntegerField')())

    models = {
        'smart_manager.cpumetric': {
            'Meta': {'object_name': 'CPUMetric'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'smode': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'umode': ('django.db.models.fields.IntegerField', [], {}),
            'umode_nice': ('django.db.models.fields.IntegerField', [], {})
        },
        'smart_manager.diskstat': {
            'Meta': {'object_name': 'DiskStat'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ios_progress': ('django.db.models.fields.FloatField', [], {}),
            'ms_ios': ('django.db.models.fields.FloatField', [], {}),
            'ms_reading': ('django.db.models.fields.FloatField', [], {}),
            'ms_writing': ('django.db.models.fields.FloatField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'reads_completed': ('django.db.models.fields.FloatField', [], {}),
            'reads_merged': ('django.db.models.fields.FloatField', [], {}),
            'sectors_read': ('django.db.models.fields.FloatField', [], {}),
            'sectors_written': ('django.db.models.fields.FloatField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'weighted_ios': ('django.db.models.fields.FloatField', [], {}),
            'writes_completed': ('django.db.models.fields.FloatField', [], {}),
            'writes_merged': ('django.db.models.fields.FloatField', [], {})
        },
        'smart_manager.loadavg': {
            'Meta': {'object_name': 'LoadAvg'},
            'active_threads': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idle_seconds': ('django.db.models.fields.IntegerField', [], {}),
            'latest_pid': ('django.db.models.fields.IntegerField', [], {}),
            'load_1': ('django.db.models.fields.FloatField', [], {}),
            'load_15': ('django.db.models.fields.FloatField', [], {}),
            'load_5': ('django.db.models.fields.FloatField', [], {}),
            'total_threads': ('django.db.models.fields.IntegerField', [], {}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.meminfo': {
            'Meta': {'object_name': 'MemInfo'},
            'active': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'buffers': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'cached': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'dirty': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'free': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inactive': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'swap_free': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'swap_total': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'total': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.netstat': {
            'Meta': {'object_name': 'NetStat'},
            'carrier': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'colls': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'compressed_rx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'compressed_tx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'device': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'drop_rx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'drop_tx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'errs_rx': ('django.db.models.fields.FloatField', [], {}),
            'errs_tx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'fifo_rx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'fifo_tx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'frame': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_rx': ('django.db.models.fields.FloatField', [], {}),
            'kb_tx': ('django.db.models.fields.FloatField', [], {}),
            'multicast_rx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'packets_rx': ('django.db.models.fields.FloatField', [], {}),
            'packets_tx': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsdcalldistribution': {
            'Meta': {'object_name': 'NFSDCallDistribution'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_create': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_lookup': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_remove': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'sum_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sum_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsdclientdistribution': {
            'Meta': {'object_name': 'NFSDClientDistribution'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'num_commit': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_create': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_lookup': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_remove': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'sum_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sum_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {})
        },
        'smart_manager.nfsdshareclientdistribution': {
            'Meta': {'object_name': 'NFSDShareClientDistribution'},
            'client': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_create': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_lookup': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_remove': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sum_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sum_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsdsharedistribution': {
            'Meta': {'object_name': 'NFSDShareDistribution'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_create': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_lookup': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_remove': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sum_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sum_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.nfsduidgiddistribution': {
            'Meta': {'object_name': 'NFSDUidGidDistribution'},
            'client': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'gid': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_commit': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_create': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_lookup': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_remove': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'num_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.SProbe']"}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sum_read': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sum_write': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'uid': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'smart_manager.poolusage': {
            'Meta': {'object_name': 'PoolUsage'},
            'count': ('django.db.models.fields.BigIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'usage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'})
        },
        'smart_manager.receivetrail': {
            'Meta': {'object_name': 'ReceiveTrail'},
            'end_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_received': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'receive_failed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'receive_pending': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'receive_succeeded': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'rshare': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.ReplicaShare']"}),
            'snap_name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'smart_manager.replica': {
            'Meta': {'object_name': 'Replica'},
            'appliance': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'data_port': ('django.db.models.fields.IntegerField', [], {'default': '10002'}),
            'dpool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'dshare': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_port': ('django.db.models.fields.IntegerField', [], {'default': '10003'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'share': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'task_name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        },
        'smart_manager.replicashare': {
            'Meta': {'object_name': 'ReplicaShare'},
            'appliance': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'data_port': ('django.db.models.fields.IntegerField', [], {'default': '10002'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_port': ('django.db.models.fields.IntegerField', [], {'default': '10003'}),
            'pool': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'share': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4096'}),
            'src_share': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'})
        },
        'smart_manager.replicatrail': {
            'Meta': {'object_name': 'ReplicaTrail'},
            'end_ts': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'error': ('django.db.models.fields.CharField', [], {'max_length': '4096', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kb_sent': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'replica': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.Replica']"}),
            'send_failed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'send_pending': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'send_succeeded': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'snap_name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'snapshot_created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'snapshot_failed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'smart_manager.service': {
            'Meta': {'object_name': 'Service'},
            'config': ('django.db.models.fields.CharField', [], {'max_length': '8192', 'null': 'True'}),
            'display_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24'})
        },
        'smart_manager.servicestatus': {
            'Meta': {'object_name': 'ServiceStatus'},
            'count': ('django.db.models.fields.BigIntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'service': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.Service']"}),
            'status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.shareusage': {
            'Meta': {'object_name': 'ShareUsage'},
            'count': ('django.db.models.fields.BigIntegerField', [], {'default': '1'}),
            'e_usage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'r_usage': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        'smart_manager.sprobe': {
            'Meta': {'object_name': 'SProbe'},
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'smart': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '7'})
        },
        'smart_manager.task': {
            'Meta': {'object_name': 'Task'},
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'task_def': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['smart_manager.TaskDefinition']"})
        },
        'smart_manager.taskdefinition': {
            'Meta': {'object_name': 'TaskDefinition'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json_meta': ('django.db.models.fields.CharField', [], {'max_length': '8192'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'task_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'smart_manager.vmstat': {
            'Meta': {'object_name': 'VmStat'},
            'free_pages': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['smart_manager']