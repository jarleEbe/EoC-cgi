#!/usr/bin/perl -w

#Ebeling, ILOS, 30.08.2006. Updated 8.4.15 JE - Search English-Norwegian Parallel Corpus (ENPC)

use strict;
use CGI;
use CGI::Carp;
use utf8;

#nabu
# 
my $css_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $general_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";
my $database_path = "/data/hf/ilos/enpc2";
my $action = "https://nabu.usit.uio.no/cgi-bin/enpc2";
my $source_path = "https://nabu.usit.uio.no/hf/ilos/enpc2/source";
my $js_path = "https://nabu.usit.uio.no/hf/ilos/enpc2";

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $searchstring = $mycgi->param('searchstring') || "";
my $subcorpus = $mycgi->param('subcorpus') || "Eng-Fict";
my $origtran = $mycgi->param('origtran') || "Original";
my $sortkrit = $mycgi->param('sort') || "";
my $maxcontext = $mycgi->param('maxcontext') || 1000;

my $txtfile = $subcorpus;
my $ll = $origtran;

$ll =~ s/Original/Org/;
$ll =~ s/Translation/Tran/;
$txtfile =~ s/-/$ll/;

my $database = "ENPC2_" . $txtfile . ".txt";
my $corrbase = $database;
if ($corrbase =~ /_Eng/)
{
	$corrbase =~ s/_Eng/_Nor/;
}
else
{
	$corrbase =~ s/_Nor/_Eng/;
}

if ($corrbase =~ /Org/)
{
	$corrbase =~ s/Org/Tran/;
}
else
{
	$corrbase =~ s/Tran/Org/;
}

my @contextvalues = ();
my %contextlabels = ();

my $maxlines = 50000;
my $tablestart = "<table align='center' border='0' cellpadding='0' cellspacing='0' width='98%'>\n";
my $tableend = "</table>\n";

my $asterisk = "[A-Za-z0-9ÆØÅæøå'-]*";
my $sep1 = '[ ,.:;?!>(\)\'\"]+';
my $sep2 = '[ ,.:;?!<(\)\"]+';
#open(LOGG, ">oielogg.txt");

my @output = ();
my $numbhits = 0;
my @ands = ();
my @nots = ();
my $gg = "";

