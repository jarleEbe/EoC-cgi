#!/usr/bin/perl -w

#Ebeling, USIT, 19.02.2018.

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
my $css_path = "https://nabu.usit.uio.no/hf/ilos/cbf/imagecssjs";
my $general_path = "https://nabu.usit.uio.no/hf/ilos/cbf/imagecssjs";
my $action = "http://127.0.0.1/cgi-bin/cbf";
#itfds-utv01
#my $action = "http://itfds-utv01.uio.no/cgi-bin/cbf";
my $contextaction = "http://127.0.0.1/cgi-bin/cbf/CBFcontext.cgi?id=";
my $source_path = "https://nabu.usit.uio.no/hf/ilos/cbf/source";
my $js_path = "https://nabu.usit.uio.no/hf/cbf/ilos/imagecssjs";
my $stats_path = "http://127.0.0.1/cgi-bin/cbf/CBFstats.cgi?json=";
#itfds-utv01
#my $stats_path = "http://itfds-utv01.uio.no/cgi-bin/cbf/CBFstats.cgi?json=";

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $searchstring = $mycgi->param('searchstring') || "";
my $decade = $mycgi->param('decade') || "";
my $gender = $mycgi->param('gender') || "";
my $sortkrit = $mycgi->param('sort') || "";
my $maxcontext = $mycgi->param('maxcontext') || 59;
my $maxshow = $mycgi->param('maxshow') || 1000000;

my @contextvalues = ();
my %contextlabels = ();

#NB! Constants
my $maxlines = 15000; #Max number of hits to display
my $absolutemax = 250000; #Max number og hits counted
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
my %tdecade = (); #Text's decade
my %sdecades = (); #The decades to include in search
my $totnotexts = 0;

$totnotexts = &readcbf_json();

if ($searchstring)
{
	&print_header($searchstring);

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


#	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
#	print "$min:$sec<br/>";

	($numbhits, $totalhits, $cqpsearch, @cqpresult) = &cqp($searchstring, $decade, $gender, $sortkrit, $maxcontext, $maxlines, $absolutemax);	
    my $result = &cqptoJSON($searchstring, $maxlines, @cqpresult);

#	($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
#	print "$min:$sec";

	$result = encode('utf-8', $result);
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
#		$sunit = encode('utf-8', $sunit);
		my $gender = $json_data->{'Hits'}->[$ind]->{'sunit'};
		my $source = $json_data->{'Hits'}->[$ind]->{'sunitId'};
		$source =~ s/\. /\./;
		my $textid = $json_data->{'Hits'}->[$ind]->{'textId'};
#		$numbhits++;
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
#		$keyword =~ s/<b>/<a style="text-decoration: none; color: #000000" href="$link">/;
#		$keyword =~ s/<\/b>/<\/a>/;
#		$keyword = '<a style="text-decoration: none; color: #000000; font-weight: bold" href="$link">' . $keyword . '</a>';
		$keyword = '<a style="text-decoration: none; color: #000000; font-weight: bold">' . $keyword . '</a>';
		push(@output, "$leftcontext\t$keyword\t$rightcontext\t$source\t$textid");
	}
	if ($sortkrit eq 'source')
	{
		&sort_kwic;
	}
	
	my $concordance = "";
	my $nbmessage = '';
	if ($numbhits > $maxlines)
	{
		&build_simple_output();
		$nbmessage = "No. of hits exceeds $maxlines. Displays counts only.";
		if ($numbhits == $absolutemax)
		{
		    $nbmessage = $nbmessage . "<br/>Tot. no. of hits exceeds $absolutemax. Result set randomised and reduced to $absolutemax.";
		}
	}
	else
	{
		($concordance, $numbhits) = &build_output($numbhits, $source_path);
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
#	my $statsLink = '';
	$concordance = "<center>" . $numbhits  . " hits in " . $numberoftexts . " of " . $totnotexts . " texts<br/>(male: " . $male . " (" . $nomaletexts . " texts) / female " . $female . " (" . $nofemaletexts . " texts)) " . $statsLink . "<br/>" . $decadesstring . "</center>" . "<br/>" . $concordance;
	print $concordance;
	print "<hr/>";
	if ($maxcontext != 2000)
	{
		print "<table border='1' cellpadding='2' cellspacing='2'>";
		print "<tr><td>Text code</td><td>Tot. words</td><td>No. of hits</td><td>Hits per 100,000</td><td>Decade</td><td>Gender</td></tr>";
		foreach my $key (sort(keys(%orig)))
		{
			my $sum = $orig{$key};
			my $actualno = $empty{$key};
			my $perht = 0.0;
			if ($gender eq '' || $tgender{$key} eq $gender)
			{
#			if ($decade eq '' || $tdecade{$key} eq $decade)
				if ($decade eq '' || exists($sdecades{$tdecade{$key}}))
				{
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
			}
		}
		print "</table>";
	}
	else
	{
		print "<pre>\n";
		print "TextCode\tTotNoWords\tNoOfHits\tHitsPer100k\tDecade\tGender\n";
		foreach my $key (sort(keys(%orig)))
		{
			my $sum = $orig{$key};
			my $actualno = $empty{$key};
			my $perht = 0.0;
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
					}
					print "$perht\t";
					print "$tdecade{$key}\t";
					print "$tgender{$key}\n";
				}
			}
		}
		print "</pre>";
	}
	print "<hr/>";
	print "<p>The search string sent to cqp: $cqpsearch</p>";
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
	print "<table align='center' width='789' border='0' style='padding:0; border-spacing:0'>\n";
	print "<tr bgcolor='#000000'>\n";
