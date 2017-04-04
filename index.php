<?php
if(isset($_POST['btn-upload']))
{
	$pic = rand(1000,100000)."-".$_FILES['pic']['name'];
        $pic_loc = $_FILES['pic']['tmp_name'];
	$folder="uploaded_files/";
	$cmd = "/usr/bin/igc2kmz $folder$pic $pic_loc";
	if(!system($cmd,$ret_val))
	{
		?><script>alert('successfully uploaded');</script><?php

	}
	else
	{
		?><script>alert('error while uploading file');</script><?php
	}
}
?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>IGC to KMZ converter</title>
</head>
<body>
Upload IGC tracklog
<form action="" method="post" enctype="multipart/form-data">
<input type="file" name="pic" />
<button type="submit" name="btn-upload">upload</button>
</form>
Download your KMZ from <a href=uploaded_files/>HERE</a><br>
<a href=https://github.com/cyberorg/igc2kmz>This page source code</a><br>
<a href=http://cyberorg.github.io/xcleague/>All about Paragliding in India</a><br>
</body>
</html>
