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
          user_id: { label: '快手账号ID', fieldType: FieldType.Text, isPrimary: true},
          user_name: { label: '快手账号名称', fieldType: FieldType.Text, },
          eid: { label: '账号eid', fieldType: FieldType.Text, },
          kwaiId: { label: '快手号', fieldType: FieldType.Text, },
          user_text: { label: '简介', fieldType: FieldType.Text, },
          fan: { label: '粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          photo: { label: '作品数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fan_diff: { label: '新增粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          photo_diff: { label: '新增作品数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          shareLink: { label: '分享链接', fieldType: FieldType.Url, },
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
          photo_id: { label: '作品ID', fieldType: FieldType.Text, isPrimary: true},
          caption: { label: '标题', fieldType: FieldType.Text, },
          user_id: { label: '快手账号ID', fieldType: FieldType.Text, isPrimary: true},
          user_name: { label: '快手账号名称', fieldType: FieldType.Text, },
          eid: { label: '作品eid', fieldType: FieldType.Text, },
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

      const paneData = ref({
        user_id: null,
        shareLink: null,
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
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/ks_user_data_v2',
            body: {
              share_text: paneData.value.shareLink,
              key: props.formData.key,
            }
          })

          const tmpUserFields = userFields()
          if (res && res.data && res.data.code === 0) {
            const user_id = res.data.data.profile.user_id
            const [record, fieldMap] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.user_id.label, user_id)
            if (record) {
              const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_fan = record.fields[fieldMap[tmpUserFields.fan.label].id] || 0
              const last_photo = record.fields[fieldMap[tmpUserFields.photo.label].id] || 0
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

                    shareLink: paneData.value.shareLink,

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
                [{
                  user_id: user_id, 
                  user_name: res.data.data.profile.user_name,
                  eid: res.data.data.profile.eid,
                  kwaiId: res.data.data.profile.kwaiId,
                  user_text: res.data.data.profile.user_text,

                  fan: res.data.data.ownerCount.fan,
                  photo: res.data.data.ownerCount.photo,

                  shareLink: paneData.value.shareLink,
                  current_get_time: get_time,
                  get_work_flag: 'unknow',
                }],
                tmpUserFields,
              );
            }

            props.formData.message = '新增快手账号完成，消耗：' + res.data.price
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
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.price
              const last_get_time = userRecord.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_fan = userRecord.fields[fieldMap[tmpUserFields.fan.label].id] || 0
              const last_photo = userRecord.fields[fieldMap[tmpUserFields.photo.label].id] || 0
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
            props.formData.message = '更新快手账号信息完成，'+'尝试更新'+ recordIdList.length + '条账号信息，成功'+ successCount + '条，消耗' + totalCost.toFixed(3) + '元'
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


      const upsertWork = async(item, get_time) => {
        const tmpWorkFields = workFields()
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
          const last_get_time = record.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
          const last_like_count = record.fields[fieldMap[tmpWorkFields.like_count.label].id] || 0
          const last_view_count = record.fields[fieldMap[tmpWorkFields.view_count.label].id] || 0
          const last_forward_count = record.fields[fieldMap[tmpWorkFields.forward_count.label].id] || 0
          const last_comment_count = record.fields[fieldMap[tmpWorkFields.comment_count.label].id] || 0
          result = await updateTable(
            paneData.value.workTableId,
            [{
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
            }],
            tmpWorkFields,
          );
        }
        else{
          result = await writeToTable(
            paneData.value.workTableId,
            [{
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
            }],
            tmpWorkFields,
          );
        }
        if (result && result.success) {
          return result.success
        }
        return false
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
              '快手视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
            userInfoList = [{ user_id: paneData.value.user_id }]
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
              for (const item of preFilteringData){
                if (item.timestamp > min_time){
                  workAccordCount += 1  
                  const upsertSuccett = await upsertWork(item, get_time)
                  if (upsertSuccett){
                    workSuccessCount += 1
                  }
                }
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
            props.formData.message = '更新快手视频完成, 共尝试更新'+recordIdList.length+'条, 成功'+successCount+'条, 消耗'+totalCost.toFixed(3);
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
          创建快手视频表空模板
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
          创建快手账号表空模板
      </el-button>
    </el-form-item>


    <el-form-item 
      :label="'快手视频表'"
      v-show="paneData.getDataType !== 0"
    >
      <TableSelect v-model="paneData.workTableId" :placeholder="'未选自动创建'" />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-radio-group v-model="paneData.getWorksType" style="display: flex;">
        <el-radio :label="1">根据账号id获取</el-radio>
        <el-radio :label="0">根据账号表获取</el-radio>
      </el-radio-group>
    </el-form-item>


    <el-form-item 
      :label="'快手账号表'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType === 0"
    >
      <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择快手账号表'" />
    </el-form-item>


    <el-form-item
      :label="'快手账号id'"
      v-show="paneData.getDataType !== 0 && paneData.getWorksType !== 0"
    >
      <el-input 
        v-model="paneData.user_id"
        :placeholder="'请输入快手账号id'"
      />
    </el-form-item>


    <el-form-item
      :label="'账号分享链接'"
      v-show="paneData.getDataType === 0"
    >
      <el-input 
        v-model="paneData.shareLink"
        :placeholder="'请输入快手账号分享链接'"
      />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType === 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.shareLink"
        @click="upsertUser"
        plain
        style="flex: 1;"
      >
        写入快手账号数据
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
        批量更新快手账号数据
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
        :disabled="isLocked || !formData.key || !paneData.userTableId && paneData.getWorksType === 0 || !paneData.user_id && paneData.getWorksType !== 0"
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
        批量更新快手视频数据
      </el-button>
    </el-form-item>

    <!-- <p>{{ paneData }}</p> -->
  </el-form>
</template>

<style scoped>
</style>