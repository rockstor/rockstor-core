#!/bin/bash
set -e
set -u
#set -x

export VAGRANT_EXPERIMENTAL="disks"

VAGRANT_HOST="rockstor-core"

if ! vagrant status | grep -q running; then
  vagrant up ${VAGRANT_HOST}
fi
# We are rsync'ing the build directory and it needs to be refreshed with changes.
# (Note: this will also delete the build artifacts - effectively forcing a clean build.
vagrant rsync

VAGRANT_PATH="/root"
#vagrant ssh -c "ls -l ${VAGRANT_PATH}" ${VAGRANT_HOST}

CODE_PATH="${VAGRANT_PATH}"
echo "$(basename ${BASH_SOURCE[0]}): CODE_PATH is '${CODE_PATH}'"

vagrant ssh -c "sudo /vagrant/build_rockstor.sh" ${VAGRANT_HOST}