module Main (
    main
) where

import Test.Framework
import Test.Framework.Providers.HUnit (testCase)
import Test.Framework.Providers.QuickCheck2 (testProperty)

import Test.QuickCheck()
import Test.HUnit

main = defaultMain [
    testGroup "Sanity" [
        testProperty "==" prop_eq,
        testCase "2 + 2 == 4" (2 + 2 @?= (4 :: Int))
        ]
    ]

prop_eq :: Int -> Bool
prop_eq i = i == i
