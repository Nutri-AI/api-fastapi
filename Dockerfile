FROM python:3.9

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install fastapi
RUN pip install uvicorn
RUN pip install boto3
RUN pip install python-multipart
RUN pip install onnxruntime
RUN pip install opencv-python

