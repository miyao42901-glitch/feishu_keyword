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
          user_name: { label: t('ksForm.userFields.user_name'), fieldType: FieldType.Text, isPrimary: true},
          user_id: { label: t('ksForm.userFields.user_id'), fieldType: FieldType.Text, },
          eid: { label: t('ksForm.userFields.eid'), fieldType: FieldType.Text, },
          kwaiId: { label: t('ksForm.userFields.kwaiId'), fieldType: FieldType.Text, },
          user_text: { label: t('ksForm.userFields.user_text'), fieldType: FieldType.Text, },
          fan: { label: t('ksForm.userFields.fan'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          follow: { label: t('ksForm.userFields.follow'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          photo: { label: t('ksForm.userFields.photo'), fieldType: FieldType.Text, },
          cityName: { label: t('ksForm.userFields.cityName'), fieldType: FieldType.Text, },
          shareLink: { label: t('ksForm.userFields.shareLink'), fieldType: FieldType.Url, },
          last_get_time: { label: t('ksForm.workFields.last_get_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: t('ksForm.userFields.get_interaction_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('ksForm.options.interaction.unknow'),
              fail: t('ksForm.options.interaction.fail'),
              success: t('ksForm.options.interaction.success'),
            },
          },
          interaction_fail_reason: { label: t('ksForm.userFields.interaction_fail_reason'), fieldType: FieldType.Text, },
          get_work_flag: {
            label: t('ksForm.userFields.get_work_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('ksForm.options.work.unknow'),
              fail: t('ksForm.options.work.fail'),
              success: t('ksForm.options.work.success'),
            },
          },
          work_fail_reason: { label: t('ksForm.userFields.work_fail_reason'), fieldType: FieldType.Text, },
        }
      }

      function workFields(linkTableId = '') {
        return {
          caption: { label: t('ksForm.workFields.caption'), fieldType: FieldType.Text, isPrimary: true},
          user_link: {
            label: t('ksForm.workFields.user_link'),
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          photo_id: { label: t('ksForm.workFields.photo_id'), fieldType: FieldType.Text, },
          eid: { label: t('ksForm.workFields.eid'), fieldType: FieldType.Text, },
          timestamp: { label: t('ksForm.workFields.timestamp'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          like_count: { label: t('ksForm.workFields.like_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          view_count: { label: t('ksForm.workFields.view_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          forward_count: { label: t('ksForm.workFields.forward_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: t('ksForm.workFields.comment_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          last_get_time: { label: t('ksForm.workFields.last_get_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: t('ksForm.workFields.get_interaction_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('ksForm.options.interaction.unknow'),
              fail: t('ksForm.options.interaction.fail'),
              success: t('ksForm.options.interaction.success'),
            },
          },
          interaction_fail_reason: { label: t('ksForm.workFields.interaction_fail_reason'), fieldType: FieldType.Text, },
        }
      }
      
      const alertList = computed(() => ({
        0: { title: t('ksForm.alerts.template') },
        1: { title: t('ksForm.alerts.duplicate') },
      }))
      
      const alterShow = ref({
        0: true,
        1: true,
      })

      const dateRange = ref([1,3,7,15,30])

      const paneData = ref({
        shareLink: null,
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
            timestamp + t('ksForm.template.userTable')
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              workFields(res1.data.tableId),
              timestamp + t('ksForm.template.workTable')
            );
            if (res2.success) {
              paneData.value.userTableId = res1.data.tableId
              paneData.value.workTableId = res2.data.tableId
            }
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ksForm.messages.operationFailed', { error: error.message || t('ksForm.messages.unknownError') });
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
          const res = await pluginAPI.post(`/fbmain/monitor/v3/ks_user_data_v2`, {
            share_text: paneData.value.shareLink,
            key: props.formData.key,
          })

          if (res && res.data && res.data.code === 0) {
            const result = await writeToTable(
              paneData.value.userTableId,
              [{
                ...res.data.data.ownerCount,
                ...res.data.data.profile,
                cityName:res.data.data.cityName,
                shareLink: paneData.value.shareLink,
                get_work_flag: 'unknow',
                get_interaction_flag: 'success',
                last_get_time: get_time,
              }],
              userFields(),
            );
            props.formData.message = t('ksForm.messages.addUserSuccess', { price: res.data.price });
            props.formData.messageType = 'success';
          }
          else{
            props.formData.message = t('ksForm.messages.operationFailed', { error: res.data.msg || t('ksForm.messages.unknownError') });
            props.formData.messageType = 'error';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ksForm.messages.operationFailed', { error: error.message || t('ksForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const updateUser = async() => {
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

          const user_fields = userFields()
          const totalInteract = []
          for (const user_recordId of recordIdList){
            const userRecord = await userTable.getRecordById(user_recordId);
            const share_link = userRecord.fields[fieldMap[user_fields.shareLink.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/fbmain/monitor/v3/ks_user_data_v2`, {
                share_text: share_link.text,
                key: props.formData.key,
            })

            // 构建 updateTable 所需的格式
            const updateItem = { recordId: user_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
              updateItem.data = {
                ...res.data.data.ownerCount,
                ...res.data.data.profile,
                cityName:res.data.data.cityName,
                shareLink: paneData.value.shareLink,
                last_get_time: get_time,
                get_interaction_flag: 'success',
                interaction_fail_reason: '',
              }
              successCount++
              totalCost += res.data.price
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                interaction_fail_reason: res.data.msg || t('ksForm.messages.unknownError'),
              }
            }
            
            totalInteract.push(updateItem);
          }
          
          await updateTable(
            paneData.value.userTableId,
            totalInteract,
            userFields()
          )

          if(recordIdList.length > 0){
            props.formData.message = t('ksForm.messages.updateUserSuccess', {
              total: recordIdList.length,
              success: successCount,
              price: totalCost.toFixed(2)
            });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ksForm.messages.operationFailed', { error: error.message || t('ksForm.messages.unknownError') });
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
            
            let user_cut_time = min_time
            if (timeCut){
              user_cut_time = await getMaxCreateTimeByUser(
                paneData.value.workTableId,
                user_record,
                workFields(),
                'user_link',
                'timestamp',
                min_time
              );
            }

            let last_buffer = ""
            let i = 0
            while(true){
              i += 1
              const get_time = Date.now()

              const res = await pluginAPI.post(`/fbmain/monitor/v3/ks_user_post_v1`, {
                uid: user_id.text,
                pcursor: last_buffer,
                key: props.formData.key,
              })

              if (!(res && res.data && res.data.code === 0)) {
                totalLastTime[user_record] = {
                  recordId: user_record, 
                  data: {
                    get_work_flag: 'fail',
                    fail_reason: res.data.msg || t('ksForm.messages.unknownError'),
                  }
                };
                break
              }

              last_buffer = res.data.data.pcursor
              totalCost += res.data.price
              
              const preProcessingData = res.data.data.feeds ? res.data.data.feeds : []

              const dataList = preProcessingData
              .filter(item => item.timestamp > user_cut_time)
              .map(item => {
                // Extract photoId from share_info
                let photoIdFromShareInfo = '';
                if (item.share_info) {
                  const params = new URLSearchParams(item.share_info);
                  photoIdFromShareInfo = params.get('photoId') || '';
                }
                return {
                  caption: item.caption,
                  photo_id: item.photo_id,
                  eid: photoIdFromShareInfo,
                  timestamp: item.timestamp,
                  like_count: item.like_count,
                  view_count: item.view_count,
                  forward_count: item.forward_count,
                  comment_count: item.comment_count,
                  user_link: [user_record],
                  last_get_time: get_time,
                  get_interaction_flag: 'success',
                };
              })

              // 将数据添加到对象中，第一层以 recordId 为键，第二层以 photo_id 为键
              dataList.forEach(item => {
                if (item.photo_id) {
                  if (!totalData[user_record]) {
                    totalData[user_record] = {};
                  }
                  totalData[user_record][item.photo_id] = item;
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

              if (dataList.length === 0 || dataList.length < preProcessingData.length){
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
            props.formData.message = t('ksForm.messages.getWorksSuccess', { total: recordIdList.length, success: successCount, new: flatData.length, price: totalCost.toFixed(2) });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ksForm.messages.operationFailed', { error: error.message || t('ksForm.messages.unknownError') });
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
            const eid = workRecord.fields[fieldMap[work_fields.eid.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/fbmain/monitor/v3/ks_video_detail`, {
              share_text: "https://www.kuaishou.com/short-video/" + eid.text,
              key: props.formData.key,
            })
            
            // 构建 updateTable 所需的格式
            const updateItem = { recordId: work_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
              successCount += 1
              totalCost += res.data.price
              updateItem.data = {
                caption: res.data.data[0].caption,
                like_count: res.data.data[0].likeCount,
                view_count: res.data.data[0].viewCount,
                forward_count: res.data.data[0].forwardCount,
                comment_count: res.data.data[0].commentCount,
                last_get_time: get_time,
                get_interaction_flag: 'success',
                fail_reason: '',
              }
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                fail_reason: res.data.msg || t('ksForm.messages.unknownError'),
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
            props.formData.message = t('ksForm.messages.updateWorkSuccess', { total: recordIdList.length, success: successCount, price: totalCost.toFixed(2) });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ksForm.messages.operationFailed', { error: error.message || t('ksForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      return {
        paneData,
        alertList,
        alterShow,
        dateRange,
        addTableTemplate,
        addUser,
        updateUser,
        getRecentWorks,
        getWorksInteract,
        t,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="auto">

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
        :content="t('ksForm.tooltips.generateTemplate')" 
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
          {{ t('ksForm.form.generateTemplate') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('ksForm.form.userTable')"
    >
      <TableSelect v-model="paneData.userTableId" />
    </el-form-item>

    <el-form-item
      :label="t('ksForm.form.shareLink')"
    >
      <el-input 
        v-model="paneData.shareLink"
        :placeholder="t('ksForm.form.shareLinkPlaceholder')"  
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.shareLink || 
        !paneData.userTableId ? t('ksForm.tooltips.addUser') : t('ksForm.form.addUser') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.shareLink || !paneData.userTableId"
          @click="addUser"
          plain
          style="flex: 1;"
        >
          {{ t('ksForm.form.addUser') }}
        </el-button>
      </el-tooltip>
    </el-form-item>
    
    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || 
        !paneData.userTableId ? t('ksForm.tooltips.updateUser') : t('ksForm.form.updateUser') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.userTableId"
          @click="updateUser"
          plain
          style="flex: 1;"
        >
          {{ t('ksForm.form.updateUser') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('ksForm.form.workTable')"
    >
      <TableSelect v-model="paneData.workTableId" />
    </el-form-item>

    <el-form-item :label="t('ksForm.form.dateLimit')">
      <el-select v-model="paneData.searchDate" :placeholder="t('ksForm.form.dateLimitPlaceholder')">
        <el-option v-for="item in dateRange" :key="item" :label="item > 1 ? item + t('ksForm.form.days') : t('ksForm.form.today')" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null">
      <el-radio-group v-model="paneData.useTimeCut">
        <el-radio :label="false">{{ t('ksForm.form.allInDate') }}</el-radio>
        <el-radio :label="true">{{ t('ksForm.form.newInDate') }}</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || 
        !paneData.workTableId ? t('ksForm.tooltips.getWorks') : t('ksForm.form.getWorks') " 
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
          {{ t('ksForm.form.getWorks', { days: paneData.searchDate > 1 ? paneData.searchDate + t('ksForm.form.days') : t('ksForm.form.today') }) }}
        </el-button>
      </el-tooltip>
    </el-form-item>


    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.workTableId ? t('ksForm.tooltips.updateWorkInteraction') : '更新视频互动信息' " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.workTableId"
          @click="getWorksInteract()"
          plain
          style="flex: 1;"
        >
          {{ t('ksForm.form.updateWorkInteraction') }}
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
</style>