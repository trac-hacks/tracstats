<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include "nav.cs"?>

<div id="content" class="wiki">

<h1>Statistics - Wiki</h1>

<table>
<?cs if:stats.author ?>
<tr><td width="150">Author<td align="right"><?cs var:stats.author ?></tr>
<?cs /if ?>
<tr><td width="150">First edit<td align="right"><?cs var:stats.wiki.mintime ?></tr>
<tr><td width="150">Last edit<td align="right"><?cs var:stats.wiki.maxtime ?></tr>
<tr><td width="150">Wiki age<td align="right"><?cs var:stats.wiki.age ?></tr>
<tr><td width="150">Editors<td align="right"><?cs var:stats.wiki.editors ?></tr>
<tr><td width="150">Edits<td align="right"><?cs var:stats.wiki.edits ?></tr>
<tr><td width="150">Edits-per-year<td align="right"><?cs var:stats.wiki.peryear ?></tr>
<tr><td width="150">Edits-per-month<td align="right"><?cs var:stats.wiki.permonth ?></tr>
<tr><td width="150">Edits-per-day<td align="right"><?cs var:stats.wiki.perday ?></tr>
<tr><td width="150">Edits-per-hour<td align="right"><?cs var:stats.wiki.perhour ?></tr>
</table>

<?cs if:len(stats.wiki.history) > 0 ?>
<br>

<h2>Total Pages</h2>

<div id="totalpages" style="width:600px;height:300px;"></div>

<script language="javascript" type="text/javascript">
$(function () {
    
    var options = {
        lines: { show: true, fill: true }, 
        xaxis: { mode: "time", timeformat: "%b %y" },
        colors: [ "#afd8f8" ],
    };
    
    var d = [<?cs 
               each:stat = stats.wiki.history ?><?cs
               set:last = name(stat) == len(stats.wiki.history) - #1 ?>[<?cs
               var:stat.x ?>, <?cs
               var:stat.y ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];
    
    $.plot($("#totalpages"), [ d ], options);
});
</script>
<?cs /if ?>

<br>

<h2>Edits by author</h2>

<table id="editsbyauthor" class="tablesorter">
<thead>
<tr>
  <th>Author
  <th>Edits
  <th>Pages
  <th>Percent
</tr>
</thead>
<tbody>
<?cs each:stat = stats.wiki.byauthor ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="100" align="right"><?cs var:stat.count ?>
<td width="100" align="right"><?cs var:stat.pages ?>
<td width="100" align="right"><?cs var:stat.percent ?>%
</tr>
<?cs /each ?>
</tbody>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function()
    {
        $("#editsbyauthor").tablesorter( {sortList: [[1,1]]} );
    }
);
</script>

<br>

<h2>Latest wiki pages changed</h2>

<table>
<?cs each:stat = stats.wiki.recent ?>
<tr>
<td width="200"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="150"><a href="<?cs var:stat.url2 ?>"><?cs var:stat.author ?></a>
<td width="100" align="right"><?cs var:stat.time ?>
</tr>
<?cs /each ?>
</table>

<br>

<h2>Most active wiki pages</h2>

<table>
<?cs each:stat = stats.wiki.pages ?>
<tr>
<td width="200"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="75" align="right"><?cs var:stat.count ?>
<td width="75" align="right"><?cs var:stat.percent ?>%
</tr>
<?cs /each ?>
</table>

<br>

<h2>Largest wiki pages</h2>

<table>
<?cs each:stat = stats.wiki.largest ?>
<tr>
<td width="200"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="150" align="right"><?cs var:stat.size ?>
</tr>
<?cs /each ?>
</table>

<br>

</div>

<?cs include "footer.cs"?>

