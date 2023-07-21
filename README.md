# 推しとLINEがしたい！ （ LINE x GPT x AWS CDK ）

## 【注意】作成中のため Readme のため、不備不足がある場合があります。

## アプリ概要
- 自分の「推しキャラ」（のAI）と LINE ができるシステムを開発しました。
- 詳しくは、Qiita のこちらの記事を参照ください。（動画やスライドあり）
 
## 要素技術
- LINE Messaging API
- Open AI API (GPT3.5, GPT4)
- AWS CDK (Python / API Gateway, Lambda, DynamoDB, SecretsManger)

## 展開方法 （概要のみ記載）
本リポジトリをクローンし、自身の AWS アカウントでデプロイする場合を想定

### 1. OpenAI 側の設定
1. GPT API を呼び出すために、APIキーを発行し、メモしておく。

### 2. LINE Developers 側の設定（前半）
1. 「プロバイダー」の作成
2. 「チャネル」を Messaging API で作成
3. 「チャネルシークレット」をメモしておく
4. 「チャネルアクセストークン（長期）」を発行し、メモしておく

### 3. AWS 側のインフラ展開
- 以下は、AWS Cloud9 (Amazon Linux2) を用いてデプロイする想定で記載（2023年7月時点で動作確認）  
- Cloud9 を利用する場合、AWS managed temporary credentials が有効だと `$ cdk deploy` でエラーが発生するので、右上の "Preferences" から無効化したのち `$ aws configure` で認証情報を設定しておく。

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
##（注：AWS CDK アプリケーションを環境（アカウント/リージョン）に初めてデプロイするときのみ実施）
$ cdk bootstrap

## 設定ファイルを編集
- 「4. 設定ファイルの編集」を要参照

## アプリのデプロイ
$ cdk deploy

## デプロイ後の作業
- デプロイ後に表示される Outputs の URL をメモする。（後ほど、LINE の Webhook URL に設定する）
- マネジメントコンソールから、SecretsManager の画面に移り、OPEN AI と LINE の APIキーを設定する。
```
### 4. 設定ファイルの編集
`./lambda/settings.py` を編集する。  
ここを書き換えることで、好きなキャラクターを演じさせることができる。  
書き方はこちらの資料などが参考になる。
[ChatGPTにギルガメッシュ王の人格を与えるには？｜深津 貴之 (fladdict)](https://note.com/fladdict/n/neff2e9d52224)


### 5. LINE Developers 側の設定（後半）
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
        - 「プロフィールのプレビューを確認」から、背景画像やボタンを編集できる
    - 「機能の利用」
        - 任意に設定
            - 例：写真や動画の受け取り　→　受け取らない
            - 例：LINE VOOM関連機能　→　利用しない

上記手順で一応動作する。あとはLINEの見た目にこだわったり、キャラクター設定を工夫していく。

## 使い方メモ
- 「リセット」と投稿すると、DBから過去のチャット内容が消えて、文脈がリセットされる。
    - `settings.py` を編集することで、「リセット」以外の単語を設定することも可能。
- Token の上限値に達すると、DBから過去のチャット内容が消えて、文脈がリセットされる。
    - こちらも、`settings.py` を編集することで、Tokenの上限値よりも前にリセットをかけることが可能。課金が膨れ上がることを防げる。

## デプロイ後の設定


## クリーンアップ
```
$ cdk destroy

## ブートストラップスタックの削除
- 注：将来CDKを使う予定があれば削除は不要
- CloudFormation のコンソール画面から「CDK Toolkit」スタックを削除
```


