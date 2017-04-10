<?php
if(isset($_POST['btn-upload']))
{
        $pic = rand(1000,100000)."-".$_FILES['pic']['name'];
        $pic_loc = $_FILES['pic']['tmp_name'];
        $folder="uploaded_files/";
        $cmd = "/usr/bin/igc2kmz $folder$pic $pic_loc";
        system($cmd,$ret_val);
        echo "<meta http-equiv=\"refresh\" content=\"1;URL=index.php\">";
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
</body>
