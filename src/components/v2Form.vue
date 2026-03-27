<script>
  import { ref } from 'vue';
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
  } from 'element-plus';
  import pluginAPI from '@/utils/request'
  import { writeToTable, updateTable } from '@/utils/tableHelper'
  import TableSelect from './TableSelect.vue'

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
          nickname: { label: '视频号昵称', fieldType: FieldType.Text, isPrimary: true},
          username: { label: '视频号id', fieldType: FieldType.Text, },
          signature: { label: '简介', fieldType: FieldType.Text, },
          get_time_cut: { label: '获取视频截至时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_work_flag: {
            label: '获取视频标志', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过视频',
              fail: '上次获取视频失败',
              success: '上次获取视频成功',
            },
          },
          fail_reason: { label: '获取失败原因', fieldType: FieldType.Text, },
        }
      }

      function workFields(linkTableId = '') {
        return {
          title: { label: '视频标题', fieldType: FieldType.Text, isPrimary: true},
          user_link: {
            label: '视频号',
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          object_id: { label: '视频id', fieldType: FieldType.Text, },
          export_id: { label: '导出id', fieldType: FieldType.Text, },
          publish_time: { label: '视频发布时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          video_play_len: { label: '视频播放时长', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          like_count: { label: '点赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fav_count: { label: '喜欢数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          forward_count: { label: '转发数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          download_url: { label: '视频下载地址', fieldType: FieldType.Url, },
          last_get_time: { label: '互动数据更新时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: '获取互动数标志', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过互动数',
              fail: '上次获取互动数失败',
              success: '上次获取互动数成功',
            },
          },
          fail_reason: { label: '获取失败原因', fieldType: FieldType.Text, },
        }
      }
      
      const alertList = ref([
        { title: '建议使用模板数据表' },
        { title: '对于数据重复的问题，推荐使用插件【删除重复数据】处理重复数据' },
        { title: '请注意账号数据表中的【获取视频截至时间】字段，不会获取【获取视频截至时间】之前的用户发布的视频。可以手动修改此字段以获取更早的视频数据，但有可能在视频数据表中写入重复数据。' }
      ])

      const paneData = ref({
        v2_name: null,
        userTableId: null,
        workTableId: null,
      })

      const addTableTemplate = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const timestamp = Date.now()
          const res1 = await writeToTable(
            null,
            [],
            userFields(),
            '视频号账号数据表模板' + timestamp
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              workFields(res1.data.tableId),
              '视频号视频数据表模板' + timestamp
            );
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败: ' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const addUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const get_time = Date.now()
          const res = await pluginAPI.post(`/fbmain/monitor/v3/wxvideo`, {
            keywords: paneData.value.v2_name,
            type: 6,
            key: props.formData.key,
          })

          if (res && res.data && res.data.code === 0) {
            const result = await writeToTable(
              paneData.value.userTableId,
              [{...res.data.v2_info_list.contact,
                get_work_flag: 'unknow',
              }],
              userFields(),
            );
            props.formData.message = '新增账户数据完成，消耗：' + res.data.cost;
            props.formData.messageType = 'success';
          }
          else{
            props.formData.message = '操作失败: ' + (res.data.msg || '未知错误');
            props.formData.messageType = 'error';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败: ' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const getRecentWorks = async(maxDay = 1) => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let totalCost = 0
          let lastRemainMoney = 0

          const searchDays = typeof maxDay === 'number' && !isNaN(maxDay) ? Math.min(30, Math.max(1, Math.floor(maxDay))) : 1
          const date = new Date()
          date.setHours(0, 0, 0, 0)
          date.setDate(date.getDate() - (searchDays - 1))
          const min_time = date.getTime()
          
          const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId)
          const userTable = await bitable.base.getTable(paneData.value.userTableId)

          const fieldList = await userTable.getFieldList()
          const fieldMap = {};  
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }
          const user_fields = userFields()

          const totalData = {}
          const totalLastTime = {}
          for (const user_record of recordIdList){
            const userRecord = await userTable.getRecordById(user_record);
            const v2_name = userRecord.fields[fieldMap[user_fields.username.label].id][0]
            const user_cut_time = Math.max(userRecord.fields[fieldMap[user_fields.get_time_cut.label].id] || min_time, min_time)

            // let new_cut_time = Math.max(user_cut_time, Date.now())
            // console.log(user_cut_time)
            let new_cut_time = user_cut_time
            let last_buffer = ""
            let i = 0
            while(true){
              i += 1
              const get_time = Date.now()

              const res = await pluginAPI.post(`/fbmain/monitor/v3/wxvideo`, {
                v2_name: v2_name.text,
                type: 1,
                last_buffer: last_buffer,
                key: props.formData.key,
              })

              if (!(res && res.data && res.data.code === 0)) {
                totalLastTime[user_record] = {
                  recordId: user_record, 
                  data: {
                    get_work_flag: 'fail',
                    fail_reason: res.data.msg || '未知错误',
                  }
                };
                break
              }

              last_buffer = res.data.last_buffer
              totalCost += res.data.cost
              lastRemainMoney = res.data.remain_money

              const dataList = res.data.object
              .filter(item => getTimeFromStr(item.publish_time) > user_cut_time)
              .map(item => ({
                object_id: item.object_id,
                export_id: item.export_id,
                title: item.title,
                publish_time: getTimeFromStr(item.publish_time),
                // fav_count: item.fav_count,
                // like_count: item.like_count,
                // forward_count: item.forward_count,
                // comment_count: item.comment_count,
                video_play_len: item.video_play_len,
                user_link: [user_record],
                get_interaction_flag: 'unknow',
              }))

              new_cut_time = Math.max(...dataList.map(item => item.publish_time), new_cut_time)
            // console.log(new_cut_time)

              // 将数据添加到对象中，第一层以 recordId 为键，第二层以 object_id 为键
              dataList.forEach(item => {
                if (item.object_id) {
                  if (!totalData[user_record]) {
                    totalData[user_record] = {};
                  }
                  totalData[user_record][item.object_id] = item;
                }
              });
              
              // 将数据添加到对象中，使用 user_record 作为 key
              totalLastTime[user_record] = {
                recordId: user_record, 
                data: {
                  get_time_cut: new_cut_time,
                  get_work_flag: 'success',
                  fail_reason: '',
                }
              };

              if (dataList.length === 0 || res.data.continue_flag === 0){
                break
              }
            }
          }
          
          // 将嵌套的 totalData 结构展平为数组，只包含 totalLastTime 中为 success 的记录 recordId
          const flatData = Object.entries(totalData)
            .filter(([recordId]) => totalLastTime[recordId].data.get_work_flag === 'success')
            .flatMap(([_, recordData]) => Object.values(recordData));
          
          await writeToTable(
            paneData.value.workTableId,
            flatData,
            workFields(), 
          );
          
          await updateTable(
            paneData.value.userTableId,
            Object.values(totalLastTime),
            userFields()
          )
          
          if(recordIdList.length > 0){
            const successCount = Object.values(totalLastTime).filter(item => item.data.get_work_flag === 'success').length;
            props.formData.message = '获取视频数据完成，共操作' + recordIdList.length + '条账户数据，成功操作' +
              successCount + '条账户数据，新增' + flatData.length + '条视频数据，消耗：' + totalCost.toFixed(2);
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败: ' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getWorksInteract = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let successCount = 0
          let totalCost = 0
          let lastRemainMoney = 0

          const workTable = await bitable.base.getTable(paneData.value.workTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.workTableId)

          const fieldList = await workTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const work_fields = workFields()
          const totalInteract = []
          for (const work_recordId of recordIdList){
            const workRecord = await workTable.getRecordById(work_recordId);
            const object_id = workRecord.fields[fieldMap[work_fields.object_id.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/fbmain/monitor/v3/wxvideo`, {
              object_id: object_id.text,
              key: props.formData.key,
              type: 3,
            })
            
            // 构建 updateTable 所需的格式
            const updateItem = { recordId: work_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
              successCount += 1
              totalCost += res.data.cost
              lastRemainMoney = res.data.remain_money
              updateItem.data = {
                fav_count: res.data.fav_count,
                like_count: res.data.like_count,
                forward_count: res.data.forward_count,
                comment_count: res.data.comment_count,
                download_url: res.data.download_url,
                last_get_time: get_time,
                get_interaction_flag: 'success',
                fail_reason: '',
              }
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                fail_reason: res.data.msg || '未知错误',
              }
            }
            
            totalInteract.push(updateItem);
          }
          
          await updateTable(
            paneData.value.workTableId,
            totalInteract,
            workFields()
          )
          if(recordIdList.length > 0){
            props.formData.message = '获取互动数据完成，共操作' + recordIdList.length + 
              '条视频数据，成功操作' + successCount + '条视频数据，消耗：' + totalCost.toFixed(2);
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败: ' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getTimeFromStr = (dateStr) => {
        if (!dateStr) return 0;
        const date = new Date(dateStr);
        return date.getTime();
      }

      return {
        paneData,
        alertList,
        addTableTemplate,
        addUser,
        getRecentWorks,
        getWorksInteract,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="120px">
    <el-form-item 
      label="视频号数据表"
    >
      <TableSelect v-model="paneData.userTableId" />
    </el-form-item>

    <el-form-item 
      label="视频数据表"
    >
      <TableSelect v-model="paneData.workTableId" />
    </el-form-item>

    <el-form-item
      label="视频号名称"
    >
      <el-input 
        v-model="paneData.v2_name"
        placeholder="请输入视频号名称"  
      />
    </el-form-item>

    <el-form-item v-for="(item, idx) in alertList" :key="item.title" label-width="null">
      <el-alert
        :title="item.title"
        type="primary"
        show-icon
        @close="() => alertList.splice(idx, 1)"
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="'生成一对关联的视频号用户数据表空模板、视频号视频数据表空模板，修改视频数据表的【视频号】字段可以设置关联的用户数据表'" 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked"
          @click="addTableTemplate"
          plain
          style="flex: 1;"
        >
          生成数据表空模板
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.v2_name || 
        !paneData.userTableId ? '需要key、视频号名称、账号数据表' : '添加视频号' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.v2_name || !paneData.userTableId"
          @click="addUser"
          plain
          style="flex: 1;"
        >
          添加视频号
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? '需要key、账号数据表、视频数据表' : '获取今日发布视频' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.userTableId || !paneData.workTableId"
          @click="getRecentWorks(1)"
          plain
          style="flex: 1;"
        >
          获取今日发布视频
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? '需要key、账号数据表、视频数据表' : '获取近期最多3天视频' " 
        effect="dark"
        placement="top"
      >
        <el-button 
            type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.userTableId || !paneData.workTableId"
          @click="getRecentWorks(3)"
          plain
          style="flex: 1;"
        >
          获取近期最多3天视频
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? '需要key、账号数据表、视频数据表' : '获取近期最多10天视频' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.userTableId || !paneData.workTableId"
          @click="getRecentWorks(10)"
          plain
          style="flex: 1;"
        >
          获取近期最多10天视频
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.workTableId ? '需要key、视频数据表' : '更新视频互动信息' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.workTableId"
          @click="getWorksInteract"
          plain
          style="flex: 1;"
        >
          更新视频互动信息
        </el-button>
      </el-tooltip>
    </el-form-item>

    <!-- <p>{{ paneData }}</p> -->
  </el-form>
</template>

<style scoped>
  .ghForm :deep(.el-form-item__label) {
    font-size: 16px;
    color: var(--el-text-color-primary);
  }
  .ghForm :deep(.el-form-item__content), .ghForm :deep(.el-button) {
    font-size: 16px;
  }
  .ghForm :deep(.el-form-item:last-child) {
    margin-bottom: 0;
  }
</style>