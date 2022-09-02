<?php
//start the server by running the ezphp.exe in parent folder
//call https://scopesim.univie.ac.at/InstPkgSvr/api.php?package_name=MICADO

    function log_package_use() {
        $log_file = "scopesim.log";
        $log_dict = array("timestamp"=>time(),
                          "time"=>date("Y-m-d")."T".date("H:i:s"),
                          "ip"=>$_SERVER['REMOTE_ADDR'],
                          "package_name"=>$_GET['package_name']
                          );

        file_put_contents($log_file,
                          json_encode($log_dict)."\n",
                          FILE_APPEND | LOCK_EX
                          );

        return $log_dict;
    }

    if (array_key_exists("package_name", $_GET)) {
        $log_dict = log_package_use();
    }

    echo json_encode($log_dict);

?>