if ($searchstring)
{
	&print_header($searchstring);
	if ($searchstring =~ /AND/ || $searchstring =~ /NOT/)
	{
		$searchstring = &get_AND_NOT($searchstring);
	}
	$searchstring =~ s/\*/$asterisk/g;

	my @hits = &searching($searchstring);
	foreach my $hit (@hits)
	{
#New
		my ($source, $corresp, $id) = &get_source($hit);
		$hit = &skrell($hit);
		$hit =~ s/(\W)($searchstring)(\W)/$1<b>$2<\/b>$3/ig;
		$hit =~ s/^($searchstring)(\W)/<b>$1<\/b>$2/ig;
		$hit =~ s/(\W)($searchstring)$/$1<b>$2<\/b>/ig;
		my @arr = split/<b>/, $hit;
		my $hitsperline = $#arr;
		if ($hitsperline > 1)
		{
			$numbhits = $numbhits + $hitsperline;
			my $bees = 0;
			while ($hit =~ /<b>/)
			{
				$bees++;
				my $localstartb = "<b$bees>";
				my $localendb = "</b$bees>";
				$hit =~ s/<b>/$localstartb/;
				$hit =~ s/<\/b>/$localendb/;
			}

			my @multihits = ();
			for (my $i = 1; $i <= $hitsperline; $i++)
			{
				my $templine = $hit;
				my $localstartb = "<b$i>";
				my $localendb = "</b$i>";
				$templine =~ s/$localstartb/<b>/;
				$templine =~ s/$localendb/<\/b>/;
				$templine =~ s/<b[0-9]+?>//g;
				$templine =~ s/<\/b[0-9]+?>//g;
				$templine =~ s/\s+/ /g;
				$templine =~ s/^ //;
				$templine =~ s/ $//;
				if ($templine && $templine ne ' ')
				{
				    push(@multihits, $templine);
				}
			}

			foreach my $localhit (@multihits)
			{
				$localhit =~ s/(.*?)(<b>$searchstring<\/b>)(.*)/$1$2$3/i;
				my $leftcontext = $1 || "";
				if (length($leftcontext) > $maxcontext)
				{
					$leftcontext = reverse($leftcontext);
					$leftcontext = substr($leftcontext, 0, $maxcontext);
#					$leftcontext =~ s/</&lt;/g;
#					$leftcontext =~ s/>/&gt;/g;
					$leftcontext = "&hellip;" . reverse($leftcontext);
				}

				my $keyword = $2 || "";
				my $rightcontext = $3 || "";
				if (length($rightcontext) > $maxcontext)
				{
					$rightcontext = substr($rightcontext, 0, $maxcontext) . "&hellip;";
#					$rightcontext =~ s/</&lt;/g;
#					$rightcontext =~ s/>/&gt;/g;
				}
#NEW
				$keyword =~ s/<b>/<span name="kw" class="keyword" onclick="goto_context2('$action', '$subcorpus', '$origtran', '$id')">/g;
				$keyword =~ s/<\/b>/<\/span>/g;
				push(@output, "$leftcontext\t$keyword\t$rightcontext\t$source\t$corresp");
			}
		}
		else
		{
			$numbhits++;
			$hit =~ s/(.*?)(<b>$searchstring<\/b>)(.*)/$1$2$3/i;
			my $leftcontext = $1 || "";
			if (length($leftcontext) > $maxcontext)
			{
				$leftcontext = reverse($leftcontext);
				$leftcontext = substr($leftcontext, 0, $maxcontext);
#				$leftcontext =~ s/</&lt;/g;
#				$leftcontext =~ s/>/&gt;/g;
				$leftcontext = "&hellip;" . reverse($leftcontext);
			}

			my $keyword = $2 || "";
			my $rightcontext = $3 || "";
			if (length($rightcontext) > $maxcontext)
			{
				$rightcontext = substr($rightcontext, 0, $maxcontext) . "&hellip;";
#				$rightcontext =~ s/</&lt;/g;
#				$rightcontext =~ s/>/&gt;/g;
			}
#NEW
			$keyword =~ s/<b>/<span name="kw" class="keyword" onclick="javascript:goto_context2('$action', '$subcorpus', '$origtran', '$id')">/g;
			$keyword =~ s/<\/b>/<\/span>/g;

			push(@output, "$leftcontext\t$keyword\t$rightcontext\t$source\t$corresp");
		}
	}

	if ($sortkrit)
	{
		&sort_kwic;
	}
	
	my $concordance = "";
	($concordance, $numbhits) = &build_output($numbhits);
	$concordance = $tablestart . $concordance . $tableend;
	$concordance = "<center>Number of hits: " . $numbhits ."</center>" . "<br/>" . $concordance;
	print $concordance;
}
else
{
	&print_header("");
}
#print "$gg<br/>";
print $mycgi->end_html;
#close(LOGG);
exit;


sub searching
{
	my $ss = shift(@_);
	my $orgline = "";

	my $egrep = 'egrep';
	unless (-r "$database_path/$database")
	{
		print "Cannot open $database_path/$database.\n";
		exit();
	}

	my $sep11 = '([ ,.:;?!>\(\)\']+)';
	my $sep22 = '([ ,.:;?!<\(\)]+)';
	$ss =~ s/ OR / \| /g;

#	my $sep11 = '(\W)';
#	my $sep22 = '(\W)';

	my $temp = $sep11 . $ss . $sep22;

#	binmode STDIN, ":utf8";

#	print "$temp</br>";

#	$temp =~ s/\Æ/\æ/;

	my @resultlines = `$egrep -i -m $maxlines "$temp" $database_path/$database`;

#	print "$egrep -i -m $maxlines \"$temp\" $database_path/$database";


#	open(CORPUS, "egrep -i -m $maxlines \"$temp\" $database_path/ENPC2/$database |");
#	open(CORPUS, "$database_path/ENPC2/$database");
#	my @resultlines = <CORPUS>;
#	close(CORPUS);
	my @hitlines = ();

	foreach (@resultlines)
	{
		chomp;
#		$orgline = $_;
#		s/<[^>]+?>//g;
#		if (/$sep2$ss$sep2/i || /^$ss$sep2/i || /$sep2$ss$/i)
#		{
			push(@hitlines, $_);
#		}
	}
	
#	return @resultlines;
	return @hitlines;
}


