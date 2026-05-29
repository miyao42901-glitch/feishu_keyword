# 缁熶竴 HTTP 鏁版嵁鎺ュ彛璇存槑

鏈嶅姟鐢?`run.py` 鍚姩锛岄粯璁ょ洃鍚?**`http://<涓绘満>:8765`**锛堝彲鐢ㄧ幆澧冨彉閲?`HTTP_HOST`銆乣HTTP_PORT` 瑕嗙洊锛夈€?
浜や簰寮忔枃妗ｏ細鏈嶅姟鍚姩鍚庤闂?**`http://<涓绘満>:<绔彛>/docs`**锛圫wagger UI锛夈€?*`/redoc`**銆?
---

## 0. 鎺ュ彛涓€瑙?
| 鏂规硶 | 璺緞 | 璇存槑 |
|------|------|------|
| GET | `/api/v1/health` | 鍋ュ悍妫€鏌?|
| POST | `/api/v1/run` | 鑱氬悎鍏ュ彛锛坰nake_case `action`锛?|
| POST | `/api/v1/sync/douyin/search-page` | 鎶栭煶鍗曢〉鎼滅储锛堝悓姝ワ級 |
| POST | `/api/v1/sync/douyin/search-all` | 鎶栭煶澶氶〉鎼滅储锛堝悓姝ワ級 |
| POST | `/api/v1/sync/xhs/search-page` | 灏忕孩涔﹀崟椤垫悳绱紙鍚屾锛?|
| POST | `/api/v1/sync/xhs/search-all` | 灏忕孩涔﹀椤垫悳绱紙鍚屾锛?|
| POST | `/api/v1/async/tasks` | 鎻愪氦寮傛浠诲姟锛坘ebab-case `action`锛?|
| POST | `/api/v1/async/tasks/edit` | 缂栬緫浠诲姟锛堥儴鍒嗘洿鏂帮級 |
| GET | `/api/v1/async/tasks` | 浠诲姟鍒楄〃涓庢眹鎬伙紙`X-API-Key` + `X-User-Id`锛?|
| GET | `/api/v1/async/tasks/{task_id}` | 鏌ヨ浠诲姟鐘舵€?|
| GET | `/api/v1/async/tasks/{task_id}/results` | 鍒嗛〉鏌ヨ钀藉簱缁撴灉 |
| POST | `/api/v1/async/tasks/{task_id}/cancel` | 鍙栨秷浠诲姟 |
| POST | `/api/v1/async/tasks/{task_id}/delete` | 鍒犻櫎浠诲姟锛堝仠姝?Celery 骞跺垹搴擄級 |
| POST | `/api/v1/async/tasks/{task_id}/restart` | 閲嶅惎浠诲姟 |
| GET | `/api/v1/results/acceptance` | 寰呴獙鏀?id锛堝钩鍙?鈫?id 鍒楄〃锛?|
| POST | `/api/v1/results/acceptance` | 鎵归噺楠屾敹锛坄is_upload=1`锛?|

涓嬫枃浠?**`BASE = http://127.0.0.1:8765`** 涓轰緥锛屼笟鍔¤矾寰勫潎涓?**`BASE + /api/v1` + 璧勬簮璺緞**銆?
**Content-Type锛?* 闄?`GET` 澶栧潎涓?**`application/json`**銆?
---

## 1. 璺緞鐗堟湰

褰撳墠瀵瑰 API 缁熶竴鎸傚湪 **`/api/v1`** 涓嬶紙瑙?`http_api/versions.py` 涓?`API_V1_PREFIX`锛夈€?
---

## 2. 閴存潈涓庤姹備綋绾﹀畾

### 2.1 鍚屾鎺ュ彛 `POST /api/v1/sync/...`

| 浣嶇疆 | 璇存槑 |
|------|------|
| **Header `X-API-Key`** | 蹇呭～锛屼笅娓?YDDM / 澶у姞鎷夌瓑浣跨敤鐨?**`key`** |
| **Header `X-User-Id`** | 蹇呭～锛岀敤鎴锋爣璇嗭紝鐢ㄤ簬缁撴灉钀藉簱 |
| **JSON Body** | 浠呬笟鍔″瓧娈碉紙濡?`keyword`锛夛紝**涓嶈**鍖呬竴灞?`body` / `params` |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\": \"浜烘皯鏃ユ姤\"}"
```

### 2.2 鑱氬悎 `POST /api/v1/run`

JSON锛歚action` + `params`銆俙params` 鍐呭嚟璇佸彲鐢?**`key`** 鎴?**`X-API-KEY`**锛堟槧灏勪负涓嬫父 `key`锛涗簩鑰呴兘鏈夋椂闈炵┖ **`key`** 浼樺厛锛夈€傝绗?8 鑺傘€?
### 2.3 寮傛 `POST /api/v1/async/tasks`

| 浣嶇疆 | 璇存槑 |
|------|------|
| **Header `X-API-Key`** | 蹇呭～ |
| **Header `X-User-Id`** | 蹇呭～锛岄』涓?yddm `users/me` 杩斿洖鐨勭敤鎴?id 涓€鑷?|
| **JSON Body** | `{ "action": "<kebab-case>", "body": { ... } }`锛宍body` 瀛楁涓庡悓骞冲彴鍚屾 search 鎺ュ彛涓€鑷?|
| **Query `priority`** | 鍙€夛紝**0锝?**锛岄粯璁?`0`锛屾暟鍊艰秺澶?Celery 浼樺厛绾ц秺楂?|

寮傛 **GET** 鎺ュ彛鍙€夊甫 **`X-User-Id`**锛氳嫢鎻愪緵涓斾笌浠诲姟鎵€灞炵敤鎴蜂笉涓€鑷达紝杩斿洖 **403**銆?
**鏍￠獙澶辫触锛?* 鍙兘杩斿洖 **422**锛團astAPI 鏍囧噯鏍￠獙缁撴瀯锛夋垨 **400**锛坄code` + `msg`锛夈€?
### 2.4 闄愭祦锛堟寜鎺ュ彛鐙珛 scope锛?
鍚屼竴鐢ㄦ埛锛坄X-User-Id`锛屾棤鍒欐寜 IP锛夊湪 **60 绉?* 婊戝姩绐楀彛鍐呰鏁帮紱**姣忎釜 HTTP 璺敱鍗曠嫭涓€涓?Redis 妗?*锛屼簰涓嶅崰棰濆害锛堝嬁鍐嶇敤缁熶竴鐨?`async_list` 绛夊悎骞?scope锛夈€?
| 鏂规硶 | 璺緞 | scope | 榛樿涓婇檺 / 60s |
|------|------|-------|----------------|
| POST | `/api/v1/async/tasks` | `async_submit` | 30 |
| POST | `/api/v1/async/tasks/edit` | `async_task_edit` | 60 |
| GET | `/api/v1/async/tasks` | `async_task_list` | 60 |
| GET | `/api/v1/async/tasks/{task_id}` | `async_task_status` | 120 |
| GET | `/api/v1/async/tasks/{task_id}/results` | `async_task_results` | 120 |
| POST | `/api/v1/async/tasks/{task_id}/cancel` | `async_task_cancel` | 30 |
| POST | `/api/v1/async/tasks/{task_id}/delete` | `async_task_delete` | 30 |
| POST | `/api/v1/async/tasks/{task_id}/restart` | `async_task_restart` | 30 |
| GET | `/api/v1/results/acceptance` | `result_acceptance_pending` | 120 |
| POST | `/api/v1/results/acceptance` | `result_acceptance_accept` | 60 |

