<?php
$html = file_get_contents("http://www.heise.de/extras/foren/go.shtml?forum_id=117625&list=1&hs=0&c=all");
$html = preg_replace("/<!--.*-->/","",$html);
$html = preg_replace('/class="thread_tree"/','id="thread_tree"',$html);
$dom = new DOMDocument();
$doc = @$dom->loadHTML($html);
$thread = $dom->getElementById("thread_tree");
$items = $thread->getElementsByTagName("li");
$output = new DOMDocument("1.0","UTF-8");
$rss = $output->createElement("rss");
$rss->setAttribute("version","2.0");
$channel = $output->createElement("channel");
$title = $output->createElement("title");
$title->appendChild($output->createTextNode("Heise-OTF"));
$channel->appendChild($title);
$link = $output->createElement("link");
$link->appendChild($output->createTextNode("http://www.heise.de/extras/foren/go.shtml?list=1&forum_id=117625"));
$channel->appendChild($link);
$pubDate = $output->createElement("pubDate");
$pubDate->appendChild($output->createTextNode(date("c")));
$channel->appendChild($pubDate);
foreach ($items as $item) {
	$values = $item->getElementsByTagName("div");
	$link = $values->item(5)->getElementsByTagName("a")->item(0);

	$item = $output->createElement("item");
	$title = $output->createElement("title");
	#$title->appendChild($output->createTextNode(trim($link->nodeValue)));
	$title->appendChild($output->createTextNode(trim($link->nodeValue)." (".trim($values->item(3)->nodeValue).")"));
	$item->appendChild($title);
	$locallink = $output->createElement("link");
	$locallink->appendChild($output->createTextNode("http://www.heise.de".$link->getAttribute
	("href")));
	$item->appendChild($locallink);
	$author = $output->createElement("author");
	$author->appendChild($output->createTextNode(trim($values->item(3)->nodeValue)));
	$item->appendChild($author);
	#print "<hr>Datum: ".$values->item(2)->getElementsByTagName("span")->item(0)->firstChild->nodeValue; 
	#print "<br>Voting: ".$values->item(4)->getElementsByTagName("img")->item(0)->getAttribute("src");
	$channel->appendChild($item);
}
$rss->appendChild($channel);
$output->appendChild($rss);
echo $output->saveXML();
?>
