module TorrentFile (
	TorrentFile,
	FileInfo,
	openTorrent,
    readTorrent,
) where

import Data.BEncode

import Data.Time
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
import Control.Exception

--define a ! with better errors for showable keys
(!) :: (Ord k, Show k) => Map.Map k m -> k -> m
(!) dict key = case Map.lookup key dict of
    Just val -> val
    Nothing -> error (show key ++ " not found in dictionary")

infixl 9 ! --same as in Data.Map

data TorrentFile = TorrentFile
	{announce :: String
	,creationDate :: Maybe UTCTime
	,comment :: Maybe String
	,pieceLen :: Int64
	,pieces :: [BS.ByteString]
	,fileInfo :: FilesInfo
    }
    deriving Show

data FilesInfo = SingleFile FileInfo | MultiFile FilePath [FileInfo]
    deriving Show

data FileInfo = FileInfo
	{path :: FilePath
	,fileLength :: Int64
    }
    deriving Show

openTorrent :: FilePath -> IO TorrentFile
openTorrent torrentPath =
    handle (\ (ErrorCall m) -> error (torrentPath ++ " is not a valid .torrent file:\n\t" ++ m)) $
    do fileData <- BSL.readFile torrentPath
       case bRead fileData of
           Nothing -> error "Not a torrent file"
           Just benc -> return $ readTorrent $ benc
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
readTorrent _ = error "expected a dictionary"

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
getFileInfo _ = error "expected a dictionary"

bStrToString :: BEncode -> String
bStrToString (BString s) = toString (toStrict s)
bStrToString _ = error "expected a string"

bIntToTime :: BEncode -> UTCTime
bIntToTime (BInt i) = posixSecondsToUTCTime (fromIntegral i)
bIntToTime _ = error "expected an integer"

bInt :: Integral a => BEncode -> a
bInt (BInt i) = fromIntegral i
bInt _ = error "expected an integer"

--break the ByteString into a list of 20-byte SHA1 pieces
bStrToPieces :: BEncode -> [BS.ByteString]
bStrToPieces (BString s) = unfoldr nextpiece (toStrict s)
    where nextpiece s' | BS.null s' = Nothing
                       | otherwise = Just (BS.splitAt 20 s') 
          --unfoldr want a pair (output, next) which splitAt provides
bStrToPieces _ = error "expected a string"

bListToPath :: BEncode -> FilePath
bListToPath (BList dirs) = joinPath (map bStrToString dirs)
bListToPath _ = "expected a list of strings"
