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
          user_id: { label: '小红书id', fieldType: FieldType.Text, isPrimary: true, },
          nickname: { label: '小红书昵称', fieldType: FieldType.Text, },
          desc: { label: '简介', fieldType: FieldType.Text, },
          fans: { label: '粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          like_collect: { label: '获赞与收藏', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fans_diff: { label: '新增粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          like_collect_diff: { label: '新增获赞与收藏', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          follows: { label: '关注数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          current_get_time: { label: '当前获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          last_get_time: { label: '上次获取时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_work_flag: {
            label: '获取笔记状态', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过',
              fail: '获取失败',
              partial_success: '部分成功',
              success: '获取成功',
            },
          },
          work_fail_reason: { label: '获取笔记失败原因', fieldType: FieldType.Text, },
        }
      }

      function workFields() {
        return {
          note_id: { label: '笔记id', fieldType: FieldType.Text, isPrimary: true, },
          title: { label: '笔记标题', fieldType: FieldType.Text, },
          desc: { label: '笔记简介', fieldType: FieldType.Text, },
          nickname: { label: '小红书昵称', fieldType: FieldType.Text, },
          user_id: { label: '小红书id', fieldType: FieldType.Text, },
          create_time: { label: '发布时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          likes: { label: '喜欢数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comments_count: { label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_count: { label: '分享数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collected_count: { label: '收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          likes_diff: { label: '新增喜欢数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comments_count_diff: { label: '新增评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_count_diff: { label: '新增分享数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collected_count_diff: { label: '新增收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
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
        userTableId: null,
        workTableId: null,
        searchRange: '1页',
        getDataType: 0,
        getWorksType: 1,
      })


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
              '小红书账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
            );
            if (tableRes.success) {
              paneData.value.userTableId = tableRes.data.tableId
            }
          }

          const get_time = Date.now()
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/xhs',
            body: {
              user_id: paneData.value.user_id,
              key: props.formData.key,
              type: 2,
              pwd: "jzl_xc"
            }
          })

          const tmpUserFields = userFields()
          if (res && res.data && res.data.code === 0) {
            const res_user_id = paneData.value.user_id
            let current_follows = 0
            let current_fans = 0
            let current_like_collect = 0
            for (const item of res.data.interactions) {
              if (item.type === 'fans') {
                current_fans = item.count
              }
              if (item.type === 'interaction') {
                current_like_collect = item.count
              }
              if (item.type === 'follows') {
                current_follows = item.count
              }
            }
            const [record, fieldMap] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.user_id.label, res_user_id)
            if (record) {
              const last_get_time = record.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_fans = record.fields[fieldMap[tmpUserFields.fans.label].id] || 0
              const last_like_collect = record.fields[fieldMap[tmpUserFields.like_collect.label].id] || 0
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: record.recordId,
                  data: {
                    user_id: res_user_id, 
                    nickname: res.data.basic_info.nickname,
                    desc: res.data.basic_info.desc,

                    fans: current_fans,
                    like_collect: current_like_collect,
                    follows: current_follows,

                    fans_diff: current_fans - last_fans,
                    like_collect_diff: current_like_collect - last_like_collect,

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
                  user_id: res_user_id, 
                  nickname: res.data.basic_info.nickname,
                  desc: res.data.basic_info.desc,

                  fans: current_fans,
                  like_collect: current_like_collect,
                  follows: current_follows,

                  current_get_time: get_time,
                  get_work_flag: 'unknow',
                }],
                tmpUserFields,
              );
            }

            
            props.formData.message = '新增小红书账号完成，消耗：' + res.data.cost
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
            const user_id = userRecord.fields[fieldMap[tmpUserFields.user_id.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
            //     sec_user_id: secUid,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/xhs',
              body: {
                user_id: user_id,
                key: props.formData.key,
                type: 2,
                pwd: "jzl_xc"
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.cost
              let current_follows = 0
              let current_fans = 0
              let current_like_collect = 0
              for (const item of res.data.interactions) {
                if (item.type === 'fans') {
                  current_fans = item.count
                }
                if (item.type === 'interaction') {
                  current_like_collect = item.count
                }
                if (item.type === 'follows') {
                  current_follows = item.count
                }
              }
              const last_get_time = userRecord.fields[fieldMap[tmpUserFields.current_get_time.label].id]
              const last_fans = userRecord.fields[fieldMap[tmpUserFields.fans.label].id] || 0
              const last_like_collect = userRecord.fields[fieldMap[tmpUserFields.like_collect.label].id] || 0
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: user_recordId,
                  data: {
                    user_id: user_id, 
                    nickname: res.data.basic_info.nickname,
                    desc: res.data.basic_info.desc,

                    fans: current_fans,
                    like_collect: current_like_collect,
                    follows: current_follows,

                    fans_diff: current_fans - last_fans,
                    like_collect_diff: current_like_collect - last_like_collect,

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
          const note_id = item.id
          const [record, fieldMap] = await getFirstRecordByField(paneData.value.workTableId, tmpWorkFields.note_id.label, note_id)
          let result = {}
          if (record) {
            const last_get_time = record.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
            const last_likes = record.fields[fieldMap[tmpWorkFields.likes.label].id] || 0
            const last_comments_count = record.fields[fieldMap[tmpWorkFields.comments_count.label].id] || 0
            const last_share_count = record.fields[fieldMap[tmpWorkFields.share_count.label].id] || 0
            const last_collected_count = record.fields[fieldMap[tmpWorkFields.collected_count.label].id] || 0
            updateData.push({
              recordId: record.recordId,
              data: {
                note_id: note_id,
                title: item.title,
                desc: item.desc,
                user_id: item.user.userid,
                nickname: item.user.nickname,
                create_time: item.create_time * 1000, // 转换为毫秒级时间戳

                likes: item.likes,
                comments_count: item.comments_count,
                share_count: item.share_count,
                collected_count: item.collected_count,

                likes_diff: item.likes - last_likes,
                comments_count_diff: item.comments_count - last_comments_count,
                share_count_diff: item.share_count - last_share_count,
                collected_count_diff: item.collected_count - last_collected_count,

                current_get_time: get_time,
                last_get_time: last_get_time,
              }
            })
          }
          else{
            insertData.push({
              note_id: note_id,
              title: item.title,
              desc: item.desc,
              user_id: item.user.userid,
              nickname: item.user.nickname,
              create_time: item.create_time * 1000, // 转换为毫秒级时间戳

              likes: item.likes,
              comments_count: item.comments_count,
              share_count: item.share_count,
              collected_count: item.collected_count,

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
              '小红书笔记' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
                url: '/fbmain/monitor/v3/xhs',
                body: {
                  user_id: userInfo.user_id,
                  type: 6,
                  cursor: max_cursor,
                  key: props.formData.key,
                  pwd: "jzl_xc",
                },
                params: {
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

              max_cursor = String(res.data.cursor)
              totalCost += res.data.cost

              // 过滤掉时间范围外的置顶视频
              let preFilteringData = res.data.notes
              if (range.type === 'date'){
                preFilteringData = res.data.notes.filter(item => item.sticky == false || item.create_time * 1000 > min_time)
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
            props.formData.message = '获取笔记完成，尝试获取' + userInfoList.length + '个账号，成功操作'+userSuccessCount+'个账号，共写入' + workSuccessCount + '条笔记信息，共消耗' + totalCost.toFixed(3);
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
            const note_id = workRecord.fields[fieldMap[tmpWorkFields.note_id.label].id][0].text
            const get_time = Date.now()

            // const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_aweme_detail?key=${props.formData.key}`, {
            //     aweme_id: aweme_id.text,
            // })

            const res = await pluginAPI.post('/plugin_forward', {
              url: '/fbmain/monitor/v3/xhs',
              body: {
                note_id: note_id,
                key: props.formData.key,
                type : 11,
                pwd: "jzl_xc"
              }
            })

            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.cost
              const last_get_time = workRecord.fields[fieldMap[tmpWorkFields.current_get_time.label].id]
              const last_likes = workRecord.fields[fieldMap[tmpWorkFields.likes.label].id] || 0
              const last_comments_count = workRecord.fields[fieldMap[tmpWorkFields.comments_count.label].id] || 0
              const last_share_count = workRecord.fields[fieldMap[tmpWorkFields.share_count.label].id] || 0
              const last_collected_count = workRecord.fields[fieldMap[tmpWorkFields.collected_count.label].id] || 0
              const result = await updateTable(
                paneData.value.workTableId,
                [{
                  recordId: workRecordId,
                  data: {
                    note_id: note_id,
                    title: res.data.note_list[0].title,
                    desc: res.data.note_list[0].desc,
                    user_id: res.data.user.id,
                    nickname: res.data.user.nickname,
                    create_time: res.data.note_list[0].create_time * 1000, // 转换为毫秒级时间戳

                    likes: res.data.note_list[0].liked_count,
                    comments_count: res.data.note_list[0].comments_count,
                    share_count: res.data.note_list[0].share_count,
                    collected_count: res.data.note_list[0].collected_count,

                    likes_diff: res.data.note_list[0].liked_count - last_likes,
                    comments_count_diff: res.data.note_list[0].comments_count - last_comments_count,
                    share_count_diff: res.data.note_list[0].shared_count - last_share_count,
                    collected_count_diff: res.data.note_list[0].collected_count - last_collected_count,

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
            props.formData.message = '更新小红书笔记完成, 共尝试更新'+recordIdList.length+'条, 成功'+successCount+'条, 消耗'+totalCost.toFixed(3);
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
        ranges,
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
        <el-radio :label="1">获取笔记数据</el-radio>
      </el-radio-group>
    </el-form-item>


    <!-- <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
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
    </el-form-item> -->


    <el-form-item 
      :label="'小红书笔记表'"
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
      :label="'小红书账号表'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType === 0"
    >
      <TableSelect v-model="paneData.userTableId" :placeholder="paneData.getDataType === 0 ? '未选自动创建' : '请选择小红书账号表'" />
    </el-form-item>


    <el-form-item
      :label="'小红书账号id'"
      v-show="paneData.getDataType === 0 || paneData.getWorksType !== 0"
    >
      <el-input 
        v-model="paneData.user_id"
        :placeholder="'请输入小红书账号id'"
      />
    </el-form-item>


    <el-form-item label-width="null" v-show="paneData.getDataType === 0">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.user_id
          ? '需要登录、填写小红书账号id' : '写入小红书账号数据' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.user_id"
          @click="upsertUser"
          plain
          style="flex: 1;"
        >
          写入小红书账号数据
        </el-button>
      </el-tooltip>
    </el-form-item>


    <el-form-item label-width="null"  v-show="paneData.getDataType === 0">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId
          ? '需要登录、选择小红书账号表' : '批量更新小红书账号数据' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.userTableId"
          @click="batchUpdateUser"
          plain
          style="flex: 1;"
        >
          批量更新小红书账号数据
        </el-button>
      </el-tooltip>
    </el-form-item>


    <el-form-item :label="'数据范围'"  v-show="paneData.getDataType !== 0">
      <el-select v-model="paneData.searchRange" :placeholder="'请选择数据范围'">
        <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId && paneData.getWorksType === 0 || !paneData.user_id && paneData.getWorksType !== 0
          ? '需要登录、选择小红书账号表或填写小红书账号id' : '获取小红书笔记数据' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.userTableId && paneData.getWorksType === 0 || !paneData.user_id && paneData.getWorksType !== 0"
          @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)"
          plain
          style="flex: 1;"
        >
          {{ '获取' + paneData.searchRange + '发布笔记'}}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null"  v-show="paneData.getDataType !== 0">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.workTableId
          ? '需要登录、选择小红书笔记表' : '批量更新小红书笔记数据' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.workTableId"
          @click="updateWorks"
          plain
          style="flex: 1;"
        >
          批量更新小红书笔记数据
        </el-button>
      </el-tooltip>
    </el-form-item>

    <!-- <p>{{ paneData }}</p> -->
  </el-form>
</template>

<style scoped>
</style>