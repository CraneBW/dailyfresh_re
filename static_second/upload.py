import os
import pymysql
from fdfs_client.client import Fdfs_client
from datetime import datetime


class FdfsUploader:
    def __init__(self, fdfs_config_path, db_config):
        """
        初始化FastDFS上传器和MySQL连接
        :param fdfs_config_path: FastDFS客户端配置文件路径
        :param db_config: 数据库配置字典
        """
        # 初始化FastDFS客户端
        self.client = Fdfs_client(fdfs_config_path)

        # 初始化数据库连接
        self.db_config = db_config
        self.conn = pymysql.connect(**db_config)
        self.cursor = self.conn.cursor()

    def upload_file(self, file_path):
        """
        上传文件到FastDFS并返回文件信息
        :param file_path: 本地文件路径
        :return: 上传结果字典
        """
        # 转换为绝对路径
        # abs_path = os.path.abspath(file_path)
        # print(f"绝对路径: {abs_path}")  # 调试输出
        # print(f"文件是否存在: {os.path.exists(abs_path)}")
        # # 验证文件可访问性
        # if not os.path.exists(abs_path):
        #     raise FileNotFoundError(f"文件不存在: {abs_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 {file_path} 不存在")
        print(f"文件是否存在: {os.path.exists(file_path)}")
        # 获取文件扩展名
        file_ext = os.path.splitext(file_path)[1][1:]

        # 上传文件
        try:
            upload_result = self.client.upload_by_filename(file_path)
            return upload_result
        except Exception as e:
            raise Exception(f"文件上传失败: {str(e)}")

    def update_database(self, goods_id, file_path):
        """
        更新数据库中的文件路径
        :param goods_id: 商品ID
        :param file_path: FastDFS返回的文件路径
        :return: 影响的行数
        """
        try:
            update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

            sql = """
            UPDATE df_goods_type
            SET image = %s, update_time = %s 
            WHERE id = %s
            """

            affected_rows = self.cursor.execute(sql, (file_path, update_time, goods_id))
            self.conn.commit()
            return affected_rows
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"数据库更新失败: {str(e)}")

    def process_upload(self, goods_id, file_path):
        """
        完整的文件上传和数据库更新流程
        :param goods_id: 商品ID
        :param file_path: 本地文件路径
        :return: 操作结果信息
        """
        try:
            # 上传文件
            upload_result = self.upload_file(file_path)

            if upload_result.get('Status') != 'Upload successed.':
                return {"status": "error", "message": "文件上传失败", "detail": upload_result}

            file_id = upload_result.get('Remote file_id')

            # 更新数据库
            affected_rows = self.update_database(goods_id, file_id)

            if affected_rows == 0:
                return {"status": "warning", "message": "文件上传成功但未找到匹配的商品记录", "file_id": file_id}

            return {
                "status": "success",
                "message": "文件上传并数据库更新成功",
                "file_id": file_id,
                "affected_rows": affected_rows
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close(self):
        """关闭数据库连接"""
        self.cursor.close()
        self.conn.close()


def main():
    # FastDFS客户端配置文件路径
    fdfs_config_path = '/etc/fdfs/client.conf'  # 根据你的实际路径修改

    # 数据库配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'dailyfresh',  # 替换为你的数据库名
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    # 创建上传器实例
    uploader = FdfsUploader(fdfs_config_path, db_config)

    try:
        print("=== FastDFS文件上传工具 ===")
        print("请输入以下信息：")

        goods_id = input("商品ID: ").strip()
        file_path = input("本地文件路径: ").strip()

        if not goods_id.isdigit():
            print("错误: 商品ID必须是数字")
            return

        result = uploader.process_upload(int(goods_id) - 1, file_path)

        print("\n操作结果:")
        for key, value in result.items():
            print(f"{key}: {value}")
    finally:
        uploader.close()


if __name__ == '__main__':
    while(True):
        main()