sub print_header
{
	my $ss = shift(@_);
	print "Content-Type: text/html; charset=utf-8\n\n";
#	print $mycgi->header;
	print "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">\n";
	print "<html>\n";
	print "<head><title>ENPC2search</title>\n";
	print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8'/>\n";
	print "<link rel='stylesheet' type='text/css' href='$css_path/OMCsearch.css'/>\n";
	print "<script src='$js_path/selectcorpus.js'></script>\n";
	print "</head>\n";
	print "<body>\n";
	print "<form name='readcorpus' method='POST' action='$action/ENPC2search.cgi'>\n";
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
	print "<td align='right'><p class='marg2'>Subcorpus \n";
	print $mycgi->popup_menu(-name=>'subcorpus', -values=>['Eng-Fict', 'Nor-Fict']);
	print "&nbsp;";
	print $mycgi->popup_menu(-name=>'origtran', -values=>['Original', 'Translation']);
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
#NEW
		if ($sortkrit eq 'right word')
		{
			$krit = &get_rightkrit($kline);	
			my $krit2 = &get_keykrit($kline);
			$krit2 =~ s/<[^>]+?>//;
#			$krit2 =~ s/<\/b>//;
			$krit = "$krit$pad$krit2";
		}
		elsif ($sortkrit eq 'left word')
		{
			$krit = &get_leftkrit($kline);	
			my $krit2 = &get_keykrit($kline);
			$krit2 =~ s/<[^>]+?>//;
#			$krit2 =~ s/<\/b>//;
			$krit = "$krit$pad$krit2";
		}
		elsif ($sortkrit eq 'keyword')
		{
			$krit = &get_keykrit($kline);
			my $krit2 = &get_rightkrit($kline);
			$krit =~ s/<[^>]+?>//;
#			$krit =~ s/<\/b>//;
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
#			$krit =~ s/<\/b>//;
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
	my ($left, $key, $right, $source, $corr) = split/\t/, $temp;
	$right =~ s/&mdash;//g;
	$right =~ s/^\W+//;
	my @krits = split/ /, $right;
	
	return $krits[0];
}

sub get_leftkrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $corr) = split/\t/, $temp;
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
	my ($left, $key, $right, $source, $corr) = split/\t/, $temp;
	return $key;
}

sub get_sourcekrit
{
	my $temp = shift(@_);
	my ($left, $key, $right, $source, $corr) = split/\t/, $temp;
	$source =~ s/\[//;
	$source =~ s/\]//;
	$source =~ s/<[^>]+>//g;
	return $source;
}


sub build_output
{
	my $nh = shift(@_);

	my $kwic_line = "";
	foreach my $kline (@output)
	{
		my ($left, $key, $right, $source, $corr) = split/\t/, $kline;
		$corr = &get_corresp($corr);
		if (@ands)
		{
			if (&_and($corr))
			{
			}
			else
			{
				$nh--;
				next;
			}
		}
		if (@nots)
		{
			if (&_not($corr))
			{
				$nh--;
				next;
			}
		}
		$corr = &skrell($corr);
		if ($maxcontext == 1000)
		{
			$kwic_line = $kwic_line. "<tr><td align='left'>" . $left . $key . $right . " [" . $source . "]</td></tr><tr><td align='left'><p class='trad'>$corr</p></td></tr>\n";
		}
		elsif ($maxcontext == 59)
		{
			$kwic_line = $kwic_line. "<tr><td align='right'>" . $left . "</td><td align='center'>" . $key . "</td><td align='left'>" . $right . " [" . $source . "]</td></tr><tr><td colspan='3' align='center'><p class='kwic'>$corr</p></td></tr>\n";
		}
		elsif ($maxcontext == 2000)
		{
		    $left  =~ s/<([^>]+?)>//g;
		    $right =~ s/<([^>]+?)>//g;
		    $key =~   s/<([^>]+?)>//g;
		    $source =~ s/<([^>]+?)>//g;
		    $left =~ s/^ //;
		    $kwic_line = $kwic_line . $left . "\t" . $key . "\t" . $right . "\t" . $source . "\n";
		}
	}
	return $kwic_line, $nh;
}