瓒呴檺杩斿洖 **429**锛宍code` 涓洪檺娴佷笟鍔＄爜锛屽搷搴斿ご鍚?**`Retry-After`**锛堢锛夈€傚父閲忓畾涔夎 `http_api/rate_limit_scopes.py`銆?
---

## 3. 缁熶竴鍝嶅簲鏍煎紡

鎴愬姛鎴栦笟鍔″眰閿欒鏃讹紝HTTP 鐘舵€佺爜澶氫负 **200**锛堝紓姝ユ湭閰嶇疆搴撲负 **503**锛屼换鍔′笉瀛樺湪涓?**404**锛夛紝閫氳繃 **`code`** 鍖哄垎锛?
| 瀛楁 | 绫诲瀷 | 璇存槑 |
|------|------|------|
| `code` | int | **`0` 琛ㄧず鎴愬姛**锛涢潪 0 瑙?`social_platform/api_status_codes.py`锛堝 **`1001`** 浣欓涓嶈冻銆?*`1021`** 寮傛浠诲姟鏁拌秴闄愶級 |
| `msg` | string | 浜虹被鍙璇存槑 |
| `data` | object \| null | 璐熻浇锛岀粨鏋勫洜鎺ュ彛鑰屽紓锛堣涓嬭〃锛?|

### 3.1 鍝嶅簲 `data` 缁撴瀯瀵圭収

| 鎺ュ彛绫诲瀷 | 鎴愬姛鏃?`data` 缁撴瀯 |
|----------|-------------------|
| `GET /health` | `{ "status": "ok" }`锛?*鏃?* `result` / `meta` 鍖呰锛?|
| 鍚屾 search / `POST /run` | `{ "result": <Worker 杩斿洖>, "meta": { "worker", "version", ... } }` |
| 寮傛涓変釜鎺ュ彛 | `{ "result": <涓氬姟鏁版嵁>, "meta": { "worker": "async_api", "platform", "source", "action", "result_table", ... } }` |

**鍚屾 / 寮傛鎴愬姛绀轰緥锛?*

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "result": { },
    "meta": {
      "worker": "douyin_worker",
      "version": "1.0.0",
      "platform": "douyin",
      "source": "douyin",
      "action": "douyin-search-all",
      "result_table": "feishu_douyin_results"
    }
  }
}
```

> 鍚屾鎺ュ彛鐨?`meta` 涓昏鏉ヨ嚜 Worker锛堝 `douyin_worker`锛夛紝骞跺彲鑳藉悎骞跺椤甸噰闆嗗瓧娈碉紙`pages_fetched`銆乣records_returned` 绛夛紝瑙佺 12.7 鑺傦級銆傚紓姝ユ帴鍙ｇ殑 `meta` 鐢?HTTP 灞傛敞鍏ワ紝鐢ㄤ簬鏍囪瘑骞冲彴涓庣粨鏋滆〃锛?*涓嶅惈**绗笁鏂归噰闆嗚繃绋嬪瓧娈点€?
**涓氬姟澶辫触绀轰緥锛?*

```json
{
  "code": 400,
  "msg": "鍙傛暟閿欒",
  "data": null
}
```

---

## 4. 鍋ュ悍妫€鏌?
### `GET /api/v1/health`

鏃犻渶閴存潈銆?
```bash
curl -s "http://127.0.0.1:8765/api/v1/health"
```

**鎴愬姛鍝嶅簲锛?*

```json
{
  "code": 0,
  "msg": "ok",
  "data": { "status": "ok" }
}
```

---

## 5. 鑱氬悎浠诲姟 `POST /api/v1/run`

鍗曞叆鍙ｆ寜 **`action`**锛?*snake_case**锛夊垎鍙戝埌鎶栭煶鎴栧皬绾功 Worker锛坄social_platform/aggregated_job.py`锛夈€?
**璇锋眰浣擄細**

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
|------|------|------|------|
| `action` | string | 鏄?| 瑙佷笅琛?|
| `params` | object | 鍚?| 榛樿 `{}`锛涗笟鍔″瓧娈佃绗?8 鑺?|

**鏀寔鐨?`action`锛?*

| `action` | 璇存槑 |
|----------|------|
| `douyin_search_page` | 鎶栭煶鍗曢〉鎼滅储 |
| `douyin_search_all` | 鎶栭煶澶氶〉鑱氬悎 |
| `xhs_search_page` | 灏忕孩涔﹀崟椤垫悳绱?|
| `xhs_search_all` | 灏忕孩涔﹀椤佃仛鍚?|

**璇锋眰绀轰緥锛?*

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/run" \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"douyin_search_page\",\"params\":{\"X-API-KEY\":\"YOUR_SECRET\",\"keyword\":\"鍏抽敭璇峔"}}"
```

**鎴愬姛鍝嶅簲锛?* 涓庣 3 鑺備竴鑷达紝`data.result` 涓?Worker 鍘熷 `data`锛宍data.meta` 鍚?`jzl_social` 涓庡叿浣?Worker 淇℃伅銆?
涓嶆敮鎸佺殑 `action` 鏃讹紝`code` 闈?0锛宍msg` 涓惈 `unsupported action`銆?
---

## 6. 鎶栭煶鍚屾鎺ュ彛

璺緞鍓嶇紑锛?*`/api/v1/sync/douyin`**銆傚潎闇€ **Header `X-API-Key` + `X-User-Id`** + **鎵佸钩 JSON Body**銆?
### 6.1 鍗曢〉鎼滅储 `POST .../search-page`

**Body 鍙傛暟锛坄DouyinSearchPageBody`锛夛細**

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 榛樿 | 璇存槑 |
|------|------|------|------|------|
| `keyword` | string | 鏄?| 鈥?| 鎼滅储鍏抽敭璇嶏紝**1锝?00** 瀛?|
| `cursor` | string | 鍚?| `""` | 缈婚〉娓告爣锛涢椤电暀绌?|
| `log_id` / `logid` | string | 鍚?| `""` | 缈婚〉鍙傛暟锛涢椤电暀绌?|
| `sort_type` | string | 鍚?| `"0"` | `0` 缁煎悎锛宍1` 鏈€澶氱偣璧烇紝`2` 鏈€鏂板彂甯?|
| `publish_time` | string | 鍚?| `"0"` | `0` 涓嶉檺锛宍1` 1 澶╁唴锛宍7` 7 澶╁唴锛宍180` 180 澶╁唴 |
| `filter_duration` | string | 鍚?| `"0"` | `0` 涓嶉檺锛宍0-1` 1 鍒嗛挓鍐咃紝`1-5` 1锝? 鍒嗛挓锛宍1-10000` 5 鍒嗛挓浠ヤ笂 |
| `content_type` | string | 鍚?| `"0"` | `0` 涓嶉檺锛宍1` 瑙嗛锛宍2` 鍥炬枃 |
| `exclude_words` | string | 鍚?| `""` | 鎺掗櫎璇嶏紝绌烘牸鍒嗛殧 |

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"浜烘皯鏃ユ姤\",\"sort_type\":\"2\",\"publish_time\":\"7\"}"
```

**鎴愬姛鏃?`data.result`锛?* 绗笁鏂瑰崟椤靛師濮嬬粨鏋勶紙鍚?`data` 鍒楄〃銆乣cursor`銆乣log_id` 绛夛紝浠ュ疄闄呰繑鍥炰负鍑嗭級銆傞厤缃?`DATABASE_URL` 鏃舵暣椤电粨鏋滀細钀藉簱 `feishu_douyin_results`銆?
---

### 6.2 澶氶〉鎼滅储 `POST .../search-all`

**Body 鍙傛暟锛坄DouyinSearchAllBody` = 鍏叡澶氶〉瀛楁 + 鎶栭煶鎵╁睍锛夛細**

