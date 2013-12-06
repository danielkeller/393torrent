# 393torrent
A software engineering class project to make a bittorrent client in python.

To install dependencies, run 'pip install -r requirements.txt'

## How to Use the Application

Python 2.7 and pip are required to run the application. As described above, use pip to install the needed libraries. To download a torrent, run the application as 'python torrent/torrent.py torrentfile.torrent'. To interrupt the download, hit Ctrl-C.

### Full Usage Text

<pre>
usage: torrent.py [-h] [--seed] [--port PORT] torrent_file

Process a torrent file.

positional arguments:
  torrent_file  a single torrent file

optional arguments:
  -h, --help    show this help message and exit
  --seed        seed forever (default: seed while downloading)
  --port PORT   Optionally set the port for the client to listen o
</pre>

## In action!
![Screenshot](https://raw.github.com/danielkeller/393torrent/master/Screen.png)
