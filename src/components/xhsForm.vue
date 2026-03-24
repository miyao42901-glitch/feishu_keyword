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
          nickname: { label: '小红书用户名', fieldType: FieldType.Text, isPrimary: true},
          user_id: { label: '用户id', fieldType: FieldType.Text, },
          gender: { 
            label: '性别', 
            fieldType: FieldType.SingleSelect, 
            options: 
            { 
              0: '男', 
              1: '女' 
            } 
          },
          desc: { label: '简介', fieldType: FieldType.Text, },
          follows: { label: '关注', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fans: { label: '粉丝', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          interaction: { label: '获赞与收藏', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          last_get_time: { label: '用户数据更新时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: '获取互动数标志', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过互动数',
              fail: '上次获取互动数失败',
              success: '上次获取互动数成功',
            },
          },
          get_time_cut: { label: '获取笔记截至时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_work_flag: {
            label: '获取笔记标志', 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: '未获取过笔记',
              fail: '上次获取笔记失败',
              success: '上次获取笔记成功',
            },
          },
        }
      }

      function workFields(linkTableId = '') {
        return {
          display_title: { label: '笔记标题', fieldType: FieldType.Text, isPrimary: true},
          user_link: {
            label: '笔记作者',
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          note_id: { label: '笔记id', fieldType: FieldType.Text, },
          xsec_token: { label: '小红书token', fieldType: FieldType.Text, },
          time: { label: '笔记创建时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          desc: { label: '笔记描述', fieldType: FieldType.Text, },
          liked_count: { label: '点赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collected_count: { label: '收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comments_count: { label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          shared_count: { label: '分享数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          type: { 
            label: '笔记类型',
            fieldType: FieldType.SingleSelect,
            options: 
             { 
               normal: '普通笔记',
               video: '视频',
             } 
            },
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
        }
      }

      const paneData = ref({
        user_id: null,
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
            '小红书账号数据表模板' + timestamp
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              workFields(res1.data.tableId),
              '小红书笔记数据表模板' + timestamp
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
          const res = await pluginAPI.post(`/xhs/user_detail`, {
              user_id: paneData.value.user_id,
            },
            {
              headers: {
                'X-API-Key': props.formData.key,
              },
            }
          )

          if (res && res.data) {
            if(res.data.code === 0){

              const interactionsObj = {};
              if (res.data.data.interactions && Array.isArray(res.data.data.interactions)) {
                res.data.data.interactions.forEach(item => {
                  if (item.type && item.count !== undefined) {
                    interactionsObj[item.type] = parseInt(item.count);
                  }
                });
              }

              console.log(interactionsObj)
              
              const result = await writeToTable(
                paneData.value.userTableId,
                [{...res.data.data.basic_info,
                  ...interactionsObj,
                  user_id: paneData.value.user_id,
                  last_get_time: get_time, 
                  get_interaction_flag: 'success',
                  get_work_flag: 'unknow',
                }],
                userFields(),
              );
            }
            else{
              props.formData.message = '操作失败: ' + (res.data.msg || '未知错误');
              props.formData.messageType = 'error';
            }
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败: ' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const updateUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const userTable = await bitable.base.getTable(paneData.value.userTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId)

          const fieldList = await userTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const user_fields = userFields()
          const totalInteract = []
          for (const user_recordId of recordIdList){
            const userRecord = await userTable.getRecordById(user_recordId);
            const user_id = userRecord.fields[fieldMap[user_fields.user_id.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/xhs/user_detail`, {
                user_id: user_id.text,
              },
              {
                headers: {
                  'X-API-Key': props.formData.key,
                },
              }
            )

            // 构建 updateTable 所需的格式
            const updateItem = { recordId: user_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {

              const interactionsObj = {};
              if (res.data.interactions && Array.isArray(res.data.interactions)) {
                res.data.interactions.forEach(item => {
                  if (item.type && item.count !== undefined) {
                    interactionsObj[item.type] = item.count;
                  }
                });
              }

              updateItem.data = {
                ...res.data.basic_info, 
                ...interactionsObj,
                last_get_time: get_time,
                get_interaction_flag: 'success',
              }

            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
              }
            }
            
            totalInteract.push(updateItem);
          }
          
          await updateTable(
            paneData.value.userTableId,
            totalInteract,
            userFields()
          )
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
            const user_id = userRecord.fields[fieldMap[user_fields.user_id.label].id][0]
            const user_cut_time = Math.max(userRecord.fields[fieldMap[user_fields.get_time_cut.label].id] || min_time, min_time)

            // let new_cut_time = Math.max(user_cut_time, Date.now())
            // console.log(user_cut_time)
            let new_cut_time = user_cut_time
            let max_cursor = ""
            let i = 0
            while(true){
              i += 1
              const get_time = Date.now()

              const res = await pluginAPI.post(`/xhs/user_post`, {
                  user_id: user_id.text,
                  cursor: max_cursor,
                },
                {
                  headers: {
                    'X-API-Key': props.formData.key,
                  },
                }
              )

              if (!(res && res.data && res.data.code === 0)) {
                totalLastTime[user_record] = {
                  recordId: user_record, 
                  data: {
                    get_work_flag: 'fail',
                  }
                };
                break
              }

              max_cursor = res.data.cursor

              const dataList = res.data.notes
              .filter(item => getTimeFromNoteId(item.note_id) > user_cut_time)
              .map(item => ({
                note_id: item.note_id,
                type: item.type,
                display_title: item.display_title,
                like_count: item.interact_info.like_count,
                time: getTimeFromNoteId(item.note_id), 
                xsec_token: item.xsec_token,
                user_link: [user_record],
                get_interaction_flag: 'unknow',
              }))

              new_cut_time = Math.max(...dataList.map(item => item.time), new_cut_time)
            // console.log(new_cut_time)

              // 将数据添加到对象中，第一层以 recordId 为键，第二层以 note_id 为键
              dataList.forEach(item => {
                if (item.note_id) {
                  if (!totalData[user_record]) {
                    totalData[user_record] = {};
                  }
                  totalData[user_record][item.note_id] = item;
                }
              });
              
              // 将数据添加到对象中，使用 user_record 作为 key
              totalLastTime[user_record] = {
                recordId: user_record, 
                data: {
                  get_time_cut: new_cut_time,
                  get_work_flag: 'success',
                }
              };

              if (dataList.length === 0 || res.data.hasMore === false){
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
            const articleRecord = await workTable.getRecordById(work_recordId);
            const note_id = articleRecord.fields[fieldMap[work_fields.note_id.label].id][0]
            const xsec_token = articleRecord.fields[fieldMap[work_fields.xsec_token.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/xhs/note_detail`, {
                note_id: note_id.text,
                xsec_token: xsec_token.text,
              },
              {
                headers: {
                  'X-API-Key': props.formData.key,
                },
              }
            )
            
            // 构建 updateTable 所需的格式
            const updateItem = { recordId: work_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
                updateItem.data = {
                liked_count: res.data.note_list.like_count,
                comments_count: res.data.note_list.comments_count,
                collected_count: res.data.note_list.collected_count,
                shared_count: res.data.note_list.shared_count,
                last_get_time: get_time,
                get_interaction_flag: 'success',
              }
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
              }
            }
            
            totalInteract.push(updateItem);
          }
          
          await updateTable(
            paneData.value.workTableId,
            totalInteract,
            workFields()
          )
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = '操作失败: ' + (error.message || '未知错误');
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getTimeFromNoteId = (note_id) => {
        if (!note_id || typeof note_id !== 'string' || note_id.length < 8) {
          return 0;
        }
        try {
          // 提取前 8 位 16 进制字符串
          const hexTimestamp = note_id.substring(0, 8);
          const seconds = parseInt(hexTimestamp, 16);
          return seconds * 1000;
        } catch (error) {
          console.error('转换 note_id 时间戳失败:', error);
          return 0;
        }
      }

      return {
        paneData,
        addTableTemplate,
        addUser,
        updateUser,
        getRecentWorks,
        getWorksInteract,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="120px">
    <el-form-item 
      label="用户数据表"
    >
      <TableSelect v-model="paneData.userTableId" />
    </el-form-item>

    <el-form-item 
      label="笔记数据表"
    >
      <TableSelect v-model="paneData.workTableId" />
    </el-form-item>

    <el-form-item
      label="小红书用户id"
    >
      <el-input 
        v-model="paneData.user_id"
        placeholder="请输入小红书用户id"  
      />
    </el-form-item>
    
    <el-form-item label-width="null">
      <el-alert
        title="建议使用模板"
        type="primary"
        class="item-section"
        show-icon
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="'生成一对关联的小红书用户数据表空模板、笔记数据表空模板，修改笔记数据表的笔记作者字段可以设置关联的用户数据表'" 
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
        :content="isLocked || !formData.key || !paneData.user_id || 
        !paneData.userTableId ? '需要key、用户id、用户数据表' : '添加用户' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.user_id || !paneData.userTableId"
          @click="addUser"
          plain
          style="flex: 1;"
        >
          添加小红书用户
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      
      <el-tooltip 
        :content="isLocked || !formData.key || 
        !paneData.userTableId ? '需要key、用户数据表' : '更新小红书用户数据' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          size="large" 
          :disabled="isLocked || !formData.key || !paneData.userTableId"
          @click="updateUser"
          plain
          style="flex: 1;"
        >
          更新小红书用户数据  
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? '需要key、用户数据表、笔记数据表' : '获取今日发布笔记' " 
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
          获取今日发布笔记
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? '需要key、用户数据表、笔记数据表' : '获取近期最多3天笔记' " 
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
          获取近期最多3天笔记
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? '需要key、用户数据表、笔记数据表' : '获取近期最多10天笔记' " 
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
          获取近期最多10天笔记
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.workTableId ? '需要key、用户数据表、笔记数据表' : '更新笔记互动信息' " 
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
          更新笔记互动信息
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