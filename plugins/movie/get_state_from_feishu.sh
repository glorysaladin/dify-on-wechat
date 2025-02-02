WK_DIR=$(dirname $(readlink -f $0))
python=`which python`
tat=$($python $WK_DIR/get_feishu_tat.py)
#curl --location --request GET 'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/Uz9tsZ7fHhV3Fgt7jWMcBl8VnNg/values/BWApW0!A2:C50?valueRenderOption=ToString&dateTimeRenderOption=FormattedString' \
curl --location --request GET 'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/VK4eshqpRhhFartYqR3c7wbRnfh/values/4938f5!A2:D200?valueRenderOption=ToString&dateTimeRenderOption=FormattedString' \
--header 'Authorization: Bearer '${tat}
