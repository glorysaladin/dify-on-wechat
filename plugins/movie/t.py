import re

url = "https://20241230.online/zb_users/plugin/mochu_search/url.php?url=https://20241230.online/post/12548.html&id=12548"

# 正则表达式匹配url=后面的部分
match = re.search(r'url=(.*?)&', url)

if match:
    # 如果找到匹配，打印匹配的URL
    print(match.group(1))
else:
    # 如果没有找到匹配，打印错误信息
    print("No match found")
