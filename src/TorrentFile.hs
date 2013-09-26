module TorrentFile (
	TorrentFile,
	TorrentInfo,
	FileInfo,
	openTorrent,
) where

import Data.BEncode
import Data.Time
import Data.ByteString
import Data.Binary(decodeFile)
import Data.Int(Int64)
import Data.Map ((!))
import qualified Data.Map as Map ()

data TorrentFile = TorrentFile {
	info :: TorrentInfo,
	announce :: String,
	creationDate :: Maybe UTCTime,
	comment :: Maybe String
}

data TorrentInfo = TorrentInfo {
	pieceLen :: Int64,
	pieces :: ByteString,
	fileInfo :: FilesInfo
}

data FilesInfo = SingleFile FileInfo | MultiFile [FileInfo]

data FileInfo = FileInfo {
	name :: FilePath,
	length :: Int64,
	md5sum :: ByteString
}

openTorrent :: FilePath -> IO 
openTorrent path = do
	benc <- decodeFile path
	return (readTorrent benc)

readTorrent :: BEncode -> TorrentFile
readTorrent (BDict dict) = TorrentFile {
	info = readTorrentInfo (dict ! "info"),
	announce = 
	}
readTorrent _ = error "Broken torrent file"

bStrToString :: 