#### 鍏叡澶氶〉瀛楁锛坄PublicSearchAllBody`锛屽皬绾功 search-all 鍏辩敤锛?
| 瀛楁 | 绫诲瀷 | 蹇呭～ | 榛樿 | 璇存槑 |
|------|------|------|------|------|
| `keyword` | string | 鏄?| 鈥?| 鎼滅储鍏抽敭璇?|
| `fetch_count` | int | 鍚?| `100` | 鏈€澶氶噰闆?*涓嶉噸澶?*鏉℃暟锛堟寜 `aweme_id`锛夛紝**1锝?00**锛岃揪鍒板嵆鍋?|
| `sort_type` | int | 鍚?| `1` | `0`/`1`锛氫笉鎸夊鎴风鍙戝竷鏃堕棿鎴獥锛?*`2`**锛氬惎鐢ㄦ椂闂寸獥锛堣绗?12 鑺傦級 |
| `time_range` | int | 鍚?| `7` | 澶╂暟锛?*鈮?**锛?*浠?`sort_type=2` 鏃?*鍙備笌瀹㈡埛绔椂闂寸獥 |
| `exclude_words` | string | 鍚?| `""` | 鎺掗櫎璇嶏紝绌烘牸鍒嗛殧锛岃繃婊ゆ爣棰?鎻忚堪 |

#### 鎶栭煶鎵╁睍瀛楁锛堝彲閫夛紝浼犵粰绗笁鏂圭瓫閫?/ 缈婚〉锛?
| 瀛楁 | 绫诲瀷 | 蹇呭～ | 榛樿 | 璇存槑 |
|------|------|------|------|------|
| `cursor` | string | 鍚?| `""` | 鍙€夎捣濮嬬炕椤垫父鏍?|
| `log_id` / `logid` | string | 鍚?| `""` | 鍙€夎捣濮嬬炕椤靛弬鏁?|
| `publish_time` | string | 鍚?| `""` | 绗笁鏂瑰彂甯冩椂闂寸瓫閫夛紙绌哄垯涓嬫父榛樿锛?|
| `filter_duration` | string | 鍚?| `""` | 瑙嗛鏃堕暱绛涢€?|
| `content_type` | string | 鍚?| `""` | 鍐呭褰㈠紡绛涢€?|

**钀藉簱锛?* 姣忓悜绗笁鏂规垚鍔熸媺鍙栦竴椤靛苟杩囨护鍚庡啓鍏?`feishu_douyin_results`锛堥渶 `DATABASE_URL`锛夈€?
**鏈€绠€璇锋眰锛?*

```json
{ "keyword": "绌挎惌" }
```

绛変环浜?`fetch_count=100`銆乣sort_type=1`銆乣time_range=7`锛坄time_range` 鍦?`sort_type鈮?` 鏃朵笉鎴柇锛夈€?
**鎸夎繎 7 澶╂椂闂寸獥锛?*

```json
{
  "keyword": "绌挎惌",
  "fetch_count": 100,
  "sort_type": 2,
  "time_range": 7
}
```

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/douyin/search-all" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"绌挎惌\",\"fetch_count\":100,\"sort_type\":2,\"time_range\":7}"
```

**鎴愬姛鏃?`data.result` 甯歌瀛楁锛?* `records`锛堢粨鏋滃垪琛級銆乣balance`銆乣insufficient_balance`銆乣last_error`锛沗data.meta` 鍚?`pages_fetched`銆乣records_returned`銆乣fetch_count_cap`銆佹椂闂寸獥瀛楁绛夛紙瑙佺 12.7 鑺傦級銆?
**閲囬泦琛屼负璇﹁В锛?* 绗?12 鑺傘€?
---

## 7. 灏忕孩涔﹀悓姝ユ帴鍙?
璺緞鍓嶇紑锛?*`/api/v1/sync/xhs`**銆傚潎闇€ **Header `X-API-Key` + `X-User-Id`** + **鎵佸钩 JSON Body**銆?
### 7.1 鍗曢〉鎼滅储 `POST .../search-page`

**Body 鍙傛暟锛坄XhsSearchPageBody`锛夛細**

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 榛樿 | 璇存槑 |
|------|------|------|------|------|
| `keyword` | string | 鏄?| 鈥?| 鎼滅储鍏抽敭璇?|
| `page` | int | 鍚?| `1` | 椤电爜锛屸墺1 |
| `sort_type` | string | 鍚?| `"0"` | `0` 缁煎悎锛宍1` 鏈€澶氱偣璧烇紝`2` 鏈€鏂板彂甯?|
| `content_type` | string | 鍚?| `""` | `video` 瑙嗛绗旇锛宍note` 鏅€氱瑪璁帮紝绌?涓嶉檺 |
| `note_time` | string | 鍚?| `"0"` | `0` 涓嶉檺锛宍1` 1 澶╁唴锛宍7` 7 澶╁唴锛宍180` 180 澶╁唴 |
| `exclude_words` | string | 鍚?| `""` | 鎺掗櫎璇?|

璇锋眰浣撲細鏄犲皠涓?YDDM 瀛楁锛歚sort`锛堝 `time_descending`锛夈€乣note_type`銆乣note_time`锛堝 `week`锛夌瓑銆?
```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/xhs/search-page" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"绌挎惌鍗氫富\",\"page\":1,\"sort_type\":\"2\",\"content_type\":\"video\",\"note_time\":\"7\"}"
```

---

### 7.2 澶氶〉鎼滅储 `POST .../search-all`

**Body 鍙傛暟锛坄XhsSearchAllBody`锛夛細**

#### 蹇呭～ / 甯哥敤锛堜笌鎶栭煶鍏叡瀛楁鐩稿悓锛?
| 瀛楁 | 绫诲瀷 | 蹇呭～ | 榛樿 | 璇存槑 |
|------|------|------|------|------|
| `keyword` | string | 鏄?| 鈥?| 鎼滅储鍏抽敭璇?|
| `fetch_count` | int | 鍚?| `100` | **1锝?00**锛屾寜 `note_id` 鍘婚噸绱 |
| `sort_type` | int | 鍚?| `1` | 鍚屾姈闊筹紱**`2`** 鏃跺惎鐢ㄥ鎴风鏃堕棿绐?|
| `time_range` | int | 鍚?| `7` | 浠?`sort_type=2` 鐢熸晥 |
| `exclude_words` | string | 鍚?| `""` | 鎺掗櫎璇?|

> 妯″瀷涓繕澹版槑浜?`cursor`銆乣log_id`銆乣publish_time`銆乣filter_duration`銆乣content_type`锛堜笌鎶栭煶妯″瀷瀵归綈锛夛紝**灏忕孩涔﹀椤?Worker 涓嶄娇鐢?*锛岃姹備腑鍙渷鐣ャ€?
**钀藉簱锛?* 姣忛〉鍐欏叆 `feishu_xhs_results`銆?
```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/sync/xhs/search-all" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: user_001" \
  -d "{\"keyword\":\"绌挎惌鍗氫富\",\"fetch_count\":50,\"sort_type\":2,\"time_range\":7}"
```

**鍗曢〉绛涢€?*锛坄content_type`銆乣note_time` 绛夛級璇蜂娇鐢?**search-page**锛泂earch-all 涓昏閫氳繃 `sort_type` / `time_range` 鎺у埗瀹㈡埛绔椂闂寸獥涓庢潯鏁颁笂闄愩€?
**閲囬泦琛屼负璇﹁В锛?* 绗?12 鑺傘€?
---

## 8. `POST /api/v1/run` 鐨?`params` 涓庡紓姝?`body` 瀵圭収

