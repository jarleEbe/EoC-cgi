#!/usr/bin/perl -w

#Ebeling, USIT, 26.01.2017.

use strict;
use CGI;
use CGI::Carp;
use LWP::Simple;
use JSON;
use Data::Dumper;
use Encode qw(decode encode);
use utf8;
use HTML::Entities;

binmode STDIN, ":utf8";

#nabu
# 
my $css_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $general_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $action = "http://127.0.0.1/cgi-bin/cbf";
my $contextaction = "http://127.0.0.1/cgi-bin/cbf/CBFcontext.cgi?id=";
my $source_path = "http://127.0.0.1/hf/ilos/cbf/source";
my $js_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $stats_path = "http://127.0.0.1/cgi-bin/cbf/CBFstats.cgi?json=";

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $searchstring = $mycgi->param('searchstring') || "";
my $decade = $mycgi->param('decade') || "";
my $sex = $mycgi->param('sex') || "";
my $sortkrit = $mycgi->param('sort') || "";
my $maxcontext = $mycgi->param('maxcontext') || 1000;
my $maxshow = $mycgi->param('maxshow') || 1000000;

my $filters = "";
if (defined($sex) && $sex ne '')
{
	$filters = "sex=" . lc($sex);
}
if (defined($decade) && $decade ne '')
{
	$filters = $filters . "decade=" . $decade;
}

my @contextvalues = ();
my %contextlabels = ();

my $maxlines = '5000';
my $tablestart = "<table align='center' border='0' cellpadding='0' cellspacing='0' width='98%'>\n";
my $tableend = "</table>\n";

my @output = ();
my $numbhits = 0;
my $male = 0;
my $female = 0;
my $numberoftexts = 0;
my $statsString = '';

if ($searchstring)
{
	&print_header($searchstring);

	my $result = &searching($searchstring, $maxlines, $filters);

	my $json_data = decode_json($result);
	my $reqnumberofhits = $json_data->{'requestednoHits'};
	my $actualnumberofhits = $json_data->{'numberofHits'};

	my $male = $json_data->{'male'};
	my $female = $json_data->{'female'};
	my $nomaletexts = $json_data->{'noMaleTexts'};
	my $nofemaletexts = $json_data->{'noFemaleTexts'};
	my $numberoftexts = $json_data->{'numberofTexts'};

	my $numberofhits = $json_data->{'numberofHits'};
	for (my $ind = 0; $ind < $numberofhits; $ind++)
	{
		my $sunit = $json_data->{'Hits'}->[$ind]->{'sunit'};
		$sunit = encode('utf-8', $sunit);
		my $sex = $json_data->{'Hits'}->[$ind]->{'sunit'};
		my $source = $json_data->{'Hits'}->[$ind]->{'sunitId'};
		my $textid = $json_data->{'Hits'}->[$ind]->{'textId'};
		$numbhits++;
		$sunit =~ s/(.*?)(<b>.+<\/b>)(.*)/$1$2$3/i;
		my $leftcontext = $1 || "";
		if (length($leftcontext) > $maxcontext)
		{
			$leftcontext = reverse($leftcontext);
			$leftcontext = substr($leftcontext, 0, $maxcontext);
			$leftcontext = "&hellip;" . reverse($leftcontext);
		}

		my $keyword = $2 || "";
		my $rightcontext = $3 || "";
		if (length($rightcontext) > $maxcontext)
		{
			$rightcontext = substr($rightcontext, 0, $maxcontext) . "&hellip;";
		}

#		$keyword =~ s/<b>/<span name="kw" class="keyword" onclick="javascript:goto_context2('$contextaction', $source, '')">/;
#		$keyword =~ s/<\/b>/<\/span>/;
		my $link = $contextaction . $source;
		$keyword =~ s/<b>/<a style="text-decoration: none; color: #000000" href="$link">/;
		$keyword =~ s/<\/b>/<\/a>/;

		push(@output, "$leftcontext\t$keyword\t$rightcontext\t$source\t$textid");
	}
	if ($sortkrit)
	{
		&sort_kwic;
	}
	
	my $concordance = "";
	($concordance, $numbhits) = &build_output($numbhits, $source_path);
	$concordance = $tablestart . $concordance . $tableend;
	my $decades = $json_data->{'Decades'};
#	print Dumper($decades);
	my $decadesstring = '';
#$json = '{"Decades" : { "1990": 2, "1980": 6, "1940": 2, "1950": 2, "1960": 1, "1970": 4, "1920": 1, "1930": 5, "1910": 2, "2010": 1, "1900": 4}, "female": 9, "male": 21, "totnoWords": 30 }';
	$statsString = '{"totnoWords":' . $numbhits . ', "male":' .$male . ', "female":' . $female . ', "Decades": {';
	foreach my $key (sort(keys(%$decades)))
	{
#		print $key;
#		print $decades->{$key};
		$statsString = $statsString . '"' . $key . '":' . $decades->{$key} . ", ";  
		$decadesstring = $decadesstring . $key . ' : ' . $decades->{$key} . ', ';
	}
	$decadesstring =~ s/, $//;
	$statsString =~ s/, $//;
	$statsString = $statsString . '}}';
	my $statsLink = "<a href='" . $stats_path . $statsString . "' target='CBFstats'> More statistics</a>";
	$concordance = "<center>" . $numbhits  . " hits in " . $numberoftexts . " texts<br/>(male: " . $male . " (" . $nomaletexts . " texts) / female " . $female . " (" . $nofemaletexts . " texts)) " . $statsLink . "<br/>" . $decadesstring . "</center>" . "<br/>" . $concordance;
	print $concordance;
}
else
{
	&print_header("");
}
print $mycgi->end_html;
exit;

