from aws_cdk import (
    Stack,
    SecretValue,
    Duration,
    RemovalPolicy,
    aws_secretsmanager as sm,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
)
from constructs import Construct

# インフラ定義
class LineGptStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 1. SecretManager の定義
        secrets = sm.Secret(
            self,
            'ApiSecrets',
            secret_object_value={
                "LINE_MESSAGING_API_CHANNEL_ACCESS_TOKEN":  SecretValue.unsafe_plain_text("Must be changed after deployment - LINE_MESSAGING_API_CHANNEL_ACCESS_TOKEN"),
                "LINE_MESSAGING_API_CHANNEL_SECRET":        SecretValue.unsafe_plain_text("Must be changed after deployment - LINE_MESSAGING_API_CHANNEL_SECRET"),
                "OPEN_AI_API_KEY":                          SecretValue.unsafe_plain_text("Must be changed after deployment - OPEN_AI_API_KEY")
            }
        )
        
        # 2-1. DynamoDBの定義
        chats_table = dynamodb.Table(
            self,
            'ChatsTable',
            partition_key=dynamodb.Attribute(
                name="ChatId",
                type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY, # スタック削除時にDynamoDBテーブルを削除する
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST, # 従量課金型に変更
        )
        
        # 2-2. DynamoDBにGSI（グローバルセカンダリインデックス）を設定
        chats_table_gsi=chats_table.add_global_secondary_index(
            index_name="UserIdIndex",
            partition_key=dynamodb.Attribute(
                name="ChatUserId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="CreatedAt",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # 3-1. Lambdaレイヤーの設定（AWS Parameters and Secrets Lambda Extension）
        params_and_secrets = _lambda.ParamsAndSecretsLayerVersion.from_version(
            _lambda.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=_lambda.ParamsAndSecretsLogLevel.DEBUG
        )
        
        # 3-2. Lambda関数の設定
        line_gpt_function = _lambda.Function(
            self,
            'LineGptFunction',
            runtime = _lambda.Runtime.PYTHON_3_10,
            code    = _lambda.Code.from_asset('lambda'), # ハンドラーコードのパス
            handler = 'linegpt.lambda_handler', # ハンドラー関数の名前（ファイル名.関数名）
            timeout = Duration.minutes(1),
            environment={
                # lambda関数の環境変数の設定
                'CHATS_TABLE_NAME':     chats_table.table_name,
                'SECRETS_MANAGER_NAME': secrets.secret_name,
            },
            params_and_secrets = params_and_secrets, # 定義したLambdaレイヤーを利用
        )
        
        # 4. API Gateway を追加 (3-2のLambdaをKickするREST-APIエンドポイント)
        line_gpt_endpoint = apigw.LambdaRestApi(
            self,
            'LineGptEndpoint',
            handler=line_gpt_function,
        )
        
        # 5. 権限付与
        secrets.grant_read(line_gpt_function)
        chats_table.grant_read_write_data(line_gpt_function)
