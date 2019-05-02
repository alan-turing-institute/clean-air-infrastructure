#! /bin/bash
cd /home/laqndaemon
if [ ! -e clean-air-infrastructure ]; then
    git clone git@github.com:alan-turing-institute/clean-air-infrastructure.git
fi
if [ "$(cat /var/www/update_needed)" == "yes" ]; then
    cd clean-air-infrastructure
    git fetch
    git checkout master
    git pull
    echo "" > /var/www/update_needed
fi