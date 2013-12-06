#! /bin/bash


PYTHONPATH=. coverage run --source torrent test/tracker_test.py
mv .coverage .coverage.tracker
PYTHONPATH=. coverage run --source torrent test/torrent_test.py
mv .coverage .coverage.torrenttest
PYTHONPATH=. coverage run --source torrent test/fileinfo_test.py
mv .coverage .coverage.fileinfo

coverage combine

coverage report -m
