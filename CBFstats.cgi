#!/usr/bin/perl -w

#Ebeling, USIT, 18.04.2017.

use strict;
use CGI;
use CGI::Carp;
use LWP::Simple;
use JSON;
use utf8;
use Encode qw(decode encode);

#nabu
my $statsPath = "http://127.0.0.1/cgi-bin/cbf/gencbfstats.cgi";
my $scriptpath = "/home/jarlee/prog/R/script/";
my $proptest = "scriptPropTest.R";

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $json = $mycgi->param('json') || "";

#$json = '{"totnoWords":2089, "male":1245, "female":844, "Decades": {"1900":301, "1910":256, "1920":319, "1930":217, "1940":119, "1950":93, "1960":129, "1970":95, "1980":156, "1990":197, "2000":89, "2010":118}}';
if ($json)
{

	my $jsonResult = &getthestats($statsPath, $json);
	my $json_data = decode_json($jsonResult);
	my $male = $json_data->{'male'};
	my $allmale = $json_data->{'noMaleWords'};
	my $female = $json_data->{'female'};
	my $allfemale = $json_data->{'noFemaleWords'};
	my $decades = $json_data->{'Decades'};

	my $vektorString = '';
	foreach my $decade (sort keys %$decades)
	{
		my $num = $decades->{$decade};
		$vektorString = $vektorString . '["' . $decade . '",' . $num . '],' 
	}
	$vektorString =~ s/,$//;
	$json =~ s/\{//g;
	$json =~ s/\}//g;
	$json =~ s/, "male/<br\/>"male/g;
	$json =~ s/, "female/<br\/>"female/g;
	$json =~ s/, "Decades/<br\/>"Decades/g;
	$json =~ s/:/: /g;
	$json =~ s/"//g;

	my $arguments = $male . " " . $female . " " . $allmale . " " . $allfemale;
	my $proptestPvalue = getRstats($arguments, $scriptpath, $proptest);
	my $returnvalue = &printJavascript($vektorString, $json, $male, $female, $proptestPvalue);
}
else
{
	&printJavascript();
}
exit;


sub printJavascript
{
	my ($data, $jsonCopy, $msex, $fsex, $pvalue) = @_;

	print $mycgi->header(-charset => 'utf-8');
	print "<!DOCTYPE html\">\n";
	my $htmlContent = &prepareHtml($data, $jsonCopy, $msex, $fsex, $pvalue);
	print $htmlContent;
}


sub getthestats
{

	my ($path, $localJson) = @_;

	my $url = $path . '?json=' . $localJson;
	my $result = get($url);
	die "Couldn't get it!" unless defined $result;
	return $result;

}


sub getRstats
{

	my ($args, $path, $script) = @_;

	my $command = 'Rscript ' . $path . $script . ' ' . $args;
#	print "<p>$command</p>";
	my $result = `$command`;
	die "Couldn't get it!" unless defined $result;
	my @output = split/\n/, $result;
	my $pvalue = '';
	foreach (@output)
	{
		if (/p-value/)
		{
			$pvalue = $_;
		}
	}
	$pvalue =~ s/^(.*)p-value = (.*)/$2/;
	if ($pvalue =~ /e/)
	{
		$pvalue = "< 0.001";
	}
#	print "<p>$pvalue</p>";
	return $pvalue;
}


sub prepareHtml
{
	my ($vektor,  $myJSON, $male, $female, $pval) = @_;
#print <<HTML;
#$vektor = '1900';
my $html = <<"HTMLEND";
<html>
<head>
<!--Load the AJAX API-->
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
<script type="text/javascript">
// Load the Visualization API and the corechart package.
google.charts.load('current', {'packages':['corechart']});
// Set a callback to run when the Google Visualization API is loaded.
google.charts.setOnLoadCallback(drawChart);
// Callback that creates and populates a data table,
// instantiates the pie chart, passes in the data and
// draws it.
function drawChart() {
// Create the data table.
var data = new google.visualization.DataTable();
data.addColumn('string', 'Decade');
data.addColumn('number', 'Words');
data.addRows([
$vektor
//["1900", 1943372],
//["1910", 1700990],
//["1920", 2043234], 
//["1930", 1799257], 
//["1940", 1255643], 
//["1950", 904719],
//["1960", 925106], 
//["1970", 1042326], 
//["1980", 1529115], 
//["1990", 1143289], 
//["2000", 755679], 
//["2010", 1407688]
]);
// Set chart options
var options = {'title':'No. of words per mil. per decade', 'width':700, 'height':500};
// Instantiate and draw our chart, passing in some options.
var chart = new google.visualization.BarChart(document.getElementById('chart_div'));
chart.draw(data, options);
}
</script>
</head>
<body>
<!--Div that will hold the pie chart-->
<div id="chart_div"></div>
<div id="raw_data"><p>Male / Female per mil.: $male / $female (prop.test <i>p</i> $pval)</p><p>$myJSON</p></div>
</body>
</html>
HTMLEND

return $html;

}