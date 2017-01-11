# TracStats

The TracStats project is a plugin for the [trac](https://trac.edgewall.org/)
project management tool.

The TracStats plugin adds a "Stats" tab to the trac project. Underneath this
tab can be found statistics about changesets, wiki pages, and tickets.

Some features include:

* Recent activity (last 30 days) showing top 10 developers, projects, and paths
  within the repository.

* Detailed statistics of source code development:

  * Total files by time
  * Commits by time, author, month, day of week, hour of day
  * Recent commits
  * Activity by time, author, project, filetype, change type
  * Most active paths, files
  * Commit cloud (built from checkin comments)

* Detailed statistics of Trac wiki pages:

  * Total pages by time
  * Edits by author
  * Latest wiki pages changed
  * Most active wiki pages
  * Largest wiki pages

* Detailed statistics of Trac tickets:

  * Open tickets by time
  * Tickets by author, component
  * Most active tickets
  * Oldest open tickets
  * Latest tickets reported, changed

* Drill down by author or path within the repository for more information.

The TracStats plugin supports Trac installations with SQLite, MySQL, and
PostgreSQL database backends.

The TracStats plugin has been tested with Subversion, Mercurial, and Git
version control systems.

## Installation

The TracStats plugin can be installed using standard:

```
$ pip install tracstats
```

Or, grab the sources and build using:

```
$ python setup.py install
```

## Configuration

It is configured in the ``trac.ini`` file by enabling and configuring:

```ini
[components]
tracstats.* = enabled
```

The ``STATS_VIEW`` permission is used to control access to the statistics
pages.

In addition, an optional "project root" within your repository can be
configured as the base for all projects and source code statistics:

```ini
[stats]
root = path/to/projects
```

## Troubleshooting

If you use Git (i.e. the GitPlugin for Trac) and are not able to see any of
the code statistics, you likely need to configure it to cache the repository
to make it work:

```ini
[git]
cached_repository = true
persistent_cache = true
```

You might need to run ``trac-admin <project-env> repository resync
<reponame>`` after the change.
