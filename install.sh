#!/bin/bash

cp about.html /var/www/www.bibliosaur.com/
cp accountsettings.html /var/www/www.bibliosaur.com/
cp authors.html /var/www/www.bibliosaur.com/
cp coupons.html /var/www/www.bibliosaur.com/
cp currentdeals.html /var/www/www.bibliosaur.com/
cp dealsmenu.html /var/www/www.bibliosaur.com/
cp displaybooks.xml /var/www/www.bibliosaur.com/
cp edit.html /var/www/www.bibliosaur.com/
cp getdisplaybooks.xml /var/www/www.bibliosaur.com/
cp index.html /var/www/www.bibliosaur.com/
cp notloggedin.html /var/www/www.bibliosaur.com/
cp search.html /var/www/www.bibliosaur.com/
cp standardfooter.html /var/www/www.bibliosaur.com/
cp standardheader.html /var/www/www.bibliosaur.com/

cp js/bibliosaur.js /var/www/www.bibliosaur.com/js/

cp scripts/bibliologin.py /var/www/www.bibliosaur.com/scripts/
cp scripts/bibliosaur.py /var/www/www.bibliosaur.com/scripts/
cp scripts/dbbookupdate.py /var/www/www.bibliosaur.com/scripts/
cp scripts/getkindledeals.py /var/www/www.bibliosaur.com/scripts/
cp scripts/importer.py /var/www/www.bibliosaur.com/scripts/
cp scripts/randomizebooktimes.py /var/www/www.bibliosaur.com/scripts/
cp scripts/sendmail.py /var/www/www.bibliosaur.com/scripts/
cp scripts/singlebookupdate.py /var/www/www.bibliosaur.com/scripts/
cp scripts/updateallprices.py /var/www/www.bibliosaur.com/scripts/
cp scripts/webapp2.py /var/www/www.bibliosaur.com/scripts/
cp scripts/xmlparser.py /var/www/www.bibliosaur.com/scripts/

cp scripts/bottlenose/api.py /var/www/www.bibliosaur.com/scripts/bottlenose/
cp scripts/bottlenose/__init__.py /var/www/www.bibliosaur.com/scripts/bottlenose/

cp stylesheets/main.css /var/www/www.bibliosaur.com/stylesheets/

sed -i 's:/var/www/dev.bibliosaur.com/scripts/:/var/www/www.bibliosaur.com/scripts/:' tmp/bibliosaur.py