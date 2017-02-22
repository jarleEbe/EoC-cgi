#!/usr/bin/perl -w

#Ebeling, USIT, 17.02.2017.

use strict;
use CGI;
use CGI::Carp;
use LWP::Simple;
use JSON;
use utf8;
use Encode qw(decode encode);

#nabu
# 
my $action_path = "http://127.0.0.1/cgi-bin/cbf";
my $css_path = "http://nabu.usit.uio.no/hf/ilos/enpc";
my $general_path = "http://nabu.usit.uio.no/hf/ilos/enpc";
my $source_path = "http://nabu.usit.uio.no/hf/ilos/enpc";

my $mycgi = new CGI;
my @fields = $mycgi->param;

my $id = $mycgi->param('id') || "";
my $increase = $mycgi->param('increase') || 0;
if ($increase == 0)
{
	$increase = 5;
}
else
{
	$increase = $increase + 5;
}
if ($increase > 25)
{
	$increase = 25;
}

my $params = "id=$id&increase=$increase";

if ($id)
{
	my $ref = $id;
	$ref =~ s/^([A-Z0-9]+)(.+)/$1/;
	&print_header();
	print "<table align='center' width='600' border='0' cellpadding='4' cellspacing='2'>\n";

	my $result = &getthecontext($id, $increase);

	my $json_data = decode_json($result);
	my $reqnumberofhits = $json_data->{'requestednoHits'};
	my $actualnumberofhits = $json_data->{'numberofHits'};
	my $numberofhits = $json_data->{'Range'};
	for (my $ind = 0; $ind < $numberofhits; $ind++)
	{
		my $rawtext = $json_data->{'Context'}->[$ind]->{'rawText'};
		$rawtext = encode('utf-8', $rawtext);
		my $source = $json_data->{'Context'}->[$ind]->{'sunitId'};
		print "<tr>\n";
		print "<td>$rawtext</td>\n";
		if ($id eq $source)
		{
			print "<td><b>$source</b></td>\n";
		}
		else
		{
			print "<td>$source</td>\n";
		}
		print "</tr>\n";
	}
	print "</table>\n";
	print "<center>\n";
	print "Not working: <a href='$action_path/ENPCcontext.cgi?$params'>Increase context</a>\n";
	print "</center>\n";
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
	print "<head><title>CBFsearch -- Context</title>\n";
	print "<meta http-equiv='Content-Type' content='text/html; charset=utf8'/>\n";
	print "<link rel='stylesheet' type='text/css' href='$css_path/OMCsearch.css'/>\n";
	print "</head>\n";
	print "<body>\n";
	print "<table align='center' width='600' border='0' cellpadding='2' cellspacing='2'>\n";
	print "<tr><td colspan='2'>";
	print "<img src='$general_path/ENPCcontext.gif' width='600' height='25' border='0' alt='' usemap='#logomini_Map'/>";
	print "<map name='logomini_Map'>";
	print "<area shap='rect' title='UiO' COORDS='0,0,75,31' HREF='http://www.uio.no/' target='_self'/>";
	print "</map>";
	print "</td></tr>\n</table>\n";
}


sub getthecontext
{

	my ($id, $increase) = @_;
	my ($query, $nohits, $filters) = @_;

	my $url = 'http://127.0.0.1/cgi-bin/cbf/getcbfcontext.cgi?' . 'sunitid=' . $id . '&increase=' . $increase;
	my $result = get($url);
	die "Couldn't get it!" unless defined $result;
	return $result;

}
