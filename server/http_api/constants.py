"""对外 API 版本前缀与第三方 monitor URL（修改此处即可，不读 .env）。"""

# 路径前缀：新增 v2 时在 `http_api/v2/` 增加路由并在此登记
API_V1_PREFIX = "/api/v1"

DOUYIN_GENERAL_URL = "https://api.yddm.com/douyin/general_search"
XHS_GENERAL_URL = "https://api.yddm.com/xhs/search_note_app"
MP_GENERAL_URL = "https://api.yddm.com/mp/search"
WXVIDEO_GENERAL_URL = "https://api.yddm.com/wxvideo/search"
SHIPINHAO_GENERAL_URL = "https://api.yddm.com/wx/sousou"

GONGZHONGHAO_GENERAL_URL = "https://www.dajiala.com/fbmain/monitor/v3/kw_search"
KUAISHOU_GENERAL_URL = "https://www.dajiala.com/fbmain/monitor/v3/ks_search_video_v1"
WEIBO_GENERAL_URL = "https://www.dajiala.com/fbmain/monitor/v3/weibo_search_data"
BILIBILI_GENERAL_URL = "https://www.dajiala.com/fbmain/monitor/v3/bilibili_search"