sub searching
{
	my ($query, $nohits, $filters) = @_;

#	print $query;
	$query = decode('utf-8', $query);
#	print $query;
	my $url = 'http://127.0.0.1/cgi-bin/cbf/rawcbfsearch.cgi?' . 'q=' . $query . '&nohits=' . $nohits . '&filter=' . $filters;
	my $result = get($url);
	die "Couldn't get it!" unless defined $result;
#	print $result;
	$result = encode('utf-8', $result);
#	print $result;
	return $result;
}

sub print_header
{
	my $ss = shift(@_);
	print "Content-Type: text/html; charset=utf-8\n\n";
	print "<!DOCTYPE html>\n";
	print "<html>\n";
	print "<head><title>CBFsearch</title>\n";
#	print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n";
	print "<link rel='stylesheet' type='text/css' href='$css_path/OMCsearch.css'/>\n";
	print "<script src='$js_path/selectcorpus.js'></script>\n";
	print "</head>\n";
	print "<body>\n";
	print "<form name='readcorpus' method='POST' action='$action/CBFsearch.cgi'>\n";
	print "<table align='center' width='789' border='0' cellpadding='0' cellspacing='0'>\n";
	print "<tr bgcolor='#FFD112'><td>";
	print "<img src='$general_path/ENPCbanner3.gif' width='450' height='25' border='0' alt='' usemap='#logomini_Map'/>";
	print "<map name='logomini_Map'>";
	print "<area shap='rect' title='UiO' COORDS='0,0,75,31' HREF='http://www.uio.no/' target='_self'/>";
	print "</map></td>\n";
	print "<td align='right'><a href='$general_path/search_help.html'>Search help</a></td></tr>\n";
	print "<tr><td align='right'><p class='marg2'>\n";
	print "<input name='searchstring' size='40' value='$ss'/>";
	print "<input type='submit' value='Search'>";
	print "</p></td>\n";
	print "<td align='right'><p class='marg2'>Decade \n";
	print $mycgi->popup_menu(-name=>'decade', -values=>['', '1900', '1910', '1920', '1930', '1940', '1950', '1960', '1970', '1980', '1990', '2000', '2010']);
	print "&nbsp;Sex";
	print $mycgi->popup_menu(-name=>'sex', -values=>['', 'Female', 'Male']);
	print "</p></td></tr>\n";
	print "<tr><td align='right'><p class='marg2'>\n";
	print "Sort concordance by ";
	print $mycgi->popup_menu(-name=>'sort', -values=>['keyword', 'right word', 'left word', 'source', '']);
	print "</p></td><td align='right'><p class='marg2'>";
	@contextvalues = ('59', '1000', '2000');
	%contextlabels = ('59' => 'kwic', '1000' => 's-unit', '2000' => 'tab');
	print "Choose kwic or s-unit layout ";
	print $mycgi->popup_menu(-name=>'maxcontext', -values=>\@contextvalues, -labels=>\%contextlabels);
	print "</p></td></tr>\n";
	print "<tr><td colspan='2'><hr/>\n";
	print "</td></tr></table>\n";
	print "</form>";
}


