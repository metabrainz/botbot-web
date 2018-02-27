# Developer Makefile

### Default Configuration.  Override in a make.config file

VIRTUAL_ENV = $(pipenv --venv)

# where executables are stored
LOCAL_BIN=$(VIRTUAL_ENV)/bin

# where misc files are stored
LOCAL_VAR=$(VIRTUAL_ENV)/var

# This doesn't seem to work in venvs and will always result in Node.js being downloaded and compiled.
NPM_BIN := $(or $(shell command -v npm),$(LOCAL_BIN)/npm)
LESS_BIN := $(or $(shell command -v lessc),$(LOCAL_BIN)/lessc)
JSHINT_BIN := $(or $(shell command -v jshint),$(LOCAL_BIN)/jshint)
WATCHMEDO_BIN := $(or $(shell command -v watchmedo),$(LOCAL_BIN)/watchmedo)

# allows a file make.config to override the above variables
-include make.config


$(LOCAL_BIN)/sphinx-build:
	pip install Sphinx

### GENERAL PYTHON COMMANDS
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

### GO SUPPORT

$(LOCAL_BIN)/brainzbot-bot:
	go get github.com/metabrainz/brainzbot-bot

test-bot:
	go test github.com/metabrainz/brainzbot-bot

### LOCAL LESS SUPPORT
$(NPM_BIN):
	$(error Couldn't find npm, please install Node.js and npm.)

$(LESS_BIN): $(NPM_BIN)
	npm install "less@<1.4" -g

less-install: $(LESS_BIN)

less-compile:
	lessc botbot/less/screen.less > botbot/static/css/screen.css
	lessc botbot/less/home.less > botbot/static/css/home.css

$(WATCHMEDO_BIN):
	# Install watchdog to run commands when files change
	pip install watchdog argcomplete

less-watch: $(WATCHMEDO_BIN)
	watchmedo shell-command --patterns=*.less --recursive --command="make less-compile" botbot/less


### Local JSHint

$(JSHINT_BIN): $(NPM_BIN)
	npm install jshint -g

jshint-install: $(JSHINT_BIN)

jshint:
	jshint botbot/static/js/app/

### Local Settings

local-settings:
	cp .env.example .env

### General Tasks
dependencies: local-settings less-install $(LOCAL_BIN)/brainzbot-bot

$(LOCAL_VAR)/GeoLite2-City.mmdb:
	curl http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz | gunzip -c > $@

geoip-db: $(LOCAL_VAR)/GeoLite2-City.mmdb

run: dependencies
	honcho start

docs: $(LOCAL_BIN)/sphinx-build
	cd docs && make html

.PHONY: clean-pyc run less-install jshint-install dependencies local-settings docs geoip-db
