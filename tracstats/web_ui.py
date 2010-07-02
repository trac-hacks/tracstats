
# stdlib imports
import datetime
import re
import string
import time
from math import floor, log
from operator import itemgetter

# trac imports
import trac
from trac.core import *
from trac.mimeview import Mimeview
from trac.perm import IPermissionRequestor
from trac.util import get_reporter_id
from trac.util.datefmt import pretty_timedelta, to_datetime
from trac.util.html import html, Markup
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_ctxtnav, add_stylesheet, add_script
from trac.versioncontrol.api import RepositoryManager


# In version 0.12, the time field in the database was changed
# from seconds to microseconds.  This allows us to support both
# 0.11 and 0.12 with the same piece of code.  It could be prettier.
if trac.__version__.startswith('0.12'):
    SECONDS = 'time / 1000000'
else:
    SECONDS = 'time'

# In version 0.12, the database was changed to allow multiple
# repositories.  Where the "rev" field was previously unique,
# the "(repos,rev)" fields are now unique.  Doing it this way
# is a big performance boost.
if trac.__version__.startswith('0.12'):
    USING = "on r.repos = nc.repos and r.rev = nc.rev"
else:
    USING = "using (rev)"


class TracStatsPlugin(Component):
    implements(INavigationContributor, IPermissionRequestor, IRequestHandler, ITemplateProvider)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['STATS_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'stats'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('STATS_VIEW'):
            return
        yield 'mainnav', 'stats', html.A('Stats', href= req.href.stats())

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('stats', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler methods

    def match_request(self, req):
        import re
        match = re.match(r'/stats(?:(/.*))?', req.path_info)
        if match:
            path, = match.groups()
            req.args['path'] = path or '/'
            return True

    def process_request(self, req):
        req.perm.require('STATS_VIEW')

        author = req.args.get('author', '')
        path = req.args.get('path', '')
        last = req.args.get('last', '')

        where = []
        if author:
            where.append("author = '%s'" % author)
        if last:
            m = re.match('(\d+)m', last)
            if m is not None:
                now = time.time()
                months, = m.groups()
                ago = (24 * 60 * 60 * 30 * int(months))
                where.append('%s > %s' % (SECONDS, now - ago))
        if where:
            where = 'where ' + ' and '.join(where)
        else:
            where = ''

        data = {}
        data['author'] = author
        data['last_1m'] = req.href.stats(path, last='1m', author=author)
        data['last_12m'] = req.href.stats(path, last='12m', author=author)
        data['last_all'] = req.href.stats(path, author=author)

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        db_str = self.env.config.get('trac', 'database')
        db_type, db_path = db_str.split(':', 1)
        assert db_type in ('sqlite', 'mysql', 'postgres'), \
            'Unsupported database "%s"' % db_type
        self.db_type = db_type

        # Include trac wiki stylesheet
        add_stylesheet(req, 'common/css/wiki.css')

        # Include trac stats stylesheet
        add_stylesheet(req, 'stats/common.css')

        # Include javascript libraries
        add_script(req, 'stats/jquery-1.4.2.min.js')
        add_script(req, 'stats/jquery.flot.pack.js')
        add_script(req, 'stats/jquery.tablesorter.min.js')
        add_script(req, 'stats/jquery.sparkline.min.js')
        add_script(req, 'stats/excanvas.pack.js')

        # Include context navigation links
        add_ctxtnav(req, 'Summary', req.href.stats())
        add_ctxtnav(req, 'Code', req.href.stats('code'))
        add_ctxtnav(req, 'Wiki', req.href.stats('wiki'))
        add_ctxtnav(req, 'Tickets', req.href.stats('tickets'))

        if path == '/':
            data['title'] = 'Stats'
            result = self._process(req, cursor, where, data)
            cursor.close()
            return result

        elif path == '/code':
            data['title'] = 'Code' + (author and (' (%s)' % author))
            result = self._process_code(req, cursor, where, data)
            cursor.close()
            return result

        elif path == '/wiki':
            data['title'] = 'Wiki ' + (author and (' (%s)' % author))
            result = self._process_wiki(req, cursor, where, data)
            cursor.close()
            return result

        elif path == '/tickets':
            data['title'] = 'Tickets' + (author and (' (%s)' % author))
            result = self._process_tickets(req, cursor, where, data)
            cursor.close()
            return result

        else:
            cursor.close()
            raise ValueError, "unknown path '%s'" % path


    def _process(self, req, cursor, where, data):

        cursor.execute("""
        select count(distinct author), 
               count(distinct rev) 
        from revision
        """)
        authors, revisions, = cursor.fetchall()[0]

        cursor.execute("select count(distinct name) from wiki")
        pages, = cursor.fetchall()[0]

        cursor.execute("select count(distinct id) from ticket")
        tickets, = cursor.fetchall()[0]

        data['authors'] = authors
        data['revisions'] = revisions
        data['pages'] = pages
        data['tickets'] = tickets

        cursor.execute("""
        select min(%s), max(%s)
        from revision
        """ % (SECONDS, SECONDS))
        mintime, maxtime = cursor.fetchall()[0]

        if mintime and maxtime:
            age = float(maxtime - mintime)
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        data['years'] = years
        data['days'] = days
        data['hours'] = hours

        if self.db_type == 'sqlite':
            strftime = "strftime('%%Y-%%W', %s, 'unixepoch')" % SECONDS
        elif self.db_type == 'mysql':
            strftime = "date_format(from_unixtime(%s), '%%Y-%%u')" % SECONDS
        elif self.db_type == 'postgres':
            strftime = "to_char(to_timestamp(%s), 'YYYY-IW')" % SECONDS # FIXME: Not %Y-%W
        else:
            assert False

        now = time.time()
        start = now - (52 * 7 * 24 * 60 * 60)
        cursor.execute("""
        select %s,
               count(*)
        from revision
        where %s > %d
        group by 1 
        order by 1
        """ % (strftime, SECONDS, start))
        rows = cursor.fetchall()

        d = dict(rows)
        year, week = map(int, time.strftime('%Y %W').split())
        stats = []
        while len(stats) < 52:
            name = '%04d-%02d' % (year, week)
            stats.append({'week': name,
                          'total': d.get(name, 0)})
            week -= 1
            if week < 0:
                year -= 1
                week = 52
        data['weeks'] = list(reversed(stats))

        now = time.time()
        start = now - (30 * 24 * 60 * 60)
        cursor.execute("""
        select author, count(*) 
        from revision 
        where %s > %d 
        group by 1 
        order by 2 desc 
        limit 10
        """ % (SECONDS, start))
        rows = cursor.fetchall()

        stats = []
        for author, commits in rows:
            stats.append({'name': author, 
                          'url': req.href.stats("code", author=author),})
        data['byauthors'] = stats


        cursor.execute("""
        select nc.path
        from node_change nc
        join revision r %s
        where %s > %d
        """ % (USING, SECONDS, start))
        rows = cursor.fetchall()

        d = {}
        for path, in rows:
            slash = path.rfind('/')
            if slash > 0:
                path = path[:slash]
            try:
                d[path] += 1
            except KeyError:
                d[path] = 1
        stats = []
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k,
                          'url': req.href.log(k),})
        data['bypaths'] = stats

        d = {}
        for path, in rows:
            slash = path.find('/')
            if slash < 0:
                continue
            project = path[:slash] or 'None'
            try:
                d[project] += 1
            except KeyError:
                d[project] = 1
        total = float(sum(d.itervalues()))
        stats = []
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k,
                          'url': req.href.log(k),})
        data['byproject'] = stats

        return 'stats.html', data, None

    def _process_code(self, req, cursor, where, data):

        project = req.args.get('project', '')

        if project:
            cursor.execute("""
            select rev, %s, author, message
            from revision
            join (
               select rev
               from node_change
               where path like "%s%%"
               group by rev
            ) changes using (rev)
            """ % (SECONDS, project) + where + " order by 2")
        else:
            cursor.execute("""
            select rev, %s, author, message
            from revision
            """ % SECONDS + where + " order by 2")
        revisions = cursor.fetchall()

        if project:
            query = """
            select nc.rev, nc.path, nc.change_type, r.author
            from node_change nc
            join revision r %s
            """ % USING
            if where:
                query += ' and path like "%s%%"' % project
            else:
                query += ' where path like "%s%%"' % project
            cursor.execute(query)
        else:
            cursor.execute("""
            select nc.rev, nc.path, nc.change_type, r.author
            from node_change nc
            join revision r %s
            """ % USING + where)
        changes = cursor.fetchall()

        # Convert the revision field from text to a number... this might
        # break with DVCS-type SHA hashes.
        if RepositoryManager(self.env).repository_type == 'svn':
            revisions = [(int(rev), t, author, msg)
                         for rev, t, author, msg in revisions]
            changes = [(int(rev), path, change_type, author)
                        for rev, path, change_type, author in changes]

        if revisions:
            head = revisions[0]
            tail = revisions[-1]
            minrev, mintime = head[0], head[1]
            maxrev, maxtime = tail[0], tail[1]
        else:
            minrev = maxrev = mintime = maxtime = 0

        commits = len(revisions)
        developers = len(set(author for _, _, author, _ in revisions))

        data['maxrev'] = maxrev
        data['minrev'] = minrev
        if maxtime:
            data['maxtime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(maxtime))
        else:
            data['maxtime'] = 'N/A'
        if mintime:
            data['mintime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(mintime))
        else:
            data['mintime'] = 'N/A'

        if mintime and maxtime:
            age = float(maxtime - mintime)
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        data['age'] = '%d years, %d days, %d hours' % (years, days, hours)

        data['developers'] = developers
        data['commits'] = commits
        if age:
            data['commitsperyear'] = '%.2f' % (commits * 365 * 24 * 60 * 60. / age)
            data['commitspermonth'] = '%.2f' % (commits * 30 * 24 * 60 * 60. / age)
            data['commitsperday'] = '%.2f' % (commits * 24 * 60 * 60. / age)
            data['commitsperhour'] = '%.2f' % (commits * 60 * 60. / age)
        else:
            data['commitsperyear'] = 0
            data['commitspermonth'] = 0
            data['commitsperday'] = 0
            data['commitsperhour'] = 0

        if revisions:
            avgsize = sum(len(msg) for _, _, _, msg in revisions) / float(len(revisions))
            avgchanges = float(len(changes)) / len(revisions)
            data['logentry'] = '%d chars' % avgsize
            data['changes'] = '%.2f' % avgchanges
        else:
            data['logentry'] = 'N/A'
            data['changes'] = 'N/A'

        if self.db_type == 'sqlite':
            strftime = "strftime('%%Y-%%W', %s, 'unixepoch')" % SECONDS
        elif self.db_type == 'mysql':
            strftime = "date_format(from_unixtime(%s), '%%Y-%%u')" % SECONDS
        elif self.db_type == 'postgres':
            strftime = "to_char(to_timestamp(%s), 'YYYY-IW')" % SECONDS # FIXME: Not %Y-%W
        else:
            assert False

        now = time.time()
        start = now - (52 * 7 * 24 * 60 * 60)
        d = {}
        for _, t, author, _ in revisions:
            if t > start:
                week = time.strftime('%Y-%W', time.localtime(t))
                try:
                    d[author][week] += 1
                except KeyError:
                    d[author] = { week : 1 }

        stats = []
        for author in sorted(set(author for _, _, author, _ in revisions)):
            commits = len(set(x[0] for x in revisions if x[2] == author))
            mintime = min(x[1] for x in revisions if x[2] == author)
            maxtime = max(x[1] for x in revisions if x[2] == author)
            if maxtime > mintime:
                rate = commits * 24.0 * 60 * 60 / float(maxtime - mintime)
            else:
                rate = 0
            change = sum(1 for x in changes if x[3] == author)
            paths = len(set(x[1] for x in changes if x[3] == author))

            year, week = map(int, time.strftime('%Y %W').split())
            weeks = []
            while len(weeks) < 52:
                name = '%04d-%02d' % (year, week)
                try:
                    total = d[author][name]
                except KeyError:
                    total = 0
                weeks.append({'week': name,
                              'total': total})
                week -= 1
                if week < 0:
                    year -= 1
                    week = 52
            stats.append({'name': author, 
                          'url': req.href.stats("code", author=author),
                          'commits': commits,
                          'rate': '%.2f' % (rate and float(rate) or 0),
                          'changes': change,
                          'paths': paths,
                          'weeks': list(reversed(weeks)),})
        data['byauthors'] = stats

        stats = []
        for rev, t, author, msg in reversed(revisions[-10:]):
            stats.append({'name': msg, 
                          'author' : author,
                          'rev': rev,
                          'url': req.href.changeset(rev),
                          'url2': req.href.stats("code", author=author),
                          'time': pretty_timedelta(to_datetime(float(t))),})
        data['recent'] = stats

        times = dict((rev, t) for rev, t, _, _ in revisions)

        stats = []
        if not req.args.get('author', ''):
            d = {}
            total = set()
            for rev, path, change_type, _ in sorted(changes, key=lambda x: (times[x[0]], x[1])):
                if change_type in ('A', 'C'):
                    total.add(path)
                elif change_type == 'D' and path in total:
                    total.remove(path)
                d[int(times[rev] * 1000)] = len(total)
            stats = []
            steps = max(len(d) / 50, 1)
            for k, v in sorted(d.iteritems(), key=itemgetter(0))[::steps]:
                stats.append({'x': k, 
                              'y': v,})
        data['totalfiles'] = stats

        d = {}
        total = 0
        for rev, t, _, _ in sorted(revisions, key=lambda x: x[1]):
            total += 1
            d[int(t * 1000)] = total
        stats = []
        steps = max(len(d) / 50, 1)
        for k, v in sorted(d.iteritems(), key=itemgetter(0))[::steps]:
            stats.append({'x': k, 
                          'y': v,})
        data['totalcommits'] = stats

        times = dict((rev, t) for rev, t, _, _ in revisions)
        d = {}
        total = 0
        for rev, path, change_type, _ in sorted(changes, key=lambda x: times[x[0]]):
            total += 1
            d[int(times[rev] * 1000)] = total
        stats = []
        steps = max(len(d) / 50, 1)
        for k, v in sorted(d.iteritems(), key=itemgetter(0))[::steps]:
            stats.append({'x': k, 
                          'y': v,})
        data['totalchanges'] = stats

        d = {}
        for rev, path, change_type, _ in changes:
            try:
                d[path] += 1
            except KeyError:
                d[path] = 1
        total = float(sum(d.itervalues()))
        stats = []
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k, 
                          'url': req.href.log(k),
                          'count': v,
                          'percent': '%.2f' % (100 * v / total)})
        data['byfiles'] = stats

        d = {}
        for rev, path, change_type, author in changes:
            try:
                d[author][change_type] += 1
            except KeyError:
                d[author] = {'A':0,'E':0,'M':0,'C':0,'D':0}
                d[author][change_type] += 1
        stats = []
        for k, v in sorted(d.iteritems()):
            total = sum(v.itervalues())
            adds = int(100.0 * v['A'] / total)
            copies = int(100.0 * v['C'] / total)
            deletes = int(100.0 * v['D'] / total)
            moves = int(100.0 * v['M'] / total)
            edits = int(100.0 * v['E'] / total)
            edits = 100 - (adds + copies + deletes + moves)
            stats.append({'name': k, 
                          'url': req.href.stats("code", author=k),
                          'adds': adds,
                          'copies': copies,
                          'deletes': deletes,
                          'edits': edits,
                          'moves': moves})
        data['bychangetypes'] = stats

        d = {}
        for rev, path, change_type, _ in changes:
            slash = path.rfind('/')
            if slash > 0:
                path = path[:slash]
            try:
                d[path] += 1
            except KeyError:
                d[path] = 1
        total = float(sum(d.itervalues()))
        stats = []
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k, 
                          'url': req.href.log(k),
                          'count': v,
                          'percent': '%.2f' % (100 * v / total)})
        data['bypaths'] = stats

        d = {}
        for rev, path, change_type, _ in changes:
            slash = path.rfind('/')
            if slash > 0:
                path = path[slash+1:]
            dot = path.rfind('.')
            if dot > 0:
                ext = path[dot:]
                try:
                    d[ext] += 1
                except KeyError:
                    d[ext] = 1
        total = float(sum(d.itervalues()))
        stats = []
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k, 
                          'count': v,
                          'percent': '%.2f' % (100 * v / total)})
        data['byfiletypes'] = stats

        d = {}
        for rev, path, change_type, _ in changes:
            slash = path.find('/')
            if slash < 0:
                continue
            project = path[:slash] or 'None'
            try:
                d[project][0] += 1
                d[project][1].add(rev)
                d[project][2].add(path)
            except KeyError:
                d[project] = [1, set([rev]), set([path])]
        stats = []
        for k, v in sorted(d.iteritems(), key=lambda x: len(x[0][1]), reverse=True):
            stats.append({'name': k, 
                          'url': req.href.browser(k),
                          'changes': v[0],
                          'commits': len(v[1]),
                          'paths': len(v[2]),})
        data['byproject'] = stats

        hours = ['0%d:00' % i for i in range(10)]
        hours += ['%d:00' % i for i in range(10, 24)]
        hours = dict((hour, i) for i, hour in enumerate(hours))
        d = dict((i, 0) for i in range(24))
        for rev, t, author, _ in revisions:
            hour = time.strftime('%H:00', time.localtime(t))
            d[hours[hour]] += 1
        stats = []
        for x, y in sorted(d.iteritems()):
            stats.append({'x': x, 
                          'y': y,})
        data['byhour'] = stats

        days = dict((day, i) for i, day in enumerate(('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')))
        d = dict((i, 0) for i in range(7))
        for rev, t, author, _ in revisions:
            day = time.strftime('%a', time.localtime(t))
            d[days[day]] += 1
        stats = []
        for x, y in sorted(d.iteritems()):
            stats.append({'x': x, 
                          'y': y,})
        data['byday'] = stats

        d = {}
        for _, t, _, _ in revisions:
            t = time.localtime(t)
            t = (t[0], t[1], 0, 0, 0, 0, 0, 0, 0)
            t = time.mktime(t)
            try:
                d[t] += 1
            except KeyError:
                d[t] = 1
        if d:
            mintime = min(d.keys())
            maxtime = max(d.keys())
            t = time.localtime(mintime)
            while mintime < maxtime:
                t = (t[0], t[1]+1, 0, 0, 0, 0, 0, 0, 0)
                mintime = time.mktime(t)
                if mintime not in d:
                    d[mintime] = 0
        stats = []
        for k, v in sorted(d.iteritems()):
            stats.append({'x': int(k * 1000),
                          'y': v})
        data['bymonth'] = stats

        cursor.execute("select distinct(author) from revision")
        authors = set(s for s, in cursor.fetchall())

        projects = set(p[:p.find('/')] for _, p, _, _ in changes if p.find('/') != -1)

        ignore = set(stopwords)
        ignore.update(authors)
        ignore.update(projects)

        delete = dict((ord(k), u' ') for k in '.,;:!?-+/\\()<>{}[]=_~`|0123456789*')
        delete.update(dict((ord(k), None) for k in '\"\''))

        d = {}
        for _, _, _, msg in revisions:
            msg = msg.lower()
            msg = msg.translate(delete)
            for word in msg.split():
                if word not in ignore and len(word) > 1:
                    try:
                        d[word] += 1
                    except KeyError:
                        d[word] = 1
        fonts = ['0.8em', '1.0em', '1.25em', '1.5em', '1.75em', '2.0em']
        items = sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:200]
        min_count = items and min(map(itemgetter(1), items)) or 0
        max_count = items and max(map(itemgetter(1), items)) or 0
        stats = []
        for k, v in sorted(items):
             weight = (log(v) - log(min_count)) / max(log(max_count) - log(min_count), 1)
             index = int(floor(weight * len(fonts)))
             index = min(index, len(fonts) - 1)
             stats.append({'word': k,
                           'url': req.href.search(q=k, noquickjump=1,
                                                  changeset="on"),
                           'size': fonts[index]})
        data['cloud'] = stats

        return 'code.html', data, None


    def _process_wiki(self, req, cursor, where, data):

        cursor.execute("""
        select min(%s),
               max(%s),
               count(*),
               count(distinct author) """ % (SECONDS, SECONDS) + """
        from wiki """ + where)
        mintime, maxtime, edits, editors = cursor.fetchall()[0]

        data['editors'] = editors
        if maxtime:
            data['maxtime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(maxtime))
        else:
            data['maxtime'] = 'N/A'
        if mintime:
            data['mintime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(mintime))
        else:
            data['mintime'] = 'N/A'

        if mintime and maxtime:
            age = float(maxtime - mintime)
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        data['age'] = '%d years, %d days, %d hours' % (years, days, hours)

        data['edits'] = edits
        if age:
            data['peryear'] = '%.2f' % (edits * 365 * 24 * 60 * 60. / age)
            data['permonth'] = '%.2f' % (edits * 30 * 24 * 60 * 60. / age) 
            data['perday'] = '%.2f' % (edits * 24 * 60 * 60. / age) 
            data['perhour'] = '%.2f' % (edits * 60 * 60. / age) 
        else:
            data['peryear'] = 0
            data['permonth'] = 0
            data['perday'] = 0
            data['perhour'] = 0

        cursor.execute("select name, author, count(*) from wiki " + where + " group by 1, 2")
        pages = cursor.fetchall()

        d = {}
        for name, author, count in pages:
            try:
                d[author][0] += count
                d[author][1].add(name)
            except KeyError:
                d[author] = [count, set([name])]
        total = float(sum(x[0] for x in d.values()))
        stats = []
        for k, v in sorted(d.items(), key=itemgetter(1), reverse=True):
            stats.append({'name': k, 
                          'url': req.href.stats("wiki", author=k),
                          'count': v[0],
                          'pages': len(v[1]),
                          'percent': '%.2f' % (100 * v[0] / total)})
        data['byauthor'] = stats

        cursor.execute("""
        select name, %s """ % SECONDS + """
        from wiki """ + where + """
        order by 2 asc
        """)
        history = cursor.fetchall()

        stats = []
        if not req.args.get('author', ''):
            d = {}
            total = set()
            for name, t in history:
                total.add(name)
                d[int(t * 1000)] = len(total)
            stats = []
            steps = max(len(d) / 10, 1)
            for k, v in sorted(d.iteritems(), key=itemgetter(0))[::steps]:
                stats.append({'x': k, 
                              'y': v,})
        data['history'] = stats

        d = {}
        for name, _, count in pages:
            try:
                d[name] += count
            except KeyError:
                d[name] = count
        total = float(sum(d.values()))
        stats = []
        for k, v in sorted(d.items(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k, 
                          'url': req.href.wiki(k),
                          'count': v,
                          'percent': '%.2f' % (100 * v / total)})
        data['pages'] = stats

        cursor.execute("""
        select name, version, length(text)
        from wiki """ + where + """
        group by 1, 2, 3
        having version = max(version)
        order by 3 desc
        limit 10
        """)
        rows = cursor.fetchall()
        d = dict((name, int(size)) for name, _, size in rows)
        stats = []
        for k, v in sorted(d.items(), key=itemgetter(1), reverse=True):
            stats.append({'name': k, 
                          'url': req.href.wiki(k),
                          'size': v})
        data['largest'] = stats

        cursor.execute("""
        select name, version, author, %s """ % SECONDS + """
        from wiki """ + where + """
        order by 4 desc
        limit 10
        """)
        rows = cursor.fetchall()
        stats = []
        for name, version, author, t in rows:
            stats.append({'name': name, 
                          'author': author,
                          'url': req.href.wiki(name, version=version),
                          'url2': req.href.stats("wiki", author=author),
                          'time': pretty_timedelta(to_datetime(float(t))),})

        data['recent'] = stats

        return 'wiki.html', data, None


    def _process_tickets(self, req, cursor, where, data):

        cursor.execute("""
        select
            min(%s),
            max(%s),
            count(*),
            count(distinct reporter) """ % (SECONDS, SECONDS) + """
        from ticket """ + where.replace('author', 'reporter'))
        mintime, maxtime, tickets, reporters = cursor.fetchall()[0]

        data['reporters'] = reporters
        if maxtime:
            data['maxtime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(maxtime))
        else:
            data['maxtime'] = 'N/A'
        if mintime:
            data['mintime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(mintime))
        else:
            data['mintime'] = 'N/A'

        if mintime and maxtime:
            age = float(maxtime - mintime)
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        data['age'] = '%d years, %d days, %d hours' % (years, days, hours)

        data['total'] = tickets
        if age:
            data['peryear'] = '%.2f' % (tickets * 365 * 24 * 60 * 60. / age)
            data['permonth'] = '%.2f' % (tickets * 30 * 24 * 60 * 60. / age)
            data['perday'] = '%.2f' % (tickets * 24 * 60 * 60. / age)
            data['perhour'] = '%.2f' % (tickets * 60 * 60. / age)
        else:
            data['peryear'] = 0
            data['permonth'] = 0
            data['perday'] = 0
            data['perhour'] = 0

        cursor.execute("""\
        select author, sum(reports), sum(changes)
        from (select reporter as author, count(*) as reports, 0 as changes
              from ticket """ + where.replace('author', 'reporter') + """
              group by 1
              union
              select author, 0 as reports, count(*) as changes
              from ticket_change """ + where + """
              group by 1
              ) as data
        group by 1 order by 2 desc
        """)
        rows = cursor.fetchall()
        d = dict((path, (int(x), int(y))) for path, x, y in rows)
        stats = []
        for k, v in sorted(d.items(), key=itemgetter(1), reverse=True):
            stats.append({'name': k, 
                          'url': req.href.stats("tickets", author=k),
                          'reports': v[0],
                          'changes': v[1]})
        data['byauthor'] = stats

        cursor.execute("""\
        select t.component, count(distinct t.id), count(distinct open.id)
        from ticket t
        join ticket open using (component)
        where (open.resolution is null or length(open.resolution) = 0) """ +
                       where.replace('where',
                                     'and').replace('time',
                                                    't.time').replace('author',
                                                                      't.reporter')+ """
        group by 1 order by 2 desc
        """)
        rows = cursor.fetchall()
        stats = []
        for component, total, open in rows:
            stats.append({'name': component, 
                          'url': req.href.query(status=("new", "opened", "resolved"), component=component, order="priority"),
                          'open' : open,
                          'total' : total,})
        data['bycomponent'] = stats

        stats = []
        if not req.args.get('author', ''):
            cursor.execute("""\
            select id, %s, 'none' as oldvalue, 'new' as newvalue
            from ticket """ % SECONDS + where + """
            union
            select ticket, %s, oldvalue, newvalue
            from ticket_change where field = 'status' """  % SECONDS +
                           where.replace('where', 'and'))
            rows = cursor.fetchall()
            d = {}
            opened = 0
            accepted = 0
            for ticket, t, oldvalue, newvalue in sorted(rows, key=itemgetter(1)):
                if newvalue == 'accepted' and oldvalue != 'accepted':
                    accepted += 1
                elif newvalue != 'accepted' and oldvalue == 'accepted':
                    accepted -= 1
                if newvalue in ("new", "reopened") and oldvalue not in ("new", "reopened"):
                    opened += 1
                elif newvalue == "closed" and oldvalue != "closed":
                    opened -= 1
                d[int(t * 1000)] = (opened, accepted)
            steps = max(len(d) / 10, 1)
            for k, v in sorted(d.iteritems(), key=itemgetter(0))[::steps]:
                stats.append({'x': k,
                              'opened': v[0],
                              'accepted': v[1],})
        data['history'] = stats

        cursor.execute("""\
        select tc.ticket, t.component, t.summary, count(*)
        from ticket_change tc
        join ticket t on t.id = tc.ticket """ + where.replace('time', 'tc.time') + """
        group by 1, 2, 3
        order by 3 desc
        limit 10
        """)
        rows = cursor.fetchall()
        total = float(sum(int(v) for _, _, _, v in rows))
        stats = []
        for ticket, component, summary, v in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'count': int(v),
                          'percent': '%.2f' % (100 * int(v) / total)})
        data['active'] = stats

        cursor.execute("""
        select id, component, summary, %s
        from ticket
        where status != 'closed' """ % SECONDS + 
                       where.replace('where',
                                     'and').replace('author',
                                                    'reporter') + """
        order by 4 asc
        limit 10
        """)
        rows = cursor.fetchall()
        stats = []
        for ticket, component, summary, t in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'time': pretty_timedelta(to_datetime(t)),})
        data['oldest'] = stats

        cursor.execute("""
        select id, component, summary, %s
        from ticket """ % SECONDS + where.replace('author', 'reporter') + """
        order by 4 desc
        limit 10
        """)
        rows = cursor.fetchall()
        stats = []
        for ticket, component, summary, t in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'time': pretty_timedelta(to_datetime(t)),})
        data['newest'] = stats

        cursor.execute("""
        select tc.ticket, t.component, t.summary, tc.%s
        from ticket_change tc
        join ticket t on t.id = tc.ticket """ % SECONDS +
                       where.replace('where', 'and').replace('time', 'tc.time') + """
        order by 4 desc
        limit 10
        """)
        rows = cursor.fetchall()
        stats = []
        for ticket, component, summary, t in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'time': pretty_timedelta(to_datetime(t)),})

        data['recent'] = stats

        return 'tickets.html', data, None


