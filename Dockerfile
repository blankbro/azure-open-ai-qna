FROM python:3.9.10-slim-buster
RUN apt-get update && apt-get install python-tk python3-tk tk-dev -y
COPY ./code/requirements.txt /usr/local/src/azure-open-ai-qna/requirements.txt
WORKDIR /usr/local/src/azure-open-ai-qna
RUN pip install -r requirements.txt

# 下载OCR需要的简体中文库
RUN curl -o /usr/share/tessdata/chi_sim.traineddata https://github.com/tesseract-ocr/tessdata/raw/4.00/chi_sim.traineddata

COPY ./code /usr/local/src/azure-open-ai-qna
EXPOSE 80
CMD ["streamlit", "run", "Home.py", "--server.port", "80", "--server.enableXsrfProtection", "false"]