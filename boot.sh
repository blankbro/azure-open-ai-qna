#!/bin/bash

# 发生错误则退出
set -e

# 拉取最新代码
git pull

# 删除旧容器
if docker ps -a | grep -q "azure-open-ai-qna"; then
    docker rm -f azure-open-ai-qna
fi

# 删除旧镜像
if docker image ls | grep -q "azure-open-ai-qna"; then
    docker image rm -f azure-open-ai-qna
fi

# 打包新镜像
docker build . -f Dockerfile -t azure-open-ai-qna

# 启动新容器
docker run -d --env-file .env -p 8088:80 --name azure-open-ai-qna azure-open-ai-qna

# 清除未被使用的镜像及其数据
docker image prune -a
