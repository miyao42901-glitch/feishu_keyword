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
          biz: { label: '公众号标识(base64)', fieldType: FieldType.Text, isPrimary: true, },
          name: { label: '公众号名称', fieldType: FieldType.Text, },
          desc: { label: '公众号描述', fieldType: FieldType.Text, },
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
          biz: { label: '公众号biz', fieldType: FieldType.Text, },
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
        '全部': {value: 0 , type: 'all'},
      })

      const paneData = ref({
        name: null,
        biz: null,
        userTableId: null,
        workTableId: null,
        searchDate: 3,
        searchRange: '1页',
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
            url: '/fbmain/monitor/v3/avatar_type',
            body: {
              name: paneData.value.name,
              key: props.formData.key,
            },
          })

          const tmpUserFields = userFields()
          if (res && res.data && res.data.code === 0) {
            const biz = res.data.data.biz
            const [record, fieldMap] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.biz.label, biz)
            if (record) {
              const result = await updateTable(
                paneData.value.userTableId,
                [{
                  recordId: record.recordId,
                  data: {
                    biz: biz,
                    name: res.data.data.name,
                    desc: res.data.data.desc,
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
                    biz: biz,
                    name: res.data.data.name,
                    desc: res.data.data.desc,
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
                biz: userInfo.biz,
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
              biz: userInfo.biz,
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
              '公众号文章' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_')
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
            const biz_set = {}
            for (const userRecordId of recordIdList){
              const userRecord = await userTable.getRecordById(userRecordId);
              const biz = userRecord.fields[fieldMap[tmpUserFields.biz.label].id][0].text

              if (biz_set[biz]) continue
              biz_set[biz] = true
              userInfoList.push({
                recordId: userRecordId,
                biz: biz
              })
            }
          }
          else{
            userInfoList = [{ biz: paneData.value.biz }]
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
                    biz: userInfo.biz,
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

              // 过滤
              const preFilteringData = res.data.data.filter(item => !mid_set[item.appmsgid])
              let workAccordCount = 0
              const items = []
              for (const item of preFilteringData){
                mid_set[item.appmsgid] = true
                if (range.type !== 'date' || item.post_time * 1000 > min_time){
                  workAccordCount += 1  
                  items.push(item)
                }
              }
              if (items.length > 0){
                  workSuccessCount += await upsertWork(items, get_time,{biz: userInfo.biz})
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
        ranges,
        addUserTableTemplate,
        addWorkTableTemplate,
        upsertUser,
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
        <el-radio :label="1">根据公众号biz获取</el-radio>
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
      v-show="paneData.getDataType === 0"
    >
      <el-input
        v-model="paneData.name"
        :placeholder="'请输入公众号名称或id'"
      />
    </el-form-item>

    <el-form-item
      :label="'公众号biz'"
      v-show="paneData.getDataType !== 0 && paneData.getWorksType !== 0"
    >
      <el-input
        v-model="paneData.biz"
        :placeholder="'请输入公众号biz'"
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


    <el-form-item :label="'数据范围'"  v-show="paneData.getDataType !== 0">
      <el-select v-model="paneData.searchRange" :placeholder="'请选择数据范围'">
        <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null" v-show="paneData.getDataType !== 0">
      <el-button 
        type="primary" 
        :disabled="isLocked || !formData.key || !paneData.userTableId && paneData.getWorksType === 0 || !paneData.biz && paneData.getWorksType !== 0"
        @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)"
        plain
        style="flex: 1;"
      >
        {{ '获取' + paneData.searchRange + '发布文章'}}
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