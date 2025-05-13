# AWS Lambda Pythonランタイムの公式ベースイメージを使用します
# Pythonコードと互換性のあるバージョンを選択します (例: 3.8, 3.9, 3.11, 3.12)
FROM public.ecr.aws/lambda/python:3.13

# Lambdaハンドラ関数コードをコピーします
COPY app.py ${LAMBDA_TASK_ROOT}/

# requirementsファイルをコピーします
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# requirements.txtで指定された依存関係をインストールします
# --targetフラグにより、ライブラリがLambda用の正しいディレクトリにインストールされます
RUN pip3 install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# CMDをハンドラ関数 (ファイル名.ハンドラ関数名) に設定します
CMD [ "app.handler" ]
