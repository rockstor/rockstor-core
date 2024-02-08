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

# Install Poetry via PIPX as a global app
# https://peps.python.org/pep-0668/#guide-users-towards-virtual-environments
# https://pipx.pypa.io/stable/installation/
export PIPX_HOME=/opt/pipx  # virtual environment location, default ~/.local/pipx
export PIPX_BIN_DIR=/usr/local/bin  # binary location for pipx-installed apps, default ~/.local/bin
export PIPX_MAN_DIR=/usr/local/share/man  # manual page location for pipx-installed apps, default ~/.local/share/man
# https://python-poetry.org/docs/#installing-with-pipx
pipx ensurepath
pipx install --python python3.11 poetry==1.7.1
# https://pypi.org/project/poetry-plugin-dotenv/
# https://python-poetry.org/docs/master/plugins/#using-plugins
pipx inject --verbose poetry poetry-plugin-dotenv==0.6.11
pipx list

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

# Add js libs. See: https://github.com/rockstor/rockstor-jslibs
# Set jslibs_version of GitHub release:
jslibs_version=5.0.7
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
echo "Sourcing ${pwd}.env"
source .env  # also read by rockstor-build.service
set +o allexport
/usr/bin/pass init rockstor@localhost
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
echo "3. Run './build.sh'."
echo "4. Run 'poetry run initrock' as root (equivalent to rockstor-pre.service ExecStart)."
echo "5. Run 'systemctl enable --now rockstor-bootstrap'."