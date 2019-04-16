#!/usr/bin/perl

use strict;
use utf8;

#E.g. prepdata/
my ($basePath) = @ARGV;


my $headerfile = "allheaders.txt";
open(INN, "$headerfile");
binmode INN, ":utf8";
my @tempcontent = <INN>;
close(INN);
my %texthash = ();
foreach (@tempcontent)
{
	chomp;
	s/\n//;
	s/\r//;
	my ($code, $author, $title, $YofP, $gender, $YofB, $decade, $genre) = split/\t/;
	$texthash{$code} = $_;
}

opendir(DS, $basePath) or die $!;
my $numFiles = 0;
my $numhits = 0;
my $referencefile = "WLL-refCorpus.txt";
open(REF, ">$referencefile");
binmode REF, ":utf8";
my %corpusList = ();
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
		my %textList = ();
		my $outputfile = 'singlefiles/' . $txt . '-WLL' . '.txt';
		open(KEYS, ">$outputfile");
		binmode KEYS, ":utf8";
		my $meta = shift(@content);
		foreach my $line (@content)
		{
		    $line =~ s/\n//;
		    $line =~ s/\r//;
			if ($line !~ /<\/s>/ && $line !~ /<s>/)
			{
				if ($line =~ /\t/)
				{
					my @rad = split/\t/, $line;
					my $word = $rad[0];
					my $pos = $rad[1];
					my $lem = $rad[2];

					if ($pos eq 'NP' || $pos eq 'NP1' or $pos eq 'NP2')
					{
#						print "$lem : $pos\n";
					}
					else
					{
						$pos = substr($pos, 0,1);
						my $wp = lc($word) . '_' . $pos;
						my $lp = $lem . '_' . $pos; #Egen fil / Egen linje?

						if ($wp =~ /(^[A-Za-z]{2,})/)
						{
							if (exists($textList{$lp}))
							{
								my $temp = $textList{$lp};
								$temp++;
								$textList{$lp} = $temp;
							}
							else
							{
								$textList{$lp} = 1;
							}

							if (exists($corpusList{$lp}))
							{
								my $temp = $corpusList{$lp};
								$temp++;
								$corpusList{$lp} = $temp;
							}
							else
							{
								$corpusList{$lp} = 1;
							}
						}
					}
				}
			}
		}
		foreach my $key (sort(keys(%textList)))
		{
			print KEYS "$key\t$textList{$key}\n";
		}
		close(KEYS);
	}
}

foreach my $key (sort(keys(%corpusList)))
{
	print REF "$key\t$corpusList{$key}\n";
}
close(REF);
print "Number of files: $numFiles\n";
exit;
