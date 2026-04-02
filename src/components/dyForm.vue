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
    ElTabs,
    ElTabPane,
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
      const { t } = useI18n();

      function dyUserFields() {
        return {
          nickname: { label: t('dyForm.userFields.nickname'), fieldType: FieldType.Text, isPrimary: true},
          sec_uid: { label: t('dyForm.userFields.sec_uid'), fieldType: FieldType.Text, },
          max_follower_count: { label: t('dyForm.userFields.max_follower_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          mplatform_followers_count: { label: t('dyForm.userFields.mplatform_followers_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          following_count: { label: t('dyForm.userFields.following_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          signature: { label: t('dyForm.userFields.signature'), fieldType: FieldType.Text, },
          total_favorited: { label: t('dyForm.userFields.total_favorited'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          last_get_time: { label: t('dyForm.userFields.last_get_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: t('dyForm.userFields.get_interaction_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('dyForm.options.interaction.unknow'),
              fail: t('dyForm.options.interaction.fail'),
              success: t('dyForm.options.interaction.success'),
            },
          },
          interaction_fail_reason: { label: t('dyForm.userFields.interaction_fail_reason'), fieldType: FieldType.Text, },
          get_vedio_flag: {
            label: t('dyForm.userFields.get_vedio_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('dyForm.options.video.unknow'),
              fail: t('dyForm.options.video.fail'),
              success: t('dyForm.options.video.success'),
            },
          },
          vedio_fail_reason: { label: t('dyForm.userFields.vedio_fail_reason'), fieldType: FieldType.Text, },
        }
      }

      function dyVedioFields(linkTableId = '') {
        return {
          caption: { label: t('dyForm.videoFields.caption'), fieldType: FieldType.Text, isPrimary: true},
          dy_link: {
            label: t('dyForm.videoFields.dy_link'),
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          aweme_id: { label: t('dyForm.videoFields.aweme_id'), fieldType: FieldType.Text, },
          vedio_url: { label: t('dyForm.videoFields.vedio_url'), fieldType: FieldType.Url, },
          create_time: { label: t('dyForm.videoFields.create_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          digg_count: { label: t('dyForm.videoFields.digg_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: t('dyForm.videoFields.comment_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_count: { label: t('dyForm.videoFields.share_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_count: { label: t('dyForm.videoFields.collect_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          last_get_time: { label: t('dyForm.videoFields.last_get_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: t('dyForm.videoFields.get_interaction_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('dyForm.options.interaction.unknow'),
              fail: t('dyForm.options.interaction.fail'),
              success: t('dyForm.options.interaction.success'),
            },
          },
          interaction_fail_reason: { label: t('dyForm.videoFields.interaction_fail_reason'), fieldType: FieldType.Text, },
        }
      }

      const alertList = computed(() => ({
        0: {title: t('dyForm.alerts.template')},
        1: {title: t('dyForm.alerts.duplicate')},
      }))

      const alterShow = ref({
        0: true,
        1: true,
      })

      const dateRange = ref([1,3,7,15,30])

      const dyData = ref({
        sec_user_id: null,
        share_text: null,
        userTableId: null,
        vedioTableId: null,
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
            dyUserFields(),
            timestamp + '抖音账号'
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              dyVedioFields(res1.data.tableId),
              timestamp + '抖音视频'
            );
            if (res2.success) {
              dyData.value.userTableId = res1.data.tableId
              dyData.value.vedioTableId = res2.data.tableId
            }
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('dyForm.messages.operationFailed', { error: error.message || t('dyForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const addDyUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const get_time = Date.now()
          const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
              sec_user_id: dyData.value.sec_user_id,
              share_text: dyData.value.share_text,
          })

          if (res && res.data && res.data.code === 0) {
            const result = await writeToTable(
              dyData.value.userTableId,
              [{...res.data.data.user, 
                get_interaction_flag: 'success',
                last_get_time: get_time,
                get_vedio_flag: 'unknow',
              }],
              dyUserFields(),
            );
            props.formData.message = t('dyForm.messages.addUserSuccess', { price: res.data.price });
            props.formData.messageType = 'success';
          }
          else{
            props.formData.message = t('dyForm.messages.operationFailed', { error: res.data.msg || t('dyForm.messages.unknownError') });
            props.formData.messageType = 'error';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('dyForm.messages.operationFailed', { error: error.message || t('dyForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const updateDyUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let successCount = 0
          let totalCost = 0
          let lastRemainMoney = 0

          const userTable = await bitable.base.getTable(dyData.value.userTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(dyData.value.userTableId)

          const fieldList = await userTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const user_fields = dyUserFields()
          const totalInteract = []
          for (const user_recordId of recordIdList){
            const userRecord = await userTable.getRecordById(user_recordId);
            const sec_user_id = userRecord.fields[fieldMap[user_fields.sec_uid.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
                sec_user_id: sec_user_id.text,
            })

            // 构建 updateTable 所需的格式
            const updateItem = { recordId: user_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
              updateItem.data = {
                ...res.data.data.user, 
                last_get_time: get_time,
                get_interaction_flag: 'success',
                interaction_fail_reason: '',
              }
              successCount++
              totalCost += res.data.price
              lastRemainMoney = res.data.remain_money
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                interaction_fail_reason: res.data.msg || t('dyForm.messages.unknownError'),
              }
            }
            
            totalInteract.push(updateItem);
          }
          
          await updateTable(
            dyData.value.userTableId,
            totalInteract,
            dyUserFields()
          )

          if(recordIdList.length > 0){
            props.formData.message = t('dyForm.messages.updateUserSuccess', {
              total: recordIdList.length,
              success: successCount,
              price: totalCost.toFixed(2)
            });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('dyForm.messages.operationFailed', { error: error.message || t('dyForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getRecentVedios = async(maxDay = 1, timeCut = true) => {
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
          
          const recordIdList = await bitable.ui.selectRecordIdList(dyData.value.userTableId)
          const userTable = await bitable.base.getTable(dyData.value.userTableId)

          const fieldList = await userTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }
          const user_fields = dyUserFields()

          const totalData = {}
          const totalLastTime = {}
          for (const user_record of recordIdList){
            const userRecord = await userTable.getRecordById(user_record);
            const sec_user_id = userRecord.fields[fieldMap[user_fields.sec_uid.label].id][0]

            let user_cut_time = min_time
            if (timeCut){
              user_cut_time = await getMaxCreateTimeByUser(
                dyData.value.vedioTableId,
                user_record,
                dyVedioFields(),
                'dy_link',
                'create_time',
                min_time
              );
            }

            // let new_cut_time = Math.max(user_cut_time, Date.now())
            // console.log(user_cut_time)
            let new_cut_time = user_cut_time
            let max_cursor = ""
            let i = 0
            while(true){
              i += 1
              const get_time = Date.now()
              const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_post?key=${props.formData.key}`, {
                  sec_user_id: sec_user_id.text,
                  max_cursor: max_cursor,
              })

              if (!(res && res.data && res.data.code === 0)) {
                totalLastTime[user_record] = {
                  recordId: user_record, 
                  data: {
                    get_vedio_flag: 'fail',
                    vedio_fail_reason: res.data.msg || t('dyForm.messages.unknownError'),
                  }
                };
                break
              }

              max_cursor = String(res.data.data.max_cursor)
              totalCost += res.data.price
              lastRemainMoney = res.data.remain_money

              const dataList = res.data.data.aweme_list
              .filter(item => item.create_time * 1000 > user_cut_time)
              .map(item => ({
                digg_count: item.statistics.digg_count,
                comment_count: item.statistics.comment_count,
                share_count: item.statistics.share_count,
                collect_count: item.statistics.collect_count,
                caption: item.caption,
                aweme_id: item.aweme_id,
                vedio_url: 'https://www.douyin.com/video/' + item.aweme_id,
                create_time: item.create_time * 1000, // 转换为毫秒级时间戳
                dy_link: [user_record],
                last_get_time: get_time,
                get_interaction_flag: 'success',
              }))

              new_cut_time = Math.max(...dataList.map(item => item.create_time), new_cut_time)
            // console.log(new_cut_time)

              // 将数据添加到对象中，第一层以 recordId 为键，第二层以 aweme_id 为键
              dataList.forEach(item => {
                if (item.aweme_id) {
                  if (!totalData[user_record]) {
                    totalData[user_record] = {};
                  }
                  totalData[user_record][item.aweme_id] = item;
                }
              });
              
              // 将数据添加到对象中，使用 user_record 作为 key
              totalLastTime[user_record] = {
                recordId: user_record, 
                data: {
                  get_vedio_flag: 'success',
                  vedio_fail_reason: '',
                }
              };

              if (dataList.length === 0 || dataList.length < res.data.data.aweme_list.length){
                break
              }
            }
          }

          
          // 将嵌套的 totalData 结构展平为数组，只包含 totalLastTime 中为 success 的记录 recordId
          const flatData = Object.entries(totalData)
            // .filter(([recordId]) => totalLastTime[recordId].data.get_vedio_flag === 'success')
            .flatMap(([_, recordData]) => Object.values(recordData));
          
          await writeToTable(
            dyData.value.vedioTableId,
            flatData,
            dyVedioFields(),
          );
          
          await updateTable(
            dyData.value.userTableId,
            Object.values(totalLastTime),
            dyUserFields()
          )

          if(recordIdList.length > 0){
            const successCount = Object.values(totalLastTime).filter(item => item.data.get_vedio_flag === 'success').length;
            props.formData.message = t('dyForm.messages.getVideosSuccess', {
              total: recordIdList.length,
              success: successCount,
              new: flatData.length,
              price: totalCost.toFixed(2)
            });
            props.formData.messageType = 'success';
          }

        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('dyForm.messages.operationFailed', { error: error.message || t('dyForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getVedioInteract = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let successCount = 0
          let totalCost = 0
          let lastRemainMoney = 0

          const vedioTable = await bitable.base.getTable(dyData.value.vedioTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(dyData.value.vedioTableId)

          const fieldList = await vedioTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const vedio_fields = dyVedioFields()
          const totalInteract = []
          for (const vedio_recordId of recordIdList){
            const articleRecord = await vedioTable.getRecordById(vedio_recordId);
            const aweme_id = articleRecord.fields[fieldMap[vedio_fields.aweme_id.label].id][0]
            const get_time = Date.now()

            const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_aweme_detail?key=${props.formData.key}`, {
                aweme_id: aweme_id.text,
            })

            // 构建 updateTable 所需的格式
            const updateItem = { recordId: vedio_recordId, data: {} };
            if (res && res.data && res.data.code === 0) {
              successCount++
              totalCost += res.data.price
              lastRemainMoney = res.data.remain_money
              updateItem.data = {
                digg_count: res.data.data.aweme_detail.statistics.digg_count,
                comment_count: res.data.data.aweme_detail.statistics.comment_count,
                share_count: res.data.data.aweme_detail.statistics.share_count,
                collect_count: res.data.data.aweme_detail.statistics.collect_count,
                last_get_time: get_time,
                get_interaction_flag: 'success',
                interaction_fail_reason: '',
              }
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                interaction_fail_reason: res.data.msg || t('dyForm.messages.unknownError'),
              }
            }
            
            totalInteract.push(updateItem);
          }
          
          await updateTable(
            dyData.value.vedioTableId,
            totalInteract,
            dyVedioFields()
          )
          
          if(recordIdList.length > 0){
            props.formData.message = t('dyForm.messages.updateVideoSuccess', {
              total: recordIdList.length,
              success: successCount,
              price: totalCost.toFixed(2)
            });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('dyForm.messages.operationFailed', { error: error.message || t('dyForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      return {
        dyData,
        alertList,
        alterShow,
        dateRange,
        addTableTemplate,
        addDyUser,
        updateDyUser,
        getRecentVedios,
        getVedioInteract,
        t
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="auto">   

    <el-form-item v-if="alterShow[0]" label-width="null" >
      <el-alert
        :title="alertList[0].title"
        type="primary"
        show-icon
        @close="() => alterShow[0] = false"
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="t('dyForm.tooltips.generateTemplate')" 
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
          {{ t('dyForm.form.generateTemplate') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('dyForm.form.userTable')"
    >
      <TableSelect v-model="dyData.userTableId" />
    </el-form-item>


    <el-form-item
      :label="t('dyForm.form.userId')"
    >
      <el-input 
        v-model="dyData.sec_user_id"
        :placeholder="t('dyForm.form.userIdPlaceholder')"  
      />
    </el-form-item>

    <el-form-item
      :label="t('dyForm.form.shareLink')"
    >
      <el-input 
        v-model="dyData.share_text"
        :placeholder="t('dyForm.form.shareLinkPlaceholder')"
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !dyData.sec_user_id && !dyData.share_text || 
        !dyData.userTableId ? t('dyForm.tooltips.addUser') : t('dyForm.form.addUser') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !dyData.sec_user_id && !dyData.share_text || !dyData.userTableId"
          @click="addDyUser"
          plain
          style="flex: 1;"
        >
          {{ t('dyForm.form.addUser') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || 
        !dyData.userTableId ? t('dyForm.tooltips.updateUser') : t('dyForm.form.updateUser') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !dyData.userTableId"
          @click="updateDyUser"
          plain
          style="flex: 1;"
        >
          {{ t('dyForm.form.updateUser') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('dyForm.form.videoTable')"
    >
      <TableSelect v-model="dyData.vedioTableId" />
    </el-form-item>

    <el-form-item :label="t('dyForm.form.dateLimit')">
      <el-select v-model="dyData.searchDate" :placeholder="t('dyForm.form.dateLimitPlaceholder')">
        <el-option v-for="item in dateRange" :key="item" :label="item > 1 ? item + t('dyForm.form.days') : t('dyForm.form.today')" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null">
      <el-radio-group v-model="dyData.useTimeCut">
        <el-radio :label="false">{{ t('dyForm.form.allInDate') }}</el-radio>
        <el-radio :label="true">{{ t('dyForm.form.newInDate') }}</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !dyData.userTableId || 
        !dyData.vedioTableId ? t('dyForm.tooltips.getVideos') : t('dyForm.form.getVideos') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !dyData.userTableId || !dyData.vedioTableId"
          @click="getRecentVedios(dyData.searchDate, dyData.useTimeCut)"
          plain
          style="flex: 1;"
        >
          {{ t('dyForm.form.getVideos', { days: dyData.searchDate > 1 ? dyData.searchDate + t('dyForm.form.days') : t('dyForm.form.today') }) }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip
        :content="isLocked || !formData.key || !dyData.vedioTableId ? t('dyForm.tooltips.updateVideoInteraction') : t('dyForm.form.updateVideoInteraction') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !dyData.vedioTableId"
          @click="getVedioInteract"
          plain
          style="flex: 1;"
        >
          {{ t('dyForm.form.updateVideoInteraction') }}
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

    <!-- <p>{{ dyData }}</p> -->
  </el-form>
</template>

<style scoped>
</style>