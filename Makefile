.PHONY: install dev build run stop logs clean backend-dev frontend-dev

# 安装依赖
install:
	pip install -r requirements.txt
	cd frontend && npm install

# 开发模式
dev:
	docker-compose up -d

# 构建镜像
build:
	docker-compose build

# 运行
run:
	docker-compose up -d

# 停止
stop:
	docker-compose down

# 查看日志
logs:
	docker-compose logs -f

# 清理
clean:
	docker-compose down -v
	rm -rf app/__pycache__ exports/* uploads/*

# 后端开发
backend-dev:
	uvicorn app.main:app --reload --port 8000

# 前端开发
frontend-dev:
	cd frontend && npm run dev

# 测试
test:
	pytest tests/ -v

# 格式化代码
format:
	black app/
	isort app/
