# 推しと LINE ができるシステム （ LINE / GPT / AWS CDK ）
![line-gpt-gif-anime](https://github.com/cloud8high/line-gpt/assets/40209684/d37fd7da-ea3e-4251-a46b-1b3ecd3990b8)


## 概要
- アニメなどのキャラクターと、LINE でチャットができるシステムを開発しました。
    - 注：もちろん、実態はキャラクターを演じている AI です。
- 詳細や技術面の工夫は、[**Qiita のこちらの記事**](https://qiita.com/hayate_h/items/2e8ee634b456d751f744) をぜひご参照ください。
    - LTでの動画やスライド資料を載せています。

## 技術
### 要素技術
- [LINE Messaging API](https://developers.line.biz/ja/services/messaging-api/)
- [Open AI API (GPT4、3.5)](https://openai.com/blog/openai-api)
- [AWS CDK](https://aws.amazon.com/jp/cdk/) (Python / API Gateway, Lambda, DynamoDB, SecretsManger)

### アーキテクチャ図
![Architecture _diagram](https://github.com/cloud8high/line-gpt/assets/40209684/bf4cf133-7547-41bc-8157-cc66a88fa348)

### デプロイ方法 （概要のみ）
本リポジトリをクローンし、自身の AWS アカウント上に展開をする前提です。

#### 1. OpenAI 側の設定
1. GPT API を呼び出すために、APIキーを発行し、控えておく。

#### 2. LINE Developers 側の設定（前半）
1. 「プロバイダー」の作成
2. 「チャネル」を Messaging API で作成
3. 「チャネルシークレット」を控えておく
4. 「チャネルアクセストークン（長期）」を発行し、控えておく

#### 3. AWS 側のインフラ展開
- 以下は、AWS Cloud9 (Amazon Linux2) 開発環境を用いて、リソースをデプロイする想定で記載（2023年7月時点で動作確認済）  
    - 【重要】 Cloud9 を利用する場合、"AWS managed temporary credentials" が標準で有効となっており、`$ cdk deploy` コマンド実行時にエラーが発生する。
    - そのため、Cloud9 エディタ画面の右上 "Preferences" から "AWS Settings" → "AWS managed temporary credentials" の項目を無効化する。
    - 加えて、ターミナルで `$ aws configure` コマンドを実行し、AWSの認証情報を手動で設定する必要がある。（[参照](https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/cli-configure-files.html#cli-configure-files-methods)）

```
## プロジェクトのコピーと各種準備
$ git clone {本リポジトリURL}
$ cd {クローンしたディレクトリ}/

## python の仮想環境を作成して必要なモジュールをインストール
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
$ pip install -r lambda/requirements.txt -t lambda/

## AWS CDK のブートストラップ
## 注：AWS CDK アプリケーションを環境（アカウント/リージョン）に初めてデプロイするときのみ実施
$ cdk bootstrap

## 設定ファイルを編集
- 「4. 設定ファイルの編集」を要参照

## アプリのデプロイ（以降、変更の反映も同じコマンドを実施）
$ cdk deploy

## デプロイ後の作業
- デプロイ後に表示される Outputs の URL を控える。（後ほど、LINE の Webhook URL に設定する）
- マネジメントコンソールから、SecretsManager の画面に移り、
  控えておいた OPEN AI と LINE の APIキーで設定値を上書きする。
```
#### 4. 設定ファイルの編集
`./lambda/settings.py` 内の変数を任意に編集する。  
ここを書き換えることで、好きなキャラクターを演じさせることができる。  
書き方は以下のナレッジなどが参考になる。  
[ChatGPTにギルガメッシュ王の人格を与えるには？｜深津 貴之 (fladdict)](https://note.com/fladdict/n/neff2e9d52224)  
編集後は、`$ cdk deploy` コマンドを実行して、反映させる。

#### 5. LINE Developers 側の設定（後半）
1. 「LINE Developers」 → 作成したチャネルを選択 → 「Messaging API 設定」タブ
    - 「Webhook 設定」
        - 「Webook URL」 に `$ cdk deploy` 後に表示されたURLを入力
        - 「Webhook の利用」　を ON
    - 「LINE公式アカウント機能」
        - 「応答メッセージ」：編集　→　オフにする
        - 「あいさつメッセージ」：編集　→　任意の設定にする
2. 「LINE Official Account Manager」 → 「設定」
    - 「アカウント設定」
        - 任意に設定（アカウント名, プロフィール画像）
        - 「プロフィールのプレビューを確認」から、背景画像や表示するボタンを任意に設定
    - 「機能の利用」
        - 任意に設定
            - 例：写真や動画の受け取り　→　受け取らない
            - 例：LINE VOOM関連機能　→　利用しない

ここまでの手順で、一通り動作するようになる。  
あとは、キャラクター設定をチューニングしてみたり、LINEの見た目にこだわるなどの工夫をする。

### クリーンアップ方法（終了時）
1. AWS 上に展開した、今回のリソースを削除
    - `$ cdk destroy` コマンドの実行
2. AWS 上に展開した、CDKブートストラップスタックを削除
    - 注意：今後もCDKを使う予定があれば削除は不要
    - CloudFormation のコンソール画面から「CDK Toolkit」スタックを削除
3. OpenAI 側の API キーを削除
4. LINE Developers の画面から、「チャネル」と「プロバイダー」を削除

## メモ
### DB設計メモ
#### DynamoDB の設計内容

| カラム名 | PK | GSI | Type | 内容 |
| :--- | :---: | :---: | :---: | :--- |
| ChatId | PK | | String | メッセージを一意にするID。 今回は "UserId#time" の形で発番 |
| ChatRole |  | | String | 利用者からのメッセージは"user" / GPTからの返答は"assistant"を設定 |
| ChatUserId |  | PK | String | 誰とのトークルームのメッセージであるかを特定するもの。[LINEのuserId](https://developers.line.biz/ja/docs/messaging-api/getting-user-ids/)を設定|
| ChatMessage |  | | String | メッセージ本文。利用者から受け取ったメッセージや、GPTからのメッセージを保持 |
| CreatedAt |  | SK | String | 当該レコード（Item）の作成時刻を設定 |

#### インデックス設計
- Primary の Partition key は ChatId
- Global Secondary Index の Partition Key と Sort Key は、ChatUserId と CreatedAt 

#### CRUD処理
- C（作成）: 利用者がメッセージを送信した際、および、GPTから返答文を受け取った際に、Itemを追加。
- R（読込）: DBから、当該利用者の過去のメッセージを取り出す際に、GSI を用いて Item を取得。
- U（更新）: 当該処理なし。
- D（削除）: リセットワードを受信した場合、および、トークンの上限値に達した場合、BatchWrite で Item を削除。

### 使い方メモ
- 「リセット」とメッセージを送ると、DBから過去のチャット内容が消えて、会話内容がリセットされる。
    - `./lambda/settings.py` を編集することで、「リセット」以外の単語をリセットワードに設定することが可能。
- Token の上限値に達すると、DBから過去のチャット内容が消えて、会話内容がリセットされる。
    - こちらも、`./lambda/settings.py` を編集することで、Tokenの上限値よりも前にリセットをかけることが可能。
    - GPT API の課金が膨れ上がることを防げる。

### 初期設定 「しりとり上手の高木さん」について
- `settings.py` の `CHARACTER_SETTING` の初期値は、「[からかい上手の高木さん （© 山本崇一朗 小学館）](https://ja.wikipedia.org/wiki/%E3%81%8B%E3%82%89%E3%81%8B%E3%81%84%E4%B8%8A%E6%89%8B%E3%81%AE%E9%AB%98%E6%9C%A8%E3%81%95%E3%82%93)」 という漫画・アニメにヒントを得た、「しりとり上手の高木さん」 を設定しています。
- 「こんにちは」や「おはよう」などのメッセージを最初に送信すると、しりとりゲームが始まります。
- シンプルに見えて、実は色々な工夫が詰まっています。[詳細は Qiita の記事](https://qiita.com/hayate_h/items/2e8ee634b456d751f744) のLT発表資料などをご参照ください。

## ライセンス
- [MIT](https://github.com/cloud8high/line-gpt/blob/main/LICENSE)

## 開発者について
- [Hayate.H](https://github.com/cloud8high/profile)