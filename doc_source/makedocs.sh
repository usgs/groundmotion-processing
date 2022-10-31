#!/bin/bash

function usage() {
    echo "usage: makedocs.sh [rebuild | update | clean_data | clean_all ]"
    echo ""
    echo "  rebuild    Build documentation from a clean starting point."
    echo "  update     Incremental build of the documentation. No cleaning."
    echo "  clean_data Remove all temporary data files generated when building the documentation."
    echo "  clean_all  Remove all temporary data files and generated documentation."
}
	

function build_docs() {
    make html
    if [ $? -ne 0 ];then
        echo "Failed make HTML. Exiting."
        exit 1
    fi
    rm -fr ../docs
    cp -r _build/html ../docs
    touch ../docs/.nojekyll
}


function clean_data() {
    rm -fr contents/tutorials/data
}


function clean_docs() {
    rm -fr _build
}


target="rebuild"
if [ $# == 1 ]; then
    target=$1
fi
case $target in
    "rebuild")
        echo "Performing complete (re)build of documentation..."
        clean_docs
	clean_data
	build_docs
	;;
    "update" )
        echo "Performing incremental rebuild of documentation..."
	build_docs
	;;
    "clean_data" )
        echo "Removing temporary data files generated when building documentation..."
	clean_data
	;;
    "clean_all" )
        echo "Removing all temporary data and documentation files ..."
	clean_data
	clean_docs
	;;
    *)
	usage
	exit 0
	;;
esac
