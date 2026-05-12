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

      const paneData = ref({
        sec_user_id: null,
        share_text: null,
        userTableId: null,
        workTableId: null,
        searchDate: 3,
        getDataType: 0,
        getWorksType: 1,
      })


      const addUserTableTemplate = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const today = new Date();
          const res = await writeToTable(
            null,
            [],
            userFields(),
            '抖音账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
          );
          if (res.success) {
            paneData.value.userTableId = res.data.tableId
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const addWorkTableTemplate = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const today = new Date();
          const res = await writeToTable(
            null,
            [],
            workFields(),
            '抖音视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
          );
          if (res.success) {
            paneData.value.workTableId = res.data.tableId
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败:' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const upsertUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          if (!paneData.value.userTableId) {
            const today = new Date();
            const tableRes = await writeToTable(
              null,
              [],
              userFields(),
              '抖音账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
            );
            if (tableRes.success) {
              paneData.value.userTableId = tableRes.data.tableId
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
              const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_follower_count = record.fields[fieldMap[tmpUserFields.follower_count.label].id] || 0
              const last_aweme_count = record.fields[fieldMap[tmpUserFields.aweme_count.label].id] || 0
              const last_total_favorited = record.fields[fieldMap[tmpUserFields.total_favorited.label].id] || 0
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
              const last_get_time = userRecord.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_follower_count = userRecord.fields[fieldMap[tmpUserFields.follower_count.label].id] || 0
              const last_aweme_count = userRecord.fields[fieldMap[tmpUserFields.aweme_count.label].id] || 0
              const last_total_favorited = userRecord.fields[fieldMap[tmpUserFields.total_favorited.label].id] || 0
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


      const getRecentWorks = async(maxDay = 1, getWorksType = 0) => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          if (!paneData.value.workTableId) {
            const today = new Date();
            const tableRes = await writeToTable(
              null,
              [],
              workFields(),
              '抖音视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
            );
            if (tableRes.success) {
              paneData.value.workTableId = tableRes.data.tableId
            }
          }

          let workSuccessCount = 0
          let singleUserSuccess = 1
          let totalCost = 0

          const searchDays = typeof maxDay === 'number' && !isNaN(maxDay) ? Math.min(15, Math.max(1, Math.floor(maxDay))) : 1
          const date = new Date()
          date.setHours(0, 0, 0, 0)
          date.setDate(date.getDate() - (searchDays - 1))
          const min_time = date.getTime()
          
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
              const preFilteringData = res.data.data.aweme_list.filter(item => item.is_top != 1 || item.create_time * 1000 > min_time)
              let workAccordCount = 0
              const items = []
              for (const item of preFilteringData){
                if (item.create_time * 1000 > min_time){
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
              
              if (workAccordCount === 0 || workAccordCount < preFilteringData.length){
                break
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

      return {
        paneData,
        dateRange,
        addUserTableTemplate,
        addWorkTableTemplate,
        upsertUser,
        batchUpdateUser,
        upsertWork,
        getRecentWorks,
        updateWorks,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="auto">  

    <el-form-item label-width="null">
      <el-radio-group v-model="paneData.getDataType" style="display: flex;">
        <el-radio :label="0">获取账号数据</el-radio>
        <el-radio :label="1">获取视频数据</el-radio>
      </el-radio-group>
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-button 
        type="primary" 
        :disabled="isLocked"
        @click="addWorkTableTemplate"
        plain
        style="flex: 1;"
      >
          创建抖音视频表空模板
      </el-button>
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType === 0">
      <el-button 
        type="primary" 
        :disabled="isLocked"
        @click="addUserTableTemplate"
        plain
        style="flex: 1;"
      >
          创建抖音账号表空模板
      </el-button>
    </el-form-item>


    <el-form-item 
      :label="'抖音视频表'"
      v-show="paneData.getDataType !== 0"
    >
      <TableSelect v-model="paneData.workTableId" :placeholder="'未选自动创建'" />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-radio-group v-model="paneData.getWorksType" style="display: flex;">
        <el-radio :label="1">根据账号id或分享链接获取</el-radio>
        <el-radio :label="0">根据账号表获取</el-radio>
      </el-radio-group>
    </el-form-item>


    <el-form-item 
      :label="'抖音账号表'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType === 0"
    >
      <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择抖音账号表'" />
    </el-form-item>


    <el-form-item
      :label="'抖音账号id'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType !== 0"
    >
      <el-input 
        v-model="paneData.sec_user_id"
        :placeholder="'请输入抖音账号id'"
      />
    </el-form-item>


    <el-form-item
      :label="'账号分享链接'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType !== 0"
    >
      <el-input 
        v-model="paneData.share_text"
        :placeholder="'请输入抖音账号分享链接'"
      />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType === 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.sec_user_id && !paneData.share_text"
        @click="upsertUser"
        plain
        style="flex: 1;"
      >
        写入抖音账号数据
      </el-button>
    </el-form-item>


    <el-form-item label-width="null"  v-show="paneData.getDataType === 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.userTableId"
        @click="batchUpdateUser"
        plain
        style="flex: 1;"
      >
        批量更新抖音账号数据
      </el-button>
    </el-form-item>


    <el-form-item :label="'日期范围'"  v-show="paneData.getDataType !== 0">
      <el-select v-model="paneData.searchDate" :placeholder="'请选择日期范围'">
        <el-option v-for="item in dateRange" :key="item" :label="item > 1 ? item + '天' : '当天'" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.userTableId && paneData.getWorksType === 0 || !paneData.sec_user_id && !paneData.share_text && paneData.getWorksType !== 0"
        @click="getRecentWorks(paneData.searchDate, paneData.getWorksType)"
        plain
        style="flex: 1;"
      >
        {{ '获取' + (paneData.searchDate > 1 ? paneData.searchDate + '天内' : '今日') + '发布视频'}}
      </el-button>
    </el-form-item>

    <el-form-item label-width="null"  v-show="paneData.getDataType !== 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.workTableId"
        @click="updateWorks"
        plain
        style="flex: 1;"
      >
        批量更新抖音视频数据
      </el-button>
    </el-form-item>

    <!-- <p>{{ paneData }}</p> -->
  </el-form>
</template>

<style scoped>
</style>