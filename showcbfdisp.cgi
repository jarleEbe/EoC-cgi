#!/usr/bin/perl -w

#Ebeling, USIT, 26.01.2017.

use strict;
use CGI;
use CGI::Carp;
use LWP::Simple;
use JSON;
use Data::Dumper;
use Encode qw(decode encode);
use utf8;
use HTML::Entities;

binmode STDIN, ":utf8";

# Nabu
print "Content-Type: text/html; charset=utf-8\n\n";
print "<!DOCTYPE html>\n";
print "<html>";
print "<head><title>Test</title></head></body>";

open(JSONFILE, "cbf.json");
my @content = <JSONFILE>;
close(JSONFILE);
my $jsonfromfile = join(" ", @content);

my $json_data = decode_json($jsonfromfile);

#my $reqnumberofhits = $json_data->{'requestednoHits'};
#my $actualnumberofhits = $json_data->{'numberofHits'};

my $male = $json_data->{'male'};
my $female = $json_data->{'female'};
my $nomaletexts = $json_data->{'noMaleTexts'};
my $nofemaletexts = $json_data->{'noFemaleTexts'};
my $numberoftexts = $json_data->{'numberofTexts'};
my $textcodes = $json_data->{'Texts'};
#my $texts = from_json($textcodes);

print "<p>$female</p>";
foreach my $key (sort(keys(%$textcodes)))
{
	print "$key - $textcodes->{$key}<br/>";
}
#my $numberofhits = $json_data->{'numberofHits'};
#for (my $ind = 0; $ind < $numberofhits; $ind++)
#{
#	my $sunit = $json_data->{'Hits'}->[$ind]->{'sunit'};
#	$sunit = encode('utf-8', $sunit);
#	my $sex = $json_data->{'Hits'}->[$ind]->{'sunit'};
#	my $source = $json_data->{'Hits'}->[$ind]->{'sunitId'};
#	my $textid = $json_data->{'Hits'}->[$ind]->{'textId'};
#}
	
print "</body></html>";
exit;
