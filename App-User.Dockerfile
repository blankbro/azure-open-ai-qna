FROM python:3.9.10-slim-buster
RUN apt-get update && apt-get install python-tk python3-tk tk-dev curl -y

# 下载OCR需要的库
RUN mkdir -p /usr/share/tessdata
RUN curl -o /usr/share/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/4.00/eng.traineddata
RUN curl -o /usr/share/tessdata/chi_sim.traineddata https://github.com/tesseract-ocr/tessdata/raw/4.00/chi_sim.traineddata

COPY ./code/requirements.txt /usr/local/src/azure-open-ai-qna/requirements.txt
WORKDIR /usr/local/src/azure-open-ai-qna
RUN pip install -r requirements.txt

COPY ./code /usr/local/src/azure-open-ai-qna
# 删除自测页面（Dockerfile.dockerignore不好使，所以用了这种方法）
RUN rm -rf pages/03_Document_Edit.py
RUN mv pages/01_Chat.py 01_Chat.py

EXPOSE 80
CMD ["streamlit", "run", "01_Chat.py", "--server.port", "80", "--server.enableXsrfProtection", "false"]