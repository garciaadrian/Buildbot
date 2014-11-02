# -*- python -*-
# ex: set syntax=python:

import os

from buildbot import buildslave
from buildbot.changes import gitpoller
from buildbot.process import factory
from buildbot.schedulers import basic
from buildbot.schedulers import filter
from buildbot.schedulers import forcesched
from buildbot.status import html
from buildbot.status import mail
from buildbot.status.web import authz
from buildbot.steps import shell
from buildbot.steps import source

PASSWORD    = "hunter2"


def GitBaseUrl(repository):
  return "https://github.com/clementine-player/%s.git" % repository


def GitArgs(repository):
  return {
    "repourl": GitBaseUrl(repository),
    "branch": "master",
    "mode": "copy",
    "retry": (5*60, 3),
  }


class OutputFinder(shell.ShellCommand):
  def __init__(self, pattern=None, **kwargs):
    if pattern is None:
      shell.ShellCommand.__init__(self, **kwargs)
    else:
      shell.ShellCommand.__init__(self,
        name="get output filename",
        command=["sh", "-c", "basename `ls -d " + pattern + "|head -n 1`"],
        **kwargs
      )

  def commandComplete(self, cmd):
    filename = self.getLog('stdio').readlines()[0].strip()
    self.setProperty("output-filename", filename)


def MakeDebBuilder(dist, dist_type):
  env = {
    "DEB_BUILD_OPTIONS": 'parallel=4',
  }

  cmake_cmd = [
    "cmake", "..",
    "-DWITH_DEBIAN=ON",
    "-DDEB_ARCH=amd64",
    "-DDEB_DIST=" + dist,
    "-DENABLE_SPOTIFY_BLOB=OFF",
  ]
  make_cmd = ["make", "deb"]

  f = factory.BuildFactory()
  f.addStep(source.Git(**GitArgs("Clementine")))
  f.addStep(shell.ShellCommand(name="cmake", command=cmake_cmd, haltOnFailure=True, workdir="source/bin"))
  f.addStep(shell.Compile(command=make_cmd, haltOnFailure=True, workdir="source/bin", env=env))
  f.addStep(OutputFinder(pattern="bin/clementine_*.deb"))
  return f


def MakeWindowsDepsBuilder():
  f = factory.BuildFactory()
  f.addStep(source.Git(**GitArgs("Dependencies")))
  f.addStep(shell.ShellCommand(name="clean", workdir="source/windows", command=["make", "clean"]))
  f.addStep(shell.ShellCommand(name="compile", workdir="source/windows", command=["make"]))
  return f


# Basic config
c = BuildmasterConfig = {
  'projectName':  "Clementine",
  'projectURL':   "http://www.clementine-player.org/",
  'buildbotURL':  "http://buildbot.clementine-player.org/",
  'slavePortnum': 9989,
  'slaves': [
    buildslave.BuildSlave("precise", PASSWORD),
    buildslave.BuildSlave("trusty",  PASSWORD),
    buildslave.BuildSlave("utopic",  PASSWORD),
    buildslave.BuildSlave("mingw",   PASSWORD),
  ],
  'change_source': [
    gitpoller.GitPoller(
      project="clementine",
      repourl=GitBaseUrl("Clementine"),
      pollinterval=60*5, # seconds
      branch='master',
      workdir="gitpoller_work",
    ),
  ],
  'status': [
    html.WebStatus(
      http_port="tcp:8010",
      authz=authz.Authz(
        forceBuild=True,
        forceAllBuilds=True,
        stopBuild=True,
        stopAllBuilds=True,
        cancelPendingBuild=True,
        cancelAllPendingBuilds=True,
        stopChange=True,
      ),
    ),
    mail.MailNotifier(
      fromaddr="buildmaster@zaphod.purplehatstands.com",
      lookup="gmail.com",
      mode="failing",
    ),
  ],
}

change_filter = filter.ChangeFilter(project="clementine", branch=u"master")

normal_scheduler = basic.SingleBranchScheduler(
  name="deb",
  change_filter=change_filter,
  treeStableTimer=2*60,
  builderNames=[
    "Deb Trusty",
    "Deb Precise",
    "Deb Utopic",
  ],
)
force_scheduler = forcesched.ForceScheduler(
  name="force",
  reason=forcesched.FixedParameter(name="reason", default="force build"),
  branch=forcesched.StringParameter(name="branch", default="master"),
  revision=forcesched.FixedParameter(name="revision", default=""),
  repository=forcesched.FixedParameter(name="repository", default=""),
  project=forcesched.FixedParameter(name="project", default=""),
  properties=[],
  builderNames=[
    "Deb Trusty",
    "Deb Precise",
    "Deb Utopic",
    "Windows Dependencies",
  ],
)

c['schedulers'] = [
  normal_scheduler,
  force_scheduler,
]

c['builders'] = [
  {
    'name':      'Deb Precise',
    'builddir':  'deb-precise',
    'slavename': 'precise',
    'factory':   MakeDebBuilder('precise', 'ubuntu'),
  },
  {
    'name':      'Deb Trusty',
    'builddir':  'deb-trusty',
    'slavename': 'trusty',
    'factory':   MakeDebBuilder('trusty', 'ubuntu'),
  },
  {
    'name':      'Deb Utopic',
    'builddir':  'deb-utopic',
    'slavename': 'utopic',
    'factory':   MakeDebBuilder('utopic', 'ubuntu'),
  },
  {
    'name':      'Windows Dependencies',
    'builddir':  'windows-dependencies',
    'slavename': 'mingw',
    'factory':   MakeWindowsDepsBuilder(),
  },
]