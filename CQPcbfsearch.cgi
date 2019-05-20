#!/usr/bin/perl -w

#Ebeling, USIT, 4.4.2019

use strict;
use CGI;
use CGI::Carp;
use IPC::Open2;
use LWP::Simple;
use JSON;
use Data::Dumper;
use Encode qw(decode encode);
use utf8;
use HTML::Entities;

binmode STDIN, ":utf8";

#All hosts / general paths
my $css_path = "https://nabu.usit.uio.no/hf/ilos/cbf/imagecssjs";
my $general_path = "https://nabu.usit.uio.no/hf/ilos/cbf/imagecssjs";
my $source_path = "https://nabu.usit.uio.no/hf/ilos/cbf/source";
my $LL_path = "https://nabu.usit.uio.no/hf/ilos/cbf/LL";
my $js_path = "https://nabu.usit.uio.no/hf/cbf/ilos/imagecssjs";

#For cache files used in R/Shiny
my $cachefile = "/var/www/html/hf/ilos/cbf/cache/";

#Path to CQP registryfiles
my $cbfregistry = "/usr/local/share/cwb/registry";

#Paths for localhost
my $action = "http://127.0.0.1/cgi-bin/cbf";
my $stats_path = "http://127.0.0.1/cgi-bin/cbf/CBFstats.cgi?json=";
my $urlcache = "http://127.0.0.1/hf/ilos/cbf/cache/";
my $shinypathnormal = "http://127.0.0.1:6989";
my $shinypathcompare = "http://127.0.0.1:6989";

#Paths for server (e.g. itfds-utv05)
#my $action = "http://itfds-utv05.uio.no/cgi-bin/cbf";
#my $stats_path = "http://itfds-utv05.uio.no/cgi-bin/cbf/CBFstats.cgi?json=";
#my $urlcache = "http://itfds-utv05.uio.no/hf/ilos/cbf/cache/";
#my $shinypathnormal = "http://itfds-utv05.uio.no/shiny/cbf/normaldist";
#my $shinypathcompare = "http://itfds-utv05.uio.no/shiny/cbf/compareperiods";

my $requestIP = $ENV{'REMOTE_ADDR'};
my $randomno = rand();
$randomno =~ s/^(\d+)\.//;
$cachefile = $cachefile . 'resultJSON_' . $requestIP . '-' . $randomno . '.txt';

my $cacheFlag = 0;
my $htmlfile = '';
my $nbmessage = '';

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $searchstring = $mycgi->param('searchstring') || "";
my $decade = $mycgi->param('decade') || "";
my $gender = $mycgi->param('gender') || "";
my $genre = $mycgi->param('genre') || "";
my $sortkrit = $mycgi->param('sort') || "";
my $maxcontext = $mycgi->param('maxcontext') || 59;
my $maxshow = $mycgi->param('maxshow') || 1000000;

my @contextvalues = ();
my %contextlabels = ();

#NB! Constants
my $absolutemax = 25000; #Max number of hits counted

if ($maxcontext == 4000) #No display of KWIC lines
{
	$absolutemax = 1000000;
}

my $maxkwiclines = 2500; #Max number of lines output
my $tablestart = "<table align='center' border='0' cellpadding='0' cellspacing='0' width='98%'>\n";
my $tableend = "</table>\n";

my @output = ();
my $numbhits = 0;
my $male = 0;
my $female = 0;
my $numberoftexts = 0;
my $statsString = '';
my $cqpsearch = '';

my %orig = (); #Text code
my %empty = (); #Hits per text

my %tgender = (); #Text's author's gender
my %ttypes = (); #Text's number of types (as opposded to tokens)
my %thapax = (); #Text's texts number og hapax

my %tgenre = (); #Text's genre
my %sgenres = (); #The genres to include in search. 

my %tdecade = (); #Text's decade
my %sdecades = (); #The decades to include in search
my $totnotexts = 0;
my $concordance = "";
my $maxconcordance = "";

$totnotexts = &readcbf_json();