stopwords = set('''
a about above across after afterwards again against all almost alone along
already also although always am among amongst amoungst amount an and another
any anyhow anyone anything anyway anywhere are around as at back be became
because become becomes becoming been before beforehand behind being below
beside besides between beyond bill both bottom but by call can cannot cant co
computer con could couldnt cry de describe detail do done down due during each
eg eight either eleven else elsewhere empty enough etc even ever every
everyone everything everywhere except few fifteen fify fill find fire first
five for former formerly forty found four from front full further get give go
had has hasnt have he hence her here hereafter hereby herein hereupon hers
herself him himself his how however hundred i ie if in inc indeed instead
interest into is it its itself keep last latter latterly least less ltd made
many may me meanwhile might mill mine more moreover most mostly move much must
my myself name namely neither never nevertheless next nine no nobody none
noone nor not nothing now nowhere of off often on once one only onto or other
others otherwise our ours ourselves out over own part per perhaps please put
rather re same see seem seemed seeming seems serious several she should show
side since sincere six sixty so some somehow someone something sometime
sometimes somewhere still such system take ten than that the their them
themselves then thence there thereafter thereby therefore therein thereupon
these they thick thin third this those though three through throughout thru
thus to together too top toward towards twelve twenty two un under until up
upon us very via was we well were what whatever when whence whenever where
whereafter whereas whereby wherein whereupon wherever whether which while
whither who whoever whole whom whose why will with within without would yet
you your yours yourself yourselves
'''.split())

stopwords.update('''
add added adding 
adjust adjusted adjusting
change changed changes changing 
check checked checking 
cleanup
close closed closes closing 
commit committed committing 
correct corrected correcting
create created creating
delete deleted deleting
display displayed displaying
do dont does doesnt
edit edited editing
enable enabled enables enabling
format formatting
fix fixed fixes fixing 
include included includes including
initial
modify modified modifying
move moved moving
new
refactor refactored refactoring
remove removed removing 
replace replaced replaces replacing
review reviewed reviewing 
revise revised revising
update updated updates updating
use used using 
'''.split())


