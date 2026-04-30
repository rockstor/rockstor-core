#!/bin/bash
# exit on error
set -o errexit

# Install Poetry, a dependency management, packaging, and build system.
# Uninstall legacy/transitional Poetry version of 1.1.15
PATH="/root/.local/bin:$PATH"  # ensure legacy path.
if which poetry && poetry --version | grep -q "1.1.15"; then
  echo "Poetry version 1.1.15 found - UNINSTALLING"
  curl -sSL https://install.python-poetry.org | python3 - --uninstall
  rm --force /root/.local/bin/poetry  # remove dangling dead link.
fi
PATH="${PATH//'/root/.local/bin:'/''}" # null all legacy poetry paths
# We are run by rockstor-build.service.
# As such our .venv dir has already been removed in %post (update mode).
echo "Unset VIRTUAL_ENV"
# Redundant when updating from rockstor 5.0.3-0 onwards: src/rockstor/system/pkg_mgmt.py
unset VIRTUAL_ENV
PATH="${PATH//'/opt/rockstor/.venv/bin:'/''}" # null now removed .venv from path.

echo "build.sh has PATH=$PATH"
echo
# Establish LANG from install.
source /etc/locale.conf
echo "Adopting installs' LANG=${LANG}"

# Default host python
DEFAULT_HOST_PYTHON="python3.13"
# Set `Poetry install python ..." version:
STANDALONE_PYTHON_VERSION="3.13"

# TODO this conditional is to be removed once we no-longer build for Leap 15.6.
# Establish OS Python version to host Poetry, via `lsb-release -r`,
# enables holding back to Py3.11 for Leap 15.6.
# e.g. "Release:        15.6" to "15.6" via:
if [ $(lsb-release -r | sed 's/Release:[[:space:]]*//') == "15.6" ]; then  # Leap 15.6 only:
  POETRY_HOST_PYTHON="python3.11"
else
  POETRY_HOST_PYTHON=${DEFAULT_HOST_PYTHON}
fi
echo "Using ${POETRY_HOST_PYTHON} as Poetry host."

# Install Poetry via PIPX as a global app
# https://peps.python.org/pep-0668/#guide-users-towards-virtual-environments
# https://pipx.pypa.io/stable/installation/
export PIPX_HOME=/opt/pipx  # virtual environment location, default ~/.local/pipx
export PIPX_BIN_DIR=/usr/local/bin  # binary location for pipx-installed apps, default ~/.local/bin
export PIPX_MAN_DIR=/usr/local/share/man  # manual page location for pipx-installed apps, default ~/.local/share/man
# https://python-poetry.org/docs/#installing-with-pipx
pipx ensurepath
# Remove any prior pipx installed poetry, and all plugins: || true as RC=1 if no poetry found.
pipx uninstall poetry || true
# Install to enable --python changes and poetry version changes without the problematic --force.
pipx install --python ${POETRY_HOST_PYTHON} poetry==2.3.4
# Poetry's own venv maintenance: https://python-poetry.org/docs/cli/#self-sync
# The following sync also removes all plugins (e.g. legacy poetry-plugin-export),
# and updates /root/.config/pypoetry/poetry.lock accordingly.
# However we use pipx to maintainer our poetry and uninstall/reinstall to permit updating the host python
# poetry self sync > poetry-self-sync.txt
# https://pypi.org/project/poetry-plugin-dotenv/
# https://python-poetry.org/docs/master/plugins/#using-plugins
pipx inject --verbose poetry poetry-plugin-dotenv==3.3.0
pipx list

# Establish Poetry managed standalone python (around 100 MB per version)
# Capture list of options, both System (OS) and Poetry Managed (/root/.local/share/pypoetry/python/...)
# poetry python list -m  # for installed managed version.
poetry python list --no-ansi > poetry-python.txt
# python install returns 1 if version is already installed, so "... || true".
poetry python install -vvv --no-interaction --no-ansi ${STANDALONE_PYTHON_VERSION} >> poetry-python.txt || true
# poetry python remove --no-interaction 3.11.15   # to be added once we move to a newer standalone python version.

# Install project dependencies defined in cwd pyproject.toml using poetry.toml
# specific configuration, i.e. virtualenv in cwd/.venv
# /opt/rockstor/.venv
# poetry env remove --all  # removes all venvs associated with a pyproject.toml
# rm -rf ~/.cache/pypoetry/virtualenvs/*  # to delete default location venvs.
# ** --no-ansi avoids special characters **
env > poetry-install.txt
poetry --version >> poetry-install.txt
poetry self show plugins >> poetry-install.txt
# /usr/local/bin/poetry -> /opt/pipx/venvs/poetry
poetry install -vvv --no-interaction --no-ansi >> poetry-install.txt 2>&1
echo

# Source package version from pyproject.toml's (version = "5.0.14") via `poetry version` output:
# e.g. "rockstor 5.0.14"
ROCKSTOR_VERSION=$(poetry version | sed 's/rockstor //')

# Add js libs. See: https://github.com/rockstor/rockstor-jslibs
# Set jslibs_version of GitHub release:
jslibs_version=$ROCKSTOR_VERSION
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

# Ensure GNUPG is setup for 'pass' (Idempotent)
/usr/bin/gpg --quick-generate-key --batch --passphrase '' rockstor@localhost || true
# Init 'pass' in .env defined PASSWORD_STORE_DIR using above GPG key, and generate Django SECRET_KEY
set -o allexport
echo "Sourcing $(pwd)/.env"
source $(pwd)/.env  # also read by rockstor-build.service via "EnvironmentFile=/opt/rockstor/.env"
set +o allexport
# Ensure password-store is initialized:
/usr/bin/pass init rockstor@localhost || true
/usr/bin/pass generate --no-symbols --force python-keyring/rockstor/SECRET_KEY 100

# Collect all static files in the STATIC_ROOT subdirectory. See settings.py.
# /opt/rockstor/static
# Additional collectstatic options --clear --dry-run
# must be run in project root:
poetry run django-admin collectstatic --no-input --verbosity 2
echo

echo "ROCKSTOR BUILD SCRIPT COMPLETED"
echo
echo "If installing from source, from scratch, for development; i.e. NOT via RPM:"
echo "Note GnuPG & password-store ExecStartPre steps in /opt/rockstor/conf/rockstor-pre.service"
echo "1. Run 'systemctl start postgresql'."
echo "2. Run 'cd /opt/rockstor'."
echo "3. Run 'sh ./build.sh'."
echo "4. Run 'poetry run initrock' as root (equivalent to rockstor-pre.service ExecStart)."
echo "5. Run 'systemctl enable --now rockstor-bootstrap'."