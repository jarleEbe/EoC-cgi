#!/usr/bin/perl -w

#Ebeling, USIT, 26.01.2017.

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

# Nabu
my $css_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $general_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $action = "http://127.0.0.1/cgi-bin/cbf";
my $contextaction = "http://127.0.0.1/cgi-bin/cbf/CBFcontext.cgi?id=";
my $source_path = "https://nabu.usit.uio.no/hf/ilos/cbf/source";
my $js_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $stats_path = "http://127.0.0.1/cgi-bin/cbf/CBFstats.cgi?json=";

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $searchstring = $mycgi->param('searchstring') || "";
my $decade = $mycgi->param('decade') || "";
my $gender = $mycgi->param('gender') || "";
my $sortkrit = $mycgi->param('sort') || "";
my $maxcontext = $mycgi->param('maxcontext') || 1000;
my $maxshow = $mycgi->param('maxshow') || 1000000;

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

my %orig = (); #Text code
my %empty = (); #Hits per text
my %tgender = (); #Text's author's gender
my %tdecade = (); #Text's decade
my $totnotexts = 0;

$totnotexts = &readcbf_json();

if ($searchstring)
{
	&print_header($searchstring);

#	my $result = &searching($searchstring, $maxlines, $filters);
	my ($numbhits, @cqpresult) = &cqp($searchstring, $decade, $gender);
    my $result = &cqptoJSON($searchstring, $maxlines, @cqpresult);

#    foreach my $hit (@cqpresult)
#    {
#        $hit =~ s/</&lt;/g;
#        $hit =~ s/>/&gt;/g;
#        print "$hit<br/>";
#    }

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
		my $gender = $json_data->{'Hits'}->[$ind]->{'sunit'};
		my $source = $json_data->{'Hits'}->[$ind]->{'sunitId'};
		$source =~ s/\. /\./;
		my $textid = $json_data->{'Hits'}->[$ind]->{'textId'};
		$numbhits++;
#		$sunit =~ s/(.*?)(<b>.+<\/b>)(.*)/$1$2$3/i;
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
	$concordance = "<center>" . $numbhits  . " hits in " . $numberoftexts . " of " . $totnotexts . " texts<br/>(male: " . $male . " (" . $nomaletexts . " texts) / female " . $female . " (" . $nofemaletexts . " texts)) " . $statsLink . "<br/>" . $decadesstring . "</center>" . "<br/>" . $concordance;
	print $concordance;
	print "<hr/>";
	print "<table border='1' cellpadding='2' cellspacing='2'>";
	print "<tr><td>Text code</td><td>Tot. words</td><td>No. of hits</td><td>Hits per 100,000</td><td>Decade</td><td>Gender</td></tr>";
	foreach my $key (sort(keys(%orig)))
	{
		my $sum = $orig{$key};
		my $actualno = $empty{$key};
		my $perht = 0.0;
		print "<tr><td>$key</td><td style='text-align:right'>$orig{$key}</td>";
		print "<td style='text-align:right'>$empty{$key}</td>";
		if ($actualno > 0)
		{
			$perht = ($actualno / $sum) * 100000;
			$perht = sprintf("%.1f", $perht);
		}
		print "<td style='text-align:right'>$perht</td>";
		print "<td style='text-align:center'>$tdecade{$key}</td>";
		print "<td style='text-align:center'>$tgender{$key}</td></tr>";
	}
	print "</table>";
}
else
{
	&print_header("");
}
print $mycgi->end_html;
exit;

#depricated
#sub searching
#{
#	my ($query, $nohits, $filters) = @_;

#	$query = decode('utf-8', $query);
#	my $url = 'http://127.0.0.1/cgi-bin/cbf/rawcbfsearch.cgi?' . 'q=' . $query . '&nohits=' . $nohits . '&filter=' . $filters;
#	my $result = get($url);
#	die "Couldn't get it!" unless defined $result;
#	$result = encode('utf-8', $result);
#	return $result;
#}

