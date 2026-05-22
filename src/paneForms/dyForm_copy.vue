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
  import { writeToTable, updateTable, getFirstRecordByField} from '@/utils/tableHelper'
  import TableSelect from '@/components/TableSelect.vue'
  import { Plus, ArrowDown, CircleClose, Remove, CirclePlus, QuestionFilled } from '@element-plus/icons-vue'
  import generalSelect from '@/toolComponents/generalSelect.vue'
  import '@/assets/form-styles.css'

  export default {
    components: {
      ElForm,
      ElFormItem,
      ElSelect,
      ElOption,
      ElInput,
      ElButton,
      TableSelect,
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

      const dateRange = ref([1,3,7,15])
      const ranges = ref({
        '当天': {value: 1 , type: 'date'},
        '3天内': {value: 3 , type: 'date'},
        '7天内': {value: 7 , type: 'date'},
        '15天内': {value: 15 , type: 'date'},
        '30天内': {value: 30 , type: 'date'},
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

      // 改为字典管理多个输入项
      const searchValues = ref({
        0: {
          dataType: 'input',
          data: {inputValue: ''}
        }
      });


      // 添加新行（对象结构）
      const addSearchRow = () => {
        // 获取对象中最大的key，然后+1，({}整数键默认排序，直接取最后一个)
        const newId = Number(Object.keys(searchValues.value)[Object.keys(searchValues.value).length - 1]) + 1;
        searchValues.value[newId] = {
          dataType: 'input',
          data: {inputValue: ''}
        };
      };


      // 删除指定行（对象结构）
      const removeSearchRow = (id) => {
        delete searchValues.value[id];
      }


      const changecollectionType = async (newCollectionType) => {
        paneData.value.collectionType = newCollectionType
        paneData.value.selectedTableId = null
        paneData.value.searchRange = '1页'
        const newId = Number(Object.keys(searchValues.value)[Object.keys(searchValues.value).length - 1]) + 1;
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


      const upsertUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          if (!paneData.value.userTableId) {
            const today = new Date();
            const newTableId = await createTemplateTable(
              '抖音账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_'),
              userFields()
            );
            if (newTableId) {
              paneData.value.userTableId = newTableId
            }
          }

          const get_time = Date.now()
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/douyin_user_data',
            body: {
              sec_user_id: paneData.value.sec_user_id,
              share_text: paneData.value.share_text,
            },
            params: {
              key: props.formData.key,
            }
          })

          const tmpUserFields = userFields()
          if (res && res.data && res.data.code === 0) {
            const res_sec_id = res.data.data.user.sec_uid
            const [record, fieldMap] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.sec_uid.label, res_sec_id)
            if (record) {
              const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label]?.id] || null
              const last_follower_count = record.fields[fieldMap[tmpUserFields.follower_count.label]?.id] || 0
              const last_aweme_count = record.fields[fieldMap[tmpUserFields.aweme_count.label]?.id] || 0
              const last_total_favorited = record.fields[fieldMap[tmpUserFields.total_favorited.label]?.id] || 0
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: record.recordId,
                  data: {
                    sec_uid: res.data.data.user.sec_uid, 
                    nickname: res.data.data.user.nickname,
                    signature: res.data.data.user.signature,

                    follower_count: res.data.data.user.follower_count,
                    aweme_count: res.data.data.user.aweme_count,
                    total_favorited: res.data.data.user.total_favorited,

                    follower_count_diff: res.data.data.user.follower_count - last_follower_count,
                    aweme_count_diff: res.data.data.user.aweme_count - last_aweme_count,
                    total_favorited_diff: res.data.data.user.total_favorited - last_total_favorited,

                    following_count: res.data.data.user.following_count,
                    max_follower_count: res.data.data.user.max_follower_count,
                    current_get_time: get_time,
                    last_get_time: last_get_time,
                  }
                }],
                tmpUserFields,
              );
            }
            else{
              console.log(paneData.value.userTableId)
              const result = await writeToTable(
                paneData.value.userTableId,
                [{sec_uid: res.data.data.user.sec_uid, 
                  nickname: res.data.data.user.nickname,
                  signature: res.data.data.user.signature,

                  follower_count: res.data.data.user.follower_count,
                  aweme_count: res.data.data.user.aweme_count,
                  total_favorited: res.data.data.user.total_favorited,

                  following_count: res.data.data.user.following_count,
                  max_follower_count: res.data.data.user.max_follower_count,
                  current_get_time: get_time,
                  get_work_flag: 'unknow',
                }],
                tmpUserFields,
              );
            }

            
            props.formData.message = '新增抖音账号完成，消耗：' + res.data.price
            props.formData.messageType = 'success';
          }
          else{
            props.formData.message = '操作失败:' + (res.data.msg || '未知错误');
            props.formData.messageType = 'error';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const batchUpdateUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let successCount = 0
          let totalCost = 0

          const userTable = await bitable.base.getTable(paneData.value.userTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId)

          const fieldList = await userTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const tmpUserFields = userFields()
          for (const user_recordId of recordIdList){
            const userRecord = await userTable.getRecordById(user_recordId);
            const sec_user_id = userRecord.fields[fieldMap[tmpUserFields.sec_uid.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
            //     sec_user_id: secUid,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/douyin_user_data',
              body: {
                sec_user_id: sec_user_id,
              },
              params: {
                key: props.formData.key,
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.price
              const last_get_time = userRecord.fields[fieldMap[tmpUserFields.current_get_time.label]?.id] || null
              const last_follower_count = userRecord.fields[fieldMap[tmpUserFields.follower_count.label]?.id] || 0
              const last_aweme_count = userRecord.fields[fieldMap[tmpUserFields.aweme_count.label]?.id] || 0
              const last_total_favorited = userRecord.fields[fieldMap[tmpUserFields.total_favorited.label]?.id] || 0
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: user_recordId,
                  data: {
                    sec_uid: sec_user_id, 
                    nickname: res.data.data.user.nickname,
                    signature: res.data.data.user.signature,

                    follower_count: res.data.data.user.follower_count,
                    aweme_count: res.data.data.user.aweme_count,
                    total_favorited: res.data.data.user.total_favorited,

                    follower_count_diff: res.data.data.user.follower_count - last_follower_count,
                    aweme_count_diff: res.data.data.user.aweme_count - last_aweme_count,
                    total_favorited_diff: res.data.data.user.total_favorited - last_total_favorited,

                    following_count: res.data.data.user.following_count,
                    max_follower_count: res.data.data.user.max_follower_count,
                    current_get_time: get_time,
                    last_get_time: last_get_time,
                  }
                }],
                tmpUserFields,
              );
              if (result && result.success) {
                successCount++
              }
            }
          }

          if(recordIdList.length > 0){
            props.formData.message = '更新用户信息完成，'+'尝试更新'+ recordIdList.length + '条账号信息，成功'+ successCount + '条，消耗' + totalCost.toFixed(3) + '元'
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:'+ (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const upsertWork = async(items, get_time) => {
        const tmpWorkFields = workFields()
        const insertData = []
        const updateData = []
        for (const item of items) {
          const aweme_id = item.aweme_id
          const [record, fieldMap] = await getFirstRecordByField(paneData.value.workTableId, tmpWorkFields.aweme_id.label, aweme_id)
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
          paneData.value.workTableId,
          insertData,
          tmpWorkFields,
        );
        
        const updateRes = await updateTable(
          paneData.value.workTableId,
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
        return resultCount
      }


      const getRecentWorks = async(rangeKey, getWorksType = 0) => {
        if (props.isLocked) return;
        emit('update:isLocked', true);
        
        try{
          if (!paneData.value.workTableId) {
            const today = new Date();
            const newTableId = await createTemplateTable(
              '抖音视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_'),
              workFields()
            );
            if (newTableId) {
              paneData.value.workTableId = newTableId
            }
          }

          let workSuccessCount = 0
          let singleUserSuccess = 1
          let totalCost = 0

          const range = ranges.value[rangeKey]
          let min_time = 0
          if (range.type === 'date'){
            const date = new Date()
            date.setHours(0, 0, 0, 0)
            date.setDate(date.getDate() - (range.value - 1))
            min_time = date.getTime()
          }

          const tmpUserFields = userFields()
          const totalLastTime = {}
          let userInfoList = []
          if (getWorksType === 0){
            const userTable = await bitable.base.getTable(paneData.value.userTableId)
            const fieldList = await userTable.getFieldList()
            const fieldMap = {};
            for (const field of fieldList) {
              const fieldName = await field.getName();
              fieldMap[fieldName] = field;
            }

            const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId)
            const sec_user_id_set = {}
            for (const userRecordId of recordIdList){
              const userRecord = await userTable.getRecordById(userRecordId);
              const sec_user_id = userRecord.fields[fieldMap[tmpUserFields.sec_uid.label].id][0].text
              if (sec_user_id_set[sec_user_id]) continue
              sec_user_id_set[sec_user_id] = true
              userInfoList.push({
                recordId: userRecordId,
                sec_user_id: sec_user_id
              })
            }
          }
          else{
            userInfoList = [{ sec_user_id: paneData.value.sec_user_id, share_text: paneData.value.share_text }]
          }
          
          for (const userInfo of userInfoList){
            let max_cursor = ""
            let i = 0
            while(true){
              i += 1
              const get_time = Date.now()
              // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_post?key=${props.formData.key}`, {
              //     sec_user_id: secUid,
              //     max_cursor: max_cursor,
              // })

              const res = await pluginAPI.post('/plugin_forward', {
                url: '/fbmain/monitor/v3/douyin_user_post',
                body: {
                  sec_user_id: userInfo.sec_user_id,
                  share_text: userInfo.share_text,
                  max_cursor: max_cursor,
                },
                params: {
                  key: props.formData.key,
                }
              })

              if (!(res && res.data && res.data.code === 0)) {
                if (getWorksType === 0 && userInfo.recordId){
                  totalLastTime[userInfo.recordId] = {
                    recordId: userInfo.recordId, 
                    data: {
                      get_work_flag: i > 1 ? 'partial_success' : 'fail',
                      work_fail_reason: res.data.msg || '未知错误',
                    }
                  }
                }
                else{
                  singleUserSuccess = 0
                }
                break
              }

              max_cursor = String(res.data.data.max_cursor)
              totalCost += res.data.price

              // 过滤掉时间范围外的置顶视频
              let preFilteringData = res.data.data.aweme_list
              if (range.type === 'date'){
                preFilteringData = res.data.data.aweme_list.filter(item => item.is_top != 1 || item.create_time * 1000 > min_time)
              }
              let workAccordCount = 0
              const items = []
              for (const item of preFilteringData){
                if (range.type !== 'date' || item.create_time * 1000 > min_time){
                  workAccordCount += 1
                  items.push(item)
                }
              }
              if (items.length > 0){
                workSuccessCount += await upsertWork(items, get_time)
              }
              
              // 将数据添加到对象中，使用 recordId 作为 key
              if (getWorksType === 0 && userInfo.recordId){
                totalLastTime[userInfo.recordId] = {
                  recordId: userInfo.recordId, 
                  data: {
                    get_work_flag: 'success',
                    work_fail_reason: '',
                  }
                };
              }
              
              if (range.type === 'date'){
                if (workAccordCount === 0 || workAccordCount < preFilteringData.length) break;
              }
              else if (range.type === 'page'){
                if (i >= range.value) break;
              }
              else{
                if (preFilteringData.length === 0) break;
              }
            }
          }

          await updateTable(
            paneData.value.userTableId,
            Object.values(totalLastTime),
            tmpUserFields
          )

          if(userInfoList.length > 0){
            let userSuccessCount = singleUserSuccess
            if (getWorksType === 0){
              userSuccessCount = Object.values(totalLastTime).filter(item => item.data.get_work_flag === 'success').length;
            }
            props.formData.message = '获取视频完成，尝试获取' + userInfoList.length + '个账号，成功操作'+userSuccessCount+'个账号，共写入' + workSuccessCount + '条视频信息，共消耗' + totalCost.toFixed(3);
            props.formData.messageType = 'success';
          }

        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:'+ (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const updateWorks = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let successCount = 0
          let totalCost = 0

          const workTable = await bitable.base.getTable(paneData.value.workTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.workTableId)

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

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.price
              const last_get_time = workRecord.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
              const last_digg_count = workRecord.fields[fieldMap[tmpWorkFields.digg_count.label].id] || 0
              const last_comment_count = workRecord.fields[fieldMap[tmpWorkFields.comment_count.label].id] || 0
              const last_share_count = workRecord.fields[fieldMap[tmpWorkFields.share_count.label].id] || 0
              const last_collect_count = workRecord.fields[fieldMap[tmpWorkFields.collect_count.label].id] || 0
              const result = await updateTable(
                paneData.value.workTableId,
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
            }
          }
          
          if(recordIdList.length > 0){
            props.formData.message = '更新抖音视频完成, 共尝试更新'+recordIdList.length+'条, 成功'+successCount+'条, 消耗'+totalCost.toFixed(3);
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:'+ (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const collectData = async () => {
        const post_data_list = []
        const tmpUserFields = userFields()
        if (!paneData.value.selectedTableId) {
          const today = new Date();
          const newTableId = await createTemplateTable(
            '抖音账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_'),
            userFields()
          );
          if (newTableId) {
            paneData.value.selectedTableId = newTableId
          }
        }

        for (const item of Object.values(searchValues.value)){
          if (item.dataType === 'table'){
            const tmpTable = await getTable(item.data.tableId)
            for (const user_recordId of item.data.recordIdList){
              const userRecord = await tmpTable.getRecordById(user_recordId);
              const sec_user_id = userRecord.fields[fieldMap[tmpUserFields.sec_uid.label]?.id]?.[0].text || ''
              if (sec_user_id){
                post_data_list.push({
                  sec_user_id: sec_user_id,
                })
              }
            }
          }
          else{
            post_data_list.push({
              share_text: item.data.inputValue,
            })
          }
        }

        for (const item of post_data_list){
          const get_time = Date.now()
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/douyin_user_data',
            body: item,
            params: {
              key: props.formData.key,
            }
          })

          if (res && res.data && res.data.code === 0) {
            const res_sec_id = res.data.data.user.sec_uid
            const [record, fieldMap] = await getFirstRecordByField(paneData.value.selectedTableId, tmpUserFields.sec_uid.label, res_sec_id)
            if (record) {
              const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label]?.id] || null
              const last_follower_count = record.fields[fieldMap[tmpUserFields.follower_count.label]?.id] || 0
              const last_aweme_count = record.fields[fieldMap[tmpUserFields.aweme_count.label]?.id] || 0
              const last_total_favorited = record.fields[fieldMap[tmpUserFields.total_favorited.label]?.id] || 0
              const result = await updateTable(
                paneData.value.selectedTableId,
                [{
                  recordId: record.recordId,
                  data: {
                    sec_uid: res.data.data.user.sec_uid, 
                    nickname: res.data.data.user.nickname,
                    signature: res.data.data.user.signature,

                    follower_count: res.data.data.user.follower_count,
                    aweme_count: res.data.data.user.aweme_count,
                    total_favorited: res.data.data.user.total_favorited,

                    follower_count_diff: res.data.data.user.follower_count - last_follower_count,
                    aweme_count_diff: res.data.data.user.aweme_count - last_aweme_count,
                    total_favorited_diff: res.data.data.user.total_favorited - last_total_favorited,

                    following_count: res.data.data.user.following_count,
                    max_follower_count: res.data.data.user.max_follower_count,
                    current_get_time: get_time,
                    last_get_time: last_get_time,
                  }
                }],
                tmpUserFields,
              );
            }
            else{
              console.log(paneData.value.selectedTableId)
              const result = await writeToTable(
                paneData.value.selectedTableId,
                [{sec_uid: res.data.data.user.sec_uid, 
                  nickname: res.data.data.user.nickname,
                  signature: res.data.data.user.signature,

                  follower_count: res.data.data.user.follower_count,
                  aweme_count: res.data.data.user.aweme_count,
                  total_favorited: res.data.data.user.total_favorited,

                  following_count: res.data.data.user.following_count,
                  max_follower_count: res.data.data.user.max_follower_count,
                  current_get_time: get_time,
                  get_work_flag: 'unknow',
                }],
                tmpUserFields,
              );
            }
          }
        }
      }


      return {
        paneData,
        dateRange,
        ranges,
        searchValues,
        changecollectionType,
        addSearchRow,
        removeSearchRow,
        upsertUser,
        batchUpdateUser,
        upsertWork,
        getRecentWorks,
        updateWorks,
        collectData,
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
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.collectionType === 'blogger' }" @click="changecollectionType('blogger')">采集博主数据</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.collectionType === 'post' }" @click="changecollectionType('post')">采集作品数据</el-button>
        </div>
      </div>

      <!-- 2. 采集范围 -->
      <div class="section-block" v-if="paneData.collectionType === 'post'">
        <div class="section-title">采集范围</div>
        <el-select v-model="paneData.searchRange" :placeholder="'请选择数据范围'">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>

      <!-- 3. 采集到表格 -->
      <div class="section-block">
        <div class="section-title">采集到表格</div>
        <TableSelect v-model="paneData.selectedTableId" placeholder="默认新建表格" />
      </div>
    </div>

    <div class="section-title">
      采集账号
      <el-tooltip content="请输入主页链接，或从已有表中选择博主" placement="top">
        <el-icon class="icon-hint"><QuestionFilled /></el-icon>
      </el-tooltip>
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
            placeholder="请输入主页链接，或从已有表中选择博主"
          />
          <!-- 始终显示添加按钮（第一行），其他行显示删除按钮 -->
          <el-icon 
            v-if="key === Object.keys(searchValues)[0]"
            style="cursor: pointer;" 
            size="20"
            @click="addSearchRow"
          >
            <CirclePlus />
          </el-icon>
          <el-icon 
            v-else
            style="cursor: pointer; color: #ff4d4f;" 
            size="20"
            @click="removeSearchRow(key)"
          >
            <Remove />
          </el-icon>
        </div>
      </div>
    </div>


    <el-button class="collect-btn" @click="collectData" >采集数据</el-button>
  </div>
  <p>{{ searchValues }}</p>
  <p>{{ paneData }}</p>
</template>

<style scoped>
</style>