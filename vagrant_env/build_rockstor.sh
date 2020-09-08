#!/bin/bash
set -e
set -u
#set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

shopt -s expand_aliases
source ${SCRIPT_DIR}/alias_rc

REPO_DIR="/opt/rockstor-core/"

cd "${REPO_DIR}"

if [ ! -e "${PWD}"/bin/buildout ]; then
  echo '============================================='
  echo 'Cleaning Build'
  echo '============================================='
  build_init
fi
echo '============================================='
echo 'Starting Build'
echo '============================================='
build_all

if ! grep -q "vagrant" /etc/ssh/sshd_config
then
  echo "Re-enable 'vagrant' ssh access (removed by Rockstor install)"
  sed -i 's/^.*\(AllowUsers root\)\(.*\)/\1 vagrant \2/' /etc/ssh/sshd_config
fi
echo '============================================='
echo 'Finished Build'
echo '============================================='