sub print_header
{
	my $ss = shift(@_);
	print "Content-Type: text/html; charset=utf-8\n\n";
	print "<!DOCTYPE html>\n";
	print "<html>\n";
	print "<head><title>CQPcbfsearch</title>\n";
	print "<link rel='stylesheet' type='text/css' href='$css_path/OMCsearch.css'/>\n";
	print "<script src='$js_path/selectcorpus.js'></script>\n";
	print "</head>\n";
	print "<body>\n";
	print "<form name='readcorpus' method='POST' action='$action/CQPcbfsearch.cgi'>\n";
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
	print "&nbsp;Gender of author ";
	print $mycgi->popup_menu(-name=>'gender', -values=>['', 'female', 'male']);
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
		if (exists($empty{$tid}))
		{
			my $ttemp = $empty{$tid};
			$ttemp++;
			$empty{$tid} = $ttemp;
		}
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

sub readcbf_json
{

	open(JSONFILE, "cbf.json");
	my @content = <JSONFILE>;
	close(JSONFILE);

	my $jsonfromfile = join(" ", @content);
	my $json_data = decode_json($jsonfromfile);

#	my $male = $json_data->{'male'};
#	my $female = $json_data->{'female'};
#	my $nomaletexts = $json_data->{'noMaleTexts'};
#	my $nofemaletexts = $json_data->{'noFemaleTexts'};
	my $numberoftexts = $json_data->{'noTexts'};
	my $textcodes = $json_data->{'Texts'};

	foreach my $key (sort(keys(%$textcodes)))
	{
		$orig{$key} = $textcodes->{$key}->{'noWords'};
		$tgender{$key} = $textcodes->{$key}->{'Gender'};
		$tdecade{$key} = $textcodes->{$key}->{'Decade'};
		$empty{$key} = 0;
	}

	return $numberoftexts;
}

sub cqp
{

    my ($search, $decennium, $gofA) = @_;

    my $pid = open2 my $out, my $in, "cqp -c -D CBF" or die "Could not open cqp";

    my $opened = <$out>;
    #print "$opened";
    #print $in "set AutoShow on;\n";
    print $in "set Context 59;\n";
    print $in "set PrintStructures 'text_id, text_gender, text_decade';\n";
#    print $in "set PrintStructures 'text_gender';\n";
#    print $in "set PrintStructures 'text_decade';\n";

	my $matching = '';
	if ($gofA)
	{
		$matching = ' :: match.text_gender = "' . $gofA . '"';
	}
	if ($decennium)
	{
		$matching = $matching . ' & match.text_decade = "' . $decennium . '"';
	}

	my $sokstring = '';
	if ($search =~ / /)
	{
		$search = &buildSearchString($search);
		$sokstring = $search . $matching;
	}
	else
	{
		$sokstring = '[word="' . $search . '" %cd]' . $matching;
	}

    print "$sokstring<br/>";
#    print $in "sok = [word='serendipity' %cd];\n";
    print $in "sok = $sokstring;\n";
    print $in "size sok;\n";
    my $numbhits = <$out>;
    #print "$numbhits";
    print $in "cat sok;\n";

    my $result;
    while (! ($result = <$out>))
    {
    }
#    print $result;
    my @content = ();
    push(@content, $result);
    for (my $ind = 1; $ind++; $ind <= $numbhits)
    {
        chomp($result = <$out>);
#        print "$result\n";
        push(@content, $result);
        $result = '';
        if ($ind >= $numbhits)
        {
#            print "$ind\n";
            last;
        }
    }

    print $in "exit;\n";
    close($in);
    close($out);

    waitpid($pid, 0);

    return $numbhits, @content;
}

sub buildSearchString($search)
{
	my ($inputstring) = @_;

	my @strings = split/ /, $inputstring;
	my $resturnstring = '';
	foreach my $ss (@strings)
	{
		$resturnstring = $resturnstring . '[word="' . $ss . '" %cd] '
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
	my $numbtexts = 0;
	my $numbhits = 0;
	my %decades = ();
    foreach my $hitsrow (@hitsarr)
    {
		$numbhits++;
        $hitsrow =~ s/(\d+): <text_id ([^>]+?)><text_gender ([^>]+?)><text_decade ([^>]+?)>: (.*)/$1\t$2\t$3\t$4\t$5/;
        my @cols = split/\t/, $hitsrow;
		my $localid = $cols[0];
		my $textid = $cols[1];
		my $gender = $cols[2];
		my $decade = $cols[3];
		my $sunit = $cols[4];
		my $tidlid = $textid . '.' . $localid;
		$sunit =~ s/\n//g;
		$sunit =~ s/"/&#x0022;/g;
        $localJSON = $localJSON . '{';
        $localJSON = $localJSON . &addtoJSON("localId", $localid, "number");
        $localJSON = $localJSON . &addtoJSON("textId", $textid, "text");
        $localJSON = $localJSON . &addtoJSON("Sex", $gender, "text");
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
    }

    $localJSON =~ s/,$//;
	my $decadesstring = '';
	foreach my $key (sort(keys(%decades)))
	{
		$numbtexts++;
		$decadesstring = $decadesstring . '"' . $key . '": ' . $decades{$key} . ', ';
	}
    $decadesstring =~ s/, $//;

	my $sums = '"searchstring": ' . '"' . $thesearch . '", ';
	$sums = $sums . '"female": ' . '"' . $female . '", ';
	$sums = $sums . '"numberofHits": ' . '"' . $numbhits . '", ';
	$sums = $sums . '"noMaleTexts": ' . '"' . '0' . '", ';
	$sums = $sums . '"NoFemaleTexts": ' . '"' . '0' . '", ';
	$sums = $sums . '"requestednoHits": ' . $numbreqhits . ', ';
	$sums = $sums . '"male": ' . '"' . $male . '", ';
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