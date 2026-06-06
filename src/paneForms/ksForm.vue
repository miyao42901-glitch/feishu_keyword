<script>
  import { ref, computed } from 'vue';
  import { bitable, FieldType, NumberFormatter, DateFormatter } from '@lark-base-open/js-sdk';
  import {
    ElSelect,
    ElOption,
    ElInput,
    ElButton,
    ElTooltip,
    ElIcon,
  } from 'element-plus';
  import { QuestionFilled, CirclePlus, Remove } from '@element-plus/icons-vue';
  import pluginAPI from '@/utils/request'
  import { writeToTable, updateTable, getFirstRecordByField} from '@/utils/tableHelper'
  import TableSelect from '@/components/TableSelect.vue'
  import generalSelect from '@/toolComponents/generalSelect.vue'
  import platformTip from '@/tipDialogs/platformTip.vue'
  import '@/assets/form-styles.css'
  import { setCollectResultTable, getCollectResultTableId } from '@/utils/collectResult'
  import { hasAllAccountInputs, resetAccountInputsAfterSuccess } from '@/utils/accountInput'

  export default {
    components: {
      ElSelect,
      ElOption,
      ElInput,
      ElButton,
      ElTooltip,
      ElIcon,
      QuestionFilled,
      CirclePlus,
      Remove,
      TableSelect,
      generalSelect,
      platformTip,
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
          user_id: { label: '快手用户id', fieldType: FieldType.Text, isPrimary: true},
          user_name: { label: '快手用户名', fieldType: FieldType.Text, },
          eid: { label: '标识id', fieldType: FieldType.Text, },
          kwaiId: { label: '快手号', fieldType: FieldType.Text, },
          user_text: { label: '简介', fieldType: FieldType.Text, },
          fan: { label: '粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          photo: { label: '作品数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fan_diff: { label: '新增粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          photo_diff: { label: '新增作品数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          shareLink: { label: '主页分享链接', fieldType: FieldType.Url, },
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
          photo_id: { label: '视频id', fieldType: FieldType.Text, isPrimary: true},
          caption: { label: '标题', fieldType: FieldType.Text, },
          user_id: { label: '快手账号ID', fieldType: FieldType.Text, isPrimary: true},
          user_name: { label: '快手账号名称', fieldType: FieldType.Text, },
          eid: { label: '标识id', fieldType: FieldType.Text, },
          timestamp: { label: '发布时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},

          like_count: { label: '点赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          view_count: { label: '播放数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          forward_count: { label: '转发数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },

          like_count_diff: { label: '新增点赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          view_count_diff: { label: '新增播放数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          forward_count_diff: { label: '新增转发数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count_diff: { label: '新增评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },

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
        user_id: null,
        shareLink: null,
        userTableId: null,
        workTableId: null,
        searchDate: 3,
        searchRange: '1页',
        getDataType: 0,
        getWorksType: 1,
      })

      const tipVisible = ref(false)

      const openTip = () => {
        tipVisible.value = true
      }

      const searchValues = ref({
        0: {
          dataType: 'input',
          data: { inputValue: '' },
        },
      })

      const addSearchRow = () => {
        const newId = Number(Object.keys(searchValues.value)[Object.keys(searchValues.value).length - 1]) + 1
        searchValues.value[newId] = {
          dataType: 'input',
          data: { inputValue: '' },
        }
      }

      const removeSearchRow = (id) => {
        delete searchValues.value[id]
      }

      const getAccountInputValues = () => {
        return Object.values(searchValues.value)
          .filter((item) => item?.dataType === 'input' && item.data?.inputValue?.trim())
          .map((item) => item.data.inputValue.trim())
      }

      const getAllAccountValues = async () => {
        const inputValues = getAccountInputValues()

        const tableSelections = Object.values(searchValues.value)
          .filter((item) => item?.dataType === 'table' && item.data?.tableId && item.data?.recordIdList?.length > 0)

        const idsFromTables = []
        const tmpUserFields = userFields()

        for (const selection of tableSelections) {
          try {
            const table = await bitable.base.getTable(selection.data.tableId)
            const fieldList = await table.getFieldList()
            const fieldMap = {}
            for (const field of fieldList) {
              const fieldName = await field.getName()
              fieldMap[fieldName] = field
            }
            for (const recordId of selection.data.recordIdList) {
              const record = await table.getRecordById(recordId)
              const userIdField = fieldMap[tmpUserFields.user_id.label]
              if (userIdField && record.fields[userIdField.id]) {
                const user_id = record.fields[userIdField.id][0]?.text
                if (user_id) idsFromTables.push(user_id)
              }
            }
          } catch (error) {
            console.error('读取表格账号失败:', error)
          }
        }

        return [...inputValues, ...idsFromTables]
      }

      const hasAccountInput = () => hasAllAccountInputs(searchValues.value)


      const addUserTableTemplate = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const today = new Date();
          const res = await writeToTable(
            null,
            [],
            userFields(),
            '快手账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
            '快手视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
              '快手账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
            );
            if (tableRes.success) {
              paneData.value.userTableId = tableRes.data.tableId
            }
          }

          const get_time = Date.now()
          const inputValues = getAccountInputValues()
          if (inputValues.length === 0) {
            props.formData.message = '请给出采集账号'
            props.formData.messageType = 'warning'
            return
          }

          let successCount = 0
          let totalCost = 0
          let failmsg = ''

          for (const shareLink of inputValues) {
            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/ks_user_data_v2',
              body: {
                share_text: shareLink,
                key: props.formData.key,
                verifycode: '',
              }
            })

            const tmpUserFields = userFields()
            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.price || 0
              const user_id = String(res.data.data.profile.user_id)
              const [record, fieldMap] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.user_id.label, user_id)
              if (record) {
                const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label]?.id] || null
                const last_fan = record.fields[fieldMap[tmpUserFields.fan.label]?.id] || 0
                const last_photo = record.fields[fieldMap[tmpUserFields.photo.label]?.id] || 0
                const result = await updateTable(
                  paneData.value.userTableId,
                  [{
                    recordId: record.recordId,
                    data: {
                      user_id: user_id,
                      user_name: res.data.data.profile.user_name,
                      eid: res.data.data.profile.eid,
                      kwaiId: res.data.data.profile.kwaiId,
                      user_text: res.data.data.profile.user_text,
                      fan: res.data.data.ownerCount.fan,
                      photo: res.data.data.ownerCount.photo,
                      fan_diff: res.data.data.ownerCount.fan - last_fan,
                      photo_diff: res.data.data.ownerCount.photo - last_photo,
                      shareLink: shareLink,
                      current_get_time: get_time,
                      last_get_time: last_get_time,
                    }
                  }],
                  tmpUserFields,
                );
                if (result.success) successCount++
              } else {
                const result = await writeToTable(
                  paneData.value.userTableId,
                  [{
                    user_id: user_id,
                    user_name: res.data.data.profile.user_name,
                    eid: res.data.data.profile.eid,
                    kwaiId: res.data.data.profile.kwaiId,
                    user_text: res.data.data.profile.user_text,
                    fan: res.data.data.ownerCount.fan,
                    photo: res.data.data.ownerCount.photo,
                    shareLink: shareLink,
                    current_get_time: get_time,
                    get_work_flag: 'unknow',
                  }],
                  tmpUserFields,
                );
                if (result.success) successCount++
              }
            } else {
              failmsg = res?.data?.msg || failmsg || '未知错误'
            }
          }

          if (inputValues.length > 0) {
            let returnMessage = '新增快手账号完成，尝试采集' + inputValues.length + '条，成功' + successCount + '条，消耗：' + totalCost.toFixed(2)
            if (failmsg) returnMessage += '，失败原因：' + failmsg
            props.formData.message = returnMessage
            props.formData.messageType = failmsg && successCount === 0 ? 'error' : failmsg ? 'warning' : 'success'
            if (successCount > 0) {
              resetAccountInputsAfterSuccess(searchValues)
            }
            if (props.formData.messageType === 'success') {
              setCollectResultTable(props.formData, getCollectResultTableId(paneData.value, 'user'))
            }
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
            const shareLink = userRecord.fields[fieldMap[tmpUserFields.shareLink.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
            //     sec_user_id: secUid,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/ks_user_data_v2',
              body: {
                share_text: shareLink,
                key: props.formData.key,
                verifycode: '',
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.price
              const last_get_time = userRecord.fields[fieldMap[tmpUserFields.current_get_time.label]?.id] || null
              const last_fan = userRecord.fields[fieldMap[tmpUserFields.fan.label]?.id] || 0
              const last_photo = userRecord.fields[fieldMap[tmpUserFields.photo.label]?.id] || 0
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: user_recordId,
                  data: {
                    user_id: res.data.data.profile.user_id, 
                    user_name: res.data.data.profile.user_name,
                    eid: res.data.data.profile.eid,
                    kwaiId: res.data.data.profile.kwaiId,
                    user_text: res.data.data.profile.user_text,

                    fan: res.data.data.ownerCount.fan,
                    photo: res.data.data.ownerCount.photo,

                    fan_diff: res.data.data.ownerCount.fan - last_fan,
                    photo_diff: res.data.data.ownerCount.photo - last_photo,

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
            props.formData.message = '更新快手账号信息完成，'+'尝试更新'+ recordIdList.length + '条账号信息，成功'+ successCount + '条，消耗' + totalCost.toFixed(2) + '元'
            props.formData.messageType = 'success';
            setCollectResultTable(props.formData, getCollectResultTableId(paneData.value, 'user'))
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
          const photo_id = item.photo_id.toString()
          let photoIdFromShareInfo = '';
          if (item.share_info) {
            const params = new URLSearchParams(item.share_info);
            photoIdFromShareInfo = params.get('photoId') || '';
          }
          const [record, fieldMap] = await getFirstRecordByField(paneData.value.workTableId, tmpWorkFields.photo_id.label, photo_id)
          console.log(record)
          let result = {}
          if (record) {
            const last_get_time = record.fields[fieldMap[tmpWorkFields.current_get_time.label]?.id] || null
            const last_like_count = record.fields[fieldMap[tmpWorkFields.like_count.label]?.id] || 0
            const last_view_count = record.fields[fieldMap[tmpWorkFields.view_count.label]?.id] || 0
            const last_forward_count = record.fields[fieldMap[tmpWorkFields.forward_count.label]?.id] || 0
            const last_comment_count = record.fields[fieldMap[tmpWorkFields.comment_count.label]?.id] || 0
            updateData.push({
              recordId: record.recordId,
              data: {
                photo_id: item.photo_id,
                caption: item.caption,
                eid: photoIdFromShareInfo,
                timestamp: item.timestamp,

                user_name: item.user_name,
                user_id: item.user_id,

                like_count: item.like_count,
                view_count: item.view_count,
                forward_count: item.forward_count,
                comment_count: item.comment_count,

                like_count_diff: item.like_count - last_like_count,
                view_count_diff: item.view_count - last_view_count,
                forward_count_diff: item.forward_count - last_forward_count,
                comment_count_diff: item.comment_count - last_comment_count,

                current_get_time: get_time,
                last_get_time: last_get_time,
              }
            })
          }
          else{
            insertData.push({
              photo_id: item.photo_id,
              caption: item.caption,
              eid: photoIdFromShareInfo,
              timestamp: item.timestamp,

              user_name: item.user_name,
              user_id: item.user_id,

              like_count: item.like_count,
              view_count: item.view_count,
              forward_count: item.forward_count,
              comment_count: item.comment_count,

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
            const tableRes = await writeToTable(
              null,
              [],
              workFields(),
              '快手视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
            );
            if (tableRes.success) {
              paneData.value.workTableId = tableRes.data.tableId
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

          const allValues = await getAllAccountValues()
          if (allValues.length === 0) {
            props.formData.message = '请给出采集账号'
            props.formData.messageType = 'warning'
            return
          }

          if (getWorksType === 0){
            if (!paneData.value.userTableId) {
              props.formData.message = '请先选择账号表'
              props.formData.messageType = 'warning'
              return
            }

            const userTable = await bitable.base.getTable(paneData.value.userTableId)
            const fieldList = await userTable.getFieldList()
            const fieldMap = {};
            for (const field of fieldList) {
              const fieldName = await field.getName();
              fieldMap[fieldName] = field;
            }

            const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId)
            const user_id_set = {}
            for (const userRecordId of recordIdList){
              const userRecord = await userTable.getRecordById(userRecordId);
              const user_id = userRecord.fields[fieldMap[tmpUserFields.user_id.label].id][0].text
              if (user_id_set[user_id]) continue
              user_id_set[user_id] = true
              userInfoList.push({
                recordId: userRecordId,
                user_id: user_id
              })
            }
          }
          else{
            userInfoList = allValues.map(user_id => ({ user_id }))
          }
          
          for (const userInfo of userInfoList){
            let last_buffer = ""
            let i = 0
            while(true){
              i += 1
              const get_time = Date.now()
              // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_post?key=${props.formData.key}`, {
              //     sec_user_id: secUid,
              //     max_cursor: max_cursor,
              // })

              const res = await pluginAPI.post('/plugin_forward', {
                url: '/fbmain/monitor/v3/ks_user_post_v1',
                body: {
                  uid: userInfo.user_id,
                  pcursor: last_buffer,
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

              last_buffer = res.data.data.pcursor
              totalCost += res.data.price

              const preFilteringData = res.data.data.feeds ? res.data.data.feeds : []

              let workAccordCount = 0
              const items = []
              for (const item of preFilteringData){
                if (range.type !== 'date' || item.timestamp > min_time){
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
            props.formData.message = '获取视频完成，尝试获取' + userInfoList.length + '个账号，成功操作'+userSuccessCount+'个账号，共写入' + workSuccessCount + '条视频信息，共消耗' + totalCost.toFixed(2);
            props.formData.messageType = 'success';
            setCollectResultTable(props.formData, getCollectResultTableId(paneData.value, 'work'))
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
            const eid = workRecord.fields[fieldMap[tmpWorkFields.eid.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_aweme_detail?key=${props.formData.key}`, {
            //     aweme_id: aweme_id.text,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/ks_video_detail',
              body: {
                share_text: "https://www.kuaishou.com/short-video/" + eid,
                key: props.formData.key,
                verifycode: '',
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.price
              const last_get_time = workRecord.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
              const last_like_count = workRecord.fields[fieldMap[tmpWorkFields.like_count.label].id] || 0
              const last_view_count = workRecord.fields[fieldMap[tmpWorkFields.view_count.label].id] || 0
              const last_forward_count = workRecord.fields[fieldMap[tmpWorkFields.forward_count.label].id] || 0
              const last_comment_count = workRecord.fields[fieldMap[tmpWorkFields.comment_count.label].id] || 0
              result = await updateTable(
                paneData.value.workTableId,
                [{
                  recordId: workRecord.recordId,
                  data: {
                    photo_id: item.photo_id,
                    caption: item.caption,
                    eid: photoIdFromShareInfo,
                    timestamp: item.timestamp,

                    user_name: item.user_name,
                    user_id: item.user_id,

                    like_count: item.like_count,
                    view_count: item.view_count,
                    forward_count: item.forward_count,
                    comment_count: item.comment_count,

                    like_count_diff: item.like_count - last_like_count,
                    view_count_diff: item.view_count - last_view_count,
                    forward_count_diff: item.forward_count - last_forward_count,
                    comment_count_diff: item.comment_count - last_comment_count,

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
            props.formData.message = '更新快手视频完成, 共尝试更新'+recordIdList.length+'条, 成功'+successCount+'条, 消耗'+totalCost.toFixed(2);
            props.formData.messageType = 'success';
            setCollectResultTable(props.formData, getCollectResultTableId(paneData.value, 'work'))
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
        ranges,
        searchValues,
        tipVisible,
        openTip,
        addSearchRow,
        removeSearchRow,
        hasAccountInput,
        addUserTableTemplate,
        addWorkTableTemplate,
        upsertUser,
        batchUpdateUser,
        upsertWork,
        getRecentWorks,
        updateWorks,
        getAllAccountValues,
      };
    },
  };
</script>

<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-tooltip content="将采集账号的ID、粉丝数、简介、点赞数等基础信息" placement="top">
            <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">采集博主数据</el-button>
          </el-tooltip>
          <el-tooltip content="将采集作品的点赞、评论、查看、转发、发布时间等数据" placement="top">
            <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">采集作品数据</el-button>
          </el-tooltip>
        </div>
      </div>



      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">快手视频表</div>
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0">
        <div class="field-label">采集到表格</div>
        <TableSelect v-model="paneData.userTableId" placeholder="默认新建表格" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">作品数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </div>

    <div class="section-title">
      采集账号
      <!-- <el-icon class="icon-hint" @click="openTip"><QuestionFilled /></el-icon> -->
    </div>

    <div class="collect-sub-panel">
      <div class="section-block">
        <div
          v-for="key in Object.keys(searchValues)"
          :key="key"
          class="account-input-group"
        >
          <generalSelect
            v-model="searchValues[key]"
            placeholder="输入账号主页链接，或选择已有表格"
          />
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
          @click="paneData.getDataType === 0 ? upsertUser() : getRecentWorks(paneData.searchRange, paneData.getWorksType)"
        >
          采集数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-if="paneData.getDataType === 0 && paneData.userTableId">
        <el-button class="update-btn" :disabled="isLocked || !formData.key" @click="batchUpdateUser">
          批量更新快手账号数据
        </el-button>
      </div>

      <div class="collect-btn-item" v-if="paneData.getDataType !== 0 && paneData.workTableId">
        <el-button class="update-btn" :disabled="isLocked || !formData.key" @click="updateWorks">
          批量更新快手视频数据
        </el-button>
      </div>
    </div>
  </div>

  <platformTip
    v-model:visible="tipVisible"
    platform-name="快手"
    account-field-name="快手账号ID"
  />
</template>






<style scoped>
</style>
