echo '30 8 * * * cd /root/YourPath/; /usr/bin/python dayReport.py >> log.txt 2>&1' >> /var/spool/cron/crontabs/root
crontab -u root /var/spool/cron/crontabs/root