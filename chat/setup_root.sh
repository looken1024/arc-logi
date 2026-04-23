#!/bin/bash
# Set root password for MariaDB
cd /home/yangkai/mariadb-10.6.12-linux-systemd-x86_64
echo "SET PASSWORD FOR 'root'@'localhost' = PASSWORD('root123'); FLUSH PRIVILEGES;" | ./bin/mysql -u root