#	print "<td style='text-align:left; vertical-align:bottom'>";
#	print "<img src='$general_path/cbf_blur3.png' style='border:0; vertical-align:center' alt='banner'/>";
#	print "</td>\n";
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
	print "<input name='searchstring' size='55' value=\"$ss\"/>";
	print "<input type='submit' value='Search'>";
	print "</p></td>\n";
	print "<td align='right'><p class='marg2'>Decade \n";
	print $mycgi->popup_menu(-name=>'decade', -values=>['', '1900', '1910', '1920', '1930', '1940', '1950', '1960', '1970', '1980', '1990', '2000', '2010', '00-30', '40-70', '80-10']);
	print "&nbsp;Gender of author ";
	print $mycgi->popup_menu(-name=>'gender', -values=>['', 'female', 'male']);
	print "</p></td></tr>\n";
	print "<tr><td align='right'><p class='marg2'>\n";
	print "Sort concordance by ";
	print $mycgi->popup_menu(-name=>'sort', -values=>['keyword', 'right word', 'left word', 'source', 'random', '']);
	print "</p></td><td align='right'><p class='marg2'>";
	@contextvalues = ('59', '1000', '2000', '1500');
	%contextlabels = ('59' => 'kwic', '1000' => 's-unit', '2000' => 'tab', '1500' => 's-unit5');
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
		if ($maxcontext == 1000 || $maxcontext == 1500) #s-unit / sentence output
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
	}
	if ($maxcontext == 2000)
	{
		$kwic_line = "<pre>\n" . $kwic_line . "</pre>\n";
	}
	return $kwic_line, $nh;
}


