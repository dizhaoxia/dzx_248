import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("企业知识库问答系统 - 后端服务")
    print("=" * 60)
    print(f"服务地址: http://localhost:3201")
    print(f"API 前缀: /api")
    print(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    print(f"索引目录: {app.config['INDEX_DIR']}")
    print("=" * 60)

    app.run(host='0.0.0.0', port=3201, debug=True)
