#! /bin/bash


PYTHONPATH=. coverage run --source torrent test/tracker_test.py
mv .coverage .coverage.tracker
PYTHONPATH=. coverage run --source torrent test/torrent_test.py
mv .coverage .coverage.torrenttest
PYTHONPATH=. coverage run --source torrent test/fileinfo_test.py
mv .coverage .coverage.fileinfo
PYTHONPATH=. coverage run --source torrent test/ui_test.py
mv .coverage .coverage.ui
PYTHONPATH=. coverage run --source torrent test/files_test.py
mv .coverage .coverage.ui
PYTHONPATH=. coverage run --source torrent test/peer_test.py
mv .coverage .coverage.fileinfo

coverage combine

coverage report -m
