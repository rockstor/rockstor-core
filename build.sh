#!/bin/bash
# exit on error
set -o errexit

# Install all dependencies defined in cwd pyproject.toml using poetry.toml
# specific configuration, i.e. virtualenv in cwd/.venv
# /opt/rockstor/.venv
poetry install
echo

# Add js libs. See: https://github.com/rockstor/rockstor-jslibs
## Production jslibs
jslibs_url=https://rockstor.com/downloads/jslibs/rockstor-jslibs.tar.gz
## Development jslibs
# jslibs_url=https://rockstor.com/downloads/jslibs-dev/rockstor-jslibs.tar.gz

if [ ! -f  "rockstor-jslibs.tar.gz.sha256sum" ]; then
    echo "Getting latest rockstor-jslibs and checksum files"
    wget -O rockstor-jslibs.tar.gz.sha256sum "${jslibs_url}.sha256sum"
    wget -O rockstor-jslibs.tar.gz "${jslibs_url}"
    echo
fi

if ! sha256sum --check --status rockstor-jslibs.tar.gz.sha256sum; then
    echo "rockstor-jslibs checksum failed. Exiting"
    exit
fi

if [ ! -d "jslibs" ]; then
  # See: STATICFILES_DIRS in settings.py
  echo "Creating jslibs/js & populating 'lib' subdir from rockstor-jslibs.tar.gz"
  mkdir -p jslibs/js
  tar zxvf rockstor-jslibs.tar.gz --directory jslibs/js  #archive has /lib dir.
  echo
fi

# Collect all static files in the STATIC_ROOT subdirectory. See settings.py.
# /opt/rockstor/static
# Additional collectstatic options --clear --dry-run
export DJANGO_SETTINGS_MODULE=settings
# must be run in project root:
poetry run django-admin collectstatic --no-input --verbosity 2
echo

echo "ROCKSTOR BUILD SCRIPT COMPLETED"