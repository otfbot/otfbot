#!/bin/bash
# You need:
#  * pydoctor: - get latest svn from http://codespeak.net/~mwh/pydoctor/
#              - sudo python setup.py install
#  * Nevow: - latest stable from http://www.divmod.org/trac/wiki/DivmodNevow#Download
#           - unpack, sudo python setup.py install
# Just upload the whole directory "apidocs" (which this script creates) to /home/groups/otfbot/htdocs/pages

additional_init="."
curdir=`pwd`
dir=`dirname $0`
cd $dir/..
for i in $additional_init; do
	if [ ! -e $i/__init__.py ]; then
		touch $i/__init__.py
		init="$init $i"
	fi;
done
OTFBOTDIR=`pwd`
cd ..
pydoctor 	--add-package=`basename $OTFBOTDIR` \
		--project-name="OtfBot" \
		--project-url="http://otfbot.berlios.de/" \
		--html-output=$OTFBOTDIR/doc/apidocs \
		--make-html
cd $OTFBOTDIR
for i in $init; do
	rm $i/__init__.py
done
cd $curdir
