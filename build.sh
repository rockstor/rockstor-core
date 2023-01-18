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
# ** --no-ansi avoids special characters **
PATH="$HOME/.local/bin:$PATH"
# Resolve Python 3.6 Poetry issue re char \u2022: (bullet)
# https://github.com/python-poetry/poetry/issues/3078
export LANG=C.UTF-8
export PYTHONIOENCODING=utf8
/root/.local/bin/poetry install --no-interaction --no-ansi > poetry-install.txt 2>&1
echo

# Add js libs. See: https://github.com/rockstor/rockstor-jslibs
# Set jslibs_version of GitHub release:
jslibs_version=4.5.5
jslibs_url=https://github.com/rockstor/rockstor-jslibs/archive/refs/tags/"${jslibs_version}".tar.gz

#  Check for rpm embedded, or previously downloaded jslibs.
if [ ! -f  "rockstor-jslibs.tar.gz.sha256sum" ]; then
    echo "Getting rockstor-jslibs version ${jslibs_version}"
    wget -O rockstor-jslibs.tar.gz "${jslibs_url}"
    sha256sum rockstor-jslibs.tar.gz > rockstor-jslibs.tar.gz.sha256sum
    echo
else  # Check rpm embedded, or previously downloaded jslibs are unchanged.
    if ! sha256sum --check --status rockstor-jslibs.tar.gz.sha256sum; then
      echo "rockstor-jslibs checksum failed. Exiting"
      exit
    fi
fi

if [ ! -d "jslibs" ]; then
  # See: STATICFILES_DIRS in settings.py
  echo "Creating jslibs/js/lib & populating from rockstor-jslibs.tar.gz"
  echo
  mkdir -p jslibs/js/lib
  # GitHub versioned archives have rockstor-jslibs-{jslibs_version} top directory,
  # i.e. rockstor-jslibs-#.#.#, we strip this single top directory.
  tar zxvf rockstor-jslibs.tar.gz --directory jslibs/js/lib --strip-components=1
  echo
fi

# Collect all static files in the STATIC_ROOT subdirectory. See settings.py.
# /opt/rockstor/static
# Additional collectstatic options --clear --dry-run
export DJANGO_SETTINGS_MODULE=settings
# must be run in project root:
/root/.local/bin/poetry run django-admin collectstatic --no-input --verbosity 2
echo

echo "ROCKSTOR BUILD SCRIPT COMPLETED"
echo
echo "If installing from source, from scratch, for development:"
echo "1. Run 'cd /opt/rockstor'."
echo "2. Run 'systemctl start postgresql'."
echo "3. Run 'export DJANGO_SETTINGS_MODULE=settings'."
echo "4. Run 'poetry run initrock' as root (equivalent to rockstor-pre.service)."
echo "5. Run 'systemctl enable --now rockstor-bootstrap'."