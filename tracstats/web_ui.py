
# stdlib imports
import datetime
import re
import string
import time
from math import floor, log
from operator import itemgetter

# trac imports
from trac.core import *
from trac.mimeview import Mimeview
from trac.perm import IPermissionRequestor
from trac.util import get_reporter_id
from trac.util.datefmt import pretty_timedelta, to_datetime
from trac.util.html import html, Markup
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.chrome import add_stylesheet, add_script


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

        where = []
        if author:
            where.append("author = '%s'" % author)
        if where:
            where = 'where ' + ' and '.join(where)
        else:
            where = ''

        req.hdf['stats.author'] = author

        db = self.env.get_db_cnx()
        cursor = db.cursor()

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

        if path == '/':
            req.hdf['title'] = 'Stats'
            return self._process(req, cursor, where)
        
        elif path == '/code':
            req.hdf['title'] = 'Code' + (author and (' (%s)' % author))
            return self._process_code(req, cursor, where)

        elif path == '/wiki':
            req.hdf['title'] = 'Wiki ' + (author and (' (%s)' % author))
            return self._process_wiki(req, cursor, where)

        elif path == '/tickets':
            req.hdf['title'] = 'Tickets' + (author and (' (%s)' % author))
            return self._process_tickets(req, cursor, where)

        else:
            raise ValueError, "unknown path '%s'" % path


    def _process(self, req, cursor, where):

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

        req.hdf['stats.authors'] = authors
        req.hdf['stats.revisions'] = revisions
        req.hdf['stats.pages'] = pages
        req.hdf['stats.tickets'] = tickets

        cursor.execute("select min(time), max(time) from revision")
        mintime, maxtime = cursor.fetchall()[0]

        if mintime and maxtime:
            age = maxtime - mintime
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        req.hdf['stats.years'] = years
        req.hdf['stats.days'] = days
        req.hdf['stats.hours'] = hours

        now = time.time()
        start = now - (52 * 7 * 24 * 60 * 60)
        cursor.execute("""
        select strftime('%%Y-%%W', time, 'unixepoch'), 
               count(*) 
        from revision 
        where time > %d 
        group by 1 
        order by 1
        """ % start)
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
        req.hdf['stats.code.weeks'] = list(reversed(stats))
     
        now = time.time()
        start = now - (30 * 24 * 60 * 60)
        cursor.execute("""
        select author, count(*) 
        from revision 
        where time > %d 
        group by 1 
        order by 2 desc 
        limit 10
        """ % start)
        rows = cursor.fetchall()

        stats = []
        for author, commits in rows:
            stats.append({'name': author, 
                          'url': req.href.stats("code", author=author),})
        req.hdf['stats.code.byauthors'] = stats

        cursor.execute("""
        select path 
        from node_change 
        join revision using (rev) 
        where time > %d
        """ % start)
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
        req.hdf['stats.code.bypaths'] = stats

        d = {}
        for path, in rows:
            slash = path.find('/')
            if slash < 0:
                continue
            project = path[:slash]
            try:
                d[project] += 1
            except KeyError:
                d[project] = 1
        total = float(sum(d.itervalues()))
        stats = []
        for k, v in sorted(d.iteritems(), key=itemgetter(1), reverse=True)[:10]:
            stats.append({'name': k,
                          'url': req.href.log(k),})
        req.hdf['stats.code.byproject'] = stats

        return 'stats.cs', None

    def _process_code(self, req, cursor, where):

        project = req.args.get('project', '')

        cursor.execute("""
        create temporary table tmp_revision
            ( rev text PRIMARY KEY )
        """)

        if project:
            cursor.execute("""
            insert into tmp_revision
            select rev
            from revision
            join (
               select rev 
               from node_change using (rev)
               where path like "%(project)s%%"
               group by rev
            ) changes using (rev)
            """ % locals() + where)
        else:
            cursor.execute("""
            insert into tmp_revision
            select rev
            from revision
            """ + where)
        
        cursor.execute("""
        select min(cast(rev as int)), 
               max(cast(rev as int)), 
               min(time), 
               max(time), 
               count(distinct rev), 
               count(distinct author)
        from revision
        inner join tmp_revision using (rev)
        """)
        minrev, maxrev, mintime, maxtime, commits, developers = cursor.fetchall()[0]

        req.hdf['stats.code.maxrev'] = maxrev
        req.hdf['stats.code.minrev'] = minrev
        if maxtime:
            req.hdf['stats.code.maxtime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(maxtime))
        else:
            req.hdf['stats.code.maxtime'] = 'N/A'
        if mintime:
            req.hdf['stats.code.mintime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(mintime))
        else:
            req.hdf['stats.code.mintime'] = 'N/A'

        if mintime and maxtime:
            age = maxtime - mintime
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        req.hdf['stats.code.age'] = '%d years, %d days, %d hours' % (years, days, hours)

        req.hdf['stats.code.developers'] = developers
        req.hdf['stats.code.commits'] = commits
        if age:
            req.hdf['stats.code.commitsperyear'] = '%.2f' % (commits * 365 * 24 * 60 * 60. / age)
            req.hdf['stats.code.commitspermonth'] = '%.2f' % (commits * 30 * 24 * 60 * 60. / age)
            req.hdf['stats.code.commitsperday'] = '%.2f' % (commits * 24 * 60 * 60. / age)
            req.hdf['stats.code.commitsperhour'] = '%.2f' % (commits * 60 * 60. / age)
        else:
            req.hdf['stats.code.commitsperyear'] = 0
            req.hdf['stats.code.commitspermonth'] = 0
            req.hdf['stats.code.commitsperday'] = 0
            req.hdf['stats.code.commitsperhour'] = 0

        cursor.execute("""
        select rev, time, author, length(message) 
        from revision 
        inner join tmp_revision using (rev)
        """)
        revisions = cursor.fetchall()
        #revisions = []

        if project:
            cursor.execute("""
            select nc.rev, nc.path, nc.change_type, r.author 
            from node_change nc
            inner join tmp_revision tr on tr.rev = nc.rev
            join revision r on r.rev = nc.rev
            where nc.path like "%(project)s%%"
            """ % locals())
        else:
            cursor.execute("""
            select nc.rev, nc.path, nc.change_type, r.author 
            from node_change nc
            inner join tmp_revision tr on tr.rev = nc.rev
            join revision r on r.rev = nc.rev
            """)
        changes = cursor.fetchall()
        #changes = []

        if revisions:
            avgsize = sum(int(msg) for _, _, _, msg in revisions) / float(len(revisions))
            avgchanges = float(len(changes)) / len(revisions)
            req.hdf['stats.code.logentry'] = '%d chars' % avgsize
            req.hdf['stats.code.changes'] = '%.2f' % avgchanges
        else:
            req.hdf['stats.code.logentry'] = 'N/A'
            req.hdf['stats.code.changes'] = 'N/A'

        cursor.execute("""
        select r.author, 
            count(distinct r.rev) as commits, 
            count(distinct r.rev) * 24.0 * 60 * 60 / (max(r.time) - min(r.time)) as rate,
            count(c.path) as changes,
            count(distinct c.path) as paths
        from revision r
        inner join tmp_revision tr using (rev)
        join node_change c using (rev)
        group by 1
        order by 2 desc
        """)
        details = cursor.fetchall()

        now = time.time()
        start = now - (52 * 7 * 24 * 60 * 60)
        cursor.execute("""
        select r.author,
               strftime('%%Y-%%W', time, 'unixepoch'), 
               count(r.rev) 
        from revision r
        inner join tmp_revision tr using (rev)
        where r.time > %d 
        group by 1, 2
        order by 1, 2
        """ % start)
        rows = cursor.fetchall()
        d = {}
        for author, week, count in rows:
            try:
                d[author][week] = count 
            except KeyError:
                d[author] = { week : count }
    
        stats = []
        for author, commits, rate, change, paths in details:
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
        req.hdf['stats.code.byauthors'] = stats

        cursor.execute("""
        select r.rev, r.time, r.author, r.message 
        from revision r
        inner join tmp_revision tr on tr.rev = r.rev
        order by time desc limit 10
        """)
        rows = cursor.fetchall()
        stats = []
        for rev, t, author, msg in rows:
            stats.append({'name': msg, 
                          'author' : author,
                          'rev': rev,
                          'url': req.href.changeset(rev),
                          'url2': req.href.stats("code", author=author),
                          'time': pretty_timedelta(to_datetime(t)),})
        req.hdf['stats.code.recent'] = stats

        times = dict((rev, t) for rev, t, _, _ in revisions)

        stats = []
        if not req.args.get('author', ''):
            d = {}
            total = set()
            for rev, path, change_type, _ in sorted(changes, key=lambda x: (times[x[0]], int(x[0]), x[1])):
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
        req.hdf['stats.code.totalfiles'] = stats

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
        req.hdf['stats.code.totalcommits'] = stats

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
        req.hdf['stats.code.totalchanges'] = stats

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
        req.hdf['stats.code.byfiles'] = stats

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
        req.hdf['stats.code.bychangetypes'] = stats

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
        req.hdf['stats.code.bypaths'] = stats

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
        req.hdf['stats.code.byfiletypes'] = stats

        d = {}
        for rev, path, change_type, _ in changes:
            slash = path.find('/')
            if slash < 0:
                continue
            project = path[:slash]
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
        req.hdf['stats.code.byproject'] = stats

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
        req.hdf['stats.code.byhour'] = stats

        days = dict((day, i) for i, day in enumerate(('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')))
        d = dict((i, 0) for i in range(7))
        for rev, t, author, _ in revisions:
            day = time.strftime('%a', time.localtime(t))
            d[days[day]] += 1
        stats = []
        for x, y in sorted(d.iteritems()):
            stats.append({'x': x, 
                          'y': y,})
        req.hdf['stats.code.byday'] = stats

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
        req.hdf['stats.code.bymonth'] = stats

        cursor.execute("select distinct(author) from revision")
        authors = set(s for s, in cursor.fetchall())

        cursor.execute("""
        select message 
        from revision 
        inner join tmp_revision using (rev)
        """)
        messages = cursor.fetchall()

        projects = set(p[:p.find('/')] for _, p, _, _ in changes if p.find('/') != -1)

        ignore = set(stopwords)
        ignore.update(authors)
        ignore.update(projects)

        delete = dict((ord(k), u' ') for k in '.,;:!?-+/\\()<>{}[]=_~`|0123456789*')
        delete.update(dict((ord(k), None) for k in '\"\''))

        d = {}
        for msg, in messages:
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
                           'size': fonts[index]})
        req.hdf['stats.code.cloud'] = stats

        return 'code.cs', None


    def _process_wiki(self, req, cursor, where):

        cursor.execute("select min(time), max(time), count(*), count(distinct author) from wiki " + where)
        mintime, maxtime, edits, editors = cursor.fetchall()[0]

        req.hdf['stats.wiki.editors'] = editors
        if maxtime:
            req.hdf['stats.wiki.maxtime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(maxtime))
        else:
            req.hdf['stats.wiki.maxtime'] = 'N/A'
        if mintime:
            req.hdf['stats.wiki.mintime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(mintime))
        else:
            req.hdf['stats.wiki.mintime'] = 'N/A'

        if mintime and maxtime:
            age = maxtime - mintime
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        req.hdf['stats.wiki.age'] = '%d years, %d days, %d hours' % (years, days, hours)

        req.hdf['stats.wiki.edits'] = edits
        if age:
            req.hdf['stats.wiki.peryear'] = '%.2f' % (edits * 365 * 24 * 60 * 60. / age)
            req.hdf['stats.wiki.permonth'] = '%.2f' % (edits * 30 * 24 * 60 * 60. / age) 
            req.hdf['stats.wiki.perday'] = '%.2f' % (edits * 24 * 60 * 60. / age) 
            req.hdf['stats.wiki.perhour'] = '%.2f' % (edits * 60 * 60. / age) 
        else:
            req.hdf['stats.wiki.peryear'] = 0
            req.hdf['stats.wiki.permonth'] = 0
            req.hdf['stats.wiki.perday'] = 0
            req.hdf['stats.wiki.perhour'] = 0

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
        req.hdf['stats.wiki.byauthor'] = stats

        cursor.execute("select name, time from wiki " + where + " order by 2 asc")
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
        req.hdf['stats.wiki.history'] = stats

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
        req.hdf['stats.wiki.pages'] = stats

        cursor.execute("select name, length(text) from wiki " + where + " group by 1 having version = max(version) order by 2 desc limit 10")
        rows = cursor.fetchall()
        d = dict((name, int(size)) for name, size in rows)
        stats = []
        for k, v in sorted(d.items(), key=itemgetter(1), reverse=True):
            stats.append({'name': k, 
                          'url': req.href.wiki(k),
                          'size': v})
        req.hdf['stats.wiki.largest'] = stats

        cursor.execute("select name, version, author, time from wiki " + where + " order by 4 desc limit 10")                   
        rows = cursor.fetchall()
        stats = []        
        for name, version, author, t in rows:
            stats.append({'name': name, 
                          'author': author,
                          'url': req.href.wiki(name, version=version),
                          'url2': req.href.stats("wiki", author=author),
                          'time': pretty_timedelta(to_datetime(t)),})
        
        req.hdf['stats.wiki.recent'] = stats

        return 'wiki.cs', None


    def _process_tickets(self, req, cursor, where):

        cursor.execute("select min(time), max(time), count(*), count(distinct reporter) from ticket " + where.replace('author', 'reporter'))
        mintime, maxtime, tickets, reporters = cursor.fetchall()[0]

        req.hdf['stats.tickets.reporters'] = reporters
        if maxtime:
            req.hdf['stats.tickets.maxtime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(maxtime))
        else:
            req.hdf['stats.tickets.maxtime'] = 'N/A'
        if mintime:
            req.hdf['stats.tickets.mintime'] = time.strftime('%a %m/%d/%Y %H:%M:%S %Z', time.localtime(mintime))
        else:
            req.hdf['stats.tickets.mintime'] = 'N/A'

        if mintime and maxtime:
            age = maxtime - mintime
        else:
            age = 0
        td = datetime.timedelta(seconds=age)
        years = td.days // 365
        days = (td.days % 365)
        hours = td.seconds // 3600
        req.hdf['stats.tickets.age'] = '%d years, %d days, %d hours' % (years, days, hours)

        req.hdf['stats.tickets.total'] = tickets
        if age:
            req.hdf['stats.tickets.peryear'] = '%.2f' % (tickets * 365 * 24 * 60 * 60. / age)
            req.hdf['stats.tickets.permonth'] = '%.2f' % (tickets * 30 * 24 * 60 * 60. / age)
            req.hdf['stats.tickets.perday'] = '%.2f' % (tickets * 24 * 60 * 60. / age)
            req.hdf['stats.tickets.perhour'] = '%.2f' % (tickets * 60 * 60. / age)
        else:
            req.hdf['stats.tickets.peryear'] = 0
            req.hdf['stats.tickets.permonth'] = 0
            req.hdf['stats.tickets.perday'] = 0
            req.hdf['stats.tickets.perhour'] = 0

        cursor.execute("""\
        select author, sum(ticket), sum(changes)
        from (select reporter as author, count(*) as ticket, 0 as changes
              from ticket """ + where.replace('author', 'reporter') + """
              group by 1
              union
              select author, 0, count(*) 
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
        req.hdf['stats.tickets.byauthor'] = stats

        cursor.execute("""\
        select t.component, count(distinct t.id), count(distinct open.id)
        from ticket t 
        join ticket open using (component)
        where open.resolution is null
        group by 1 order by 2 desc
        """)
        rows = cursor.fetchall()
        stats = []
        for component, total, open in rows:
            stats.append({'name': component, 
                          'url': req.href.query(status=("new", "opened", "resolved"), component=component, order="priority"),
                          'open' : open,
                          'total' : total,})
        req.hdf['stats.tickets.bycomponent'] = stats

        stats = []
        if not req.args.get('author', ''):
            cursor.execute("""\
            select id, time, "none", "new" as status from ticket
            union
            select ticket, time, oldvalue, newvalue 
            from ticket_change where field = "status"
            """)
            rows = cursor.fetchall()
            d = {}
            opened = 0
            assigned = 0
            for ticket, t, oldvalue, newvalue in sorted(rows, key=itemgetter(1)):
                if newvalue == 'assigned' and oldvalue != 'assigned':
                    assigned += 1
                elif newvalue != 'assigned' and oldvalue == 'assigned':
                    assigned -= 1
                if newvalue in ("new", "reopened") and oldvalue not in ("assigned", "new", "reopened"):
                    opened += 1
                elif newvalue == "closed":
                    opened -= 1
                d[int(t * 1000)] = (opened, assigned)
            steps = max(len(d) / 10, 1)
            for k, v in sorted(d.iteritems(), key=itemgetter(0))[::steps]:
                stats.append({'x': k, 
                              'opened': v[0],
                              'assigned': v[1],})
        req.hdf['stats.tickets.history'] = stats

        cursor.execute("select tc.ticket, t.component, t.summary, count(*) from ticket_change tc join ticket t on t.id = tc.ticket " + where + " group by 1 order by 3 desc limit 10")
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
        req.hdf['stats.tickets.active'] = stats

        cursor.execute("select id, component, summary, time from ticket where status != 'closed' order by 4 asc limit 10")
        rows = cursor.fetchall()
        stats = []
        for ticket, component, summary, t in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'time': pretty_timedelta(to_datetime(t)),})
        req.hdf['stats.tickets.oldest'] = stats

        cursor.execute("select id, component, summary, time from ticket order by 4 desc limit 10")
        rows = cursor.fetchall()
        stats = []
        for ticket, component, summary, t in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'time': pretty_timedelta(to_datetime(t)),})
        req.hdf['stats.tickets.newest'] = stats

        cursor.execute("select tc.ticket, t.component, t.summary, tc.time from ticket_change tc join ticket t on t.id = tc.ticket group by 1 order by 4 desc limit 10")
        rows = cursor.fetchall()
        stats = []
        for ticket, component, summary, t in rows:
            stats.append({'name': summary, 
                          'id': ticket,
                          'component': component,
                          'url': req.href.ticket(ticket),
                          'url2': req.href.query(component=component, order="priority"),
                          'time': pretty_timedelta(to_datetime(t)),})

        req.hdf['stats.tickets.recent'] = stats


        return 'tickets.cs', None


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