if ($searchstring)
{
	&print_header($searchstring, "screen");

	my $numbhits = 0;
	my $totalhits = 0;
	my @cqpresult = ();

    if ($decade eq '00-30')
    {
			$sdecades{"1900"} = "1900";
			$sdecades{"1910"} = "1910";
			$sdecades{"1920"} = "1920";
			$sdecades{"1930"} = "1930";
    }
    elsif ($decade eq '40-70')
    {
			$sdecades{"1940"} = "1940";
			$sdecades{"1950"} = "1950";
			$sdecades{"1960"} = "1960";
			$sdecades{"1970"} = "1970";
    }
    elsif ($decade eq '80-10')
    {
			$sdecades{"1980"} = "1980";
			$sdecades{"1990"} = "1990";
			$sdecades{"2000"} = "2000";
			$sdecades{"2010"} = "2010";
    }
    else
    {
			$sdecades{$decade} = $decade;
    }


	($numbhits, $totalhits, $cqpsearch, @cqpresult) = &cqp($cbfregistry, $searchstring, $decade, $gender, $genre, $sortkrit, $maxcontext, $absolutemax);

    my $result = &cqptoJSON($searchstring, $absolutemax, @cqpresult);

	$result = encode('utf-8', $result);
	my $json_test = eval {decode_json($result)};
	if ($@)
	{
		print "decode_json failed, invalid json. Report error: $@ Try searching with another layout option, e.g. s-unit ot tab.\n";
	}

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
		my $gender = $json_data->{'Hits'}->[$ind]->{'sunit'};
		my $source = $json_data->{'Hits'}->[$ind]->{'sunitId'};
		$source =~ s/\. /\./;
		my $textid = $json_data->{'Hits'}->[$ind]->{'textId'};
		if (exists($empty{$textid}))
		{
			my $ttemp = $empty{$textid};
			$ttemp++;
			$empty{$textid} = $ttemp;
		}

		$sunit =~ s/(.*)<([^>]+?)>(.*)/$1$2$3/i;
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
		$keyword = '<a style="text-decoration: none; color: #000000; font-weight: bold">' . $keyword . '</a>';
		push(@output, "$leftcontext\t$keyword\t$rightcontext\t$source\t$textid");
	}
	if ($sortkrit eq 'source')
	{
		&sort_kwic;
	}
	
	$concordance = "";
	$maxconcordance = "";
	$nbmessage = '';
	if ($numbhits >= $maxkwiclines && $maxcontext != 4000)
	{
		$nbmessage = $nbmessage . "<center><p>Tot. numb of hits exceeds $maxkwiclines. Displaying $maxkwiclines only. See link bottom of page.</p></center>";
		$cacheFlag = 1;
	}
	if ($numbhits >= $absolutemax && $maxcontext != 4000)
	{
		$nbmessage = $nbmessage . "<center><p>Tot. numb of hits exceeds $absolutemax. Result set reduced to $absolutemax.</p></center>";
	}

	if ($maxcontext == 4000)
	{

	}
	else
	{
		($concordance, $maxconcordance, $numbhits) = &build_output($numbhits, $source_path, $maxkwiclines);
	}

	print "<p>$nbmessage</p>";

	$concordance = $tablestart . $concordance . $tableend;
	my $decades = $json_data->{'Decades'};
	my $decadesstring = '';
	$statsString = '{"totnoWords":' . $numbhits . ', "male":' .$male . ', "female":' . $female . ', "Decades": {';
	foreach my $key (sort(keys(%$decades)))
	{
		$statsString = $statsString . '"' . $key . '":' . $decades->{$key} . ", ";  
		$decadesstring = $decadesstring . $key . ' : ' . $decades->{$key} . ', ';
	}
	$decadesstring =~ s/, $//;
	$statsString =~ s/, $//;
	$statsString = $statsString . '}}';
	my $statsLink = "<a href='" . $stats_path . $statsString . "' target='CBFstats'> More statistics</a>";

	my $genres = $json_data->{'Genres'};
	my $genresstring = '';
	foreach my $key (sort(keys(%$genres)))
	{
		$genresstring = $genresstring . $key . ' : ' . $genres->{$key} . ', ';
	}
	$genresstring =~ s/, $//;

	$concordance = "<center>" . $numbhits  . " hits in " . $numberoftexts . " of " . $totnotexts . " texts<br/>(male: " . $male . " (" . $nomaletexts . " texts) / female " . $female . " (" . $nofemaletexts . " texts)) " . $statsLink . "<br/>" . $genresstring . "<br/>" . $decadesstring . "</center>" . "<br/>" . $concordance;
	print $concordance;
	print "<hr/>";
	my %shinyhash = ();
	if ($maxcontext != 2000)
	{
		print "<table border='1' cellpadding='2' cellspacing='2'>";
		print "<tr><td>Text code</td><td>Tot. words</td><td>No. of hits</td><td>Hits per 100,000</td><td>Decade</td><td>Gender</td><td>Tertial</td><td>Genre</td><td>Types</td><td>Hapax</td><td>Hapax %</td></tr>";
		foreach my $key (sort(keys(%orig)))
		{
			my $sum = $orig{$key};
			my $actualno = $empty{$key};
			my $perht = 0.0;
			my $tertial = 'NA';
			my $thpercent = 0;
			if ($gender eq '' || $tgender{$key} eq $gender)
			{
				if ($decade eq '' || exists($sdecades{$tdecade{$key}}))
				{
					if ($actualno > 0)
					{
						my $log_likelihood_link = $LL_path . '/' . $key . '-WLL.html';
						print "<tr><td><a href='$log_likelihood_link'>$key</a></td><td style='text-align:right'>$orig{$key}</td>";
						print "<td style='text-align:right'>$empty{$key}</td>";

						$perht = ($actualno / $sum) * 100000;
						$perht = sprintf("%.1f", $perht);
						my $ltemp = $tdecade{$key};
						my $tiaar = int($ltemp);
						$tertial = "all";
						if ($tiaar >= 1900 && $tiaar < 1940)
						{
							$tertial = "1900-1939";
						}
						elsif ($tiaar >= 1940 && $tiaar < 1980)
						{
							$tertial = "1940-1979";
						}
						else
						{
							$tertial = "1980-2020";
						}
						$shinyhash{$key} = $orig{$key} . "\t" . $empty{$key} . "\t" . $perht . "\t" . $tdecade{$key} . "\t" . $tgender{$key} . "\t" . $tertial;

						$thpercent = ($thapax{$key} / $ttypes{$key}) * 100;
						$thpercent = sprintf("%.1f", $thpercent);
						print "<td style='text-align:right'>$perht</td>";
						print "<td style='text-align:center'>$tdecade{$key}</td>";
						print "<td style='text-align:center'>$tgender{$key}</td>";
						print "<td style='text-align:center'>$tertial</td>";
						print "<td style='text-align:center'>$tgenre{$key}</td>";
						print "<td style='text-align:center'>$ttypes{$key}</td>";
						print "<td style='text-align:center'>$thapax{$key}</td>";
						print "<td style='text-align:center'>$thpercent</td></tr>";
					}
				}
			}
		}
		print "</table>";
	}
	else
	{
		print "<pre>\n";
		print "TextCode\tTotNoWords\tNoOfHits\tHitsPer100k\tDecade\tGender\tTertial\tGenre\tTypes\tHapax\n";
		foreach my $key (sort(keys(%orig)))
		{
			my $sum = $orig{$key};
			my $actualno = $empty{$key};
			my $perht = 0.0;
			my $tertial = 'NA';
			my $thpercent = 0;
			if ($gender eq '' || $tgender{$key} eq $gender)
			{
				if ($decade eq '' || exists($sdecades{$tdecade{$key}}))
				{
					print "$key\t$orig{$key}\t";
					print "$empty{$key}\t";
					if ($actualno > 0)
					{
						$perht = ($actualno / $sum) * 100000;
						$perht = sprintf("%.1f", $perht);
						my $ltemp = $tdecade{$key};
						my $tiaar = int($ltemp);
						$tertial = "all";
						if ($tiaar >= 1900 && $tiaar < 1940)
						{
							$tertial = "1900-1939";
						}
						elsif ($tiaar >= 1940 && $tiaar < 1980)
						{
							$tertial = "1940-1979";
						}
						else
						{
							$tertial = "1980-2020";
						}
						$shinyhash{$key} = $orig{$key} . "\t" . $empty{$key} . "\t" . $perht . "\t" . $tdecade{$key} . "\t" . $tgender{$key} . "\t" . $tertial;
						$thpercent = ($thapax{$key} / $ttypes{$key}) * 100;
						$thpercent = sprintf("%.1f", $thpercent);
					}
					print "$perht\t";
					print "$tdecade{$key}\t";
					print "$tgender{$key}\t";
					print "$tertial\t";
					print "$tgenre{$key}\t";
					print "$ttypes{$key}\t";
					print "$thapax{$key}\n";
					print "$thpercent\n";
				}
			}
		}
		print "</pre>";
	}
	print "<hr/>";
	print "<p>The search string sent to cqp: $cqpsearch</p>";
	my $returnvalue = &toShiny(%shinyhash);
	my $parameter = $cachefile;
	$parameter =~ s/^(.+)resultJSON/resultJSON/;
	print "<a href='$shinypathnormal/?filename=$parameter' target='Shiny1'>Normal distribution?</a>";
	print " | ";
	print "<a href='$shinypathcompare/?filename=$parameter' target='Shiny2'>Compare periods</a>";
	open(CACHE, ">$cachefile");
	binmode CACHE, ":utf8";
	print CACHE "$returnvalue";
	close(CACHE);
	if ($cacheFlag == 1)
	{
		$htmlfile = $cachefile;
		$htmlfile =~ s/\.txt/\.html/;
		open(CACHE, ">$htmlfile");
		print CACHE "<!DOCTYPE html>\n";
		print CACHE "<html>\n";
		print CACHE "<head><title>CQPcbfsearchresult</title>\n";
		print CACHE $tablestart;
		print CACHE $maxconcordance;
		print CACHE $tableend;
		print CACHE "</body></html>";
		close(CACHE);
		$htmlfile =~ s/^(.+)resultJSON/resultJSON/;
		$htmlfile = $urlcache . $htmlfile;
		print "<br/><a href='$htmlfile' target='CQPcbfsearchresult'>Search result</a>";
	}
}
else
{
	&print_header("", "screen");
	my $startmessage = '<center><p>Enter a searchstring (word, LEMMA or part of speech), and click the Search button.<br/>';
	$startmessage = $startmessage . '<tr><td>More help and info here:' . '<a href="https://nabu.usit.uio.no/hf/ilos/cbf/cbfhelp.html">CBF help</p></center>';
	print $startmessage;
}
print $mycgi->end_html;
exit;


