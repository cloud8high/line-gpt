# 推しとLINEがしたい！ （ LINE x GPT API x AWS CDK ）

## 【注意】作成中のため Readme のため、不備不足がある場合があります。

## アプリ概要
- 自分の「推しキャラ」（のAI）と LINE ができるシステムを開発しました。
 
## 技術要素
- LINE Messaging API
- Open AI API (GPT3.5, GPT4)
- AWS CDK (Python / API-Gateway, Lambda, DynamoDB, SecretsManger)

## 展開方法
### 本リポジトリをクローンし、自身の AWS アカウントでデプロイする場合...
注：AWS Cloud9 (Amazon Linux2) でデプロイする想定で記載（2023年7月時点）
```
## プロジェクトのコピーと各種準備
$ git clone {リポジトリURL}
$ cd {クローンしたディレクトリ}/

## python の仮想環境を作成して必要なモジュールをインストール
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt

## AWS CDK のブートストラップ
##（注：AWS CDK アプリケーションを環境（アカウント/リージョン）に初めてデプロイするときのみ実施）
$ cdk bootstrap

## アプリのデプロイ
$ cdk deploy

## デプロイ後の設定
- デプロイ後に表示される Outputs の URL が、LINE の Webhook URL になる。
- SecretsManager のコンソール画面で LINE と OPEN AI の APIキーを設定

## クリーンアップ
$ cdk destroy

## ブートストラップスタックの削除
- 注：将来CDKを使う予定があれば削除は不要
- CloudFormation のコンソール画面から「CDK Toolkit」スタックを削除
```
