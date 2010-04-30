<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<?cs include "nav.cs"?>

<div id="content" class="wiki">

<h1>Statistics</h1>

<table cellpadding="10">
<tr><td colspan="2" align="center">
<span id="weeks">Loading...</span><br>
<img src="<?cs var:chrome.href ?>/stats/legend.png">
</td></tr>
<tr><td valign="middle">
<img src="<?cs var:chrome.href ?>/stats/code.png" align="center" valign="middle"> <a href="/stats/code">Code</a><br><br>
<img src="<?cs var:chrome.href ?>/stats/wiki.png" align="center" valign="middle"> <a href="/stats/wiki">Wiki</a><br><br>
<img src="<?cs var:chrome.href ?>/stats/tickets.png" align="center" valign="middle"> <a href="/stats/tickets">Tickets</a>
</td><td valign="middle" style="border-left: 1px lightgray solid;">
<b><?cs var: stats.years ?></b> <font color="gray">years,</font> 
<b><?cs var: stats.days ?></b> <font color="gray">days,</font> 
<b><?cs var: stats.hours ?></b> <font color="gray">hours of development</font>
<br><br>
<b><?cs var: stats.authors ?></b> <font color="gray">authors,</font>
<b><?cs var: stats.revisions ?></b> <font color="gray">revisions,</font>
<br><br>
<b><?cs var: stats.pages ?></b> <font color="gray">wiki pages, and</font>
<br><br>
<b><?cs var: stats.tickets ?></b> <font color="gray">tickets</font>
</td></tr>
</table>

<script language="javascript" type="text/javascript">
$(document).ready(function()
    {

        var values = [<?cs
          each:stat = stats.code.weeks ?><?cs
          set:last = name(stat) == len(stats.code.weeks) - #1 ?><?cs
          var:stat.total ?><?cs if:!last ?>,<?cs /if ?><?cs
        /each ?>];
        $("#weeks").sparkline(values, {
                                        type: "bar",
                                        barColor: "lightgray",
                                        barWidth: 7,
                                      });
    }
);
</script>

<table style="padding: 10px;">
<tr>
<td colspan=3>
<p><i>Recent activity (within last 30 days):</i></p>
</tr>
<tr>
<td><b>Developers</b>
<td><b>Projects</b>
<td><b>Paths</b>
</tr>
<tr>

<td width=150 valign="top">
<ol>
<?cs each:stat = stats.code.byauthors ?>
<li><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a></li>
<?cs /each ?>
</ol>
</td>

<td width=150 valign="top">
<ol>
<?cs each:stat = stats.code.byproject ?>
<li><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a></li>
<?cs /each ?>
</ol>
</td>

<td width=300 valign="top">
<ol>
<?cs each:stat = stats.code.bypaths ?>
<li><a href="<?cs var:stat.url ?>"><?cs var:stat.name ?></a></li>
<?cs /each ?>
</ol>
</td>

</tr>
</table>

</div>

<?cs include "footer.cs"?>

