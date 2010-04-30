<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include "nav.cs"?>

<div id="content" class="wiki">

<h1>Statistics - Tickets</h1>

<table>
<?cs if:stats.author ?>
<tr><td width="150">Author<td align="right"><?cs var:stats.author ?></tr>
<?cs /if ?>
<tr><td width="150">First ticket<td align="right"><?cs var:stats.tickets.mintime ?></tr>
<tr><td width="150">Last ticket<td align="right"><?cs var:stats.tickets.maxtime ?></tr>
<tr><td width="150">Ticket age<td align="right"><?cs var:stats.tickets.age ?></tr>
<tr><td width="150">Reporters<td align="right"><?cs var:stats.tickets.reporters ?></tr>
<tr><td width="150">Tickets<td align="right"><?cs var:stats.tickets.total ?></tr>
<tr><td width="150">Tickets-per-year<td align="right"><?cs var:stats.tickets.peryear ?></tr>
<tr><td width="150">Tickets-per-month<td align="right"><?cs var:stats.tickets.permonth ?></tr>
<tr><td width="150">Tickets-per-day<td align="right"><?cs var:stats.tickets.perday ?></tr>
<tr><td width="150">Tickets-per-hour<td align="right"><?cs var:stats.tickets.perhour ?></tr>
</table>

<?cs if:len(stats.tickets.history) > 0 ?>
<br>

<h2>Open Tickets</h2>

<div id="opentickets" style="width:600px;height:300px;"></div>

<script language="javascript" type="text/javascript">
$(function () {
    
    var options = {
        lines: { show: true, fill: true }, 
        xaxis: { mode: "time", timeformat: "%b %y" },
        colors: [ "#afd8f8", "#cb4b4b" ],
    };
    
    var d1 = [<?cs 
               each:stat = stats.tickets.history ?><?cs
               set:last = name(stat) == len(stats.tickets.history) - #1 ?>[<?cs
               var:stat.x ?>, <?cs
               var:stat.opened ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];
    
    var d2 = [<?cs 
               each:stat = stats.tickets.history ?><?cs
               set:last = name(stat) == len(stats.tickets.history) - #1 ?>[<?cs
               var:stat.x ?>, <?cs
               var:stat.assigned ?>]<?cs if:!last ?>,<?cs /if ?><?cs /each ?>];

    $.plot($("#opentickets"), [ d1, d2 ], options);
});
</script>
<?cs /if ?>

<br>

<h2>Tickets by author</h2>

<table id="ticketsbyauthor" class="tablesorter">
<thead>
<tr>
  <th>Author
  <th>Reports
  <th>Changes
</tr>
</thead>
<tbody>
<?cs each:stat = stats.tickets.byauthor ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="100" align="right"><?cs var:stat.reports ?>
<td width="100" align="right"><?cs var:stat.changes ?>
</tr>
<?cs /each ?>
</tbody>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function()
    {   
        $("#ticketsbyauthor").tablesorter( {sortList: [[1,1]]} );
    }
);
</script>

<br>

<h2>Tickets by component</h2>

<table id="ticketsbycomponent" class="tablesorter">
<thead>
<tr>
  <th>Component
  <th>Open
  <th>Total
</tr>
</thead>
<tbody>
<?cs each:stat = stats.tickets.bycomponent ?>
<tr>
<td width="150"><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a>
<td width="100" align="right"><?cs var:stat.open ?>
<td width="100" align="right"><?cs var:stat.total ?>
</tr>
<?cs /each ?>
</tbody>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function()
    {   
        $("#ticketsbycomponent").tablesorter( {sortList: [[1,1]]} );
    }
);
</script>

<br>

<h2>Most active tickets</h2>

<table>
<?cs each:stat = stats.tickets.active ?>
<tr>
<td width="50"><a href="<?cs var:stat.url ?>"><?cs var:stat.id ?></a>
<td width="150"><a href="<?cs var:stat.url2 ?>"><?cs var:stat.component ?></a>
<td width="350"><?cs var:stat.name ?>
<td width="75" align="right"><?cs var:stat.count ?>
<td width="75" align="right"><?cs var:stat.percent ?>%
</tr>
<?cs /each ?>
</table>

<br>

<h2>Oldest open tickets</h2>

<table>
<?cs each:stat = stats.tickets.oldest ?>
<tr>
<td width="50"><a href="<?cs var:stat.url ?>"><?cs var:stat.id ?></a>
<td width="150"><a href="<?cs var:stat.url2 ?>"><?cs var:stat.component ?></a>
<td width="350"><?cs var:stat.name ?>
<td width="100" align="right"><?cs var:stat.time ?>
</tr>
<?cs /each ?>
</table>

<br>

<h2>Latest tickets reported</h2>

<table>
<?cs each:stat = stats.tickets.newest ?>
<tr>
<td width="50"><a href="<?cs var:stat.url ?>"><?cs var:stat.id ?></a>
<td width="150"><a href="<?cs var:stat.url2 ?>"><?cs var:stat.component ?></a>
<td width="350"><?cs var:stat.name ?>
<td width="100" align="right"><?cs var:stat.time ?>
</tr>
<?cs /each ?>
</table>

<br>

<h2>Latest tickets changed</h2>

<table>
<?cs each:stat = stats.tickets.recent ?>
<tr>
<td width="50"><a href="<?cs var:stat.url ?>"><?cs var:stat.id ?></a>
<td width="150"><a href="<?cs var:stat.url2 ?>"><?cs var:stat.component ?></a>
<td width="350"><?cs var:stat.name ?>
<td width="100" align="right"><?cs var:stat.time ?>
</tr>
<?cs /each ?>
</table>

<br>

</div>

<?cs include "footer.cs"?>

