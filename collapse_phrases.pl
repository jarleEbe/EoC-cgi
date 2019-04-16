#!/usr/bin/perl

use strict;
use utf8;
use JSON;

my ($infile) = @ARGV;

open(CBF, "/var/www/cgi-bin/cbf/cbf.json");
my @content = <CBF>;
close(CBF);
my $cbf = '';
foreach (@content)
{
	chomp;
	$cbf = $cbf . $_;
}
my $jsonperl = decode_json($cbf);

open(INN, "$infile");
binmode INN, ":utf8";
my @content = <INN>;
close(INN);

my $pertextfile = "PhrasesPerText.txt";
open(OUT, ">$pertextfile");
binmode OUT, ":utf8";
print OUT "TextCode\tGender\tDateofBirth\tDecade\tDateofPubl\tNumWords\tHits\tNormHits\tUniqueHits\tNormUniqueHits\tRepetiveness\n";

my $pergenderfile = "PhrasesPerGender.txt";
open(GENDER, ">$pergenderfile");
binmode GENDER, ":utf8";

my $pergenderfile = "IndividualPhrasesPerDecade.txt";
open(IPDEC, ">$pergenderfile");
binmode IPDEC, ":utf8";
print IPDEC "Phrase\t1900\t1910\t1920\t1930\t1940\t1950\t1960\t1970\t1980\t1990\t2000\t2010\tYofBirth\tYofPub\n";

my %collapsedPhrases = ();
my %individualPhrases = ();
foreach my $line (@content)
{
    chomp($line);
	my ($phrase, $context, $textcode, $author, $title, $YofP, $gender, $YofB, $decade) = split/\t/, $line;
	my $period = '';

	if (int($decade) >= 1900 && int($decade < 1940))
	{
		$period = "1900-1939"
	}
	elsif (int($decade) >= 1940 && int($decade < 1980))
	{
		$period = "1940-1979"
	}
	elsif (int($decade) >= 1980 && int($decade < 2020))
	{
		$period = "1980-2019"
	}

	if (exists($collapsedPhrases{$textcode}))
	{
		if (exists($collapsedPhrases{$textcode}{$phrase}))
		{
			my $temp = $collapsedPhrases{$textcode}{$phrase};
			$temp++;
			$collapsedPhrases{$textcode}{$phrase} = $temp;
		}
		else
		{
			$collapsedPhrases{$textcode}{$phrase} = 1;
			my $utemp = $collapsedPhrases{$textcode}{'unique'};
			$utemp++;
			$collapsedPhrases{$textcode}{'unique'} = $utemp;
		}
		my $temp = $collapsedPhrases{$textcode}{'total'};
		$temp++;
		$collapsedPhrases{$textcode}{'total'} = $temp;
	}
	else
	{
		$collapsedPhrases{$textcode}{$phrase} = 1;
		$collapsedPhrases{$textcode}{'total'} = 1;
		$collapsedPhrases{$textcode}{'unique'} = 1;
		if ($YofB =~ /\?/)
		{
			$YofB =~ s/\?//;
		}
		if ($YofB =~ /Unknown/)
		{
			$YofB =~ s/Unknown/1950/;
		}
		if ($YofP =~ /\?/)
		{
			$YofP =~ s/\?//;
		}
		if ($YofP =~ /Unknown/)
		{
			$YofP =~ s/Unknown/1950/;
		}
		$collapsedPhrases{$textcode}{'YofB'} = $YofB;
		$collapsedPhrases{$textcode}{'YofP'} = $YofP;
	}

	my $alteredphrase = $phrase;
	$alteredphrase =~ s/ /_/g;

	if (exists($individualPhrases{$alteredphrase}))
	{
		if (exists($individualPhrases{$alteredphrase}{$decade}))
		{
			my $temp = $individualPhrases{$alteredphrase}{$decade};
			$temp++;
			$individualPhrases{$alteredphrase}{$decade} = $temp;
		}
		else
		{
			$individualPhrases{$alteredphrase}{$decade} = 1;
		}
#		my $temp = $individualPhrases{$alteredphrase}{'total'};
#		$temp++;
#		$individualPhrases{$alteredphrase}{'total'} = $temp;
	}
	else
	{
		$individualPhrases{$alteredphrase}{'1900-1909'} = 0;
		$individualPhrases{$alteredphrase}{'1910-1919'} = 0;
		$individualPhrases{$alteredphrase}{'1920-1929'} = 0;
		$individualPhrases{$alteredphrase}{'1930-1939'} = 0;
		$individualPhrases{$alteredphrase}{'1940-1949'} = 0;
		$individualPhrases{$alteredphrase}{'1950-1959'} = 0;
		$individualPhrases{$alteredphrase}{'1960-1969'} = 0;
		$individualPhrases{$alteredphrase}{'1970-1979'} = 0;
		$individualPhrases{$alteredphrase}{'1980-1989'} = 0;
		$individualPhrases{$alteredphrase}{'1990-1999'} = 0;
		$individualPhrases{$alteredphrase}{'2000-2009'} = 0;
		$individualPhrases{$alteredphrase}{'2010-2019'} = 0;

		$individualPhrases{$alteredphrase}{$decade} = 1;
#		$individualPhrases{$alteredphrase}{'total'} = 1;
		if ($YofB =~ /\?/)
		{
			$YofB =~ s/\?//;
		}
		if ($YofB =~ /Unknown/)
		{
			$YofB =~ s/Unknown/1950/;
		}
		if ($YofP =~ /\?/)
		{
			$YofP =~ s/\?//;
		}
		if ($YofP =~ /Unknown/)
		{
			$YofP =~ s/Unknown/1950/;
		}
		$individualPhrases{$alteredphrase}{'YofB'} = $YofB;
		$individualPhrases{$alteredphrase}{'YofP'} = $YofP;
#		$individualPhrases{$alteredphrase}{$gender} = 1;
	}
}