| 鍚屾璺緞 | `POST /run` 鐨?`action` | 寮傛 `action` | `body` / `params` 涓氬姟瀛楁 |
|----------|-------------------------|---------------|---------------------------|
| `.../douyin/search-page` | `douyin_search_page` | `douyin-search-page` | `keyword`锛涘彲閫?`cursor`銆乣log_id`/`logid`銆乣sort_type`銆乣publish_time`銆乣filter_duration`銆乣content_type`銆乣exclude_words` |
| `.../douyin/search-all` | `douyin_search_all` | `douyin-search-all` | `keyword`锛涘彲閫?`fetch_count`銆乣sort_type`銆乣time_range`銆乣exclude_words`锛涙姈闊冲彲閫?`cursor`銆乣log_id`銆乣publish_time`銆乣filter_duration`銆乣content_type` |
| `.../xhs/search-page` | `xhs_search_page` | `xhs-search-page` | `keyword`锛涘彲閫?`page`銆乣sort_type`銆乣content_type`銆乣note_time`銆乣exclude_words` |
| `.../xhs/search-all` | `xhs_search_all` | `xhs-search-all` | `keyword`锛涘彲閫?`fetch_count`銆乣sort_type`銆乣time_range`銆乣exclude_words` |
| 鈥?| 鈥?| `douyin-search-detail` | `post_id`锛堜綔鍝?ID / aweme_id锛夛紝**鏈疄鐜?*锛屼换鍔′細澶辫触 |
| 鈥?| 鈥?| `xhs-search-detail` | `post_id`锛堢瑪璁?note_id锛夛紝**鏈疄鐜?*锛屼换鍔′細澶辫触 |

鍙﹀姞 **`key`** 鎴?**`X-API-KEY`**锛堜粎 `POST /run` 鐨?`params` 闇€瑕侊紱鍚屾/寮傛鐢?Header `X-API-Key`锛夈€?
---

## 9. 鐜涓庨厤缃?
瑙?**仓根 `.env.example`**锛屽父鐢ㄩ」锛?
| 鍙橀噺 | 璇存槑 |
|------|------|
| `HTTP_HOST` / `HTTP_PORT` | HTTP 鐩戝惉鍦板潃涓庣鍙?|
| `DOUYIN_GENERAL_URL` / `XHS_GENERAL_URL` | 绗笁鏂?API 鍦板潃瑕嗙洊 |
| `DATABASE_URL` | MySQL 杩炴帴涓诧紱涓虹┖鍒欏紓姝ユ帴鍙?**503** |
| `ASYNC_TASK_DB_AUTO_CREATE` | 寮€鍙戠幆澧冨惎鍔ㄦ椂鑷姩寤鸿〃 |
| `REDIS_URL` / `CELERY_BROKER_URL` | Celery Broker |
| `ASYNC_DISPATCH_HTTP_ENABLED` | `run.py` 鏄惁鍦ㄥ悗鍙版壂鎻?Redis 璋冨害锛堥粯璁?**1**锛屼笌 Worker 閰嶅悎鍗冲彲锛?|
| `ASYNC_DISPATCH_POLL_SECONDS` | 涓婅堪鎵弿闂撮殧锛堢锛岄粯璁?**15**锛?|
| `ASYNC_SCHEDULE_BEAT_ENABLED` | 鏃?HTTP 鏃剁敤 Celery Beat 鍋氬悓鏍锋壂鎻忥紙榛樿 **0**锛?|
| `ASYNC_TASK_RUNNING_STALE_SECONDS` | `running` 瓒呮椂閲嶇疆涓?`pending`锛堥粯璁?**1800**锛?|
| `ASYNC_RESULTS_DEFAULT_LIMIT` | `GET .../results` 榛樿 `limit`锛堟渶澶?**200**锛?|
| `ASYNC_TASK_MAX_ACTIVE_PER_USER` | 鍗曠敤鎴?`pending`+`running` 浠诲姟涓婇檺锛岃秴闄?**429**銆乣code=1021` |
| `YDDM_USERS_ME_URL` | 鎻愪氦寮傛浠诲姟鍓嶆牎楠岀敤鎴?|

**鎺ㄨ崘閮ㄧ讲**锛坄server/` 鐩綍锛屽叡鐢?`.env` 涓殑 `DATABASE_URL` 涓?`REDIS_URL`锛夛細

```bash
python run.py
celery -A social_platform.tasks.celery_app worker -l info -P gevent -c 4 --prefetch-multiplier=1
```

骞跺彂涓?systemd / Nginx 閰嶇疆瑙?**`DEPLOYMENT.md`**銆?
浠诲姟璁板綍鍐欏叆 MySQL 琛?`feishu_async_tasks`锛沗search-all` / `search-page` 閲囬泦缁撴灉鍐欏叆瀵瑰簲 `feishu_*_results` 琛紙鍚屾鍗曟鎵ц `task_id` 鍙负绌猴紝楠屾敹璧?`/api/v1/results/acceptance`锛夈€?
---

## 10. 寮傛浠诲姟锛圕elery + MySQL锛?
### 10.1 宸叉敞鍐?`action`锛坄social_platform/actions/registry.py`锛?
| `action` | 骞冲彴 | 钀藉簱 | 璇存槑 |
|----------|------|------|------|
| `douyin-search-all` | douyin | 鏄?| 澶氶〉鎼滅储锛宐ody 鍚?搂6.2 |
| `douyin-search-page` | douyin | 鏄?| 鍗曢〉鎼滅储锛宐ody 鍚?搂6.1 |
| `douyin-search-detail` | douyin | 鍚?| 鍗犱綅锛宍body.post_id` 蹇呭～锛屾墽琛屾湭瀹炵幇 |
| `xhs-search-all` | xhs | 鏄?| 澶氶〉鎼滅储锛宐ody 鍚?搂7.2 |
| `xhs-search-page` | xhs | 鏄?| 鍗曢〉鎼滅储锛宐ody 鍚?搂7.1 |
| `xhs-search-detail` | xhs | 鍚?| 鍗犱綅锛宍body.post_id` 蹇呭～锛屾墽琛屾湭瀹炵幇 |

---

### 10.2 鎻愪氦浠诲姟 `POST /api/v1/async/tasks`

**Header锛?* `X-API-Key`銆乣X-User-Id`锛堝繀濉級

**Query锛?*

| 鍙傛暟 | 绫诲瀷 | 榛樿 | 璇存槑 |
|------|------|------|------|
| `priority` | int | `0` | **0锝?**锛孋elery 浼樺厛绾?|

**Body锛?*

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 榛樿 | 璇存槑 |
|------|------|------|------|------|
| `task_name` | string | 鏄?| 鈥?| 浠诲姟鍚嶇О锛?*1锝?00** 瀛楃锛屼笉鑳戒负绌哄瓧绗︿覆 |
| `action` | string | 鏄?| 鈥?| 涓婅〃 kebab-case 涔嬩竴 |
| `body` | object | 鍚?| `{}` | 涓氬姟鍙傛暟锛?*涓嶅惈** `fetch_count`锛夛紱鎸?`action` 鍋?Pydantic 鏍￠獙 |
| `task_start_time` | string | 鏄?| 鈥?| 瀹氭椂绐楀彛寮€濮嬶紙ISO8601 鎴栨绉掓椂闂存埑锛夛紱**鏃犳椂鍖烘椂鎸変笢鍏尯锛圓sia/Shanghai锛?* |
| `task_end_time` | string | 鏄?| 鈥?| 瀹氭椂绐楀彛缁撴潫锛岄』鏅氫簬寮€濮嬫椂闂翠笌褰撳墠鏃堕棿锛涙棤鏃跺尯鍚屼笂 |
| `interval_minutes` | int | 鍚?| `60` | 绐楀彛鍐呴噰闆嗛棿闅旓紙鍒嗛挓锛夛紝鏈€灏?**5** |
| `fetch_count` | int | 鍚?| `100` | 鍗曟閲囬泦鏉℃暟涓婇檺锛?*1锝?00**锛堜笌 `interval_minutes` 鍚岀骇锛屼笉鍏?`body`锛?|

绐楀彛鍐呯敱 Celery 鎸?`interval_minutes` 鍛ㄦ湡鎵ц锛沗fetch_count` 鍦ㄦ瘡娆℃墽琛屾椂娉ㄥ叆 `search-all` 绫?action銆?
**璇锋眰绀轰緥锛堟姈闊?search-all锛夛細**

