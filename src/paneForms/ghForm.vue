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
          ghid: { label: '公众号id', fieldType: FieldType.Text, isPrimary: true, },
          name: { label: '公众号名称', fieldType: FieldType.Text, },
          fans: { label: '预估粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          avg_top_read: { label: '头条平均阅读', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          avg_top_zan: { label: '头条平均点赞', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          week_articles: { label: '周发文量', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fans_diff: { label: '预估粉丝数变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          avg_top_read_diff: { label: '头条平均阅读变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          avg_top_zan_diff: { label: '头条平均点赞变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          week_articles_diff: { label: '周发文量变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          current_get_time: { label: '当前获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          last_get_time: { label: '上次获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_work_flag: {
            label: '获取文章状态', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过',
              fail: '获取失败',
              partial_success: '部分成功',
              success: '获取成功',
            },
          },
          work_fail_reason: { label: '获取文章失败原因', fieldType: FieldType.Text, },
        }
      }

      function workFields() {
        return {
          mid: { label: '文章id', fieldType: FieldType.Text, isPrimary: true, },
          title: { label: '文章标题', fieldType: FieldType.Text, },
          name: { label: '公众号名称', fieldType: FieldType.Text, },
          ghid: { label: '公众号id', fieldType: FieldType.Text, },
          url: { label: '文章链接', fieldType: FieldType.Url, },
          post_time: { label: '发文时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME },},
          digest: { label: '文章摘要', fieldType: FieldType.Text, },
          original: {
            label: '原创类型', 
            fieldType: FieldType.SingleSelect, 
            options: {
              0: '未声明原创',
              1: '原创',
              2: '转载',
            },
          },
          item_show_type: {
            label: '文章类型', 
            fieldType: FieldType.SingleSelect, 
            options: {
              0: "图文",
              5: "纯视频",
              7: "纯音乐",
              8: "纯图片",
              10: "纯文字",
              11: "其他"
            },
          },
          read: {label: '阅读量', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          zan: {label: '点赞量', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          looking: {label: '在看', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_num: {label: '分享量', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_num: {label: '收藏量', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: {label: '评论量', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          read_diff: {label: '阅读量变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          zan_diff: {label: '点赞量变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_num_diff: {label: '分享量变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_num_diff: {label: '收藏量变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count_diff: {label: '评论量变化', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          current_get_time: { label: '当前获取互动时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          last_get_time: { label: '上次获取互动时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
        }
      }

      const dateRange = ref([1,3,7,15])

      const paneData = ref({
        name: null,
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
            '公众号账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
            '公众号文章' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
              '公众号账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
            );
            if (tableRes.success) {
              paneData.value.userTableId = tableRes.data.tableId
            }
          }

          const get_time = Date.now()
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/Keyverifycode',
            body: {
              name: paneData.value.name,
              key: props.formData.key,
            },
          })

          const tmpUserFields = userFields()
          if (res && res.data && res.data.code === 0) {
            const ghid = res.data.data.ghid
            const [record, fieldMap] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.ghid.label, ghid)
            if (record) {
              const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_fans = record.fields[fieldMap[tmpUserFields.fans.label].id] || 0
              const last_avg_top_read = record.fields[fieldMap[tmpUserFields.avg_top_read.label].id] || 0
              const last_avg_top_zan = record.fields[fieldMap[tmpUserFields.avg_top_zan.label].id] || 0
              const last_week_articles = record.fields[fieldMap[tmpUserFields.week_articles.label].id] || 0
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: record.recordId,
                  data: {
                    ghid: ghid, 
                    name: res.data.data.name,
                    fans: res.data.data.fans,
                    avg_top_read: res.data.data.avg_top_read,
                    avg_top_zan: res.data.data.avg_top_zan,
                    week_articles: res.data.data.week_articles,
                    fans_diff: res.data.data.fans - last_fans,
                    avg_top_read_diff: res.data.data.avg_top_read - last_avg_top_read,
                    avg_top_zan_diff: res.data.data.avg_top_zan - last_avg_top_zan,
                    week_articles_diff: res.data.data.week_articles - last_week_articles,
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
                    ghid: ghid, 
                    name: res.data.data.name,
                    fans: res.data.data.fans,
                    avg_top_read: res.data.data.avg_top_read,
                    avg_top_zan: res.data.data.avg_top_zan,
                    week_articles: res.data.data.week_articles,
                    current_get_time: get_time,
                    get_work_flag: 'unknow',
                }],
                tmpUserFields,
              );
            }

            
            props.formData.message = '新增公众号账号完成，消耗：0.5'
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
            const ghid = userRecord.fields[fieldMap[tmpUserFields.ghid.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
            //     sec_user_id: secUid,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/Keyverifycode',
              body: {
                name: ghid,
                key: props.formData.key,
              },
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += 0.5
              const last_get_time = userRecord.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_fans = userRecord.fields[fieldMap[tmpUserFields.fans.label].id] || 0
              const last_avg_top_read = userRecord.fields[fieldMap[tmpUserFields.avg_top_read.label].id] || 0
              const last_avg_top_zan = userRecord.fields[fieldMap[tmpUserFields.avg_top_zan.label].id] || 0
              const last_week_articles = userRecord.fields[fieldMap[tmpUserFields.week_articles.label].id] || 0
              console.log(userRecord)
              
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: user_recordId,
                  data: {
                    ghid: ghid, 
                    name: res.data.data.name,
                    fans: res.data.data.fans,
                    avg_top_read: res.data.data.avg_top_read,
                    avg_top_zan: res.data.data.avg_top_zan,
                    week_articles: res.data.data.week_articles,
                    fans_diff: res.data.data.fans - last_fans,
                    avg_top_read_diff: res.data.data.avg_top_read - last_avg_top_read,
                    avg_top_zan_diff: res.data.data.avg_top_zan - last_avg_top_zan,
                    week_articles_diff: res.data.data.week_articles - last_week_articles,
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


      const upsertWork = async(items, get_time, userInfo) => {
        const tmpWorkFields = workFields()
        const insertData = []
        const updateData = []
        for (const item of items) {
          const mid = item.appmsgid
          const [record, fieldMap] = await getFirstRecordByField(paneData.value.workTableId, tmpWorkFields.mid.label, mid.toString())
          let result = {}
          if (record) {
            updateData.push({
              recordId: record.recordId,
              data: {
                mid: mid,
                title: item.title,
                name: userInfo.name,
                ghid: userInfo.ghid,
                url: item.url,
                post_time: item.post_time * 1000,
                digest: item.digest,
                original: item.original,
                item_show_type: item.item_show_type,
              }
            })
          }
          else{
            insertData.push({
              mid: mid.toString(),
              title: item.title,
              name: userInfo.name,
              ghid: userInfo.ghid,
              url: item.url,
              post_time: item.post_time * 1000,
              digest: item.digest,
              original: item.original,
              item_show_type: item.item_show_type,
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
              '公众号文章' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
            const ghid_set = {}
            for (const userRecordId of recordIdList){
              const userRecord = await userTable.getRecordById(userRecordId);
              let ghid = null
              if (fieldMap[tmpUserFields.ghid.label]){
                ghid = userRecord.fields[fieldMap[tmpUserFields.ghid.label].id][0].text
              }
              else{
                ghid = userRecord.fields[fieldMap[tmpUserFields.name.label].id][0].text
              }
              if (ghid_set[ghid]) continue
              ghid_set[ghid] = true
              userInfoList.push({
                recordId: userRecordId,
                ghid: ghid,
              })
            }
          }
          else{
            userInfoList = [{ ghid: paneData.value.name }]
          }
          
          for (const userInfo of userInfoList){
            let max_cursor = ""
            let i = 0
            const mid_set = {}
            while(true){
              i += 1
              const get_time = Date.now()
              // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_post?key=${props.formData.key}`, {
              //     sec_user_id: secUid,
              //     max_cursor: max_cursor,
              // })

              const res = await pluginAPI.post('/plugin_forward', {
                  url: '/fbmain/monitor/v3/post_history',
                  body: {
                    name: userInfo.ghid,
                    key: props.formData.key,
                    page: i
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

              totalCost += res.data.cost_money

              // 过滤掉时间范围外的置顶视频
              const preFilteringData = res.data.data.filter(item => !mid_set[item.appmsgid])
              let workAccordCount = 0
              const items = []
              for (const item of preFilteringData){
                mid_set[item.appmsgid] = true
                if (item.post_time * 1000 > min_time){
                  workAccordCount += 1  
                  items.push(item)
                }
              }
              if (items.length > 0){
                workSuccessCount += await upsertWork(items, get_time,{name: res.data.mp_nickname, ghid: res.data.mp_ghid})
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
            props.formData.message = '获取文章完成，尝试获取' + userInfoList.length + '个账号，成功操作'+userSuccessCount+'个账号，共写入' + workSuccessCount + '条文章信息，共消耗' + totalCost.toFixed(3);
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
            const url = workRecord.fields[fieldMap[tmpWorkFields.url.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_aweme_detail?key=${props.formData.key}`, {
            //     aweme_id: aweme_id.text,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/read_zan_pro',
              body: {
                url: url,
                key: props.formData.key,
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.cost_money
              const last_get_time = workRecord.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
              const last_read = workRecord.fields[fieldMap[tmpWorkFields.read.label].id] || 0
              const last_zan = workRecord.fields[fieldMap[tmpWorkFields.zan.label].id] || 0
              const last_share_num = workRecord.fields[fieldMap[tmpWorkFields.share_num.label].id] || 0
              const last_collect_num = workRecord.fields[fieldMap[tmpWorkFields.collect_num.label].id] || 0
              const last_comment_count = workRecord.fields[fieldMap[tmpWorkFields.comment_count.label].id] || 0
              const result = await updateTable(
                paneData.value.workTableId,
                [{
                  recordId: workRecordId,
                  data: {
                    read: res.data.data.read,
                    zan: res.data.data.zan,
                    looking: res.data.data.looking,
                    share_num: res.data.data.share_num,
                    collect_num: res.data.data.collect_num,
                    comment_count: res.data.data.comment_count,
                    read_diff: res.data.data.read - last_read,
                    zan_diff: res.data.data.zan - last_zan,
                    share_num_diff: res.data.data.share_num - last_share_num,
                    collect_num_diff: res.data.data.collect_num - last_collect_num,
                    comment_count_diff: res.data.data.comment_count - last_comment_count,
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
            props.formData.message = '更新文章完成, 共尝试更新'+recordIdList.length+'条, 成功'+successCount+'条, 消耗'+totalCost.toFixed(3);
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
        <el-radio :label="1">获取文章数据</el-radio>
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
          创建公众号文章表空模板
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
          创建公众号账号表空模板
      </el-button>
    </el-form-item>


    <el-form-item 
      :label="'公众号文章表'"
      v-show="paneData.getDataType !== 0"
    >
      <TableSelect v-model="paneData.workTableId" :placeholder="'未选自动创建'" />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-radio-group v-model="paneData.getWorksType" style="display: flex;">
        <el-radio :label="1">根据公众号名称或id获取</el-radio>
        <el-radio :label="0">根据账号表获取</el-radio>
      </el-radio-group>
    </el-form-item>


    <el-form-item 
      :label="'公众号账号表'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType === 0"
    >
      <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择公众号账号表'" />
    </el-form-item>


    <el-form-item
      :label="'公众号名称'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType !== 0"
    >
      <el-input
        v-model="paneData.name"
        :placeholder="'请输入公众号名称或id'"
      />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType === 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.name"
        @click="upsertUser"
        plain
        style="flex: 1;"
      >
        写入公众号账号数据
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
        批量更新公众号账号数据
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
        :disabled="isLocked || !formData.key || !paneData.userTableId && paneData.getWorksType === 0 || !paneData.name && paneData.getWorksType !== 0"
        @click="getRecentWorks(paneData.searchDate, paneData.getWorksType)"
        plain
        style="flex: 1;"
      >
        {{ '获取' + (paneData.searchDate > 1 ? paneData.searchDate + '天内' : '今日') + '发布文章'}}
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
        批量更新公众号文章互动数据
      </el-button>
    </el-form-item>

    <!-- <p>{{ paneData }}</p> -->
  </el-form>
</template>

<style scoped>
</style>