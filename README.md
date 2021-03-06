This directory contains Docker images for Clementine's buildbot.

Containers
==========

- `master`:
    Runs the buildbot master on port 8010.  This port is also exposed on the host
    machine.  All slaves connect to the master internally through docker over
    port 9989.

- `volumes`:
    Data-only container that holds persistent state for the master and all the
    slaves.  This is exposed as the /persistent-data directory in every
    container.

- `slave-*`:
    Every supported distro has its own container that runs its own buildbot
    slave.  The container has all the packages required to build Clementine.


Containers are built, started and stopped with docker-compose.

1. First install [docker-compose](https://docs.docker.com/compose/install/).

1. Build the containers:

  ```
  docker-compose build
  ```

1. Then you can start and stop buildbot:

  ```
  docker-compose up
  docker-compose stop
  ```

1. The master is then accessible on http://localhost:8010/.


Credentials
-----------

You need certain keys and credentials to be able to use certain builders.  These
builders will try to pull files from config/ when they run:

  - config/github_id_rsa: .ssh/id_rsa file used for authenticating to github.
    Used for pushing transifex commits to github.
  - config/passwords-external.json: Passwords for external (non-docker) slaves
    to connect to buildbot.
  - config/ppa-keys: Used by the PPA builders for uploading packages to PPAs.
    Get these keys with gpg --export-secret-keys.
  - config/transifexrc: The config file for the transifex client, including the
    password for the clementinebuildbot user.
  - config/android-remote-properties.txt: The properties file for building the
    android remote.  Contains keystore, keystore.password, key.alias and
    key.password lines.
  - config/android-remote.keystore.jks: Keys for signing the android remote apk.


Adding new slaves
=================

Replace `vivid` and `22` with the name of the Ubuntu distro or fedora version
that you want to add.

1. Create the i386 base images:

  ```
  cd base
  ./build-fedora-i386.sh 22
  ./build-ubuntu-i386.sh debian jessie
  ./build-ubuntu-i386.sh ubuntu vivid
  ```

2. Create the `slave-${distro}-${version}-{32,64}` directories by copying from
   the last distro versions and editing the two distro names in the `Dockerfile`

3. Add the distro to `config/config.json` and run `./update_config.py`

4. Build the images and containers and start the slaves:

  ```
  docker-compose build
  docker-compose up
  ```

5. See the builders on http://localhost:8010/builders.


Recreate an image and container
===============================

You might need to do this occasionaly to update a distro's packages.

```
docker-compose build --no-cache --pull slave-ubuntu-vivid-32
docker-compose up -d slave-ubuntu-vivid-32
```


View the master's log
=====================

```
docker-compose run --entrypoint tail master /persistent-data/master/twistd.log
```