sub sort_kwic
{

	my $krit = "";
	my $pad = "                           ";
	my @matrix = ();
	foreach my $kline (@output)
	{
		if ($sortkrit eq 'right word')
		{
			$krit = &get_rightkrit($kline);	
			my $krit2 = &get_keykrit($kline);
			$krit2 =~ s/<[^>]+?>//;
			$krit = "$krit$pad$krit2";
		}
		elsif ($sortkrit eq 'left word')
		{
			$krit = &get_leftkrit($kline);	
			my $krit2 = &get_keykrit($kline);
			$krit2 =~ s/<[^>]+?>//;
			$krit = "$krit$pad$krit2";
		}
		elsif ($sortkrit eq 'keyword')
		{
			$krit = &get_keykrit($kline);
			my $krit2 = &get_rightkrit($kline);
			$krit =~ s/<[^>]+?>//;

			if (defined($krit2))
			{
				$krit = "$krit$pad$krit2";
			}
			else
			{
				$krit = "$krit$pad";
			}
		}
		elsif ($sortkrit eq 'source')
		{
			$krit = &get_sourcekrit($kline);
			my $krit2 = &get_keykrit($kline);
			$krit =~ s/<[^>]+?>//;
			$krit = "$krit$pad$krit2";
		}
		$krit = lc($krit);
		push @matrix, ([$krit, $kline]);
	}

	@matrix = sort { $a->[0] cmp $b->[0] } @matrix;
	@output = ();
	my $numlines = @matrix;
	for (my $i = 0; $i < $numlines; $i++)
	{
		push(@output, $matrix[$i][1]);
	}
}


sub get_rightkrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $tid) = split/\t/, $temp;
	$right =~ s/&mdash;//g;
	$right =~ s/^\W+//;
	my @krits = split/ /, $right;
	
	return $krits[0];
}

sub get_leftkrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $tid) = split/\t/, $temp;
	$left =~ s/&mdash;//g;
	$left = reverse($left);
	$left =~ s/^\W+//;
	my @krits = split/ /, $left;
	my $lfk = reverse($krits[0]);
	$lfk =~ s/^\W+//;
	return $lfk;
}

sub get_keykrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $tid) = split/\t/, $temp;
	return $key;
}

sub get_sourcekrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $tid) = split/\t/, $temp;
	$source =~ s/\[//;
	$source =~ s/\]//;
	$source =~ s/<[^>]+>//g;
	return $source;
}


sub build_output
{
	my ($nh, $tlink) = @_;
	my $kwic_line = "";
	$tlink = '<a target="CBFheader" href="' . $tlink;
	foreach my $kline (@output)
	{
		my ($left, $key, $right, $source, $tid) = split/\t/, $kline;
		my $newsource = $tlink . '/' . $tid . '_header.xml">' . $source . '</a>';
		if ($maxcontext == 1000)
		{
			$kwic_line = $kwic_line. "<tr><td align='left'>" . $left . $key . $right . " [" . $newsource . "]</td></tr><tr><td align='left'></td></tr>\n";
		}
		elsif ($maxcontext == 59)
		{
			$kwic_line = $kwic_line. "<tr><td align='right'>" . $left . "</td><td align='center'>" . $key . "</td><td align='left'>" . $right . " [" . $newsource . "]</td></tr><tr><td colspan='3' align='center'></td></tr>\n";
		}
		elsif ($maxcontext == 2000)
		{
		    $left  =~ s/<([^>]+?)>//g;
		    $right =~ s/<([^>]+?)>//g;
		    $key =~   s/<([^>]+?)>//g;
		    $source =~ s/<([^>]+?)>//g;
		    $left =~ s/^ //;
		    $kwic_line = $kwic_line . $left . "\t" . $key . "\t" . $right . "\t" . $newsource . "\n";
		}
	}
	return $kwic_line, $nh;
}

sub skrell
{
	my $temp = shift(@_);

	$temp =~ s/<[^>]+?>//g;

	return $temp;
}

sub blanks
{
	my $temp = shift(@_);
	
	$temp =~ s/^ //;
	$temp =~ s/ $//;
	$temp =~ s/\s+/ /g;
	$temp =~ s/, /,/g;

	return $temp;
}
