#!/bin/bash
# 生产模式运行
cd /data/haotianwu/biojson/rag/web
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
