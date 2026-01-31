<!--
 Licensed to the Apache Software Foundation (ASF) under one
 or more contributor license agreements.  See the NOTICE file
 distributed with this work for additional information
 regarding copyright ownership.  The ASF licenses this file
 to you under the Apache License, Version 2.0 (the
 "License"); you may not use this file except in compliance
 with the License.  You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing,
 software distributed under the License is distributed on an
 "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 KIND, either express or implied.  See the License for the
 specific language governing permissions and limitations
 under the License.
 -->

 On Github "About" the description should be changed from "Mirror of Apache Mahout" to "Apache Mahout - an environment for quickly creating scalable, performant machine learning applications." Also the below tags should be with updated with `python` `rust`, `cuda`, `machine-learning` and `apache-mahout`

其實也不是我想法就是了xDDDDD
[10:36 AM]in short, 現在不是有一個 Dag 在等 1 / 3 個 asset 這樣嗎
[10:36 AM]但如果是 partition
[10:36 AM]那就不是
[10:36 AM]我們是在某個 partition key 等 1/3
邱冠銘  [10:36 AM]
對
Wei Lee  [10:37 AM]
partition key 好像有個東西叫做 partition key 什麼 log 的跟什麼 dag run 的
邱冠銘  [10:37 AM]
你竟然可以用兩句話講解的這麼清楚 好狠
[10:38 AM]PartitionAssetKeyLog
[10:38 AM]AssetPartitionDagRun
[10:38 AM]這超長
Wei Lee  [10:39 AM]
n 個 AssetPartitionDagRun 的 (還沒有 dag_id -> 還沒完成) -> 各字還在等 m 個 PartitionAssetKeyLog
[10:39 AM]所以會多一個頁面
[10:39 AM]大概像是這種感覺
[10:40 AM]如果沒聽懂的話，我 sprint 空擋來整理一下，能聽懂的話，那有點太強xD 我根本都在亂講
邱冠銘  [10:40 AM]
我大概懂你在講什麼，我剛花了不少時間理解了整個 partition 哈哈哈
