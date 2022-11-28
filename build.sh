#!/bin/bash
# exit on error
set -o errexit

# Install Poetry, a dependency management, packaging, and build system.
# We currently require Python 2.7 compatibility which was last in v1.1.15.
# We use the official installer which installs to: ~/.local/share/pypoetry.
# The installer is python 3 only: https://python-poetry.org/docs/#installation
# N.B. there is no harm in re-running this installer.
curl -sSL https://install.python-poetry.org | POETRY_VERSION=1.1.15 python3 -

# Install project dependencies defined in cwd pyproject.toml using poetry.toml
# specific configuration, i.e. virtualenv in cwd/.venv
# /opt/rockstor/.venv
# poetry env remove --all  # removes all venvs associated with a pyproject.toml
# rm -rf ~/.cache/pypoetry/virtualenvs/*  # to delete default location venvs.
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
echo
echo "If installing from source, from scratch, for development:"
echo "1. Run 'cd /opt/rockstor"
echo "2. Run 'systemctl start postgresql'."
echo "3. Run 'export DJANGO_SETTINGS_MODULE=settings'."
echo "4. Run 'poetry run initrock' as root (equivalent to rockstor-pre.service)."
echo "5. Run 'systemctl start rockstor-bootstrap"