sub print_header
{
	my ($ss, $medium) = @_;
	if ($medium eq "screen")
	{
		print "Content-Type: text/html; charset=utf-8\n\n";
	}
	print "<!DOCTYPE html>\n";
	print "<html>\n";
	print "<head><title>CQPcbfsearch</title>\n";
	print "<link rel='stylesheet' type='text/css' href='$css_path/OMCsearch.css'/>\n";
	print "<script src='$js_path/selectcorpus.js'></script>\n";
	print "</head>\n";
	print "<body>\n";
	print "<form name='readcorpus' method='POST' action='$action/CQPcbfsearch.cgi'>\n";
	print "<table align='center' width='789' border='0' style='padding:0; border-spacing:0'>\n";
	print "<tr bgcolor='#000000'>\n";
	print "<td style='text-align:left; color:white; font-size:16px; font-weight:bold'>";
	print "<img src='$general_path/cbf_blur3.png' style='border:0; vertical-align:middle' alt='banner' usemap='#cbfhelp_map'/>";
	print "<map name='cbfhelp_map'>";
	print "<area shap='rect' title='CBF help' coords='0,0,75,28' href='http://nabu.usit.uio.no/hf/ilos/cbf/cbfhelp.html' target='_self'/>";
	print "&nbsp;&nbsp;<span style='vertical-align:middle'>Corpus of British Fiction</span></map></td>\n";
	print "<td style='text-align:right'><img src='$general_path/uiocbfbannersmall.png' border='0' alt='banner' usemap='#logomini_map'/>";
	print "<map name='logomini_map'>";
	print "<area shap='rect' title='UiO' coords='0,0,195,31' href='http://www.uio.no/' target='_self'/>";
	print "</map></td>\n";
	print "</tr>\n";
	print "<tr><td align='left'><p class='marg2'>\n";
	print "<input name='searchstring' size='50' value=\"$ss\"/>";
	print "<input type='submit' value='Search'>";
	print "</p></td>\n";
	print "<td align='right'><p class='marg2'>Decade \n";
	print $mycgi->popup_menu(-name=>'decade', -values=>['', '1900', '1910', '1920', '1930', '1940', '1950', '1960', '1970', '1980', '1990', '2000', '2010', '00-30', '40-70', '80-10']);
	print "&nbsp;Gender of author ";
	print $mycgi->popup_menu(-name=>'gender', -values=>['', 'female', 'male']);
	print "</p></td></tr>\n";
	print "<tr><td align='left'><p class='marg2'>\n";
	print "Sort concordance by ";
	print $mycgi->popup_menu(-name=>'sort', -values=>['keyword', 'right word', 'left word', 'source', 'random', '']);
	@contextvalues = ('59', '1000', '2000', '1500', '3000', '4000');
	%contextlabels = ('59' => 'kwic', '1000' => 's-unit', '2000' => 'tab', '1500' => 's-unit5', '3000' => 's-unitT', '4000' => 'empty');
	print "&nbsp;&nbsp;Choose kwic or other layout ";
	print $mycgi->popup_menu(-name=>'maxcontext', -values=>\@contextvalues, -labels=>\%contextlabels);
	print "</p></td>";
	print "<td align='right'><p class='marg2'>Genre ";
	print $mycgi->popup_menu(-name=>'genre', -values=>['', 'adventure', 'crime', 'general', 'historical', 'romance', 'spy', 'war']);
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
		if ($sortkrit eq 'source')
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

sub get_keykrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $tid) = split/\t/, $temp;
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
	my ($nh, $tlink, $maxKW) = @_;
	my $kwic_line = "";
	my $display_line = "";
	$tlink = '<a target="CBFheader" href="' . $tlink;
	if ($#output > $maxKW)
	{
	}
	my $index = 0;
	foreach my $kline (@output)
	{
		$index++;
		my ($left, $key, $right, $source, $tid) = split/\t/, $kline;
		my $newsource = $tlink . '/' . $tid . '_header.xml">' . $source . '</a>';
		if ($maxcontext == 1000 || $maxcontext == 1500 || $maxcontext == 3000) #s-unit / sentence output
		{
			$kwic_line = $kwic_line. "<tr><td align='left'>" . $left . $key . $right . " [" . $newsource . "]<br/><br/></td></tr><tr><td align='left'></td></tr>\n";
		}
		elsif ($maxcontext == 59) #KWIC output
		{
			$kwic_line = $kwic_line. "<tr><td align='right'>" . $left . "</td><td align='center'>" . $key . "</td><td align='left'>" . $right . " [" . $newsource . "]</td></tr><tr><td colspan='3' align='center'></td></tr>\n";
		}
		elsif ($maxcontext == 2000) #tab-separated output
		{
		    $left  =~ s/<([^>]+?)>//g;
		    $right =~ s/<([^>]+?)>//g;
		    $key =~ s/<([^>]+?)>//g;
		    $source =~ s/<([^>]+?)>//g;
		    $left =~ s/^ //;
		    $kwic_line = $kwic_line . $left . "\t" . $key . "\t" . $right . "\t" . $source . "\n";
		}
		if ($index <= $maxKW)
		{
			$display_line = $kwic_line;
		}
	}
	if ($maxcontext == 2000)
	{
		$kwic_line = "<pre>\n" . $kwic_line . "</pre>\n";
		$display_line = "<pre>\n" . $display_line . "</pre>\n";
	}
	return $display_line, $kwic_line, $nh;
}


