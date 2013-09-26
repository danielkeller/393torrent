module Main (
    main
) where

import TorrentFile

import Test.Framework
import Test.Framework.Providers.HUnit (testCase)
import Test.Framework.Providers.QuickCheck2 (testProperty)

import Test.QuickCheck()
import Test.HUnit

import qualified Cli

main = defaultMain [
    testGroup "Sanity" [
        testProperty "==" prop_eq,
        testCase "2 + 2 == 4" (2 + 2 @?= (4 :: Int)),
        testCase "main" Cli.main
        ]
    ]

prop_eq :: Int -> Bool
prop_eq i = i == i
