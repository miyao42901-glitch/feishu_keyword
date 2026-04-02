<script>
  import { ref, computed } from 'vue';
  import { useI18n } from 'vue-i18n';
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
  import { writeToTable, updateTable, getMaxCreateTimeByUser } from '@/utils/tableHelper'
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
      const { t } = useI18n();
      function userFields() {
        return {
          nickname: { label: t('v2Form.userFields.nickname'), fieldType: FieldType.Text, isPrimary: true},
          username: { label: t('v2Form.userFields.username'), fieldType: FieldType.Text, },
          signature: { label: t('v2Form.userFields.signature'), fieldType: FieldType.Text, },
          get_work_flag: {
            label: t('v2Form.userFields.get_work_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('v2Form.options.work.unknow'),
              fail: t('v2Form.options.work.fail'),
              success: t('v2Form.options.work.success'),
            },
          },
          fail_reason: { label: t('v2Form.userFields.fail_reason'), fieldType: FieldType.Text, },
        }
      }

      function workFields(linkTableId = '') {
        return {
          title: { label: t('v2Form.workFields.title'), fieldType: FieldType.Text, isPrimary: true},
          user_link: {
            label: t('v2Form.workFields.user_link'),
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          object_id: { label: t('v2Form.workFields.object_id'), fieldType: FieldType.Text, },
          export_id: { label: t('v2Form.workFields.export_id'), fieldType: FieldType.Text, },
          publish_time: { label: t('v2Form.workFields.publish_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          video_play_len: { label: t('v2Form.workFields.video_play_len'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          like_count: { label: t('v2Form.workFields.like_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          fav_count: { label: t('v2Form.workFields.fav_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          forward_count: { label: t('v2Form.workFields.forward_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: t('v2Form.workFields.comment_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          download_url: { label: t('v2Form.workFields.download_url'), fieldType: FieldType.Url, },
          last_get_time: { label: t('v2Form.workFields.last_get_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: t('v2Form.workFields.get_interaction_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('v2Form.options.interaction.unknow'),
              fail: t('v2Form.options.interaction.fail'),
              success: t('v2Form.options.interaction.success'),
            },
          },
          fail_reason: { label: t('v2Form.workFields.fail_reason'), fieldType: FieldType.Text, },
        }
      }
      
      const alertList = computed(() => ({
        0: { title: t('v2Form.alerts.template') },
        1: { title: t('v2Form.alerts.duplicate') },
      }))
      
      const alterShow = ref({
        0: true,
        1: true,
      })

      const dateRange = ref([1,3,7,15,30])

      const paneData = ref({
        v2_name: null,
        userTableId: null,
        workTableId: null,
        searchDate: 3,
        useTimeCut: true,
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
            timestamp + '视频号账号'
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              workFields(res1.data.tableId),
              timestamp + '视频号视频'
            );
            if (res2.success) {
              paneData.value.userTableId = res1.data.tableId
              paneData.value.workTableId = res2.data.tableId
            }
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('v2Form.messages.operationFailed', { error: error.message || t('v2Form.messages.unknownError') });
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
            props.formData.message = t('v2Form.messages.addUserSuccess', { price: res.data.cost });
            props.formData.messageType = 'success';
          }
          else{
            props.formData.message = t('v2Form.messages.operationFailed', { error: res.data.msg || t('v2Form.messages.unknownError') });
            props.formData.messageType = 'error';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('v2Form.messages.operationFailed', { error: error.message || t('v2Form.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }


      const getRecentWorks = async(maxDay = 1, timeCut = true) => {
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

            let user_cut_time = min_time
            if (timeCut){
              user_cut_time = await getMaxCreateTimeByUser(
                paneData.value.workTableId,
                user_record,
                workFields(),
                'user_link',
                'publish_time',
                min_time
              );
            }

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
                    fail_reason: res.data.msg || t('v2Form.messages.unknownError'),
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
                fav_count: item.fav_count,
                like_count: item.like_count,
                forward_count: item.forward_count,
                comment_count: item.comment_count,
                video_play_len: item.video_play_len,
                user_link: [user_record],
                last_get_time: get_time,
                get_interaction_flag: 'success',
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
                  get_work_flag: 'success',
                  fail_reason: '',
                }
              };

              if (dataList.length === 0 || dataList.length < res.data.object.length || res.data.continue_flag === 0){
                break
              }
            }
          }
          
          // 将嵌套的 totalData 结构展平为数组，只包含 totalLastTime 中为 success 的记录 recordId
          const flatData = Object.entries(totalData)
            // .filter(([recordId]) => totalLastTime[recordId].data.get_work_flag === 'success')
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
            props.formData.message = t('v2Form.messages.getWorksSuccess', { total: recordIdList.length, success: successCount, new: flatData.length, price: totalCost.toFixed(2) });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('v2Form.messages.operationFailed', { error: error.message || t('v2Form.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getWorksInteract = async(type = 9) => {
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
              type: type,
            })
            
            // 构建 updateTable 所需的格式
            const updateItem = { recordId: work_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
              successCount += 1
              totalCost += res.data.cost
              lastRemainMoney = res.data.remain_money
              switch(type){
                case 9:
                  updateItem.data = {
                    fav_count: res.data.count_info.fav_count,
                    like_count: res.data.count_info.like_count,
                    forward_count: res.data.count_info.forward_count,
                    comment_count: res.data.count_info.comment_count,
                    last_get_time: get_time,
                    get_interaction_flag: 'success',
                    fail_reason: '',
                  }
                case 3:
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
                break;
              }

            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                fail_reason: res.data.msg || t('v2Form.messages.unknownError'),
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
            props.formData.message = t('v2Form.messages.updateWorkSuccess', { total: recordIdList.length, success: successCount, price: totalCost.toFixed(2) });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('v2Form.messages.operationFailed', { error: error.message || t('v2Form.messages.unknownError') });
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
        alterShow,
        dateRange,
        addTableTemplate,
        addUser,
        getRecentWorks,
        getWorksInteract,
        t,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="120px">

    <el-form-item v-if="alterShow[0]" label-width="null">
      <el-alert
        :title="alertList[0].title"
        type="primary"
        show-icon
        @close="() => alterShow[0] = false"
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="t('v2Form.tooltips.generateTemplate')" 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked"
          @click="addTableTemplate"
          plain
          style="flex: 1;"
        >
          {{ t('v2Form.form.generateTemplate') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('v2Form.form.userTable')"
    >
      <TableSelect v-model="paneData.userTableId" />
    </el-form-item>

    <el-form-item
      :label="t('v2Form.form.v2Name')"
    >
      <el-input 
        v-model="paneData.v2_name"
        :placeholder="t('v2Form.form.v2NamePlaceholder')"  
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.v2_name || 
        !paneData.userTableId ? t('v2Form.tooltips.addUser') : t('v2Form.form.addUser') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.v2_name || !paneData.userTableId"
          @click="addUser"
          plain
          style="flex: 1;"
        >
          {{ t('v2Form.form.addUser') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('v2Form.form.workTable')"
    >
      <TableSelect v-model="paneData.workTableId" />
    </el-form-item>

    <el-form-item :label="t('v2Form.form.dateLimit')">
      <el-select v-model="paneData.searchDate" :placeholder="t('v2Form.form.dateLimitPlaceholder')">
        <el-option v-for="item in dateRange" :key="item" :label="item > 1 ? item + t('v2Form.form.days') : t('v2Form.form.today')" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null">
      <el-radio-group v-model="paneData.useTimeCut">
        <el-radio :label="false">{{ t('v2Form.form.allInDate') }}</el-radio>
        <el-radio :label="true">{{ t('v2Form.form.newInDate') }}</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? t('v2Form.tooltips.getWorks') : t('v2Form.form.getWorks') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.userTableId || !paneData.workTableId"
          @click="getRecentWorks(paneData.searchDate, paneData.useTimeCut)"
          plain
          style="flex: 1;"
        >
          {{ t('v2Form.form.getWorks', { days: paneData.searchDate > 1 ? paneData.searchDate + t('v2Form.form.days') : t('v2Form.form.today') }) }}
        </el-button>
      </el-tooltip>
    </el-form-item>


    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.workTableId ? t('v2Form.tooltips.updateWorkInteraction') : '更新视频互动信息' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.workTableId"
          @click="getWorksInteract(9)"
          plain
          style="flex: 1;"
        >
          {{ t('v2Form.form.updateWorkInteraction') }}
        </el-button>
      </el-tooltip>
    </el-form-item>
    
    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.workTableId ? t('v2Form.tooltips.updateWorkInteraction') : '更新视频互动信息' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.workTableId"
          @click="getWorksInteract(3)"
          plain
          style="flex: 1;"
        >
          {{ t('v2Form.form.updateWorkInteractionWithDownload') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item v-if="alterShow[1]" label-width="null">
      <el-alert
        :title="alertList[1].title"
        type="primary"
        show-icon
        @close="() => alterShow[1] = false"
      />
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