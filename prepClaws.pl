#!/usr/bin/perl

use strict;
use utf8;

my ($basePath, $resultPath) = @ARGV;

opendir(DS, $basePath) or die $!;
my $numFiles = 0;
while (my $txt = readdir(DS))
{
	if ($txt =~ /\.txt$/i)
	{
		$numFiles++;
		open(INN, "$basePath$txt");
		binmode INN, ":utf8";
		my @content = <INN>;
		close(INN);
		my $outputfile = $txt;
		$outputfile =~ s/\.txt/_prepped\.txt/;
		open(OUT, ">$resultPath$outputfile");
		binmode OUT, ":utf8";
		print "Preprocessing for CLAWS $txt\n";
		print OUT "<text>\n";
		foreach my $line (@content)
		{
		    chomp($line);
			$line =~ s/^\x{FEFF}//;
			$line =~ s/\x{000B}//g;

			$line =~ s/<([^>]+?)>//g;
			$line =~ s/^\s+//;
			$line =~ s/\s+$//;
			$line =~ s/([\t\n\f\r\p{IsZ}]+)/ /g;
			$line =~ s/(\p{isAlnum})_(\p{isAlnum})/$1$2/g;
			$line =~ s/_/ /g;
			$line =~ s/\*//g;
			$line =~ s/\|//g;

			$line =~ s/&mdash;/--/g;
			$line =~ s/&ndash;/--/g;

			$line =~ s/\$/&dollar;/g;
			$line =~ s/&/&amp;/g;
			$line =~ s/\[/&lsqb; /g;
			$line =~ s/\]/ &rsqb;/g;

			$line =~ s/--/&mdash;/g;
			$line =~ s/−/&mdash;/g;
			$line =~ s/–/&mdash;/g;
			$line =~ s/—/&mdash;/g;
			$line =~ s/–/&mdash;/g;
			$line =~ s/&mdash;/ &mdash; /g;

			$line =~ s/“/"/g;
			$line =~ s/”/"/g;

			$line =~ s/‘/'/g;
			$line =~ s/’/'/g;
			$line =~ s/´/'/g;
			$line =~ s/`/'/g;
			$line =~ s/ʻ/'/g;
			$line =~ s/ʼ/'/g;

			$line =~ s/…/\.\.\. /g;
			$line =~ s/\.\.\.([A-Z]{1,1})/\.\.\. $1/g;

			$line =~ s/�/ /g;

			$line = &convert_to_entities($line);

			$line =~ s/\s+/ /g;

			$line = &insertQM($line);
			my $wlen = &check_wlength($line);
			if ($wlen > 24)
			{
				if ($line =~ /([A-Za-z"]+)([.,;:]{1,1})\"([A-Za-z]+)/)
				{
					print "$line -> ";
					$line =~ s/([.,;:]{1,1})\"/$1 "/g;
					print "$line\n";
				}
			}
        	print OUT "$line ";
		}
		print OUT "\n</text>";
		close(OUT);
	}
}
close(DS);
print "No. files processed: $numFiles\n";
exit;


sub convert_to_entities
{
	my $string = shift(@_);

    my %hasj = (
		'Š' => '&Scaron;',
		'Œ' => '&OElig;',
		'Ž' => '&Zcaron;',
		'š' => '&scaron;',
		'œ' => '&oelig;',
		'ž' => '&zcaron;',
		'Ÿ' => '&Yuml;',
		'¡' => '&iexcl;',
		'¢' => '&cent;',
		'£' => '&pound;',
		'¥' => '&yen;',
		'§' => '&sect;',
		'¿' => '&iquest;',
		'À' => '&Agrave;',
		'Á' => '&Aacute;',
		'Â' => '&Acirc;',
		'Ã' => '&Atilde;',
		'Ä' => '&Auml;',
		'Å' => '&Aring;',
		'Æ' => '&AElig;',
		'Ç' => '&Ccedil;',
		'È' => '&Egrave;',
		'É' => '&Eacute;',
		'Ê' => '&Ecirc;',
		'Ë' => '&Euml;',
		'Ì' => '&Igrave;',
		'Í' => '&Iacute;',,
		'Î' => '&Icirc;',
		'Ï' => '&Iuml;',
		'Ð' => '&ETH;',
		'Ñ' => '&Ntilde;',
		'Ò' => '&Ograve;',
		'Ó' => '&Oacute;',
		'Ô' => '&Ocirc;',
		'Õ' => '&Otilde;',
		'Ö' => '&Ouml;',
		'×' => '&times;',
		'Ø' => '&Oslash;',
		'Ù' => '&Ugrave;',
		'Ú' => '&Uacute;',
		'Û' => '&Ucirc;',
		'Ü' => '&Uuml;',
		'Ý' => '&Yacute;',
		'Þ' => '&THORN;',
		'ß' => '&szlig;',
		'à' => '&agrave;',
		'á' => '&aacute;',
		'â' => '&acirc;',
		'ã' => '&atilde;',
		'ä' => '&auml;',
		'å' => '&aring;',
		'æ' => '&aelig;',
		'ç' => '&ccedil;',
		'è' => '&egrave;',
		'é' => '&eacute;',
		'ê' => '&ecirc;',
		'ë' => '&euml;',
		'ì' => '&igrave;',
		'í' => '&iacute;',
		'î' => '&icirc;',
		'ï' => '&iuml;',
		'ð' => '&eth;',
		'ñ' => '&ntilde;',
		'ò' => '&ograve;',
		'ó' => '&oacute;',
		'ô' => '&ocirc;',
		'õ' => '&otilde;',
		'ö' => '&ouml;',
		'÷' => '&divide;',
		'ø' => '&oslash;',
		'ù' => '&ugrave;',
		'ú' => '&uacute;',
		'û' => '&ucirc;',
		'ü' => '&uuml;',
		'ý' => '&yacute;',
		'þ' => '&thorn;',
		'ÿ' => '&yuml;');

    foreach my $key (keys(%hasj))
    {
		my $char = $key;
		my $entity = $hasj{$key};
        $string =~ s/$char/$entity/g;
    }

    return $string;

}


sub insertQM
{
    my $thetext = shift(@_);

	$thetext =~ s/^'/"/;
	
	$thetext =~ s/(\.|\?|\!) '/$1 "/g;
	$thetext =~ s/(\.|\?|\!)'/$1"/g;

	$thetext =~ s/'(\.|\?|\!)/"$1/g;
	$thetext =~ s/' (\.|\?|\!)/" $1/g;

	$thetext =~ s/(\,|\;|\:)'/$1"/g;
	$thetext =~ s/(\,|\;|\:|\() '/$1 "/g;

	$thetext =~ s/'(\,|\;|\:|\))/"$1/g;

	$thetext =~ s/&mdash; '/&mdash; "/g;
	$thetext =~ s/' &mdash; /" &mdash; /g;
	$thetext =~ s/ '([A-Za-z0-9 ]+?)' / "$1" /g;

#Exceptions such as "... executin'?"
	if ($thetext =~ /in"(\.|\?|\!)"/)
	{
		print "Finding ...in\"(.?!)\": $thetext\n";
		$thetext =~ s/in"(\.|\?|\!)"/in'$1"/g;
		print "Changed to $thetext\n";
	}

    return $thetext;
}

sub check_wlength
{

	my $line = shift(@_);

	my @words = split/ /, $line;
	my $wordlength = 0;
	foreach my $word (@words)
	{
		if (length($word) > 24)
		{
			print "Too long word: $word\n";
			$wordlength = length($word);
		}
	}
	return $wordlength;
}