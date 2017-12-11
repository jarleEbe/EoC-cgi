#!/usr/bin/perl -w

use strict;
use CGI;
use CGI::Carp;
use utf8;
use CWB::Web::Query;

binmode STDIN, ":utf8";
binmode STDOUT, ":utf8";

&html5start("TEST");

print "<p>Hei og hå</p>";
#my $command = '/usr/bin/perl /var/www/cgi-bin/cwbcqp/mycqp.pl';
#my @result = `$command`;
#print "<p>$result[0]</p>";

my $query = new CWB::Web::Query 'TEST';
$query->context('10 words', '10 words');
$query->attributes('word', 'pos', 's');
$query->reduce(10);

my @matches  = $query->query("[word='it']");
my $nr_matches = @matches;
print "$nr_matches\n";

my @result = ();
my $oneRow = '';
for (my $i = 0; $i < $nr_matches; $i++)
{
    my $nr = $i + 1;               # match number
    my $m = $matches[$i];          # result struct
    $oneRow = $m->{'kwic'}->{'left'} . "\t" . $m->{'kwic'}->{'match'} . "\t". $m->{'kwic'}->{'right'}; 
    print "$m->{'cpos'}\n";               # corpus position of match
    print "$m->{'kwic'}->{'left'}\t";     # left context (HTML encoded)
    print "$m->{'kwic'}->{'match'}\t";    # match        ( ~      ~   )
    print "$m->{'kwic'}->{'right'}\n";    # right context( ~      ~   )
    print "$m->{'data'}->{'sitting'}\n";  # annotation of structural region
    push(@result, $oneRow);
    $oneRow = '';
 }

undef $query;

&html5end;

exit();

sub html5start
{
    my $title = shift(@_);
    print "Content-Type: text/html; charset=utf-8\n\n";
    print "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"UTF-8\">\n<title>$title</title>\n</head>\n<body>\n";
}

sub html5end
{
    print "\n</body>\n</html>";
}
