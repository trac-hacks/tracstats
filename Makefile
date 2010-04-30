#!/usr/bin/env make
#
# Makefile for building tracstats.
#

all: clean build

build:
	python setup.py build

install:
	python setup.py install
	/etc/init.d/httpd restart

clean:
	rm -rf build dist 


