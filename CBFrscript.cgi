#!/usr/bin/perl -w

#Ebeling, USIT, 18.04.2017.

use strict;
use CGI;
use CGI::Carp;
use LWP::Simple;


#nabu
my $scriptpath = "/home/jarlee/prog/R/script/scriptPropTest.R";

my $mycgi = new CGI;
#my @fields = $mycgi->param;
#my $arguments = $mycgi->param('args') || "";
my $arguments = "1408 1468 1110300 1119699";

if ($arguments)
{
	&print_header();

	my $result = &getstats($arguments, $scriptpath);
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
	print "<p>$pvalue</p>";
}
else
{
	&print_header();
}

print $mycgi->end_html;
exit;


sub print_header
{
	print $mycgi->header(-charset => 'utf-8');
	print "<!DOCTYPE html\">\n";
	print "<html>\n";
	print "<head><title>CBFsscript</title>\n";
	print "</head>\n";
	print "<body>\n";
	print "<p>Hei</p>";
}


sub getstats
{

	my ($args, $path) = @_;

	my $command = 'Rscript ' . $path . ' ' . $args;
	print "<p>$command</p>";
	my $result = `$command`;
	die "Couldn't get it!" unless defined $result;
	return $result;
}
