Pseudomat
=========

Datapunt pseudonymization project

Create a project, provide and pseudonymize data files for research.
Substitute personally identifiable data with a hashed version of the
value, so that the data is not identifiable anymore. Hashing is done
with a secret salt generated for the project and with a hashing
algorithm, so that data files from different sources can still be linked
together.

WIP
---

Currently the project consists of a Django app with REST API for
managing projects and users, and a file pseudonymize.py which does the
actual pseudonymization of a data file. These two are not yet linked
together. There is also a command line interface to do the
pseudonymization, cli.py.

OIDC authentication
-------------------

The Django app authenticates a user against a configured OpenId Connect
provider (OP). Provide the configuration for the OP as environment
variables. An example is given in env_example.sh

Installation for local development
----------------------------------

Add your configuration for the OP in a file env.sh in the root of your
project. See env_example.sh for an example. Then:

::

   git clone git@github.com:Amsterdam/pseudomat.git
   cd pseudomat
   docker-compose build
   source env.sh
   docker-compose up

This will fire up a web container with the Django app and a database
container running Postgres. The Django app should now be running on
127.0.0.1:8000

The first time you will have to apply some Django migrations for the
project to run properly. For this, get the id of the running web
container and:

::

   docker exec -it <ContainerId> python ./manage.py migrate
