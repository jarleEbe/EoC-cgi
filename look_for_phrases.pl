#!/usr/bin/perl

use strict;
use utf8;

#E.g. prepdata/
my ($basePath) = @ARGV;

my $inputfile = "phrases_lemma.txt";
#my $inputfile = "test_phrases.txt";
open(INN, "$inputfile");
binmode INN, ":utf8";
my @tempcontent = <INN>;
close(INN);
open(LOG, ">phrase_length3.txt");
binmode LOG, ":utf8";
my @phrases = ();
my %temphash = ();
my $numberofphrases = 0;
foreach (@tempcontent)
{
	chomp;
	s/\n//;
	s/\r//;
	s/([a-z]+)'s/$1 's/g;
	s/([a-z]+)'ll/$1 will/g;
	s/([a-z]+)n't/$1 not/g;
	s/([a-z]+)'ve/$1 have/g;
	s/([a-z]+)'m/$1 be/g;
	s/([a-z]+)'re/$1 be/g;
	s/([a-z]+)'d/$1 would/g;
	s/^ca /can /;
	s/^wo /will /;
	s/ ca / can /g;
	s/ wo / will /g;
	s/s'/s '/g;

	my @row = split/ /;
	my $ngram = 0;
	foreach (@row)
	{
		if (/[a-zA-Z0-9']/)
		{
			$ngram++;
		}
	}
#	if ($#row >= 5) #&& $#row < 4) #2 = three items/words
	if ($ngram == 3 && $_ !~ /^#/)
	{
		s/^X /\([^ ]+\) /;
		s/ X$/ \(.+\)/;
		s/ X / \([^ ]+\) /g;
		s/Z/\([a-z]+\)/g;
		if (exists($temphash{$_}))
		{	
		}
		else
		{
			push(@phrases, $_);
			$temphash{$_} = "null";
			$numberofphrases++;
			if (/X's/)
			{
				$numberofphrases--;
			}
		}
		if (/X's/)
		{
			my $tempX = $_;
			$tempX =~ s/X's/\([^ ]+\) 's/g;
			if (exists($temphash{$tempX}))
			{
			}
			else
			{
				push(@phrases, $tempX);
				$temphash{$tempX} = "null";
				$numberofphrases++;
			}
			$tempX = $_;
			$tempX =~ s/X's/\([^ ]+\)/g;
			if (exists($temphash{$tempX}))
			{
			}
			else
			{
				push(@phrases, $tempX);
				$temphash{$tempX} = "null";
			}
		}
	}
}
my @tempphrases = @phrases;
@phrases = ();
foreach (@tempphrases)
{
	if (/X/)
	{

	}
	else
	{
		push(@phrases, $_);
		print LOG "$_\n";
	}
}
print LOG "Number of phrases by rows in array: ($#phrases + 1)\n";
print LOG "Number of phrases by counting (collapsing X's & X): $numberofphrases\n";
close(LOG);
#exit;

$inputfile = "allheaders.txt";
open(INN, "$inputfile");
binmode INN, ":utf8";
@tempcontent = <INN>;
close(INN);
my %texthash = ();
foreach (@tempcontent)
{
	chomp;
	s/\n//;
	s/\r//;
	my ($code, $author, $title, $YofP, $gender, $YofB, $decade) = split/\t/;
	$texthash{$code} = $_;
}

opendir(DS, $basePath) or die $!;
my $numFiles = 0;
my $numhits = 0;
my $outputfile = "all_hits_phrases3.txt";
open(OUT, ">$outputfile");
binmode OUT, ":utf8";
open(NOHITS, ">no_hits_phrases3.txt");
binmode NOHITS, ":utf8";
while (my $txt = readdir(DS))
{
	if ($txt =~ /\.txt$/i)
	{
		$numFiles++;
		open(INN, "$basePath$txt");
		binmode INN, ":utf8";
		my @content = <INN>;
		close(INN);
		print "$txt\n";
		my $clause = ' ';
		my $origClause = ' ';
		$txt =~ s/_clean_cwb\.txt$//;
		$txt =~ s/_cwb\.txt$//;
		foreach my $line (@content)
		{
		    $line =~ s/\n//;
		    $line =~ s/\r//;
			if ($line !~ /<\/s>/ && $line !~ /<s>/)
			{
				if ($line =~ /\t/)
				{
					my @rad = split/\t/, $line;
					my $item = $rad[2];
					my $origItem = $rad[0];
					$clause = $clause . $item . ' ';
					$origClause = $origClause . $origItem . ' ';
				}
			}
			elsif ($line =~ /<s>/)
			{
				$clause = ' ';
				$origClause = '';
			}
			elsif ($clause ne '' && $clause ne ' ')
			{
				foreach my $phrase (@phrases)
				{
#					if ($clause =~ /$phrase /i) #Introducing blanks around phrase to make sure no hits are due to truncated forms
					while ($clause =~ / $phrase /i || $clause =~ /^$phrase /i) 
					{
						my $metadata = $texthash{$txt};
						print OUT "$phrase\t$origClause\t$metadata\n";
						$numhits++;
						$clause =~ s/$phrase/<FOUNDHERE>/i;
						$temphash{$phrase} = "notnull";
#						last;
					}
				}
				$clause = ' ';
				$origClause = ' ';
			}
		}
	}
}
close(OUT);
close(DS);
foreach my $key (sort(keys(%temphash)))
{
	if ($temphash{$key} eq 'null')
	{
		print NOHITS "$key\n";
	}
}
close(NOHITS);
print "Number of files: $numFiles\n";
print "Number of hits: $numhits\n";
exit;
