import logging
import json
import os
import datetime
import openai
import boto3
import settings
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage)

# logger 設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数の取得
SECRETS_MANAGER_NAME = os.environ['SECRETS_MANAGER_NAME']
CHATS_TABLE_NAME     = os.environ['CHATS_TABLE_NAME']

# SecretManager からAPIキーを取得
session  = boto3.session.Session()
smclient = session.client(service_name='secretsmanager')
try:
    get_secret_value_response = smclient.get_secret_value(SecretId=SECRETS_MANAGER_NAME)
except ClientError as e:
    logger.info(f'ERROR: {e}')
    raise e
secrets  = json.loads(get_secret_value_response['SecretString'])

# APIキーの取得
LINE_MESSAGING_API_CHANNEL_ACCESS_TOKEN = secrets["LINE_MESSAGING_API_CHANNEL_ACCESS_TOKEN"]
LINE_MESSAGING_API_CHANNEL_SECRET       = secrets["LINE_MESSAGING_API_CHANNEL_SECRET"]
OPEN_AI_API_KEY                         = secrets["OPEN_AI_API_KEY"]

# LINE Bot API と Open AI API の設定
line_bot_api    = LineBotApi(LINE_MESSAGING_API_CHANNEL_ACCESS_TOKEN)
handler         = WebhookHandler(LINE_MESSAGING_API_CHANNEL_SECRET)
openai.api_key  = OPEN_AI_API_KEY

# アクセス先 DynamoDB の定義
dynamodb = boto3.resource('dynamodb')
table    = dynamodb.Table(CHATS_TABLE_NAME)

# Lambda コントローラー関数（署名の検証とAPIレスポンスを担当）
def lambda_handler(event, context):
    logger.info('CALLED: lambda_handler()')
    
    # cf. https://github.com/line/line-bot-sdk-python
    signature   = event['headers']['x-line-signature']
    body        = event['body']
    
    # ロジック処理
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.info('ERROR: 署名検証の失敗')
    
    # LINE API の仕様に基づいたAPIレスポンス
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'OK'
    }

# ロジック処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    logger.info('CALLED: handle_message()')

    # 返答メッセージをデフォルト値で一旦設定
    response_message = settings.MESSAGE_RESPONSE_DEF_EXCEPTION
    
    try:
        # メッセージ送信者のユーザーIDとメッセージ本文を取得
        user_id      = event.source.user_id
        chat_message = event.message.text
        logger.info(f'CHAT_USER_ID: {user_id} / CHAT_MESSAGE: {chat_message}')
        
        # 当該ユーザーの過去のメッセージを、DynamoDB から取得する（GSIを利用）
        past_messages = table.query(
            IndexName = 'UserIdIndex',
            KeyConditionExpression = Key('ChatUserId').eq(user_id)
        )
        
        # 受信したメッセージが「リセットワード」であった場合、後続処理は行わずに例外を出し、トークン超過時と同じDBのItem削除を行う。
        if chat_message == settings.RESET_WORD:
            response_message = settings.MESSAGE_RESPONSE_RESET_WORD
            raise Exception('リセットワードを受信')
        
        # GPTに投入するデータ（prompts）を用意する
        prompts = []
        
        # キャラクター基本設定を prompts に追加
        character_setting = {
            "role": "system",
            "content": settings.CHARACTER_SETTING.format(username="西片")
        }
        prompts.append(character_setting)
        
        # 取得した過去のチャットメッセージを prompts に追加
        for message in past_messages['Items']:
            message_setting = {
                "role": message['ChatRole'],
                "content": message['ChatMessage']
            }
            prompts.append(message_setting)
        
        # 受信したチャットメッセージも prompts に追加
        new_message_setting = {
            "role": 'user',
            "content": chat_message
        }
        prompts.append(new_message_setting)
        
        # 完成した prompts を用いて GPT API を呼び出す
        logger.info(f'PROMPTS: {prompts}')
        result = openai.ChatCompletion.create(
            model = settings.GPT_MODEL,
            messages = prompts
        )
        logger.info(f'OPENAI_RESULT: {result}')
        
        # Token数が超過していた場合、メッセージにその旨を設定し、例外を発生させて終了
        if result.usage.total_tokens > settings.MAX_TOKEN:
            response_message = settings.MESSAGE_RESPONSE_EXCESS_TOKEN
            raise Exception('Tokenが超過')

        # ユーザーから受信したチャットメッセージを DynamoDB に保存する
        table.put_item(
            Item = {
                'ChatId':user_id + '#' + str(datetime.datetime.now()),
                'ChatRole':'user', # 利用者の入力した文字は、"user"とする
                'ChatMessage':chat_message,
                'ChatUserId':user_id,
                'CreatedAt':str(datetime.datetime.now()) # デフォルトでは世界標準時になる
            }
        )
        
        # GPTの返答内容を、DynamoDB に保存する
        response_message = result.choices[0].message.content
        table.put_item(
            Item = {
                'ChatId':user_id + '#' + str(datetime.datetime.now()),
                'ChatRole':'assistant', # GPTの返答内容は、'assistant' とする
                'ChatMessage':response_message,
                'ChatUserId':user_id,
                'CreatedAt':str(datetime.datetime.now()) # デフォルトでは世界標準時になる
            }
        )
        
    except Exception as e:
        logger.info(f'ERROR: {e}')

        # 当該ユーザーの Item を DynamoDB から削除する（DB洗替処理）
        with table.batch_writer() as batch:
            for message in past_messages['Items']:
                batch.delete_item(Key={'ChatId':message['ChatId']})
    
    finally:
        # メッセージを返信
        logger.info(f'RESPONSE_MESSAGE: {response_message}')
        line_bot_api.reply_message(
            reply_token = event.reply_token,
            messages    = TextSendMessage(text=response_message)
        )
