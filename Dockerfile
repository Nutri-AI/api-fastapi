FROM python:3.9

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install fastapi
RUN pip install uvicorn
RUN pip install boto3
RUN pip install python-multipart
RUN pip install onnxruntime

# Base ----------------------------------------
RUN pip install matplotlib>=3.2.2
RUN pip install numpy>=1.18.5
RUN pip install opencv-python>=4.1.2
RUN pip install Pillow>=7.1.2
RUN pip install PyYAML>=5.3.1
RUN pip install requests>=2.23.0
RUN pip install scipy>=1.4.1
RUN pip install torch>=1.7.0
RUN pip install torchvision>=0.8.1
RUN pip install tqdm>=4.41.0

# Logging -------------------------------------
RUN pip install tensorboard>=2.4.1
RUN pip install wandb

# Plotting ------------------------------------
RUN pip install pandas>=1.1.4
RUN pip install seaborn>=0.11.0

#WORKDIR /workspace

#CMD uvicorn app_v2.main:app --reload --host=0.0.0.0 