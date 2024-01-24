#!/bin/bash
# exit on error
set -o errexit
#
# Upgrade the database format from 10 to 13.
# Testing RPM version 5.0.6-0 updated to Django LTS 4.2 & psycopg3.
# These are no longer compatibility with databases created
# with Postgres version 10, i.e. installs originally created from:
# Rockstor-Leap15.3-generic.x86_64-4.1.0-0.install.iso Jan 14 2022
# or earlier.
# - RPM version 4.5.0-0 added a Postgresql V13 dependency.
# - RPM version 5.0.2-0 enforced Postgresql alternative to V13.
#
# Uses pg_upgrade https://www.postgresql.org/docs/13/pgupgrade.html
# Informed by:
# - https://en.opensuse.org/SDB:PostgreSQL#Upgrading_major_PostgreSQL_version
# - https://progress.opensuse.org/news/113
# ps aufx | grep '^postgres.* -D'
# V10: /usr/lib/postgresql10/bin/postgres -D /var/lib/pgsql/data
#
FROM_VERSION="$1"
TO_VERSION="$2"

if [ $# -ne 2 ]; then
    echo "This script upgrades the Rockstor Postgres database format."
    echo "It requires two integer numbers: the 'current' and 'target' DB formats."
    echo "Example: 10 13"
    exit 1
fi
# OpenSUSE postgres user home (~) is: /var/lib/pgsql/
# By default databases are created in the "data" subdirectory.
DATA_BASEDIR="/var/lib/pgsql"
# Get current database format version via PG_VERSION file.
if test -r $DATA_BASEDIR/data/PG_VERSION ; then
    CURRENT_DATA_VERSION=$(cat $DATA_BASEDIR/data/PG_VERSION)
else
  echo "No DB PG_VERSION file found."
  exit 0
fi

# Filter input parameter.
if [ "${CURRENT_DATA_VERSION}" -lt 10 ] ; then
  echo "DB format found is less than 10, this is not an official Rockstor DB format."
  exit 0
fi
if [ "${FROM_VERSION}" -lt 10 ] ; then
  echo "This script can only upgrade DB formats >=10."
  exit 0
fi
if [ "${CURRENT_DATA_VERSION}" == "${TO_VERSION}" ] ; then
  echo "Current DB format is already $TO_VERSION."
  exit 0
fi
if [ "${CURRENT_DATA_VERSION}" != "${FROM_VERSION}" ] ; then
  echo "Current DB format is $CURRENT_DATA_VERSION, This differs from expected format $FROM_VERSION entered."
  exit 0
fi

# Postgres binary directory paths, e.g.:
# 10: /usr/lib/postgresql10/bin/
# 13: /usr/lib/postgresql13/bin/
BIN_BASEDIR="/usr/lib/postgresql"

# Check for expected postgres server bin dir locations.
if ! test -e "${BIN_BASEDIR}${CURRENT_DATA_VERSION}/bin"; then
  echo "No Current postgresql${CURRENT_DATA_VERSION}-server install found: exiting."
  exit 0
fi
if ! test -e "${BIN_BASEDIR}${TO_VERSION}/bin"; then
  echo "No Target postgresql${TO_VERSION}-server install found: exiting."
  exit 0
fi
if ! test -e "${BIN_BASEDIR}${TO_VERSION}/bin/pg_upgrade"; then
  echo "No Target postgresql${TO_VERSION}-contrib install found: exiting."
  echo "Try 'zypper install --no-recommends postgresql${TO_VERSION}-contrib'"
  exit 0
fi

echo "Updating DB format from ${CURRENT_DATA_VERSION} to ${TO_VERSION} via pg_upgrade."

# Push onto dir stack our pwd and change to postgres user's home dir.
# (required as pg_upgrade creates files in pwd)
pushd /var/lib/pgsql

# Initialise TO_VERSION database in "${DATA_BASEDIR}/data${TO_VERSION}" directory.
# install -d -m 0700 -o postgres -g postgres "${DATA_BASEDIR}/data${TO_VERSION}"
# initdb creates the --pgdata directory with its preferred rights if it does not exist.
# initdb: https://www.postgresql.org/docs/13/app-initdb.html
# encoding: https://docs.djangoproject.com/en/4.2/ref/databases/#encoding
# --locale= OS available options via `locale -a`
# Establish LANG from install.
source /etc/locale.conf
echo
echo "Adopting installs' LANG=${LANG}"
sudo -u postgres "${BIN_BASEDIR}${TO_VERSION}/bin/initdb" --encoding=UTF8 --pgdata="${DATA_BASEDIR}/data${TO_VERSION}"

# Stop Postgres - may fail from within another systemd service.
echo "Stopping postgresql"
systemctl stop postgresql.service

# Move default 'data' dir DB to version-specific dir:
echo
echo "mv ${DATA_BASEDIR}/data ${DATA_BASEDIR}/data${CURRENT_DATA_VERSION}"
mv ${DATA_BASEDIR}/data ${DATA_BASEDIR}/data"${CURRENT_DATA_VERSION}"

echo
sudo -u postgres pg_upgrade \
     --old-bindir="${BIN_BASEDIR}${CURRENT_DATA_VERSION}/bin"     \
     --new-bindir="${BIN_BASEDIR}${TO_VERSION}/bin"       \
     --old-datadir="${DATA_BASEDIR}/data${CURRENT_DATA_VERSION}/" \
     --new-datadir="${DATA_BASEDIR}/data${TO_VERSION}/"
echo
echo "Linking data -> data${TO_VERSION}"
# Restore default 'data' dir as symlink to the /data${TO_VERSION}
# e.g. lrwxrwxrwx 1 postgres postgres ... data -> data13
sudo -u postgres ln --force --symbolic data"${TO_VERSION}" data

# Remove old database (approximately 80-100MB)
# rm -rf "${DATA_BASEDIR}/data${CURRENT_DATA_VERSION}/"

# Start Postgres to enable vacuumdb & reindexdb operations.
echo
echo "Starting postgresql"
systemctl start postgresql.service

# Vacuum & reindex new DB as per pg_upgrade recommendation:
echo
sudo -u postgres ${BIN_BASEDIR}"${TO_VERSION}"/bin/vacuumdb --all --analyze-in-stages
# https://www.postgresql.org/docs/13/app-reindexdb.html
# `--concurrently` slower but allows for concurrent user.
echo
sudo -u postgres ${BIN_BASEDIR}"${TO_VERSION}"/bin/reindexdb --all

# Restore our prior pwd.
echo
echo "Restoring pior pwd"
popd

echo
echo "All Rockstor services, if running, will have been stopped."
echo "Restart via 'systemctl start rockstor-bootstrap.service'"

# ps aufx | grep '^postgres.* -D'
# V13: /usr/lib/postgresql13/bin/postgres -D /var/lib/pgsql/data

