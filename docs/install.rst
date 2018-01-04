==================
Development setup
==================

Pre-requisites
---------------

Some of the suggested commands that follow may require root privileges on your system.

Python
~~~~~~~

* Python 2.7
* Pipenv (To install pipenv for your user, run ``pip install --user pipenv``.)

Go
~~

Version 1.2 or higher required

* **OS X**: ``brew install go``
* **Ubuntu**: ``apt-get install golang-go``

PostgreSQL and Redis
~~~~~~~~~~~~~~~~~~~~

We recommend you use Docker containers for development. You can however also install and run
PostgreSQL and Redis manually using your operating system's package manager.

Install
--------

Run in a terminal:

.. code-block:: bash

    # Clone the repository, if you're planning to contribute, clone your fork instead.
    git clone https://github.com/metabrainz/brainzbot-core.git && cd brainzbot-core

    # Install the python dependencies.
    pipenv --two install

    # This builds the project environment and will run for at least several minutes.
    make dependencies

    # Meanwhile you can download and run docker containers for redis and postgres.
    # Skip this step if you have already manually set up those services.
    docker run --name brainzbot_redis -d -p 6379:6379 redis
    docker run --name brainzbot_postgres -e POSTGRES_PASSWORD=brainzzz -d -p 5432:5432 postgres

    # Adjust ``.env`` file if necessary. Defaults are chosen for local debug environments.
    # If your Postgres server requires a password, you'll need to override STORAGE_URL
    # The default database name is 'brainzbot'
    $EDITOR .env

    # Enter the virtualenv and load the .env variables.
    pipenv shell

    # Connect to the postgres database inside the docker container.
    # If you're using a manual installation of postgres instead,
    # you may need to use sudo to run psql as the postgres user.
    docker exec -it brainzbot-postgres psql -U postgres

    # Set up the database.
    CREATE DATABASE brainzbot;
    \c brainzbot
    CREATE EXTENSION hstore;
    \q

    ./manage.py migrate

    # You'll need a staff account for creating a bot and registering channels.
    ./manage.py createsuperuser

Then, to run all the services defined in ``Procfile``:

.. code-block:: bash

    honcho start

.. note:: `foreman <http://ddollar.github.com/foreman/>`_ will also work if you have the gem or Heroku toolbelt installed.

You should now be able to access the site at ``http://localhost:8000``. Log in with the username you created.

See :doc:`getting_started` for instructions on configuring a bot.

If you plan make code changes, please read through the :doc:`developers` doc.

If you plan to run BrainzBot in a production environment please read the :doc:`production` doc.

To start the docker containers again at a later time run:

.. code-block:: bash

    docker start $(docker ps -aqf "name=brainzbot_redis")
    docker start $(docker ps -aqf "name=brainzbot_postgres")


Running Tests
--------------

The tests can currently be run with the following command:

.. code-block:: bash

    ./manage.py test accounts bots logs plugins


Building Documentation
----------------------

Documentation is available in ``docs`` and can be built into a number of
formats using `Sphinx <http://pypi.python.org/pypi/Sphinx>`_:

.. code-block:: bash

    pip install Sphinx
    cd docs
    make html

This creates the documentation in HTML format at ``docs/_build/html``.
