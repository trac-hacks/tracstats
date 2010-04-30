<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include "nav.cs"?>

<div id="content" class="wiki">

<h1>Statistics - Source</h1>

<table>
<?cs if:stats.author ?>
<tr><td width="150">Author<td align="right"><?cs var:stats.author ?></tr>
<?cs /if ?>
<tr><td width="150">Head Revision<td align="right"><?cs var:stats.code.maxrev ?></tr>
<tr><td width="150">First revision<td align="right"><?cs var:stats.code.mintime ?></tr>
<tr><td width="150">Last revision<td align="right"><?cs var:stats.code.maxtime ?></tr>
<tr><td width="150">Repository age<td align="right"><?cs var:stats.code.age ?></tr>
<tr><td width="150">Developers<td align="right"><?cs var:stats.code.developers ?></tr>
<tr><td width="150">Commits<td align="right"><?cs var:stats.code.commits ?></tr>
<tr><td width="150">Commits-per-year<td align="right"><?cs var:stats.code.commitsperyear ?></tr>
<tr><td width="150">Commits-per-month<td align="right"><?cs var:stats.code.commitspermonth ?></tr>
<tr><td width="150">Commits-per-day<td align="right"><?cs var:stats.code.commitsperday ?></tr>
<tr><td width="150">Commits-per-hour<td align="right"><?cs var:stats.code.commitsperhour ?></tr>
<tr><td width="150">Average log entry<td align="right"><?cs var:stats.code.logentry ?></tr>
<tr><td width="150">Average changes<td align="right"><?cs var:stats.code.changes ?></tr>
</table>

<?cs if:len(stats.code.totalfiles) > 0 ?>
<br>

<h2>Total Files</h2>

<div id="totalfiles" style="width:600px;height:300px;"></div>