my %male = ();
my %female = ();
my %P1 = ();
my %P2 = ();
my %P3 = ();
my %decades = ();
my %antmaledecade = ();
my %antfemaledecade = ();
foreach my $outerkey (sort(keys(%collapsedPhrases)))
{
	foreach my $innerkey (keys %{$collapsedPhrases{$outerkey}})
	{
#		print OUT "$outerkey\t$innerkey\t$collapsedPhrases{$outerkey}{$innerkey}\n";
		my $period = '';
		my $decade = $jsonperl->{'Texts'}->{$outerkey}->{'Decade'};
		if (int($decade) >= 1900 && int($decade < 1940))
		{
			$period = "1900-1939"
		}
		elsif (int($decade) >= 1940 && int($decade < 1980))
		{
			$period = "1940-1979"
		}
		elsif (int($decade) >= 1980 && int($decade < 2020))
		{
			$period = "1980-2019"
		}

		if ($period eq '1900-1939')
		{
			my $ant = $collapsedPhrases{$outerkey}{$innerkey};
			if (exists($P1{$innerkey}))
			{
				my $temp = $P1{$innerkey};
				$temp = $temp + $ant;
				$P1{$innerkey} = $temp;
			}
			else
			{
				$P1{$innerkey} = $ant;
			}
		}
		if ($period eq '1940-1979')
		{
			my $ant = $collapsedPhrases{$outerkey}{$innerkey};
			if (exists($P2{$innerkey}))
			{
				my $temp = $P2{$innerkey};
				$temp = $temp + $ant;
				$P2{$innerkey} = $temp;
			}
			else
			{
				$P2{$innerkey} = $ant;
			}
		}
		if ($period eq '1980-2019')
		{
			my $ant = $collapsedPhrases{$outerkey}{$innerkey};
			if (exists($P3{$innerkey}))
			{
				my $temp = $P3{$innerkey};
				$temp = $temp + $ant;
				$P3{$innerkey} = $temp;
			}
			else
			{
				$P3{$innerkey} = $ant;
			}
		}


		if ($jsonperl->{'Texts'}->{$outerkey}->{'Gender'} eq 'male')
		{
			my $ant = $collapsedPhrases{$outerkey}{$innerkey};
			if (exists($male{$innerkey}))
			{
				my $temp = $male{$innerkey};
				$temp = $temp + $ant;
				$male{$innerkey} = $temp;
			}
			else
			{
				$male{$innerkey} = $ant;
			}
		}
		if ($jsonperl->{'Texts'}->{$outerkey}->{'Gender'} eq 'female')
		{
			my $ant = $collapsedPhrases{$outerkey}{$innerkey};
			if (exists($female{$innerkey}))
			{
				my $temp = $female{$innerkey};
				$temp = $temp + $ant;
				$female{$innerkey} = $temp;
			}
			else
			{
				$female{$innerkey} = $ant;
			}
		}
		if ($innerkey eq 'total')
#		if ($innerkey eq 'ZZZ')
		{
			my $period = '';
			my $decade = $jsonperl->{'Texts'}->{$outerkey}->{'Decade'};
			if (int($decade) >= 1900 && int($decade < 1940))
			{
				$period = "1900-1939"
			}
			elsif (int($decade) >= 1940 && int($decade < 1980))
			{
				$period = "1940-1979"
			}
			elsif (int($decade) >= 1980 && int($decade < 2020))
			{
				$period = "1980-2019"
			}
#			print OUT "$outerkey\t$collapsedPhrases{$outerkey}{$innerkey}\t";
			print OUT "$outerkey\t";
			print OUT "$jsonperl->{'Texts'}->{$outerkey}->{'Gender'}\t";
			print OUT "$collapsedPhrases{$outerkey}{'YofB'}\t";
			print OUT "$jsonperl->{'Texts'}->{$outerkey}->{'Decade'}\t";
			print OUT "$collapsedPhrases{$outerkey}{'YofP'}\t";
#			print OUT "$period\t";
#			print OUT "$jsonperl->{'Texts'}->{$outerkey}->{'noWords'}\t";
			print OUT "$jsonperl->{'Texts'}->{$outerkey}->{'noWords'}\t";
			print OUT "$collapsedPhrases{$outerkey}{$innerkey}\t";

			my $nowords = $jsonperl->{'Texts'}->{$outerkey}->{'noWords'};
			my $totphrases = $collapsedPhrases{$outerkey}{$innerkey};
			my $per100k = ($totphrases / $nowords) * 100000;
			my $rounded = sprintf("%.0f", $per100k);
			print OUT "$rounded\t";

			my $totunique = $collapsedPhrases{$outerkey}{'unique'};
			my $uper100k = ($totunique / $nowords) * 100000;
			$rounded = sprintf("%.0f", $uper100k);
			print OUT "$collapsedPhrases{$outerkey}{'unique'}\t";
			print OUT "$rounded\t";
			my $repetiveness = $totphrases / $totunique;
			$rounded = sprintf("%.2f", $repetiveness);
			print OUT "$rounded\n";

			my $gender = $jsonperl->{'Texts'}->{$outerkey}->{'Gender'};
			my $tiaar = $jsonperl->{'Texts'}->{$outerkey}->{'Decade'};
			$tiaar = $tiaar . $gender;
			if ($gender eq 'male')
			{
				if (exists($antmaledecade{$tiaar}))
				{
					my $temp = $antmaledecade{$tiaar};
					$temp++;
					$antmaledecade{$tiaar} = $temp;
				}
				else
				{
					$antmaledecade{$tiaar} = 1;
				}
			}
			else
			{
				if (exists($antfemaledecade{$tiaar}))
				{
					my $temp = $antfemaledecade{$tiaar};
					$temp++;
					$antfemaledecade{$tiaar} = $temp;
				}
				else
				{
					$antfemaledecade{$tiaar} = 1;
				}
			}

			if (exists($decades{$tiaar}))
			{
				my $temp = $decades{$tiaar};
				$temp = $temp + $rounded;
				$decades{$tiaar} = $temp;
			}
			else
			{
				$decades{$tiaar} = $rounded;
			}

			#print OUT "$totphrases\n";
		}
#		if ($innerkey =~ /-/)
#		{
#			my $permill = 0;
#			if ($innerkey eq '1900-1939')
#			{
#				my $temp = $collapsedPhrases{$outerkey}{$innerkey};
#				$permill = ($temp / $P1) * 1000000;				
#			}
#			if ($innerkey eq '1940-1979')
#			{
#				my $temp = $collapsedPhrases{$outerkey}{$innerkey};
#				$permill = ($temp / $P2) * 1000000;				
#			}
#			if ($innerkey eq '1980-2019')
#			{
#				my $temp = $collapsedPhrases{$outerkey}{$innerkey};
#				$permill = ($temp / $P3) * 1000000;				
#			}
#			if ($permill >= 5)
#			{
#				my $rounded = sprintf("%.0f", $permill);
#				print PERIOD "$outerkey\t$innerkey\tpmw\t$rounded\n";
#			}
#		}
	}
}
close(OUT);

