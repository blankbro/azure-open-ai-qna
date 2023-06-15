#!/bin/bash

# 发生错误则退出
set -e

# 拉取最新代码
git pull

# 删除旧容器
if docker ps -a | grep -q "azure-open-ai-qna_user"; then
    docker rm -f azure-open-ai-qna_user
fi

# 删除旧镜像
if docker image ls | grep -q "azure-open-ai-qna:user"; then
    docker image rm -f azure-open-ai-qna:user
fi

# 打包新镜像
docker build . -f App-User.Dockerfile -t azure-open-ai-qna:user

# 启动新容器
docker run -d --env-file .env -p 8080:80 --name azure-open-ai-qna_user azure-open-ai-qna:user

# 清除未被使用的镜像及其数据
docker image prune -a