sub get_source
{
	my $temp = shift(@_);

	my $href = "<a href='$source_path/";

	if ($temp =~ /^<head corresp=/)
	{
	    $temp =~ s/^<head corresp=/<s corresp=/;
	}

	$temp =~ s/<s corresp=\"([^"]+?)\" id=([^>]+?)>/$1 $2/;
	my $filename = $2 || "";
	my $corr = $1 || "";

	$filename =~ s/^"//;
	my $id = $filename;
	$id =~ s/"$//;
	$filename =~ s/^([^.]+?)\.(.+)/$1/;
	$temp = $filename;
	$filename = "$filename" . ".xml' " . "target='source'>";
	$href = $href . $filename . "$temp</a>";

	return $href, $corr, $id;
}

sub get_corresp
{

	my $egrep = 'egrep';
	my $temp = shift(@_);
	my $correspline = "";

	if ($temp =~ / /)
	{
		$temp =~ s/"//g;
		my @corrlines = split/ /, $temp;
		foreach my $c (@corrlines)
		{
			my $onecorr = `$egrep -m 1 "$c" $database_path/$corrbase`;
			chomp($onecorr);
			$correspline = $correspline . $onecorr;

		}
	}
	else
	{
		my $onecorr = `$egrep -m 1 "$temp" $database_path/$corrbase`;
		chomp($onecorr);
		$correspline = $correspline . $onecorr;

	}
	
	if ($correspline =~ /id=/ && $correspline =~ /\.p/)
	{
		$correspline = "[no corresp]";
	}

	return $correspline;
}

sub skrell
{
	my $temp = shift(@_);

	$temp =~ s/<[^>]+?>//g;

	return $temp;
}

sub get_AND_NOT
{
	my $ss = shift(@_);

	my $a = "";
	my $n = "";

	if ($ss =~ /AND/)
	{
		($ss, $a) = split/AND/, $ss;
		if ($a =~ /NOT/)
		{
			($a, $n) = split/NOT/, $a;
			$n = &blanks($n);
			@nots = split/,/, $n;
		}
		$ss = &blanks($ss);
		$a = &blanks($a);
		@ands = split/,/, $a || $a;

	}

	if ($ss =~ /NOT/)
	{
		($ss, $n) = split/NOT/, $ss;
		$ss = &blanks($ss);
		$n = &blanks($n);
		@nots = split/,/, $n;
	}

	return ($ss);
}

sub _and
{
	my $c = shift(@_);

	my $flag = 0;

	$c = &skrell($c);
	foreach my $amp (@ands)
	{
		my $a = $amp;
		$a =~ s/\*/$asterisk/g;
		if ($c =~ /$sep2$a$sep2/i || /^$a$sep2/i || /$sep2$a$/i)
		{
			$flag = 1;
		}
	}
	return $flag;
}

sub _not
{
	my $c = shift(@_);

	my $flag = 0;

	$c = &skrell($c);
	foreach my $nn (@nots)
	{
		my $n = $nn;
		$n =~ s/\*/$asterisk/g;
		if ($c =~ /$sep2$n$sep2/i || /^$n$sep2/i || /$sep2$n$/i)
		{
			$flag = 1;
		}
	}
	return $flag;
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

sub IsOIE
{
return <<'END';
+utf8::IsAlpha
2D
27
DF
END
}

