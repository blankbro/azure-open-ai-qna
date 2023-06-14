### Azure OpenAI Question And Answer

基于 azure-open-ai-embeddings-qna 删除了一些不必要的功能，添加了一些自己的定制化需求

### 本地部署

Please ensure you have Python 3.9+ installed.

Create `venv` environment for Python:

```console
python -m venv .venv

# 进入虚拟环境
source .venv/bin/activate

# 退出虚拟环境
deactivate
```

Install `PIP` Requirements

```console
pip install -r code/requirements.txt
```

configure your .env as Environment variables

```
cp .env.template .env
vi .env # or use whatever you feel comfortable with
```

run

```console
streamlit run code/Home.py
```

docker run

```
./boot.sh
```

### 部署其它应用

```
# MySQL 挂载启动
docker run -d -p 3306:3306 --privileged=true -v /app/mysql/data:/var/lib/mysql -e MYSQL_ROOT_PASSWORD=111111 --name mysql mysql

```