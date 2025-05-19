FROM public.ecr.aws/lambda/python:3.13

WORKDIR ${LAMBDA_TASK_ROOT}

# 依存関係ファイルをコピー
COPY requirements.txt ./

# 依存関係をインストール
# --no-cache-dir オプションでキャッシュを無効にし、イメージサイズを削減
# --upgrade pip でpipを最新版に更新
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/

# Lambdaハンドラを指定 (app/lambda_function.py の lambda_handler関数)
CMD [ "app.lambda_function.lambda_handler" ]
