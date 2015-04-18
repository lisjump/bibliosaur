#!/bin/bash

set PRODPATH = "/var/www/www.bibliosaur.com/"

for file in 'about.html' \
            'accountsettings.html' \
            'authors.html' \
            'authorsmenu.html' \
            'coupons.html' \
            'currentdeals.html' \
            'dealsmenu.html' \
            'displaybooks.xml' \
            'edit.html' \
            'editauthors.html' \
            'editauthorbook.html' \
            'getdisplaybooks.xml' \
            'index.html' \
            'notloggedin.html' \
            'search.html' \
            'standardfooter.html' \
            'standardheader.html'
do
  cp $file /var/www/www.bibliosaur.com/
done

cd scripts/

for file in 'bibliologin.py' \
            'bibliosaur.py' \
            'dbbookupdate.py' \
            'dbauthorupdate.py' \
            'getkindledeals.py' \
            'importer.py' \
            'randomizebooktimes.py' \
            'sendmail.py' \
            'singlebookupdate.py' \
            'updateallprices.py' \
            'webapp2.py' \
            'xmlparser.py'
do
  cp $file /var/www/www.bibliosaur.com/scripts/
done

cd ..

cp js/bibliosaur.js /var/www/www.bibliosaur.com/js/

cp scripts/bottlenose/api.py /var/www/www.bibliosaur.com/scripts/bottlenose/
cp scripts/bottlenose/__init__.py /var/www/www.bibliosaur.com/scripts/bottlenose/

cp stylesheets/main.css /var/www/www.bibliosaur.com/stylesheets/

sed -i 's:/var/www/dev.bibliosaur.com/scripts/:/var/www/www.bibliosaur.com/scripts/:' /var/www/www.bibliosaur.com/scripts/bibliosaur.py