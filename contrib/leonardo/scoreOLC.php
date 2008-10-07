<?

	$file=$_REQUEST['file'];

	if ($_GET['dbg']) $debugActive=1;
	else $debugActive=0;

	if ($file) {
		$file=str_replace("#","^$^$^",$file);
		$url=parse_url($file);
		$dirname=dirname($url[path]);
		$basename=basename($url[path]);
		$basename=str_replace("^$^$^","#",$basename);

		$file=$url[scheme]."://".$url[host]."/". $dirname."/".rawurlencode($basename);
		$path=dirname( __FILE__ );
	
		$igcFilename=tempnam($path."/tmpFiles","IGC.");  //urlencode($basename)
		@unlink($igcFilename);
		DEBUG("igcFilename=$igcFilename");
		$lines=file($file);

		$cont="";
		foreach($lines as $line) {
			$cont.=$line;
		}	

/*		$cont="";
		$mod=0;
		$linesNum=count($lines);
		if ($linesNum > 650 ){
				$mod= 3 ;
		}

		$ii=0;
		foreach($lines as $line) {
				if ($ii % $mod != 0)
				$cont.=$line;
				$ii++;
		}	
*/
		if (!$handle = fopen($igcFilename, 'w')) exit; 
	    if (!fwrite($handle, $cont))    exit; 
		fclose ($handle); 

		@chmod ($path."/olc", 0755);  
		$cmd=$path."/olc ".$igcFilename;
		DEBUG("cmd=$cmd");
		exec($cmd,$res);
		
		DEBUG("result has ".count($res)." lines");
		foreach($res as $line) {
				DEBUG($line);
				if (substr($line,0,4)=="OUT ") echo substr($line,4)."\n";
		}

		@unlink($igcFilename);

}

	function DEBUG($msg) {
		global $debugActive;
		if ($debugActive) echo ">>$msg*<br>";
	}

?>