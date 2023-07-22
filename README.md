# 推しと LINE できるシステム （ LINE x GPT x AWS CDK ）

## アプリ概要
- アニメなどのキャラクターと、LINE ができるシステムを開発しました。
    - もちろん、実態はキャラクターを演じているAIです。
- 詳細は、Qiita のこちらの記事を参照ください。
    - LTでの動画やスライド資料があります。
 
## 要素技術
- LINE Messaging API
- Open AI API (GPT4、3.5)
- AWS CDK (Python / API Gateway, Lambda, DynamoDB, SecretsManger)

## アーキテクチャ図

## 展開方法 （概要のみ記載）
本リポジトリをクローンし、自身の AWS アカウント上にデプロイをする想定です。

### 1. OpenAI 側の設定
1. GPT API を呼び出すために、APIキーを発行し、控えておく。

### 2. LINE Developers 側の設定（前半）
1. 「プロバイダー」の作成
2. 「チャネル」を Messaging API で作成
3. 「チャネルシークレット」を控えておく
4. 「チャネルアクセストークン（長期）」を発行し、控えておく

### 3. AWS 側のインフラ展開
- 以下は、AWS Cloud9 (Amazon Linux2) 開発環境を用いて、リソースをデプロイする想定で記載（2023年7月時点で動作確認済）  
- Cloud9 を利用する場合、"AWS managed temporary credentials" が有効だと `$ cdk deploy` 実行時にエラーが発生するので、右上の "Preferences" から無効化したのち `$ aws configure` で認証情報を設定しておく。

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
- デプロイ後に表示される Outputs の URL を控える。（後ほど、LINE の Webhook URL に設定する）
- マネジメントコンソールから、SecretsManager の画面に移り、
  控えておいた OPEN AI と LINE の APIキーで設定値を上書きする。
```
### 4. 設定ファイルの編集
`./lambda/settings.py` を編集する。  
ここを書き換えることで、好きなキャラクターを演じさせることができる。  
書き方は以下のナレッジなどが参考になる。  
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
        - 「プロフィールのプレビューを確認」から、背景画像や表示するボタンを任意に編集
    - 「機能の利用」
        - 任意に設定
            - 例：写真や動画の受け取り　→　受け取らない
            - 例：LINE VOOM関連機能　→　利用しない


ここまでの手順で一通り動作するようになる。  
あとはキャラクター設定を工夫したり、LINEの見た目にこだわるなどの工夫を進める。

## 使い方メモ
- 「リセット」とメッセージを送信すると、DBから過去のチャット内容が消えて、会話内容がリセットされる。
    - `settings.py` を編集することで、「リセット」以外の単語をリセットワールドに設定することも可能。
- Token の上限値に達すると、DBから過去のチャット内容が消えて、会話内容がリセットされる。
    - こちらも、`settings.py` を編集することで、Tokenの上限値よりも前にリセットをかけることが可能。
    - GPT API の課金が膨れ上がることを防げる。

## 初期設定 「しりとり上手の高木さん」について
- チャットでは、「こんにちは」や「おはよう」などのメッセージを最初に送信すると、しりとりゲームをする流れになります。
- シンプルに見えて、実は色々な工夫が詰まっています。詳細は Qiita の記事などをご参照ください。

## クリーンアップ方法
1. AWS 上に展開した、今回のリソースを削除
    - `$ cdk destroy` コマンドの実行
2. AWS 上に展開した、CDKブートストラップスタックを削除
    - 注意：今後もCDKを使う予定があれば削除は不要
    - CloudFormation のコンソール画面から「CDK Toolkit」スタックを削除
3. OpenAI 側の API キーを削除
4. LINE Developers の画面から、「チャネル」と「プロバイダー」を削除