print GENDER "\tMale\tFemale\n";
foreach my $key (keys(%antmaledecade))
{
	my $tempmale = $key;
	my $antmale = $antmaledecade{$tempmale};

	my $tempfemale = $key;
	$tempfemale =~ s/male/female/;
	my $antfemale = $antfemaledecade{$tempfemale};
	
	my $totmale = $decades{$tempmale};
	my $mann = $totmale / $antmale;

	my $totfemale = $decades{$tempfemale};
	my $kvinne = $totfemale / $antfemale;

	my $tiaaret = $key;
	$tiaaret =~ s/male//;

	$mann = sprintf("%.0f", $mann);
	$kvinne = sprintf("%.0f", $kvinne);
	print GENDER "$tiaaret\t$mann\t$kvinne\n";
}
close(GENDER);

my $P1file = "Phr4P1.txt";
open(PFILE, ">$P1file");
binmode PFILE, ":utf8";
foreach my $key (sort(keys(%P1)))
{
	print PFILE "$key\t$P1{$key}\n";
}
close(PFILE);

my $P2file = "Phr4P2.txt";
open(PFILE, ">$P2file");
binmode PFILE, ":utf8";
foreach my $key (sort(keys(%P2)))
{
	print PFILE "$key\t$P2{$key}\n";
}
close(PFILE);

my $P3file = "Phr4P3.txt";
open(PFILE, ">$P3file");
binmode PFILE, ":utf8";
foreach my $key (sort(keys(%P3)))
{
	print PFILE "$key\t$P3{$key}\n";
}
close(PFILE);

foreach my $outerkey (sort(keys(%individualPhrases)))
{
	my $newouterkey = $outerkey;
	$newouterkey = $outerkey;
	$newouterkey =~ s/\(\[\^_\]\+\)/X/g;
	$newouterkey =~ s/\(\.\+\)/X/g;
	print IPDEC "$newouterkey\t";
	foreach my $innerkey (sort(keys %{$individualPhrases{$outerkey}}))
	{
#		print IPDEC "$outerkey\t$innerkey\t$individualPhrases{$outerkey}{$innerkey}";
		print IPDEC "$individualPhrases{$outerkey}{$innerkey}\t";
	}
	print IPDEC "\n";
}
close(IPDEC);
exit;