```json
{
  "task_name": "瀹屾垚椤圭洰鎶ュ憡",
  "action": "douyin-search-all",
  "body": {
    "keyword": "浜烘皯鏃ユ姤",
    "sort_type": 2,
    "time_range": 7
  },
  "task_start_time": "2026-05-18T00:00:00Z",
  "task_end_time": "2026-05-25T00:00:00Z",
  "interval_minutes": 60,
  "fetch_count": 100
}
```

**璇锋眰绀轰緥锛堝皬绾功 search-all锛夛細**

```json
{
  "task_name": "灏忕孩涔︾┛鎼噰闆?,
  "action": "xhs-search-all",
  "body": {
    "keyword": "绌挎惌鍗氫富"
  },
  "task_start_time": "2026-05-18T00:00:00Z",
  "task_end_time": "2026-05-20T00:00:00Z",
  "interval_minutes": 30,
  "fetch_count": 50
}
```

**鎴愬姛鍝嶅簲锛?*

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "result": {
      "task_id": 42,
      "status": "pending"
    },
    "meta": {
      "worker": "async_api",
      "version": "1.0.0",
      "platform": "douyin",
      "source": "douyin",
      "action": "douyin-search-all",
      "result_table": "feishu_douyin_results"
    }
  }
}
```

**甯歌閿欒锛?*

| HTTP | `code` / 浣?| 璇存槑 |
|------|-------------|------|
| 400 | `400` 鎴?`{"code":400,"message":"unsupported action"}` | 鏈煡 `action`銆佺己灏?`task_name` 鎴?body 鏍￠獙澶辫触 |
| 401 | `1005` 绛?| 鏃犳晥鐨?`X-API-Key`锛坹ddm 鏍￠獙澶辫触锛?|
| 429 | `1021` | 璇ョ敤鎴疯繘琛屼腑浠诲姟鏁拌秴闄?|
| 503 | 闈?0 | 鏈厤缃?`DATABASE_URL` |

---

### 10.3 鏌ヨ鐘舵€?`GET /api/v1/async/tasks/{task_id}`

**Path锛?* `task_id` 涓轰换鍔℃暟瀛椾富閿紙瀛楃涓插舰寮忎害鍙級銆?
**Header锛?* `X-User-Id` 鍙€夛紱鑻ユ彁渚涢』涓庝换鍔?`user_id` 涓€鑷淬€?
**鎴愬姛鏃?`data.result` 瀛楁锛?*

| 瀛楁 | 璇存槑 |
|------|------|
| `task_id` | 浠诲姟 ID |
| `task_name` | 浠诲姟鍚嶇О |
| `user_id` | 鎵€灞炵敤鎴?|
| `platform` | 鐢?`action` 鎺ㄥ锛坄douyin` / `xhs`锛夛紝涓嶅叆搴?|
| `status` | `pending` / `running` / `success` / `failed` / `cancelled` 绛?|
| `action` | 鎻愪氦鏃剁殑 kebab-case action |
| `error_message` | 澶辫触鎽樿锛堟渶闀?64 瀛楃锛?|
| `celery_task_id` | Celery 浠诲姟 ID |
| `priority` | 0锝? |
| `cancel_requested` | 鏄惁宸茶姹傚彇娑?|
| `success_count` / `failed_count` | 钀藉簱鎴愬姛 / 澶辫触绱 |
| `task_start_time` / `task_end_time` | 瀹氭椂绐楀彛璧锋锛圛SO8601 UTC锛宍Z`锛?|
| `interval_minutes` | 閲囬泦闂撮殧锛堝垎閽燂級 |
| `fetch_count` | 鍗曟閲囬泦鏉℃暟涓婇檺 |
| `create_time` / `update_time` | ISO8601 UTC锛堝甫 `Z`锛?|

**`data.meta`锛?* 鍚?搂10.2锛堝惈 `platform`銆乣source`銆乣result_table`锛夈€?
**404锛?* 浠诲姟涓嶅瓨鍦ㄣ€?
鍒楄〃 `GET /api/v1/async/tasks` 鐨?`data.result.items[]` 涓悓鏍峰寘鍚?`task_name` 瀛楁銆?
---

### 10.3.1 缂栬緫浠诲姟 `POST /api/v1/async/tasks/edit`

**Header锛?* `X-API-Key`銆乣X-User-Id`锛堝繀濉紝涓庢彁浜?鍙栨秷浠诲姟涓€鑷达紝缁?yddm `users/me` 鏍￠獙锛?
**Body锛圝SON锛夛細**

| 瀛楁 | 绫诲瀷 | 蹇呭～ | 璇存槑 |
|------|------|------|------|
| `task_id` | int | 鏄?| 浠诲姟 ID |
| `task_name` | string | 鍚?| 1锝?00 瀛楃 |
| `interval_minutes` | int | 鍚?| 鈮?5锛涗粎 **pending** 鍙敼 |
| `fetch_count` | int | 鍚?| 1锝?00锛涗粎 **pending** 鍙敼 |
| `task_start_time` | string | 鍚?| 瀹氭椂绐楀彛寮€濮嬶紱浠?**pending** 鍙敼 |
| `task_end_time` | string | 鍚?| 瀹氭椂绐楀彛缁撴潫锛涗粎 **pending** 鍙敼 |
| `priority` | int | 鍚?| 0锝?锛涗粎 **pending** 鍙敼 |

闄?`task_name` 澶栵紝璋冨害绫诲瓧娈典粎鍦ㄤ换鍔＄姸鎬佷负 `pending` 鏃跺厑璁镐慨鏀广€?*鑷冲皯鎻愪緵涓€涓?*瑕佷慨鏀圭殑瀛楁锛堥櫎 `task_id` 澶栵級銆?
**鎴愬姛鍝嶅簲锛?* `data.result` 涓烘洿鏂板悗鐨勫畬鏁翠换鍔″璞★紙瀛楁鍚?搂10.3锛屽惈 `task_name`锛夈€?
**绀轰緥锛?*

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/async/tasks/edit" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -H "X-User-Id: 12345" \
  -d '{"task_id": 42, "task_name": "瀹屾垚椤圭洰鎶ュ憡锛堜慨璁級"}'
```

**甯歌閿欒锛?*

| HTTP | `code` | 璇存槑 |
|------|--------|------|
| 401 | `1005` 绛?| `X-API-Key` 鏃犳晥鎴栨湭鎺堟潈 |
| 503 | `1022` | 鐢ㄦ埛鏍￠獙鏈嶅姟鏆傛椂涓嶅彲鐢紝璇风◢鍚庨噸璇?|
| 400 | `400` | 缂哄皯 `task_id`銆佹湭鎻愪緵鍙慨鏀瑰瓧娈点€乣task_name` 闀垮害涓嶅悎娉曠瓑 |
| 403 | `1020` | `X-User-Id` 涓庝换鍔″綊灞炰笉涓€鑷?|
| 404 | `1023` | 浠诲姟涓嶅瓨鍦?|

