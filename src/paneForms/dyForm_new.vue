<script>
  import { ref, computed } from 'vue';
  import { bitable, FieldType, NumberFormatter, DateFormatter } from '@lark-base-open/js-sdk';
  import {
    ElForm,
    ElFormItem,
    ElSelect,
    ElOption,
    ElInput,
    ElButton,
    ElTooltip,
    ElAlert,
    ElTabs,
    ElTabPane,
  } from 'element-plus';
  import pluginAPI from '@/utils/request'
  import { dyPlatformConfig } from '@/configs/platformConfigs'
  import { writeToTable, updateTable, getFirstRecordByField} from '@/utils/tableHelper'
  import TableSelect from '@/components/TableSelect.vue'
  import { Plus, ArrowDown, CircleClose, Remove, CirclePlus, QuestionFilled } from '@element-plus/icons-vue'
  import generalSelect from '@/toolComponents/generalSelect.vue'
  import platformTip from '@/tipDialogs/platformTip.vue'
  import '@/assets/form-styles.css'
  import { setCollectResultTable, getCollectResultTableId } from '@/utils/collectResult'
  import { hasAllAccountInputs, resetAccountInputsAfterSuccess } from '@/utils/accountInput'

  export default {
    components: {
      ElForm,
      ElFormItem,
      ElSelect,
      ElOption,
      ElInput,
      ElButton,
      ElTooltip,
      ElAlert,
      ElTabs,
      ElTabPane,
      Plus,
      ArrowDown,
      CircleClose,
      Remove,
      CirclePlus,
      QuestionFilled,
      generalSelect,
      platformTip
    },
    props: {
      formData: {
        type: Object,
        required: true
      },
      isLocked: {
        type: Boolean,
        default: false
      }
    },
    emits: ['update:isLocked'],
    setup(props, { emit }) {
      const dyConfig = dyPlatformConfig(() => '')

      function parseAccountInput(inputValue) {
        const trimmed = String(inputValue).trim()
        if (!trimmed) return null
        const secUid = dyConfig.extractSecUid(trimmed)
        if (dyConfig.isValidSecUid(secUid)) {
          return { sec_user_id: secUid }
        }
        return { share_text: trimmed }
      }

      function userFields() {
        return {
          sec_uid: { label: '用户id', fieldType: FieldType.Text, isPrimary: true, },
          nickname: { label: '抖音账号昵称', fieldType: FieldType.Text, },
          signature: { label: '简介', fieldType: FieldType.Text, },
          follower_count: { label: '当前粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          aweme_count: { label: '发布视频数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          total_favorited: { label: '获赞总数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          follower_count_diff: { label: '新增粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          aweme_count_diff: { label: '新增视频数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          total_favorited_diff: { label: '新增获赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          following_count: { label: '关注数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          max_follower_count: { label: '最大粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          current_get_time: { label: '当前获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          last_get_time: { label: '上次获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_work_flag: {
            label: '获取视频状态', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过',
              fail: '获取失败',
              partial_success: '部分成功',
              success: '获取成功',
            },
          },
          work_fail_reason: { label: '获取视频失败原因', fieldType: FieldType.Text, },
        }
      }

      function workFields() {
        return {
          aweme_id: { label: '视频id', fieldType: FieldType.Text, isPrimary: true, },
          desc: { label: '视频标题', fieldType: FieldType.Text, },
          caption: { label: '视频简介', fieldType: FieldType.Text, },
          nickname: { label: '抖音账号昵称', fieldType: FieldType.Text, },
          sec_uid: { label: '抖音账号ID', fieldType: FieldType.Text, },
          vedio_url: { label: '视频URL', fieldType: FieldType.Url, },
          create_time: { label: '发布时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          digg_count: { label: '获赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_count: { label: '分享数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_count: { label: '收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          digg_count_diff: { label: '新增获赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count_diff: { label: '新增评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_count_diff: { label: '新增分享数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_count_diff: { label: '新增收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          current_get_time: { label: '当前获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          last_get_time: { label: '上次获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
        }
      }

      const collectionTypeOptions = ref({'blogger': 1, 'post': 1})
      const ranges = ref({
        '当天': {value: 1 , type: 'date'},
        '3天': {value: 3 , type: 'date'},
        '7天': {value: 7 , type: 'date'},
        '15天': {value: 15 , type: 'date'},
        '30天': {value: 30 , type: 'date'},
        '1页': {value: 1 , type: 'page'},
        '2页': {value: 2 , type: 'page'},
        '5页': {value: 5 , type: 'page'},
        '10页': {value: 10 , type: 'page'},
        '20页': {value: 20 , type: 'page'},
        '50页': {value: 50 , type: 'page'},
        // '全部': {value: 0 , type: 'all'},
      })

      const paneData = ref({
        collectionType: 'blogger',
        selectedTableId: null,
        sec_user_id: null,
        share_text: null,
        userTableId: null,
        workTableId: null,
        searchRange: '1页',
        getDataType: 0,
        getWorksType: 1,
      })
      
      const searchValues = ref({
        0: {
          dataType: 'input',
          data: {inputValue: ''}
        }
      });

      const tipVisible = ref(false)


      
      const addSearchRow = () => {
        // 添加新行（对象结构）
        // 获取对象中最大的key，然后+1，({}整数键默认排序，直接取最后一个)
        const newId = Number(Object.keys(searchValues.value)[Object.keys(searchValues.value).length - 1]) + 1;
        searchValues.value[newId] = {
          dataType: 'input',
          data: {inputValue: ''}
        };
      }

      
      const removeSearchRow = (id) => {
        // 删除指定行（对象结构）
        delete searchValues.value[id];
      }

      const hasAccountInput = () => hasAllAccountInputs(searchValues.value)


      const changecollectionType = async (newCollectionType) => {
        paneData.value.collectionType = newCollectionType
        paneData.value.selectedTableId = null
        paneData.value.searchRange = '1页'
        let newId = 0
        if (Object.keys(searchValues.value).length > 0 && Object.keys(searchValues.value)[0] === '0'){
          newId = Number(Object.keys(searchValues.value)[Object.keys(searchValues.value).length - 1]) + 1;
        }
        searchValues.value = {
          [newId]: {
            dataType: 'input',
            data: {inputValue: ''}
          }
        }
      }


      const createTemplateTable = async(tableName, tableConfigs) => {
        const tableRes = await writeToTable(null, [], tableConfigs, tableName);
        if (tableRes.success) {
          return tableRes.data.tableId
        }
        return null
      }


      const upsertWorks = async(items, get_time, writeTableId) => {
        const tmpWorkFields = workFields()
        const insertData = []
        const updateData = []
        for (const item of items) {
          const aweme_id = item.aweme_id
          const [record, fieldMap] = await getFirstRecordByField(writeTableId, tmpWorkFields.aweme_id.label, aweme_id)
          let result = {}
          if (record) {
            const last_get_time = record.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
            const last_digg_count = record.fields[fieldMap[tmpWorkFields.digg_count.label].id] || 0
            const last_comment_count = record.fields[fieldMap[tmpWorkFields.comment_count.label].id] || 0
            const last_share_count = record.fields[fieldMap[tmpWorkFields.share_count.label].id] || 0
            const last_collect_count = record.fields[fieldMap[tmpWorkFields.collect_count.label].id] || 0
            updateData.push({
              recordId: record.recordId,
              data: {
                aweme_id: aweme_id,
                desc: item.desc,
                caption: item.caption,
                sec_uid: item.author.sec_uid,
                nickname: item.author.nickname,
                vedio_url: 'https://www.douyin.com/video/' + item.aweme_id,
                create_time: item.create_time * 1000, // 转换为毫秒级时间戳

                digg_count: item.statistics.digg_count,
                comment_count: item.statistics.comment_count,
                share_count: item.statistics.share_count,
                collect_count: item.statistics.collect_count,

                digg_count_diff: item.statistics.digg_count - last_digg_count,
                comment_count_diff: item.statistics.comment_count - last_comment_count,
                share_count_diff: item.statistics.share_count - last_share_count,
                collect_count_diff: item.statistics.collect_count - last_collect_count,

                current_get_time: get_time,
                last_get_time: last_get_time,
              }
            })
          }
          else{
            insertData.push({
              aweme_id: aweme_id,
              desc: item.desc,
              caption: item.caption,
              sec_uid: item.author.sec_uid,
              nickname: item.author.nickname,
              vedio_url: 'https://www.douyin.com/video/' + item.aweme_id,
              create_time: item.create_time * 1000, // 转换为毫秒级时间戳

              digg_count: item.statistics.digg_count,
              comment_count: item.statistics.comment_count,
              share_count: item.statistics.share_count,
              collect_count: item.statistics.collect_count,
              current_get_time: get_time,
            })
          }
        }
        const insertRes = await writeToTable(
          writeTableId,
          insertData,
          tmpWorkFields,
        );
        
        const updateRes = await updateTable(
          writeTableId,
          updateData,
          tmpWorkFields,
        );
        
        let resultCount = 0
        if (insertRes && insertRes.success) {
          resultCount += insertRes.data.recordIds.length
        }
        if (updateRes && updateRes.success) {
          resultCount += updateRes.data.recordIds.length
        }
        const failmsg = insertRes.error || updateRes.error || ''
        return [resultCount, failmsg]
      }


      const upsertUserData = async(post_data, writeTableId) => {
        const tmpUserFields = userFields()
        const get_time = Date.now()
        const res = await pluginAPI.post('/plugin_forward', {
          url: '/fbmain/monitor/v3/douyin_user_data',
          body: {
            sec_user_id: post_data.sec_user_id,
            share_text: post_data.share_text,
          },
          params: {
            key: props.formData.key,
          }
        })

        // 默认失败返回
        let result = {
          success: false,
          data: null,
          error: '未知错误'
        }

        if (res && res.data && res.data.code === 0) {
          const res_sec_id = res.data.data.user.sec_uid
          const [record, fieldMap] = await getFirstRecordByField(writeTableId, tmpUserFields.sec_uid.label, res_sec_id)
          const upsertDate = {
            sec_uid: res.data.data.user.sec_uid, 
            nickname: res.data.data.user.nickname,
            signature: res.data.data.user.signature,

            follower_count: res.data.data.user.follower_count,
            aweme_count: res.data.data.user.aweme_count,
            total_favorited: res.data.data.user.total_favorited,

            following_count: res.data.data.user.following_count,
            max_follower_count: res.data.data.user.max_follower_count,
          }
          if (record) {
            const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label]?.id] || null
            const last_follower_count = record.fields[fieldMap[tmpUserFields.follower_count.label]?.id] || 0
            const last_aweme_count = record.fields[fieldMap[tmpUserFields.aweme_count.label]?.id] || 0
            const last_total_favorited = record.fields[fieldMap[tmpUserFields.total_favorited.label]?.id] || 0
            result = await updateTable(
              writeTableId,
              [{
                recordId: record.recordId,
                data: {
                  ...upsertDate,

                  follower_count_diff: res.data.data.user.follower_count - last_follower_count,
                  aweme_count_diff: res.data.data.user.aweme_count - last_aweme_count,
                  total_favorited_diff: res.data.data.user.total_favorited - last_total_favorited,

                  current_get_time: get_time,
                  last_get_time: last_get_time,
                }
              }],
              tmpUserFields,
            );
          }
          else{
            result = await writeToTable(
              writeTableId,
              [{
                ...upsertDate,

                current_get_time: get_time,
                get_work_flag: 'unknow',
              }],
              tmpUserFields,
            );
          }
        }
        else{
          result.error = res.data?.msg || '未知错误'
        }
        return {...result, cost: res.data?.price || 0}
      }


      const upsertUserPost = async(post_data, writeTableId, fetchRange) => {
        console.log(post_data)
        const tmpUserFields = userFields()
        let totalPostCount = 0
        let totalCost = 0
        let totalWriteCount = 0
        let workSuccessCount = 0
        let failmsg = ''
        let max_cursor = ""
        let i = 0

        let min_time = 0
        if (ranges.value[fetchRange]?.type === 'date') {
          const date = new Date()
          date.setHours(0, 0, 0, 0)
          date.setDate(date.getDate() - (ranges.value[fetchRange].value - 1))
          min_time = date.getTime()
        }

        while(true){
          i += 1
          const get_time = Date.now()
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/douyin_user_post',
            body: {
              sec_user_id: post_data.sec_user_id,
              share_text: post_data.share_text,
              max_cursor: max_cursor,
            },
            params: {
              key: props.formData.key,
            }
          })
          totalPostCount++
          totalCost += res.data?.price || 0

          if (!(res && res.data && res.data.code === 0)) {
            failmsg = res.data?.msg || '未知错误'
            if (post_data.itemType && post_data.tableId && post_data.recordId){
              await updateTable(
                post_data.tableId,
                [{
                  recordId: post_data.recordId,
                  data: {
                    get_work_flag: i > 1 ? 'partial_success' : 'fail',
                    work_fail_reason: res.data.msg || '未知错误',
                  }
                }],
                tmpUserFields,
              );
            }
            break
          }

          max_cursor = String(res.data.data.max_cursor)
          totalCost += res.data.price

          // 过滤掉时间范围外的置顶视频
          let preFilteringData = res.data.data.aweme_list
          if (ranges.value[fetchRange].type === 'date'){
            preFilteringData = res.data.data.aweme_list.filter(item => item.is_top != 1 || item.create_time * 1000 > min_time)
          }
          let workAccordCount = 0
          const items = []
          for (const item of preFilteringData){
            if (ranges.value[fetchRange].type !== 'date' || item.create_time * 1000 > min_time){
              workAccordCount++
              totalWriteCount++
              items.push(item)
            }
          }
          if (items.length > 0){
            const [successConut, upsertFailMsg] = await upsertWorks(items, get_time, writeTableId)
            workSuccessCount += successConut
            failmsg = upsertFailMsg
          }
          
          if (post_data.itemType && post_data.tableId && post_data.recordId){
            await updateTable(
              post_data.tableId,
              [{
                recordId: post_data.recordId,
                data: {
                  get_work_flag: 'success',
                  work_fail_reason: '',
                }
              }],
              tmpUserFields,
            );
          }

          if (!res.data.data.has_more){ break; }
          else if (ranges.value[fetchRange].type === 'date'){
            if (workAccordCount === 0 || workAccordCount < preFilteringData.length) break;
          }
          else if (ranges.value[fetchRange].type === 'page'){
            if (i >= ranges.value[fetchRange].value) break;
          }
          else{
            if (preFilteringData.length === 0) break;
          }
        }
        return [totalPostCount, totalCost, totalWriteCount, workSuccessCount, failmsg]
      }


      const updateWorks = async() => {
        if (!props.formData.key){
          return ['请先登录', 'warning']
        }
        if (!paneData.value.selectedTableId){
          return ['请先选择要更新的表格', 'warning']
        }

        let successCount = 0
        let totalCost = 0
        let failmsg = ''


        const writeTableId = paneData.value.selectedTableId

        const workTable = await bitable.base.getTable(writeTableId)
        const recordIdList = await bitable.ui.selectRecordIdList(writeTableId)

        const fieldList = await workTable.getFieldList()
        const fieldMap = {};
        for (const field of fieldList) {
          const fieldName = await field.getName();
          fieldMap[fieldName] = field;
        }

        const tmpWorkFields = workFields()
        const totalInteract = []
        for (const workRecordId of recordIdList){
          const workRecord = await workTable.getRecordById(workRecordId);
          const aweme_id = workRecord.fields[fieldMap[tmpWorkFields.aweme_id.label].id][0].text
          const get_time = Date.now()

          // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_aweme_detail?key=${props.formData.key}`, {
          //     aweme_id: aweme_id.text,
          // })

          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/douyin_aweme_detail',
            body: {
              aweme_id: aweme_id,
            },
            params: {
              key: props.formData.key,
            }
          })
          totalCost += res.data?.price || 0

          if (res && res.data && res.data.code === 0) {
            const last_get_time = workRecord.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
            const last_digg_count = workRecord.fields[fieldMap[tmpWorkFields.digg_count.label].id] || 0
            const last_comment_count = workRecord.fields[fieldMap[tmpWorkFields.comment_count.label].id] || 0
            const last_share_count = workRecord.fields[fieldMap[tmpWorkFields.share_count.label].id] || 0
            const last_collect_count = workRecord.fields[fieldMap[tmpWorkFields.collect_count.label].id] || 0
            const result = await updateTable(
              writeTableId,
              [{
                recordId: workRecordId,
                data: {
                  aweme_id: aweme_id,
                  desc: res.data.data.aweme_detail.desc,
                  caption: res.data.data.aweme_detail.caption,
                  sec_uid: res.data.data.aweme_detail.author.sec_uid,
                  nickname: res.data.data.aweme_detail.author.nickname,
                  vedio_url: 'https://www.douyin.com/video/' + aweme_id,
                  create_time: res.data.data.aweme_detail.create_time * 1000, // 转换为毫秒级时间戳

                  digg_count: res.data.data.aweme_detail.statistics.digg_count,
                  comment_count: res.data.data.aweme_detail.statistics.comment_count,
                  share_count: res.data.data.aweme_detail.statistics.share_count,
                  collect_count: res.data.data.aweme_detail.statistics.collect_count,

                  digg_count_diff: res.data.data.aweme_detail.statistics.digg_count - last_digg_count,
                  comment_count_diff: res.data.data.aweme_detail.statistics.comment_count - last_comment_count,
                  share_count_diff: res.data.data.aweme_detail.statistics.share_count - last_share_count,
                  collect_count_diff: res.data.data.aweme_detail.statistics.collect_count - last_collect_count,

                  current_get_time: get_time,
                  last_get_time: last_get_time,
                }
              }],
              tmpWorkFields,
            );
            if(result.success){
              successCount++
            }
            else{
              failmsg = result.error || failmsg
            }
          }
          else{
            failmsg = res.data?.msg || failmsg
          }
        }

        let returnMessage = '批量更新完成，尝试更新'+recordIdList.length+'条作品数据，成功更新'+successCount+'条数据，共消耗'+totalCost+'元';
        if (failmsg){
          returnMessage += '，失败数据原因：'+failmsg
        }
        let returnType = failmsg ? 'warning' : 'success'
        return [returnMessage, returnType]
      }


      const collectData = async () => {
        if (!props.formData.key){
          return ['请先登录', 'warning']
        }

        const post_data_list = []
        const tmpUserFields = userFields()
        const collectionType = paneData.value.collectionType
        let writeTableId = paneData.value.selectedTableId
        const fetchRange = paneData.value.searchRange

        for (const item of Object.values(searchValues.value)){
          if (item.dataType === 'table'){
            const tmpTable = await bitable.base.getTableById(item.data.tableId)
            const fieldList = await tmpTable.getFieldList()
            const fieldMap = {};
            for (const field of fieldList) {
              const fieldName = await field.getName();
              fieldMap[fieldName] = field;
            }
            for (const user_recordId of item.data.recordIdList){
              const userRecord = await tmpTable.getRecordById(user_recordId);
              const rawValue = userRecord.fields[fieldMap[tmpUserFields.sec_uid.label]?.id]?.[0].text || ''
              const accountParams = parseAccountInput(rawValue)
              if (accountParams){
                post_data_list.push({
                  itemType: item.dataType,
                  tableId: item.data.tableId,
                  recordId: user_recordId,
                  ...accountParams,
                })
              }
            }
          }
          else if (item.dataType === 'input'){
            const accountParams = parseAccountInput(item.data.inputValue)
            if (accountParams){
              post_data_list.push({
                itemType: item.dataType,
                ...accountParams,
              })
            }
          }
        }

        if (post_data_list.length === 0){
          return ['请给出采集账号', 'warning']
        }

        if (!writeTableId) {
          const today = new Date();
          const tablePrefix = collectionType === 'blogger' ? '抖音账号' : collectionType === 'post' ? '抖音视频' : '数据表'
          const createFields = collectionType === 'blogger' ? tmpUserFields : collectionType === 'post' ? workFields() : tmpUserFields
          writeTableId = await createTemplateTable(
            tablePrefix + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_'),
            createFields,
          );
          if (writeTableId) {
            paneData.value.selectedTableId = writeTableId
          }
        }

        if (writeTableId){
          if (collectionType === 'blogger'){
            let successCount = 0
            let totalCost = 0
            let failmsg = ''
            for (const item of post_data_list){
              const result = await upsertUserData(item, writeTableId)
              totalCost += result.cost || 0
              if(result.success){
                successCount++
              }
              else{
                failmsg = result.error || failmsg
              }
            }
            let returnMessage = '采集博主数据完成，\n尝试采集'+post_data_list.length+'条博主数据，成功采集'+successCount+'条数据，共消耗'+totalCost.toFixed(2)+'元';
            if (failmsg){
              returnMessage += '，失败数据原因：'+failmsg
            }
            let returnType = failmsg ? 'warning' : 'success'
            return [returnMessage, returnType]
          }
          else if (collectionType === 'post'){
            let totalPostCount = 0
            let totalCost = 0
            let totalWriteCount = 0
            let totalSuccessCount = 0
            let failmsg = ''
            for (const item of post_data_list){
              const [postCount, cost, writeCount, successCount, upsertFailMsg] = await upsertUserPost(item, writeTableId, fetchRange)
              totalPostCount += postCount || 0
              totalCost += cost || 0
              totalWriteCount += writeCount || 0
              totalSuccessCount += successCount || 0
              failmsg = upsertFailMsg || failmsg
            }
            let returnMessage = '采集博主作品完成，尝试采集'+post_data_list.length+'位博主作品数据'+
            '，共尝试获取'+totalPostCount+'页作品数据，成功采集'+totalSuccessCount+'条作品数据，共消耗'+totalCost+'元';
            if (failmsg){
              returnMessage += '，失败数据原因：'+failmsg
            }
            let returnType = failmsg ? 'warning' : 'success'
            return [returnMessage, returnType]
          }
        }

        return ['采集完成', 'success']
      }


      const executeCollect = async (collect) => {
        if (props.isLocked) return;
        emit('update:isLocked', true);
        try{
          [props.formData.message, props.formData.messageType] = await collect()
          if (props.formData.messageType === 'success') {
            const isWorkOp =
              paneData.value.collectionType === 'post' ||
              /批量更新完成|更新.*作品|作品数据/.test(props.formData.message || '')
            const target = isWorkOp ? 'work' : 'user'
            setCollectResultTable(
              props.formData,
              getCollectResultTableId(paneData.value, target),
            )
            resetAccountInputsAfterSuccess(searchValues)
          } else {
            props.formData.resultTableId = null
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:'+ (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const openTip = () => {
        tipVisible.value = true
      }

      const selectedTableIds = computed(() =>
        Object.values(searchValues.value)
          .filter(item => item?.dataType === 'table' && item.data?.tableId)
          .map(item => item.data.tableId)
      )

      return {
        paneData,
        ranges,
        searchValues,
        selectedTableIds,
        tipVisible,
        changecollectionType,
        addSearchRow,
        removeSearchRow,
        hasAccountInput,
        updateWorks,
        collectData,
        executeCollect,
        openTip,
      };
    },
  };
</script>

<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <!-- 1. 采集内容 -->
      <div class="section-block">
        <div class="toggle-wrapper">
          <!-- 使用 :class 动态控制高亮状态 -->
          <el-tooltip content="将采集账号的ID、粉丝数、简介、点赞数等基础信息" placement="top">
            <el-button type="info" class="toggle-btn" :class="{ active: paneData.collectionType === 'blogger' }" @click="changecollectionType('blogger')">采集博主数据</el-button>
          </el-tooltip>
          <el-tooltip content="将采集作品的点赞、评论、查看、转发、发布时间等数据" placement="top">
            <el-button type="info" class="toggle-btn" :class="{ active: paneData.collectionType === 'post' }" @click="changecollectionType('post')">采集作品数据</el-button>
          </el-tooltip>
        </div>
      </div>

      <!-- 2. 作品数据范围 -->
      <div class="section-block" v-if="paneData.collectionType === 'post'">
        <div class="field-label">作品数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" :placeholder="'请选择数据范围'">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>

      <!-- 3. 采集到表格 -->
      <div class="section-block">
        <div class="field-label">采集到表格</div>
        <TableSelect v-model="paneData.selectedTableId" placeholder="默认新建表格" />
      </div>
    </div>

    <div class="section-title">
      采集账号
      <!-- <el-icon class="icon-hint" @click="openTip"><QuestionFilled /></el-icon> -->
    </div>

    <div class="collect-sub-panel">
      <!-- 4. 采集账号 -->
      <div class="section-block">
        <!-- 动态列表（对象结构） -->
        <div 
          v-for="key in Object.keys(searchValues)" 
          :key="key" 
          class="account-input-group"
        >
          <!-- 带下拉箭头的输入框 -->
          <generalSelect
            v-model="searchValues[key]"
            placeholder="输入账号主页链接，或选择已有表格"
            :disabledTableIds="selectedTableIds"
          />
          <!-- 始终显示添加按钮（第一行），其他行显示删除按钮 -->
          <span
            v-if="key === Object.keys(searchValues)[0]"
            class="account-add-btn"
            @click="addSearchRow"
          >
            <el-icon size="16"><CirclePlus /></el-icon>
          </span>
          <span
            v-else
            class="account-add-btn"
            style="color: #ff4d4f; border-color: #ffccc7;"
            @click="removeSearchRow(key)"
          >
            <el-icon size="16"><Remove /></el-icon>
          </span>
        </div>
      </div>
    </div>


    <div class="collect-btn-container">
      <div class="collect-btn-item">
        <el-button
          class="collect-btn"
          :disabled="isLocked || !formData.key || !hasAccountInput()"
          @click="executeCollect(collectData)"
        >
          采集数据
        </el-button>
      </div>
      <div class="collect-btn-item">
        <el-button
          class="update-btn"
          v-if="paneData.collectionType === 'post' && paneData.selectedTableId"
          :disabled="isLocked"
          @click="executeCollect(updateWorks)" 
        >
          批量更新作品数据
        </el-button>
      </div>
    </div>
  </div>

  <platformTip
    v-model:visible="tipVisible"
    platform-name="抖音"
    account-field-name="抖音账号ID"
  />

  <!-- <p>{{ searchValues }}</p>
  <p>{{ paneData }}</p> -->
</template>

<style scoped>
</style>