sub build_simple_output
{

	my ($maxKW) = @_;
	if ($#output > $maxKW)
	{
		$#output = $maxKW;
	}
	foreach my $kline (@output)
	{
		my ($left, $key, $right, $source, $tid) = split/\t/, $kline;
	}
	return;
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

sub readcbf_json
{

	open(JSONFILE, "cbf.json");
	my @content = <JSONFILE>;
	close(JSONFILE);

	my $jsonfromfile = join(" ", @content);
	my $json_data = decode_json($jsonfromfile);
	my $numberoftexts = $json_data->{'noTexts'};
	my $textcodes = $json_data->{'Texts'};

	foreach my $key (sort(keys(%$textcodes)))
	{
		$orig{$key} = $textcodes->{$key}->{'noWords'};
		$tgender{$key} = $textcodes->{$key}->{'Gender'};
		$tgenre{$key} = $textcodes->{$key}->{'Genre'};
		$ttypes{$key} = $textcodes->{$key}->{'Types'};
		$thapax{$key} = $textcodes->{$key}->{'Hapax'};
		$tdecade{$key} = $textcodes->{$key}->{'Decade'};
		$empty{$key} = 0;
	}

	return $numberoftexts;
}

sub cqp
{

    my ($CBFregistry, $search, $decennium, $gofA, $CBFgenre, $skriterium, $display, $maxtocount) = @_;

##Path to CQP depends on where it was installed and version
#Localhost
    my $pid = open2 my $out, my $in, "/usr/local/cwb-3.4.13/bin/cqp -c" or die "Could not open cqp";
#itfds-utv05
#    my $pid = open2 my $out, my $in, "/usr/local/bin/cqp -c " or die "Could not open cqp";

#itfds-utv01 (old/depricated)
#    my $pid = open2 my $out, my $in, "/usr/local/cwb-3.4.12/bin/cqp -c -D CBF" or die "Could not open cqp";

	$out->autoflush();
	$in->autoflush();
	STDIN->autoflush();
	STDOUT->autoflush();

    my $opened = <$out>;

#Point to registry file, choose corpus and decide what to output to <$out> with the 'set' command in CQP
    print $in "set Registry '" . $CBFregistry . "';\n";
    print $in "CBF;\n";
    print $in "set PrintStructures 'text_id, text_gender, text_genre, text_decade';\n";


#Based on user's choices, decide how to display the hits
	if ($display eq '1000')
	{
   		print $in "set Context 1 s;\n";
	}
	elsif ($display eq '1500')
	{
    	print $in "set Context 5 s;\n"; 	
	}
	elsif ($display eq '59')
	{
    	print $in "set Context 59;\n"; 	
	}
	elsif ($display eq '2000')
	{
    	print $in "set Context 100;\n";		
	}
	elsif ($display eq '3000')
	{
		print $in "show +pos +lemma;\n";
    	print $in "set Context 1 s;\n";		
	}

#Add filters gender, genre and/ or decade
	my $matching = '';
	if ($gofA)
	{
		$matching = ' :: match.text_gender = "' . $gofA . '"';
	}

#If genre is set
	if ($CBFgenre)
	{

		if ($matching)
		{
			$matching = $matching . ' & match.text_genre = "' . $CBFgenre . '"';
		}
		else
		{
			$matching = ' :: match.text_genre = "' . $CBFgenre . '"';
		}
	}
#If period is set
	if ($decennium)
	{
	    if ($decennium eq '00-30')
	    {
			$decennium = ' match.text_decade = "1900" | match.text_decade = "1910" | match.text_decade = "1920" | match.text_decade = "1930"';
	    }
	    elsif ($decennium eq '40-70')
	    {
			$decennium = ' match.text_decade = "1940" | match.text_decade = "1950" | match.text_decade = "1960" | match.text_decade = "1970"';
	    }
	    elsif ($decennium eq '80-10')
	    {
			$decennium = ' match.text_decade = "1980" | match.text_decade = "1990" | match.text_decade = "2000" | match.text_decade = "2010"';
	    }
	    else
	    {
			$decennium = ' match.text_decade = "' . $decennium . '"';
	    }

		if ($matching)
		{
			$matching = $matching . ' &' . $decennium;
		}
		else
		{
			$matching = ' ::' . $decennium;
		}
	}

	my $sokstring = '';
	$sokstring = &buildSearchString($search);

	$sokstring = $sokstring . $matching;

    print $in "sok = $sokstring;\n";
    print $in "size sok;\n";
    my $numbhits = <$out>;

    my @content = ();
	my $totalnumbhits = 0;
	if ($numbhits == 0)
	{
    	print $in "exit;\n";
    	close($in);
    	close($out);

    	waitpid($pid, 0);

    	return $numbhits, @content;
	}

	$totalnumbhits = $numbhits;

#Sorting/Reducing
	if ($numbhits > $maxtocount)
	{
		print $in "reduce sok to $maxtocount;\n";
    	print $in "size sok;\n";
		$numbhits = <$out>;
	}

	if ($skriterium eq 'right word')
	{
		print $in "sort by word %cd on matchend[1] .. matchend[42];\n";
	}
	elsif ($skriterium eq 'left word')
	{
		print $in "sort by word %cd on matchend[-1] .. matchend[-42];\n";
	}
	elsif ($skriterium eq 'random')
	{
		print $in "sort randomize;\n";
	}
	else
	{
		print $in "sort by word %cd;\n";
	}

    print $in "cat;\n";

    my $result;
    while (! ($result = <$out>))
    {
    }

    @content = ();
    push(@content, $result);

	if ($numbhits == 1)
	{

	}
	else
	{
	    for (my $ind = 1; $ind++; $ind <= $numbhits)
	    {
    	    chomp($result = <$out>);
        	push(@content, $result);
        	$result = '';
        	if ($ind >= $numbhits)
        	{
            	last;
        	}
    	}
	}

    print $in "exit;\n";
    close($in);
    close($out);

    waitpid($pid, 0);

    return $numbhits, $totalnumbhits, $sokstring, @content;
}

sub buildSearchString
{
	my ($inputstring) = @_;

#For genetive use _GE, e.g. one _GE to get one's

	if ($inputstring =~ /^\[/)
 	{
		$inputstring =~ s/word=([^ ]+?) /word='$1' /g;
		$inputstring =~ s/lemma=([^ ]+?) /lemma='$1' /g;
		$inputstring =~ s/pos=([^ ]+?) /pos='$1' /g;
		return $inputstring;
	}

	my @strings = split/ /, $inputstring;
	my $resturnstring = '';
	my $pos = '';
	foreach my $ss (@strings)
	{
		$pos = '';
		if ($ss eq '*')
		{
			$ss =~ s/\*//;
			$resturnstring = $resturnstring . '[]';
		}
		elsif ($ss =~ /^_/)
		{
			$ss =~ s/_//;
			$resturnstring = $resturnstring . '[pos="' . $ss . '"]';
		}
		elsif ($ss !~ /[a-z]/)
		{
			if ($ss =~ /_/)
			{
				($ss, $pos) = split/_/, $ss;
				$pos = ' & pos="' . $pos . '"';
			}
			$ss = lc($ss);
			$resturnstring = $resturnstring . '[lemma="' . $ss . '" %d' . $pos . ']';
		}
		else
		{
			if ($ss =~ /_/)
			{
				($ss, $pos) = split/_/, $ss;
				$pos = ' & pos="' . $pos . '"';
			}
			$resturnstring = $resturnstring . '[word="' . $ss . '" %cd' . $pos . ']';
		}
	}

	return $resturnstring;
}

sub cqptoJSON
{

    my ($thesearch, $numbreqhits, @hitsarr) = @_;

    my $allhits = '{"Hits": [';

    my $localJSON = '';
	my $male = 0;
	my $female = 0;
	my $nofemaletexts = 0;
	my $nomaletexts = 0;
	my $numbtexts = 0;
	my $numbhits = 0;
	my %decades = ();
	my %genres = ();
	my %textids = ();

    foreach my $hitsrow (@hitsarr)
    {
		$numbhits++;
        $hitsrow =~ s/(\d+): <text_id ([^>]+?)><text_gender ([^>]+?)><text_genre ([^>]+?)><text_decade ([^>]+?)>: (.*)/$1\t$2\t$3\t$4\t$5\t$6/;
        my @cols = split/\t/, $hitsrow;
		my $localid = $cols[0];
		my $textid = $cols[1];
		my $gender = $cols[2];
		my $genre = $cols[3];
		my $decade = $cols[4];
		my $sunit = $cols[5];
		my $tidlid = $textid . '.' . $localid;
		$sunit =~ s/\n//g;
		$sunit =~ s/"/&#x0022;/g;
		$sunit =~ s/\//&#x002F;/g;
		$sunit =~ s/\\//g;
        $localJSON = $localJSON . '{';
        $localJSON = $localJSON . &addtoJSON("localId", $localid, "number");
        $localJSON = $localJSON . &addtoJSON("textId", $textid, "text");
        $localJSON = $localJSON . &addtoJSON("Sex", $gender, "text");
        $localJSON = $localJSON . &addtoJSON("Genre", $genre, "text");
        $localJSON = $localJSON . &addtoJSON("Decade", $decade, "text");
       	$localJSON = $localJSON . &addtoJSON("sunit", $sunit, "text");
        $localJSON = $localJSON . &addtoJSON("sunitId", $tidlid, "text");
        $localJSON =~ s/, $//;
        $localJSON = $localJSON . '},';

		if ($gender eq 'male')
		{
			$male++;
		}
		elsif ($gender eq 'female')
		{
			$female++;
		}

		if (exists($decades{$decade}))
		{
			my $temp = $decades{$decade};
			$temp++;
			$decades{$decade} = $temp;
		}
		else
		{
			$decades{$decade} = 1;
		}

		if (exists($genres{$genre}))
		{
			my $temp = $genres{$genre};
			$temp++;
			$genres{$genre} = $temp;
		}
		else
		{
			$genres{$genre} = 1;
		}

		if (exists($textids{$textid}))
		{

		}
		else
		{
			$textids{$textid} = $gender;
			if ($gender eq 'male')
			{
				$nomaletexts++;
			}
			elsif ($gender eq 'female')
			{
				$nofemaletexts++;
			}
		}
    }

    $localJSON =~ s/,$//;
	my $decadesstring = '';
	foreach my $key (keys(%decades))
	{
		$decadesstring = $decadesstring . '"' . $key . '": ' . $decades{$key} . ', ';
	}
    $decadesstring =~ s/, $//;
	my $genresstring = '';
	foreach my $key (keys(%genres))
	{
		$genresstring = $genresstring . '"' . $key . '": ' . $genres{$key} . ', ';
	}
    $genresstring =~ s/, $//;


	$numbtexts = keys(%textids);
	my $sums = '"searchstring": ' . '"' . $thesearch . '", ';
	$sums = $sums . '"female": ' . '"' . $female . '", ';
	$sums = $sums . '"numberofHits": ' . '"' . $numbhits . '", ';
	$sums = $sums . '"noMaleTexts": ' . '"' . $nomaletexts . '", ';
	$sums = $sums . '"noFemaleTexts": ' . '"' . $nofemaletexts . '", ';
	$sums = $sums . '"requestednoHits": ' . $numbreqhits . ', ';
	$sums = $sums . '"male": ' . '"' . $male . '", ';
	$sums = $sums . '"Genres": {' . $genresstring . '},';
	$sums = $sums . '"Decades": {' . $decadesstring . '},';
	$sums = $sums . '"numberofTexts": ' . '"' . $numbtexts . '"';

#Counts in here
    $allhits = $allhits . $localJSON . '], ' . $sums . '}';

    return $allhits;
}


sub addtoJSON
{
    my ($attr, $value, $vtype)  = @_;

    my $JSONstring = '';
    if ($vtype eq 'number')
    {
        $JSONstring = '"' . $attr . '": ' . $value . ', ';
    }
    elsif ($vtype eq 'text')
    {
        $JSONstring = '"' . $attr . '": "' . $value . '", ';
    }

    return $JSONstring;
}

sub toShiny
{
	my (%localhash) = @_;

	my $hashstring = '';
	foreach my $key (sort(keys(%localhash)))
	{
		my $keydata = $localhash{$key};
		my @hashdata = split/\t/, $keydata;
		$hashstring = $hashstring . '{ "textCode": ' . '"' . $key . '", ';
		$hashstring = $hashstring . '"totWords": ' . $hashdata[0] . ', ';
		$hashstring = $hashstring . '"noHits": ' . $hashdata[1] . ', ';
		$hashstring = $hashstring . '"hitsPer100k": ' . $hashdata[2] . ', ';
		$hashstring = $hashstring . '"decade": ' . '"' . $hashdata[3] . '", ';
		$hashstring = $hashstring . '"gender": ' . '"' . $hashdata[4] . '", ';
		$hashstring = $hashstring . '"tertial": ' . '"' . $hashdata[5] . '"}, ';
	}
	$hashstring =~ s/, $//;
	$hashstring = '[' . $hashstring . ']';

	return $hashstring;
}

#Not used 
#	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
#	print "$min:$sec<br/>";