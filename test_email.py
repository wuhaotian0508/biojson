#!/usr/bin/env python3
"""
测试邮件发送功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "rag"))

from web.email_sender import send_verification_code

if __name__ == "__main__":
    test_email = input("请输入测试邮箱地址: ").strip()
    if not test_email:
        print("邮箱地址不能为空")
        sys.exit(1)

    test_code = "123456"
    print(f"正在发送测试验证码 {test_code} 到 {test_email}...")

    success = send_verification_code(test_email, test_code)

    if success:
        print("✅ 邮件发送成功！请检查收件箱。")
    else:
        print("❌ 邮件发送失败，请检查日志。")