鏈嶅姟绔細璁板綍缂栬緫鏃ュ織锛堢敤鎴枫€佹椂闂淬€佷换鍔?ID銆佸彉鏇村瓧娈靛強鏂板€硷級銆?
---

### 10.3.2 鍒犻櫎浠诲姟 `POST /api/v1/async/tasks/{task_id}/delete`

**Header锛?* `X-User-Id`锛堝繀濉紝椤讳笌浠诲姟鍦ㄥ簱涓殑 `user_id` 涓€鑷达級

**璇存槑锛?* 鍒犻櫎鎺ュ彛**涓嶈皟鐢?* yddm 鐢ㄦ埛鏍￠獙锛岄伩鍏嶃€岀敤鎴锋牎楠屾湇鍔℃殏鏃朵笉鍙敤銆嶆椂鏃犳硶娓呯悊浠诲姟銆俙pending` / `running` / `success` / `failed` / **`cancelled`** 绛変换鎰忕姸鎬佸潎鍙垹闄ゃ€?
**琛屼负锛?*

1. 浠?Redis 璋冨害 ZSET 绉婚櫎锛屽苟鍒犻櫎浠诲姟蹇収銆乣api_key` 缂撳瓨銆佹姇閫掗攣
2. 鑻ヤ换鍔′负 `pending` / `running`锛屽褰撳墠 `celery_task_id` 鎵ц `revoke`锛坄running` 鏃?`terminate=true` 浠ュ皾璇曠粓姝㈡鍦ㄦ墽琛岀殑 Worker锛?3. 鍒犻櫎 MySQL `feishu_async_tasks` 瀵瑰簲琛岋紱鍚勫钩鍙扮粨鏋滆〃 `feishu_*_results` 涓?`task_id` 鍏宠仈琛屽洜 **ON DELETE CASCADE** 涓€骞跺垹闄?
**鎴愬姛鍝嶅簲锛?*

```json
{
  "code": 0,
  "data": {
    "result": {
      "task_id": "42",
      "deleted": true
    }
  }
}
```

**甯歌閿欒锛?*

| HTTP | `code` | 璇存槑 |
|------|--------|------|
| 404 | `1023` | 浠诲姟涓嶅瓨鍦?|
| 403 | `1020` | `X-User-Id` 涓庝换鍔″綊灞炰笉涓€鑷?|

涓庛€屽彇娑堛€嶄笉鍚岋細鍙栨秷渚濊禆 yddm 鏍￠獙涓斿凡 `cancelled` 鏃惰繑鍥?409锛?*鍒犻櫎**涓嶄緷璧?yddm锛屼笖**宸插彇娑堜换鍔′篃鍙洿鎺ュ垹闄?*銆傚垹闄や负涓嶅彲鎭㈠锛岃璋ㄦ厧璋冪敤銆?
**绀轰緥锛?*

```bash
curl -s -X POST "http://127.0.0.1:8765/api/v1/async/tasks/42/delete" \
  -H "X-User-Id: 12345"
```

---

### 10.4 鍙栨秷浠诲姟 `POST /api/v1/async/tasks/{task_id}/cancel`

**Header锛?* `X-API-Key`銆乣X-User-Id`锛堝繀濉紝涓庢彁浜や换鍔′竴鑷达級

**琛屼负锛?*

- MySQL 浠诲姟缃负 `cancelled`锛宍cancel_requested=true`
- 鑻ュ瓨鍦ㄨ繘琛屼腑鐨?Celery 娑堟伅鍒?`revoke`锛堜笉寮哄埗鏉€杩涚▼锛?- **涓嶅垹闄?* Redis 浠诲姟蹇収涓?`api_key`锛屼繚鐣?**1 澶?*锛坄86400` 绉掞級锛屼究浜庡悗缁噸鍚鍙?`success_count` 绛?- 浠庤皟搴?ZSET 绉婚櫎锛屼笉鍐嶅懆鏈熻Е鍙?
**鎴愬姛鍝嶅簲锛?*

```json
{
  "code": 0,
  "data": {
    "result": {
      "task_id": "7",
      "status": "cancelled"
    }
  }
}
```

**甯歌閿欒锛?*

| HTTP | `code` | 璇存槑 |
|------|--------|------|
| 404 | `1023` | 浠诲姟涓嶅瓨鍦?|
| 403 | `1020` | 鐢ㄦ埛涓庝换鍔″綊灞炰笉涓€鑷?|
| 409 | `1027` | 浠诲姟宸插彇娑堬紝閲嶅鍙栨秷 |

---

### 10.5 閲嶅惎浠诲姟 `POST /api/v1/async/tasks/{task_id}/restart`

**Header锛?* `X-API-Key`銆乣X-User-Id`锛堝繀濉級

**閫傜敤鐘舵€侊細** `cancelled`銆乣success`銆乣failed` 绛夊凡缁撴潫鐘舵€侊紱**涓嶅彲**閲嶅惎 `pending` / `running`銆?
**琛屼负锛?*

1. 浠?Redis 璇诲彇浠诲姟蹇収锛堝惈 `success_count`銆乣failed_count`銆乣body_json` 绛夛級锛涜嫢鏃犵紦瀛樻垨缂哄皯 `action`锛屽洖閫€ MySQL 浠诲姟琛?2. 灏嗚鏁板啓鍥?MySQL锛宍status` 缃负 `pending`锛屾竻闄?`cancel_requested` / `celery_task_id` / `error_message`
3. 鎸夊師 `task_start_time`锝瀈task_end_time` 绐楀彛涓?`interval_minutes` 閲嶆柊鍏ラ槦閲囬泦

**鎴愬姛鍝嶅簲锛?*

```json
{
  "code": 0,
  "data": {
    "result": {
      "task_id": 7,
      "status": "pending",
      "success_count": 40,
      "failed_count": 2,
      "snapshot_source": "redis"
    }
  }
}
```

`snapshot_source`锛歚redis` 琛ㄧず璁℃暟鏉ヨ嚜鍙栨秷鍚庝繚鐣欑殑蹇収锛沗mysql` 琛ㄧず Redis 鏃犳暟鎹椂浠庡簱琛ㄨ鍙栥€?
**甯歌閿欒锛?*

| HTTP | `code` | 璇存槑 |
|------|--------|------|
| 404 | `1023` | 浠诲姟涓嶅瓨鍦?|
| 403 | `1020` | 鐢ㄦ埛涓嶄竴鑷?|
| 409 | `1028` | 浠诲姟杩涜涓紝鏃犳硶閲嶅惎 |
| 409 | `1029` | `task_end_time` 宸茶繃锛岀獥鍙ｇ粨鏉?|
| 429 | `1021` | 鐢ㄦ埛杩涜涓换鍔℃暟瓒呴檺 |
| 503 | `1024` | Redis / 鏁版嵁搴撴湭灏辩华 |

---

### 10.6 鍒嗛〉缁撴灉 `GET /api/v1/async/tasks/{task_id}/results`

浠庡搴斿钩鍙拌〃 **`feishu_{platform}_results`** 璇诲彇锛?*涓嶅仛璺ㄥ钩鍙板瓧娈电粺涓€**锛屽垪鍚嶄笌鏁版嵁搴撲竴鑷淬€?
**Query锛?*

| 鍙傛暟 | 绫诲瀷 | 榛樿 | 璇存槑 |
|------|------|------|------|
| `page` | int | `1` | 椤电爜锛屼粠 **1** 寮€濮?|
| `limit` | int | `ASYNC_RESULTS_DEFAULT_LIMIT`锛堥粯璁?20锛?| 姣忛〉鏉℃暟锛?*1锝?00** |
| `is_upload` | int | 涓嶄紶=涓嶈繃婊?| `0` 鎴?`1`锛屾寜鏄惁宸蹭笂浼犵瓫閫?|

**鎴愬姛鏃?`data.result`锛?*

```json
{
  "page": 1,
  "limit": 20,
  "total": 135,
  "items": [ { } ]
}
```

**`items[]` 涓嶈繑鍥炵殑鍩哄眰瀛楁锛?* `id`銆乣task_id`銆乣user_id`銆乣create_time`銆乣update_time`銆傞€氳繃 **`data.meta.platform`** / **`data.meta.source`** 鍖哄垎骞冲彴銆?
#### 鎶栭煶 `items[]` 瀛楁锛坄feishu_douyin_results`锛?
`post_id`銆乣keyword`銆乣nickname`銆乣sec_uid`銆乣content_type`銆乣is_upload`銆乣title`銆乣summary`銆乣page_url`銆乣avatar_url`銆乣author_signature`銆乣verify_name`銆乣cover_url`銆乣duration_seconds`銆乣has_music`銆乣publish_time_ms`銆乣like_count`銆乣comment_count`銆乣share_count`銆乣collect_count`銆乣primary_image_url`銆乣primary_video_url`

#### 灏忕孩涔?`items[]` 瀛楁锛坄feishu_xhs_results`锛?
涓庢姈闊崇浉鍚屽垪闆嗭紝**鍙﹀惈** `xsec_token`锛沗page_url` 闀垮害闄愬埗涓庢姈闊充笉鍚岋紙浠ヨ〃缁撴瀯涓哄噯锛夈€?
**绀轰緥锛?*

```bash
curl -s "http://127.0.0.1:8765/api/v1/async/tasks/42/results?page=1&limit=20&is_upload=0" \
  -H "X-User-Id: user_001"