<script language="javascript" type="text/javascript">
$(function () {

    var options = {
        lines: { show: true, fill: true },
        xaxis: { mode: "time", timeformat: "%b %y" }, 
        colors: [ "#afd8f8" ],
    };

    var d = [<?cs 
               each:stat = stats.code.totalfiles ?><?cs
               set:last = name(stat) == len(stats.code.totalfiles) - #1 ?>[<?cs 
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#totalfiles"), [ d ], options);
});
</script>
<?cs /if ?>

<br>

<h2>Commits by time</h2>

<div id="totalcommits" style="width:600px;height:300px;"></div>

<script language="javascript" type="text/javascript">
$(function () {

    var options = {
        lines: { show: true, fill: true },
        xaxis: { mode: "time", timeformat: "%b %y" }, 
    };

    var d = [<?cs 
               each:stat = stats.code.totalcommits ?><?cs
               set:last = name(stat) == len(stats.code.totalcommits) - #1 ?>[<?cs 
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#totalcommits"), [ d ], options);
});
</script>

<br>

<h2>Commits by author</h2>

<table id="commitsbyauthor" class="tablesorter">
<thead>
<tr>
  <th>Author
  <th>Commits
  <th>Rate
  <th>Changes
  <th>Paths
</tr>
</thead>
<tbody>
<?cs each:stat = stats.code.byauthors ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="100" align="right"><?cs var:stat.commits ?>
<td width="100" align="right"><?cs var:stat.rate ?>
<td width="100" align="right"><?cs var:stat.changes ?>
<td width="100" align="right"><?cs var:stat.paths ?>
</tr>
<?cs /each ?>
</tbody>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function() 
    { 
        $("#commitsbyauthor").tablesorter( {sortList: [[1,1]]} ); 
    } 
); 
</script>

<br>

<h2>Commits by month</h2>

<div id="commitsbymonth" style="width:600px;height:200px;"></div>

<script language="javascript" type="text/javascript">
$(function () {

    var options = {
        lines: { show: true, fill: true },
        xaxis: { mode: "time", timeformat: "%b %y" }, 
        colors: [ "#afd8f8" ],
    };

    var d = [<?cs 
               each:stat = stats.code.bymonth ?><?cs
               set:last = name(stat) == len(stats.code.bymonth) - #1 ?>[<?cs 
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#commitsbymonth"), [ d ], options);
});
</script>

<br>

<h2>Commits by day of week</h2>

<div id="commitsbyday" style="width:500px;height:200px;"></div>

<script language="javascript" type="text/javascript">
$(function () {

    var options = {
        grid: { tickColor: "white" },
        bars: { show: true, fill: true },
        xaxis: { ticks: [[0.5,"Sun"],[1.5,"Mon"],[2.5,"Tue"],[3.5,"Wed"],
                         [4.5,"Thu"],[5.5,"Fri"],[6.5,"Sat"]] }, 
        colors: [ "#afd8f8" ],
    };

    var d = [<?cs 
               each:stat = stats.code.byday ?><?cs
               set:last = name(stat) == len(stats.code.byday) - #1 ?>[<?cs 
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#commitsbyday"), [ d ], options);
});

</script>

<br>

<h2>Commits by hour of day</h2>

<div id="commitsbyhour" style="width:500px;height:200px;"></div>

<script language="javascript" type="text/javascript">
$(function () {

    var options = {
        lines: { show: true, fill: true },
        xaxis: { ticks: [[0.5,"00:00"],[2.5,"02:00"],
                         [4.5,"04:00"],[6.5,"06:00"],
                         [8.5,"08:00"],[10.5,"10:00"],
                         [12.5,"12:00"],[14.5,"14:00"],
                         [16.5,"16:00"],[18.5,"18:00"],
                         [20.5,"20:00"],[22.5,"22:00"]] },
        colors: [ "#afd8f8" ],
    };

    var d = [<?cs 
               each:stat = stats.code.byhour ?><?cs
               set:last = name(stat) == len(stats.code.byhour) - #1 ?>[<?cs 
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#commitsbyhour"), [ d ], options);
});

</script>

<br>

<h2>Recent commits</h2>

<table>
<?cs each:stat = stats.code.recent ?>
<tr>
<td width="50"><a href="<?cs var:stat.url ?>"><?cs var:stat.rev ?></a>
<td width="150"><a href="<?cs var:stat.url2 ?>"><?cs var:stat.author ?></a>
<td width="350"><?cs var:stat.name ?>
<td width="100" align="right"><?cs var:stat.time ?>
</tr>
<?cs /each ?>
</table>

<br>

<h2>Activity by time</h2>

<div id="totalchanges" style="width:600px;height:300px;"></div>

<script language="javascript" type="text/javascript">
$(function () {

    var options = {
        lines: { show: true, fill: true},
        xaxis: { mode: "time", timeformat: "%b %y" }, 
    };

    var d = [<?cs 
               each:stat = stats.code.totalchanges ?><?cs
               set:last = name(stat) == len(stats.code.totalchanges) - #1 ?>[<?cs 
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#totalchanges"), [ d ], options);
});
</script>

<br>

<h2>Activity by author</h2>

<table id="activitybyauthor" class="tablesorter">
<thead>
<tr>
  <th>Author
  <th>Commits
</tr>
</thead>
<tbody>
<?cs each:stat = stats.code.byauthors ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="420" align="right">
<span id="<?cs var:stat.name ?>weeks">Loading...</span>
<script language="javascript" type="text/javascript">
$(document).ready(function()
    {
        var values = [<?cs
          each:week = stat.weeks ?><?cs
          set:last = name(week) == len(stat.weeks) - #1 ?><?cs
          var:week.total ?><?cs if:!last ?>,<?cs /if ?><?cs
        /each ?>];
        $("#<?cs var:stat.name ?>weeks").sparkline(values, {
                                type: "bar",
                                barColor: "lightgray",
                                barWidth: 7,
                              });
    }
);
</script>
</td>
</tr>
<?cs /each ?>
</tbody>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function()
    {
        $("#activitybyauthor").tablesorter( {sortList: [[0,0]]} );
    }
);
</script>

<br>

<h2>Activity by project</h2>

<table id="activitybyproject" class="tablesorter">
<thead>
<tr>
  <th>Project
  <th>Commits
  <th>Changes
  <th>Paths
</tr>
</thead>
<tbody>
<?cs each:stat = stats.code.byproject ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="100" align="right"><?cs var:stat.commits ?>
<td width="100" align="right"><?cs var:stat.changes ?>
<td width="100" align="right"><?cs var:stat.paths ?>
</tr>
<?cs /each ?>
</tbody>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function()
    {
        $("#activitybyproject").tablesorter( {sortList: [[1,1]]} );
    }
);
</script>

<br>

<h2>Most active paths</h2>

<table>
<?cs each:stat = stats.code.bypaths ?>
<tr>
<td width="400"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="75" align="right"><?cs var:stat.count ?>
<td width="75" align="right"><?cs var:stat.percent ?>%
</tr>
<?cs /each ?>
</table>

<br>

<h2>Most active files</h2>

<table>
<?cs each:stat = stats.code.byfiles ?>
<tr>
<td width="400"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="75" align="right"><?cs var:stat.count ?>
<td width="75" align="right"><?cs var:stat.percent ?>%
</tr>
<?cs /each ?>
</table>

<br>

<h2>Activity by filetype</h2>

<table>
<?cs each:stat = stats.code.byfiletypes ?>
<tr>
<td width="150"><?cs var:stat.name ?>
<td width="75" align="right"><?cs var:stat.count ?>
<td width="75" align="right"><?cs var:stat.percent ?>%
</tr>
<?cs /each ?>
</table>

<br>

<h2>Activity by change type</h2>

<table class="changetypes" cellspacing="0" cellpadding="0">
<?cs each:stat = stats.code.bychangetypes ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td>
  <div style="border: 1px darkgray solid;">
    <?cs if:stat.adds > 0 ?><div class="add" style="float: left; height: 12px; width:<?cs var:stat.adds * 3 ?>px;">&nbsp;</div><?cs /if ?>
    <?cs if:stat.copies > 0 ?><div class="copy" style="float: left; height: 12px; width:<?cs var:stat.copies * 3 ?>px;">&nbsp;</div><?cs /if ?>
    <?cs if:stat.deletes > 0 ?><div class="delete" style="float: left; height: 12px; width:<?cs var:stat.deletes * 3 ?>px;">&nbsp;</div><?cs /if ?>
    <?cs if:stat.edits > 0 ?><div class="edit" style="float: left; height: 12px; width:<?cs var:stat.edits * 3 ?>px;">&nbsp;</div><?cs /if ?>
    <?cs if:stat.moves > 0 ?><div class="move" style="float: left; height: 12px; width:<?cs var:stat.moves * 3 ?>px;">&nbsp;</div><?cs /if ?>
    <div style="clear: both;"></div>
  </div>
</tr>
<?cs /each ?>
</table>
<div class="legend">
<dl>
  <dt class="add"></dt><dd>added</dd>
  <dt class="copy"></dt><dd>copied</dd>
  <dt class="delete"></dt><dd>deleted</dd>
  <dt class="edit"></dt><dd>edited</dd>
  <dt class="move"></dt><dd>moved</dd>
</dl>
</div>

<br>

<h2>Commit cloud</h2>

<div style="width:600px;">
<?cs each:stat = stats.code.cloud ?>
<span style="font-size: <?cs var:stat.size ?>"><?cs var:stat.word ?></span>
<?cs /each ?>
</div>

<br>
<br>

</div>

<?cs include "footer.cs"?>