sub build_simple_output
{
	foreach my $kline (@output)
	{
		my ($left, $key, $right, $source, $tid) = split/\t/, $kline;
		if (exists($empty{$tid}))
		{
			my $ttemp = $empty{$tid};
			$ttemp++;
			$empty{$tid} = $ttemp;
		}
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

    my ($search, $decennium, $gofA, $skriterium, $display, $maxtodisplay, $maxtocount) = @_;

    my $pid = open2 my $out, my $in, "/usr/local/cwb-3.4.13/bin/cqp -c -D CBF" or die "Could not open cqp";
#itfds-utv01
#    my $pid = open2 my $out, my $in, "/usr/local/cwb-3.4.12/bin/cqp -c -D CBF" or die "Could not open cqp";

    my $opened = <$out>;
    #print "$opened";
    #print $in "set AutoShow on;\n";

#Default KWIC context and what to output
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

    print $in "set PrintStructures 'text_id, text_gender, text_decade';\n";
#print "$search<br/>";


#How to set sentenece view (KWIC is default)
#       print $in "set Context s;\n";

#How to show <s> ... </s>
#       print $in "show +s;\n";

#How to show/hide pos and lemma info
#       print $in "show +pos +lemma;\n"; #show
#       print $in "show -pos -lemma;\n"; #(hide)


#Add filters gender and/ or (one) decade
#	print "$search<br/>";
	my $matching = '';
	if ($gofA)
	{
		$matching = ' :: match.text_gender = "' . $gofA . '"';
	}

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
#    print "$sokstring<br/>";
#    $sokstring = '[word="' . "'d" . '" %cd][word="help"]';
#    print "$sokstring<br/>";
#return;
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
		print $in "sort randomize;\n";
    	print $in "set Context 0;\n";	
		print $in "reduce sok to $maxtocount;\n";
    	print $in "size sok;\n";
		$numbhits = <$out>;
	}
	else
	{
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
#			print $in "sort by word %cd on matchend[0] .. matchend[42];\n";
		}
	}

    print $in "cat;\n";

    my $result;
    while (! ($result = <$out>))
    {
    }
#    print $result;
    @content = ();
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

    return $numbhits, $totalnumbhits, $sokstring, @content;
}

sub buildSearchString
{
	my ($inputstring) = @_;

	if ($inputstring =~ /^\[/)
 	{
		$inputstring =~ s/word=([^ ]+?) /word='$1' /g;
		$inputstring =~ s/lemma=([^ ]+?) /lemma='$1' /g;
		$inputstring =~ s/pos=([^ ]+?) /pos='$1' /g;
#		$inputstring =~ s/word=([^\]]+?)\]/word='$1'\]/g;
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
	my %textids = ();
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
		$sunit =~ s/\\ \//\\\//g;
        $localJSON = $localJSON . '{';
        $localJSON = $localJSON . &addtoJSON("localId", $localid, "number");
        $localJSON = $localJSON . &addtoJSON("textId", $textid, "text");
        $localJSON = $localJSON . &addtoJSON("Sex", $gender, "text");
        $localJSON = $localJSON . &addtoJSON("Decade", $decade, "text");
		if ($#hitsarr > $numbreqhits)
		{
	        $localJSON = $localJSON . &addtoJSON("sunit", "", "text");
		}
		else
		{
        	$localJSON = $localJSON . &addtoJSON("sunit", $sunit, "text");
		}
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
	foreach my $key (sort(keys(%decades)))
	{
		$decadesstring = $decadesstring . '"' . $key . '": ' . $decades{$key} . ', ';
	}
    $decadesstring =~ s/, $//;

	$numbtexts = keys(%textids);
	my $sums = '"searchstring": ' . '"' . $thesearch . '", ';
	$sums = $sums . '"female": ' . '"' . $female . '", ';
	$sums = $sums . '"numberofHits": ' . '"' . $numbhits . '", ';
	$sums = $sums . '"noMaleTexts": ' . '"' . $nomaletexts . '", ';
	$sums = $sums . '"noFemaleTexts": ' . '"' . $nofemaletexts . '", ';
	$sums = $sums . '"requestednoHits": ' . $numbreqhits . ', ';
	$sums = $sums . '"male": ' . '"' . $male . '", ';
	$sums = $sums . '"Decades": {' . $decadesstring . '},';
	$sums = $sums . '"numberofTexts": ' . '"' . $numbtexts . '"';

#Counts in here
    $allhits = $allhits . $localJSON . '], ' . $sums . '}';

#print "$numbhits : $numbtexts<br/>";

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