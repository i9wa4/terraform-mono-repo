FROM public.ecr.aws/lambda/python:3.13

COPY app/app.py ${LAMBDA_TASK_ROOT}/
COPY requirements.txt ${LAMBDA_TASK_ROOT}/

# --target flag ensures libraries are installed to the correct directory for Lambda.
RUN pip3 install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

CMD [ "app.handler" ]
