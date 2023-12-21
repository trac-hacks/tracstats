#!/usr/bin/make
#
# Makefile for building tracstats.
#

all: clean build

build:
	python3 setup.py build

dist:
	python3 setup.py bdist_egg

install:
	python3 setup.py install
	/etc/init.d/httpd restart

clean:
	rm -rf build dist


