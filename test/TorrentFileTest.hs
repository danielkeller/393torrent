{-# LANGUAGE StandaloneDeriving #-}
module TorrentFileTest (
    testTorrentFile
) where

import TorrentFile

import Test.Framework
import Test.Framework.Providers.HUnit (testCase)
import Test.HUnit ((@?=), assertFailure, assertBool)
import Data.ByteString.Char8 (pack)
import System.FilePath((</>))
import Control.Exception

-- these are only useful for testing
deriving instance Show TorrentFile
deriving instance Show FilesInfo
deriving instance Show FileInfo
deriving instance Eq FilesInfo
deriving instance Eq FileInfo

testTorrentFile = testGroup "TorrentFile" [
    testCase "singleFile" testSingleFile,
    testCase "multiFile" testMultiFile,
    testCase "invalidFile" testInvalidFile
    ]

testSingleFile = do
    file <- openTorrent ("testcases" </> "singlefile.torrent")
    announce file @?= "http://bttracker.debian.org:6969/announce"
    creationDate file @?= Just (read "2013-06-15 22:32:40 UTC")
    comment file @?= Just "\"Debian CD from cdimage.debian.org\""
    pieceLen file @?= 262144
    last (pieces file) @?= pack ".\NUL\SI\167\232WY\199\244\194T\212\217\195>\244\129\228Y\167"
    fileInfo file @?= SingleFile FileInfo {path = "debian-7.1.0-i386-netinst.iso", fileLength = 290455552}

testMultiFile = do
    file <- openTorrent ("testcases" </> "multifile.torrent")
    case fileInfo file of
        SingleFile _ -> assertFailure "should be multi file"
        MultiFile name infos -> do
            name @?= "Sigur Ros - ( ) - 2002"
            last infos @?= FileInfo {path = "08 Popplagi\240.mp3", fileLength = 21114859}

testInvalidFile = handle (\(ErrorCall e) -> print e) $ do
        file <- openTorrent "393torrent.cabal"
        print $ announce file
        assertFailure "should fail"
