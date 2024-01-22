#!/bin/bash
# exit on error
set -o errexit

# Install Poetry, a dependency management, packaging, and build system.
# Uninstall legacy/transitional Poetry version of 1.1.15
PATH="$HOME/.local/bin:$PATH"  # account for more constrained environments.
if which poetry && poetry --version | grep -q "1.1.15"; then
  echo "Poetry version 1.1.15 found - UNINSTALLING"
  curl -sSL https://install.python-poetry.org | python3 - --uninstall
  rm --force /root/.local/bin/poetry  # remove dangling dead link.
  # bash substring replace with "" our legacy poetry path.
  PATH="${PATH//':/root/.local/bin'/''}"
fi
# Install Poetry via PIPX as a global app
# https://peps.python.org/pep-0668/#guide-users-towards-virtual-environments
export PIPX_HOME=/opt/pipx  # virtual environment location, default ~/.local/pipx
export PIPX_BIN_DIR=/usr/local/bin  # binary location for pipx-installed apps, default ~/.local/bin
python3.11 -m pipx install poetry==1.7.1

# Install project dependencies defined in cwd pyproject.toml using poetry.toml
# specific configuration, i.e. virtualenv in cwd/.venv
# /opt/rockstor/.venv
# poetry env remove --all  # removes all venvs associated with a pyproject.toml
# rm -rf ~/.cache/pypoetry/virtualenvs/*  # to delete default location venvs.
# ** --no-ansi avoids special characters **
# Resolve Python 3.6 Poetry issue re char \u2022: (bullet)
# https://github.com/python-poetry/poetry/issues/3078
export LANG=C.UTF-8
export PYTHONIOENCODING=utf8
/usr/local/bin/poetry install --no-interaction --no-ansi > poetry-install.txt 2>&1
echo

# Add js libs. See: https://github.com/rockstor/rockstor-jslibs
# Set jslibs_version of GitHub release:
jslibs_version=5.0.6
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
# Init 'pass' in ~ using above GPG key, and generate Django SECRET_KEY
export Environment="PASSWORD_STORE_DIR=/root/.password-store"
/usr/bin/pass init rockstor@localhost
/usr/bin/pass generate --no-symbols --force python-keyring/rockstor/SECRET_KEY 100

# Collect all static files in the STATIC_ROOT subdirectory. See settings.py.
# /opt/rockstor/static
# Additional collectstatic options --clear --dry-run
export DJANGO_SETTINGS_MODULE=settings
# must be run in project root:
/usr/local/bin/poetry run django-admin collectstatic --no-input --verbosity 2
echo

echo "ROCKSTOR BUILD SCRIPT COMPLETED"
echo
echo "If installing from source, from scratch, for development; i.e. NOT via RPM:"
echo "Note GnuPG & password-store ExecStartPre steps in /opt/rockstor/conf/rockstor-pre.service"
echo "1. Run 'cd /opt/rockstor'."
echo "2. Run 'systemctl start postgresql'."
echo "3. Run 'export DJANGO_SETTINGS_MODULE=settings'."
echo "4. Run 'export PASSWORD_STORE_DIR=/root/.password-store'."
echo "5. Run 'poetry run initrock' as root (equivalent to rockstor-pre.service ExecStart)."
echo "6. Run 'systemctl enable --now rockstor-bootstrap'."