```

---

## 11. 瀹炵幇浣嶇疆锛堢淮鎶ょ敤锛?
| 鍐呭 | 璺緞 |
|------|------|
| 璺敱娉ㄥ唽涓庣増鏈墠缂€ | `http_api/v1/routes.py`銆乣http_api/versions.py` |
| 鍚屾璺敱 | `http_api/v1/sync_api.py` |
| 寮傛璺敱 | `http_api/v1/async_api.py` |
| `X-API-KEY` 鈫?`key` 鏄犲皠 | `http_api/dajiala_params.py` |
| 瀵瑰涓氬姟鐘舵€佺爜 | `social_platform/api_status_codes.py` |
| 鍝嶅簲灏佽 | `social_platform/api_response.py` |
| POST Body 妯″瀷 | `http_sync_bodies.py` |
| Action 娉ㄥ唽琛?| `social_platform/actions/registry.py` |
| 寮傛浠诲姟 / 缁撴灉鏈嶅姟 | `social_platform/services/task_service.py`銆乣result_service.py` |
| 缁撴灉琛?DDL | `social_platform/database/schema.sql` |
| 澶氶〉鎷夊彇閫昏緫 | `social_platform/utils/search_fetch_all.py` |
| Celery | `social_platform/tasks/celery_app.py` |

鐗堟湰鍙樻洿鏃惰鍚屾鏇存柊鏈枃妗ｄ笌 `docs/server/README.md`銆?
---

## 12. `*-search-all` 澶氶〉閲囬泦琛屼负璇存槑

閫傜敤浜庯細

- 鍚屾锛歚POST /api/v1/sync/douyin/search-all`銆乣POST /api/v1/sync/xhs/search-all`
- 寮傛锛歚douyin-search-all`銆乣xhs-search-all`锛坄body` 瀛楁鐩稿悓锛?- 鑱氬悎锛歚POST /api/v1/run` 涓?`action` 涓?`douyin_search_all` / `xhs_search_all`

### 12.1 鍏叡鍙傛暟閫熸煡

| 瀛楁 | 绫诲瀷 | 榛樿 | 璇存槑 |
|------|------|------|------|
| `keyword` | string | **蹇呭～** | 鎼滅储鍏抽敭璇?|
| `fetch_count` | int | `100` | 鏈€澶?**涓嶉噸澶?* 鏉℃暟锛?*1锝?00** |
| `sort_type` | int | `1` | **浠?`2` 鏃?* `time_range` 鍙備笌瀹㈡埛绔椂闂寸獥 |
| `time_range` | int | `7` | 杩?N 澶╋紙涓?`sort_type=2` 鑱旂敤锛?|
| `exclude_words` | string | `""` | 鎺掗櫎璇?|

**缁熶竴鍋滄鏉′欢锛堟弧瓒充换涓€鍗冲仠锛夛細**

1. 宸茶揪 **`fetch_count`**
2. **`sort_type=2`** 涓旀椂闂寸獥鍐呮棤鏇村绗﹀悎鏉′欢鏁版嵁
3. 绗笁鏂规棤涓嬩竴椤?/ 绌哄垪琛?4. 浣欓涓嶈冻鎴栨帴鍙ｆ姤閿?
### 12.2 `sort_type` 涓庢椂闂寸獥

| `sort_type` | `time_range` | 瀹㈡埛绔椂闂寸獥 | 鍏稿瀷琛屼负 |
|-------------|--------------|--------------|----------|
| 鏈紶锛堜粎鏃х増 `POST /run` 鐨?`params` 鏃犳閿級 | 鈥?| 鏄ㄥぉ 00:00锝炲綋鍓?| 鍏煎鍘嗗彶 |
| `0` 鎴?`1`锛堝惈浠呭啓 `keyword` 鏃剁殑榛樿 `1`锛?| 涓嶇敓鏁?| 涓嶆寜鍙戝竷鏃堕棿鎴獥 | 杩炵画缈婚〉鑷?`fetch_count` |
| `2` | 鐢熸晥 | `[褰撳墠 鈭?N 澶? 褰撳墠]` | 杩?N 澶╀笖 鈮?`fetch_count` |

> 缁忓悓姝?寮傛 Pydantic 鏍￠獙鏃讹紝缂虹渷浼氳ˉ `sort_type=1`銆乣time_range=7`锛?*`time_range` 鍦?`sort_type鈮?` 鏃朵笉鎴柇**銆?
### 12.3 鍏稿瀷鍦烘櫙

| 璇锋眰 | 琛屼负鎽樿 |
|------|----------|
| `{ "keyword": "绌挎惌" }` | 鏈€澶?**100** 鏉★紝涓嶆寜瀹㈡埛绔椂闂磋繃婊?|
| `{ "keyword": "绌挎惌", "fetch_count": 50 }` | 鏈€澶?**50** 鏉?|
| `{ "keyword": "绌挎惌", "sort_type": 2, "time_range": 7 }` | 杩?7 澶╁唴锛屾渶澶?**100** 鏉★紙鍏堝埌鍏堝仠锛?|
| `{ "keyword": "绌挎惌", "sort_type": 2, "time_range": 30, "fetch_count": 500 }` | 杩?30 澶╋紝鏈€澶?**500** 鏉?|

### 12.4 骞冲彴宸紓

| 椤圭洰 | 鎶栭煶 | 灏忕孩涔?|
|------|------|--------|
| 缈婚〉 | `cursor` + `log_id` | `page` 閫掑 |
| 绗笁鏂圭瓫閫夛紙search-all锛?| 鍙紶 `publish_time`銆乣filter_duration`銆乣content_type` | 澶氶〉涓昏鐢?`sort_type`/`time_range`锛涘崟椤电瓫閫夌敤 search-page |
| 钀藉簱琛?| `feishu_douyin_results` | `feishu_xhs_results` |
| 鍘婚噸閿?| `aweme_id` 鈫?`post_id` | `note_id` 鈫?`post_id` |

