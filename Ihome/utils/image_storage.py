from qiniu import Auth, put_data, etag
import qiniu.config
# 需要填写你的 Access Key 和 Secret Key
access_key = 'pSX5-G7In2mNaLvarIbQocHCd3wn3FaphjRKigMN'
secret_key = 'DL8IpPv7UUKAcdKb7_JjFkwmm9PGu7olPzD-WI9s'


def storage(file_data):

    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'kezhan'

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # 要上传文件的本地路径

    ret, info = put_data(token, None, file_data)
    # print(info)
    # print('-' * 100)
    # print(ret)

    if info.status_code == 200:
        return ret.get("key")

    else:
        raise Exception("七牛云上传上传失败")


if __name__ == '__main__':
    with open("./2.png", "rb") as f:
        file_data = f.read()
        storage(file_data)
