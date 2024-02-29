Reporting = {
    "report_path": "/mnt/AIRTELLOGSDIR/reports",
    "test_log_path": "/mnt/AIRTELLOGSDIR/logs/t_LogsTests",
    "session_log_path": "/mnt/AIRTELLOGSDIR/logs/f_LogsSessions",
    "log_level_default": "DEBUG"
}

OpenSearch = {
    "host": "172.16.86.199",
    "port": 9200,
    "user": "admin",
    "pass": "",
    "index_name": "test_racks",
    "service_name_velo": "Service_OpenSearch"
}

Velocity = {
    "host": "vel-airtel-test.velocity-pv.lwd.int.spirent.io",
    "user": "spirent",
    "pass": "spirent"
}

Jira = {
    "host": "jira.spirenteng.com",
    "service_name_velo": "Service_Jira"
}

Netbox = {
    "host": "172.16.86.199",
    "token": "d07e78bfdb852319f825a2ec80d215178e4adf0f",
    "service_name_velo": "Service_Netbox"
}

Mail = {
    "smtp_server": "172.16.86.193",
    "default_to_email": "george.popovici@dxc.com",
    "from_email": "velocity@spirent.com"
}