### 12.5 楂樼骇鍙傛暟锛堜竴鑸笉缁忓悓姝?Body 浼犻€掞級

閫氳繃 **`POST /api/v1/run`** 鐨?`params` 鎴栧巻鍙?`body_json` 浠嶅彲浼犲叆锛圵orker 鏀寔锛孭ydantic 鏈０鏄庯級锛?
| 瀛楁 | 浣滅敤 |
|------|------|
| `max_pages` | 浠呴檺鍒舵渶澶ч〉鏁帮紝涓嶅仛鍙戝竷鏃堕棿绐?|
| `start_date` / `end_date` | ISO 鏃堕棿锛屾樉寮忓鎴风杩囨护绐楀彛锛堜紭鍏堜簬 `time_range`锛?|

### 12.6 鍚屾 search-all 鎴愬姛鏃?`data.result` / `meta` 鎽樿

| 瀛楁 | 璇存槑 |
|------|------|
| `records` | 姹囨€诲垪琛紙鏉℃暟 鈮?`fetch_count`锛?|
| `balance` | 璐︽埛浣欓锛堣嫢鏈夛級 |
| `meta.worker` / `meta.version` | 濡?`douyin_worker` / `1.0.0` |
| `meta.use_date_window` | 鏄惁鍚敤瀹㈡埛绔彂甯冩椂闂寸獥 |
| `meta.start_date_effective` / `end_date_effective` | 瀹為檯鏃堕棿绐楋紙ISO锛?|
| `meta.records_returned` | 瀹為檯杩斿洖鏉℃暟 |
| `meta.fetch_count_cap` | 鏈鏉℃暟涓婇檺 |
| `meta.pages_fetched` | 鍚戠涓夋柟璇锋眰鐨勯〉鏁?|
| `meta.stopped_before_start_date` | 鏄惁鍥犻亣鍒版棭浜庣獥鍙ｄ笅鐣岀殑鏉＄洰鑰屽仠姝㈢炕椤?|

寮傛浠诲姟瀹屾垚鍚庯紝涓氬姟鏁版嵁鍦?**`GET .../results`** 鐨?`data.result.items` 涓寜骞冲彴琛ㄥ瓧娈佃繑鍥烇紱浠诲姟绾у厓淇℃伅鍦?**`data.meta`**锛埪?0.2锝?0.4锛夈€?
---

## 13. 瑙嗛鍙锋悳绱㈡帴鍙ｏ紙wxvideo / wx/sousou锛?
璺緞锛?- `POST /api/v1/sync/wxvideo/search-page`
- `POST /api/v1/sync/wxvideo/search-all`
- 寮傛 action: `wxvideo-search-page` / `wxvideo-search-all`

### 鍙傛暟璇存槑锛坰earch-page / search-all 閫氱敤锛?
| 瀛楁 | 绫诲瀷 | 蹇呴渶 | 璇存槑 | 绀轰緥 |
|------|------|------|------|------|
| `keyword` | string | 鏄?| 鎼滅储鍏抽敭璇?| "浜烘皯鏃ユ姤" |
| `sort_type` | int | 鍚?| 0=缁煎悎, 1=鏈€鏂? 2=鏈€鐑紙鍐呴儴鏄犲皠锛?| 1 |
| `note_time` | int | 鍚?| 0=涓嶉檺, 1=鏈€杩?澶? 2=鏈€杩?澶? 3=鏈€杩戝崐骞达紙鍘?publish_time_type锛?| 1 |
| `page` / `currentPage` | int | 鍚?| 椤电爜锛岀涓€椤?1 | 1 |
| `offset` | int | 鍚?| 缈婚〉鍋忕Щ锛岀涓€椤?0锛屽悗缁～涓婃杩斿洖 | 0 |
| `cookies_buffer` | string | 鍚?| 绗簩椤佃捣蹇呭～锛屽～涓婃杩斿洖鐨?cookies_buffer | "" |

**娉ㄦ剰**锛歚mode=1`銆乣search_type=2` 鍐呴儴鍐欐銆俙sort_type` 浼氭槧灏勪负绗笁鏂?sort_type銆?
### 绀轰緥 Body锛坰earch-page 绗竴椤碉級

```json
{
  "keyword": "浜烘皯鏃ユ姤",
  "sort_type": 1,
  "note_time": 1,
  "page": 1,
  "offset": 0,
  "cookies_buffer": ""
}
```

缈婚〉鏃跺甫涓婅繑鍥炵殑 `offset` 鍜?`cookies_buffer`銆?
杩斿洖瀛楁鍖呭惈锛歵itle銆乸ublish_time锛堟绉掞級銆乨uration锛堢锛夈€乶ickname銆乤vatar_url銆乴ike_count 绛?+ next_offset / cookies_buffer銆?
钀藉簱琛細`feishu_wxvideo_results`

---

## 14. 鍏紬鍙锋悳绱㈡帴鍙ｏ紙mp锛?
璺緞锛?- `POST /api/v1/sync/mp/search-page`
- `POST /api/v1/sync/mp/search-all`
- 寮傛 action: `mp-search-page` / `mp-search-all`

### 鍙傛暟璇存槑

| 瀛楁 | 绫诲瀷 | 蹇呴渶 | 璇存槑 | 鏄犲皠璇存槑 |
|------|------|------|------|----------|
| `keyword` | string | 鏄?| 鎼滅储鍏抽敭璇?| - |
| `sort_type` | int | 鍚?| 0/1/2 | 鏄犲皠涓?Sub_search_type: 0鈫?, 1鈫?, 2鈫? |
| `note_time` | int | 鍚?| 鏃堕棿鑼冨洿 | 鐩存帴閫忎紶 |
| `page` / `currentPage` | int | 鍚?| 椤电爜 | 鍐呴儴缁熶竴浣跨敤 currentPage 浼犵涓夋柟 |
| `offset` | int | 鍚?| 缈婚〉鍋忕Щ | 鍚岃棰戝彿 |
| `cookies_buffer` | string | 鍚?| 缈婚〉鍑瘉 | 鍚岃棰戝彿 |

**娉ㄦ剰**锛歚mode=2`銆乣BusinessType=2` 鍐欐銆?
### 绀轰緥 Body

```json
{
  "keyword": "澶фā鍨?,
  "sort_type": 0,
  "note_time": 0,
  "page": 1
}
```

杩斿洖瀛楁鏄犲皠锛?- `date` 鈫?`publish_time`锛堢鈫掓绉掞級
- `desc` 鈫?`content`
- `doc_url` 鈫?`url`
- `reportId` 鈫?`article_id` / `post_id`
- `source.title` 鈫?`author`
- `thumbUrl` 鈫?`avatar_url`
- `title` 鈫?缁?HTML 娓呮礂鍚庣殑鏍囬

钀藉簱琛細`feishu_mp_results`

---

## 15. 寮傛浠诲姟 Action 姹囨€伙紙kebab-case锛?
| 骞冲彴 | 鍗曢〉 Action | 澶氶〉 Action |
|------|-------------|-------------|
| 鎶栭煶 | douyin-search-page | douyin-search-all |
| 灏忕孩涔?| xhs-search-page | xhs-search-all |
| 瑙嗛鍙?| wxvideo-search-page | wxvideo-search-all |
| 鍏紬鍙?| mp-search-page | mp-search-all |

鎵€鏈夊紓姝ヤ换鍔℃彁浜?Body 鏍煎紡缁熶竴涓猴細

```json
{
  "action": "wxvideo-search-page",
  "body": { ...涓氬姟鍙傛暟... }
}
```

Contracts 绀轰緥鏂囦欢瑙?`contracts/v1/` 鐩綍涓嬬殑 `*.example.json`銆?
