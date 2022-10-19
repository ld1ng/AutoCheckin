echo '30 8 * * * cd /root/AutoCheckin/; /usr/bin/python dayReport.py >> log.txt 2>&1' >> /var/spool/cron/crontabs/root
echo '59 18 * * * cd /root/AutoCheckin/; /usr/bin/python getLecture.py >> log2.txt 2>&1' >> /var/spool/cron/crontabs/root
crontab -u root /var/spool/cron/crontabs/root
