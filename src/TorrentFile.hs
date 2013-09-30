--don't warn about incomplete patterns. We just let it call error and catch the exception
{-# OPTIONS_GHC -fno-warn-incomplete-patterns #-}
module TorrentFile (
	TorrentFile(..),
	FilesInfo(..),
	FileInfo(..),
	openTorrent,
    readTorrent,
) where

import Data.BEncode

import Data.Time(UTCTime)
import Data.Time.Clock.POSIX (posixSecondsToUTCTime)

import qualified Data.ByteString as BS
import qualified Data.ByteString.Lazy as BSL (readFile)
import Data.ByteString.UTF8 (toString)
--BEncode uses lazy bytestring, but most libraries use strict ones
import Data.ByteString.Lazy.Char8 (toStrict)
import Data.List(unfoldr)

import System.FilePath(joinPath)

import Data.Int(Int64)
import qualified Data.Map as Map
import Data.Map ((!))
import Control.Exception

data TorrentFile = TorrentFile
	{announce :: String
	,creationDate :: Maybe UTCTime
	,comment :: Maybe String
	,pieceLen :: Int64
	,pieces :: [BS.ByteString]
	,fileInfo :: FilesInfo
    }

data FilesInfo = SingleFile FileInfo | MultiFile FilePath [FileInfo]

data FileInfo = FileInfo
	{path :: FilePath
	,fileLength :: Int64
    }

openTorrent :: FilePath -> IO TorrentFile
openTorrent torrentPath =
    handle (\ (ErrorCall _) -> error (torrentPath ++ " is not a valid .torrent file")) $
    do fileData <- BSL.readFile torrentPath
       --use case instead of let to force evaluation
       case bRead fileData of Just benc -> return $ readTorrent $ benc
       --the binary instance for BEncode is broken

readTorrent :: BEncode -> TorrentFile
readTorrent (BDict dict) = TorrentFile
	{announce = bStrToString $ dict ! "announce"
    ,creationDate = fmap bIntToTime $ Map.lookup "creation date" dict
    ,comment = fmap bStrToString $ Map.lookup "comment" dict
    ,pieceLen = bInt $ info ! "piece length"
    ,pieces = bStrToPieces $ info ! "pieces"
    ,fileInfo = getFilesInfo info
	}
    where BDict info = dict ! "info"

getFilesInfo :: Map.Map String BEncode -> FilesInfo
getFilesInfo info
    | "files" `Map.member` info = MultiFile (bStrToString $ info ! "name") fileInfos
    | otherwise = SingleFile FileInfo {path = bStrToString $ info ! "name"
                                      ,fileLength = bInt $ info ! "length"
                                      }
    where BList files = info ! "files"
          fileInfos = map getFileInfo files

getFileInfo :: BEncode -> FileInfo
getFileInfo (BDict file) = FileInfo {path = bListToPath $ file ! "path"
                                    ,fileLength = bInt $ file ! "length"
                                    }

bStrToString :: BEncode -> String
bStrToString (BString s) = toString (toStrict s)

bIntToTime :: BEncode -> UTCTime
bIntToTime (BInt i) = posixSecondsToUTCTime (fromIntegral i)

bInt :: Integral a => BEncode -> a
bInt (BInt i) = fromIntegral i

--break the ByteString into a list of 20-byte SHA1 pieces
bStrToPieces :: BEncode -> [BS.ByteString]
bStrToPieces (BString s) = unfoldr nextpiece (toStrict s)
    where nextpiece s' | BS.null s' = Nothing
                       | otherwise = Just (BS.splitAt 20 s') 
          --unfoldr want a pair (output, next) which splitAt provides

bListToPath :: BEncode -> FilePath
bListToPath (BList dirs) = joinPath (map bStrToString dirs)
