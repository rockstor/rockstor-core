#!/bin/bash
set -e
set -u
#set -x

export VAGRANT_EXPERIMENTAL="disks"
VAGRANT_HOST="rockstor-${1:-core}"

if ! vagrant status ${VAGRANT_HOST} | grep -q running; then
  vagrant up ${VAGRANT_HOST}
fi
# We are rsync'ing the build directory and it needs to be refreshed with changes.
# (Note: this will also delete the build artifacts - effectively forcing a clean build.
vagrant rsync ${VAGRANT_HOST}

VAGRANT_PATH="/opt/rockstor-core"
#vagrant ssh -c "ls -l ${VAGRANT_PATH}" ${VAGRANT_HOST}

CODE_PATH="${VAGRANT_PATH}"
echo "$(basename ${BASH_SOURCE[0]}): CODE_PATH is '${CODE_PATH}'"

vagrant ssh -c "cd ${VAGRANT_PATH}; sudo /vagrant/build_rockstor.sh" ${VAGRANT_HOST}