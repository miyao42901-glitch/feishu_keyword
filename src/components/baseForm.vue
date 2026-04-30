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
  ElRadio,
  ElRadioGroup,
} from 'element-plus';
import pluginAPI from '@/utils/request';
import { writeToTable, updateTable, getMaxCreateTimeByUser } from '@/utils/tableHelper';
import TableSelect from './TableSelect.vue';
import '@/assets/form-styles.css';

export default {
  components: {
    ElForm,
    ElFormItem,
    ElSelect,
    ElOption,
    ElInput,
    ElButton,
    ElTooltip,
    TableSelect,
    ElAlert,
    ElRadio,
    ElRadioGroup,
  },
  props: {
    formData: {
      type: Object,
      required: true
    },
    isLocked: {
      type: Boolean,
      default: false
    },
    platformConfig: {
      type: Object,
      required: true
    }
  },
  emits: ['update:isLocked'],
  setup(props, { emit }) {
    const { t } = useI18n();

    const alertList = computed(() => ({
      0: { title: t(`${props.platformConfig.i18nPrefix}.alerts.template`) },
      1: { title: t(`${props.platformConfig.i18nPrefix}.alerts.duplicate`) },
    }));

    const alterShow = ref({
      0: true,
      1: true,
    });

    const dateRange = ref([1, 3, 7, 15, 30]);

    const paneData = ref({
      searchValue: null,
      searchValue2: null,
      userTableId: null,
      workTableId: null,
      searchDate: 3,
      useTimeCut: true,
    });

    const handleWorkTableChange = async (newWorkTableId) => {
      if (!newWorkTableId) return;
      paneData.value.userTableId = null;
      try {
        const workTable = await bitable.base.getTable(newWorkTableId);
        const fieldList = await workTable.getFieldList();
        const work_fields = props.platformConfig.workFields('');

        for (const field of fieldList) {
          const fieldName = await field.getName();
          const fieldType = await field.getType();
          if (fieldType === FieldType.SingleLink && fieldName === work_fields.user_link.label) {
            const fieldMeta = await field.getMeta();
            const property = fieldMeta.property;
            if (property && property.tableId) {
              paneData.value.userTableId = property.tableId;
              return;
            }
          }
        }
      } catch (error) {
        console.error('自动检测主表失败:', error);
      }
    };

    const addTableTemplate = async () => {
      if (props.isLocked) return;
      emit('update:isLocked', true);

      try {
        const timestamp = Date.now();
        const res1 = await writeToTable(
          null,
          [],
          props.platformConfig.userFields(),
          timestamp + t(`${props.platformConfig.i18nPrefix}.template.userTable`)
        );
        if (res1.success) {
          const res2 = await writeToTable(
            null,
            [],
            props.platformConfig.workFields(res1.data.tableId),
            timestamp + t(`${props.platformConfig.i18nPrefix}.template.workTable`)
          );
          if (res2.success) {
            paneData.value.userTableId = res1.data.tableId;
            paneData.value.workTableId = res2.data.tableId;
          }
        }
      } catch (error) {
        console.error('操作失败:', error);
        props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.operationFailed`, { error: error.message || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`) });
        props.formData.messageType = 'error';
      } finally {
        emit('update:isLocked', false);
      }
    };

    const addUser = async () => {
      if (props.isLocked) return;
      emit('update:isLocked', true);

      try {
        const get_time = Date.now();
        const requestData = props.platformConfig.buildAddUserRequest(paneData.value.searchValue, paneData.value.searchValue2, props.formData.key);
        
        const res = await pluginAPI.post('/plugin_forward', requestData);

        if (res && res.data && res.data.code === 0) {
          const userData = props.platformConfig.transformAddUserResponse(res.data, paneData.value.searchValue, paneData.value.searchValue2, get_time);
          await writeToTable(
            paneData.value.userTableId,
            [userData],
            props.platformConfig.userFields(),
          );
          props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.addUserSuccess`, { price: res.data.price || res.data.cost || 0 });
          props.formData.messageType = 'success';
        } else {
          props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.operationFailed`, { error: res.data.msg || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`) });
          props.formData.messageType = 'error';
        }
      } catch (error) {
        console.error('操作失败:', error);
        props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.operationFailed`, { error: error.message || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`) });
        props.formData.messageType = 'error';
      } finally {
        emit('update:isLocked', false);
      }
    };

    const updateUser = async () => {
      if (props.isLocked) return;
      emit('update:isLocked', true);

      try {
        let successCount = 0;
        let totalCost = 0;

        const userTable = await bitable.base.getTable(paneData.value.userTableId);
        const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId);

        const fieldList = await userTable.getFieldList();
        const fieldMap = {};
        for (const field of fieldList) {
          const fieldName = await field.getName();
          fieldMap[fieldName] = field;
        }

        const user_fields = props.platformConfig.userFields();
        const totalInteract = [];

        for (const user_recordId of recordIdList) {
          const userRecord = await userTable.getRecordById(user_recordId);
          const identifierField = userRecord.fields[fieldMap[user_fields[props.platformConfig.userIdentifierField].label].id][0];
          const get_time = Date.now();

          const requestData = props.platformConfig.buildUpdateUserRequest(identifierField?.text, props.formData.key);
          const res = await pluginAPI.post('/plugin_forward', requestData);

          const updateItem = { recordId: user_recordId, data: {} };
          if (res && res.data && res.data.code === 0) {
            updateItem.data = props.platformConfig.transformUpdateUserResponse(res.data, get_time);
            successCount++;
            totalCost += res.data.price || res.data.cost || 0;
          } else {
            updateItem.data = {
              get_interaction_flag: 'fail',
              interaction_fail_reason: res.data.msg || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`),
            };
          }

          totalInteract.push(updateItem);
        }

        await updateTable(
          paneData.value.userTableId,
          totalInteract,
          props.platformConfig.userFields()
        );

        if (recordIdList.length > 0) {
          props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.updateUserSuccess`, {
            total: recordIdList.length,
            success: successCount,
            price: totalCost.toFixed(2)
          });
          props.formData.messageType = 'success';
        }
      } catch (error) {
        console.error('操作失败:', error);
        props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.operationFailed`, { error: error.message || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`) });
        props.formData.messageType = 'error';
      } finally {
        emit('update:isLocked', false);
      }
    };

    const getRecentWorks = async (maxDay = 1, timeCut = true) => {
      if (props.isLocked) return;
      emit('update:isLocked', true);

      try {
        let totalCost = 0;

        const searchDays = typeof maxDay === 'number' && !isNaN(maxDay) ? Math.min(30, Math.max(1, Math.floor(maxDay))) : 1;
        const date = new Date();
        date.setHours(0, 0, 0, 0);
        date.setDate(date.getDate() - (searchDays - 1));
        const min_time = date.getTime();

        const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId);
        const userTable = await bitable.base.getTable(paneData.value.userTableId);

        const fieldList = await userTable.getFieldList();
        const fieldMap = {};
        for (const field of fieldList) {
          const fieldName = await field.getName();
          fieldMap[fieldName] = field;
        }
        const user_fields = props.platformConfig.userFields();

        const totalData = {};
        const totalLastTime = {};

        for (const user_record of recordIdList) {
          const userRecord = await userTable.getRecordById(user_record);
          const identifierField = userRecord.fields[fieldMap[user_fields[props.platformConfig.userIdentifierField].label].id][0];

          let user_cut_time = min_time;
          if (timeCut) {
            user_cut_time = await getMaxCreateTimeByUser(
              paneData.value.workTableId,
              user_record,
              props.platformConfig.workFields(),
              'user_link',
              props.platformConfig.workTimeField,
              min_time
            );
          }

          const fetchResult = await props.platformConfig.fetchWorks(
            identifierField?.text,
            user_cut_time,
            searchDays,
            props.formData.key,
            t,
            props.platformConfig.i18nPrefix
          );

          totalCost += fetchResult.totalCost;

          fetchResult.dataList.forEach(item => {
            item.user_link = [user_record];
            const uniqueKey = item[props.platformConfig.workUniqueKey];
            if (uniqueKey) {
              if (!totalData[user_record]) {
                totalData[user_record] = {};
              }
              totalData[user_record][uniqueKey] = item;
            }
          });

          totalLastTime[user_record] = {
            recordId: user_record,
            data: fetchResult.statusData
          };
        }

        const flatData = Object.entries(totalData)
          .flatMap(([_, recordData]) => Object.values(recordData));

        await writeToTable(
          paneData.value.workTableId,
          flatData,
          props.platformConfig.workFields(),
        );

        await updateTable(
          paneData.value.userTableId,
          Object.values(totalLastTime),
          props.platformConfig.userFields()
        );

        if (recordIdList.length > 0) {
          const successCount = Object.values(totalLastTime).filter(item => item.data.get_work_flag === 'success').length;
          props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.getWorksSuccess`, {
            total: recordIdList.length,
            success: successCount,
            new: flatData.length,
            price: totalCost.toFixed(2)
          });
          props.formData.messageType = 'success';
        }
      } catch (error) {
        console.error('操作失败:', error);
        props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.operationFailed`, { error: error.message || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`) });
        props.formData.messageType = 'error';
      } finally {
        emit('update:isLocked', false);
      }
    };

    const getWorksInteract = async (extraParams = {}) => {
      if (props.isLocked) return;
      emit('update:isLocked', true);

      try {
        let successCount = 0;
        let totalCost = 0;

        const workTable = await bitable.base.getTable(paneData.value.workTableId);
        const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.workTableId);

        const fieldList = await workTable.getFieldList();
        const fieldMap = {};
        for (const field of fieldList) {
          const fieldName = await field.getName();
          fieldMap[fieldName] = field;
        }

        const work_fields = props.platformConfig.workFields();
        const totalInteract = [];

        for (const work_recordId of recordIdList) {
          const workRecord = await workTable.getRecordById(work_recordId);
          const identifierField = workRecord.fields[fieldMap[work_fields[props.platformConfig.workIdentifierField].label].id][0];
          const get_time = Date.now();

          const requestData = props.platformConfig.buildWorkInteractRequest(identifierField?.text, props.formData.key, extraParams);
          const res = await pluginAPI.post('/plugin_forward', requestData);

          const updateItem = { recordId: work_recordId, data: {} };
          if (res && res.data && res.data.code === 0) {
            successCount++;
            totalCost += res.data.price || res.data.cost || 0;
            updateItem.data = props.platformConfig.transformWorkInteractResponse(res.data, get_time, extraParams);
          } else {
            updateItem.data = {
              get_interaction_flag: 'fail',
              fail_reason: res.data.msg || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`),
            };
          }

          totalInteract.push(updateItem);
        }

        await updateTable(
          paneData.value.workTableId,
          totalInteract,
          props.platformConfig.workFields()
        );

        if (recordIdList.length > 0) {
          props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.updateWorkSuccess`, {
            total: recordIdList.length,
            success: successCount,
            price: totalCost.toFixed(2)
          });
          props.formData.messageType = 'success';
        }
      } catch (error) {
        console.error('操作失败:', error);
        props.formData.message = t(`${props.platformConfig.i18nPrefix}.messages.operationFailed`, { error: error.message || t(`${props.platformConfig.i18nPrefix}.messages.unknownError`) });
        props.formData.messageType = 'error';
      } finally {
        emit('update:isLocked', false);
      }
    };

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
      handleWorkTableChange,
      t,
      platformConfig: props.platformConfig
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
        :content="t(`${platformConfig.i18nPrefix}.tooltips.generateTemplate`)" 
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
          {{ t(`${platformConfig.i18nPrefix}.form.generateTemplate`) }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t(`${platformConfig.i18nPrefix}.form.userTable`)"
    >
      <TableSelect v-model="paneData.userTableId" />
    </el-form-item>

    <template v-for="(field, index) in platformConfig.searchFields" :key="index">
      <el-form-item
        :label="t(`${platformConfig.i18nPrefix}.form.${field.label}`)"
      >
        <el-input 
          v-model="paneData[field.model]"
          :placeholder="t(`${platformConfig.i18nPrefix}.form.${field.placeholder}`)"  
        />
      </el-form-item>
    </template>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.searchValue || !paneData.userTableId 
          ? t(`${platformConfig.i18nPrefix}.tooltips.addUser`) 
          : t(`${platformConfig.i18nPrefix}.form.addUser`) " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !paneData.searchValue || !paneData.userTableId"
          @click="addUser"
          plain
          style="flex: 1;"
        >
          {{ t(`${platformConfig.i18nPrefix}.form.addUser`) }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item v-if="platformConfig.showUpdateUser" label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId 
          ? t(`${platformConfig.i18nPrefix}.tooltips.updateUser`) 
          : t(`${platformConfig.i18nPrefix}.form.updateUser`) " 
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
          {{ t(`${platformConfig.i18nPrefix}.form.updateUser`) }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t(`${platformConfig.i18nPrefix}.form.workTable`)"
    >
      <TableSelect v-model="paneData.workTableId" @change="handleWorkTableChange" />
    </el-form-item>

    <el-form-item :label="t(`${platformConfig.i18nPrefix}.form.dateLimit`)">
      <el-select v-model="paneData.searchDate" :placeholder="t(`${platformConfig.i18nPrefix}.form.dateLimitPlaceholder`)">
        <el-option v-for="item in dateRange" :key="item" :label="item > 1 ? item + t(`${platformConfig.i18nPrefix}.form.days`) : t(`${platformConfig.i18nPrefix}.form.today`)" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null">
      <el-radio-group v-model="paneData.useTimeCut">
        <el-radio :label="false">{{ t(`${platformConfig.i18nPrefix}.form.allInDate`) }}</el-radio>
        <el-radio :label="true">{{ t(`${platformConfig.i18nPrefix}.form.newInDate`) }}</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !paneData.userTableId || !paneData.workTableId 
          ? t(`${platformConfig.i18nPrefix}.tooltips.getWorks`) 
          : t(`${platformConfig.i18nPrefix}.form.getWorks`) " 
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
          {{ t(`${platformConfig.i18nPrefix}.form.getWorks`, { days: paneData.searchDate > 1 ? paneData.searchDate + t(`${platformConfig.i18nPrefix}.form.days`) : t(`${platformConfig.i18nPrefix}.form.today`) }) }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <template v-for="(button, index) in platformConfig.interactionButtons" :key="index">
      <el-form-item label-width="null">
        <el-tooltip 
          :content="isLocked || !formData.key || !paneData.workTableId 
            ? t(`${platformConfig.i18nPrefix}.tooltips.updateWorkInteraction`) 
            : t(`${platformConfig.i18nPrefix}.form.updateWorkInteraction`) " 
          effect="dark"
          placement="top"
        >
          <el-button 
            type="primary" 
            :disabled="isLocked || !formData.key || !paneData.workTableId"
            @click="getWorksInteract(button.params)"
            plain
            style="flex: 1;"
          >
            {{ t(`${platformConfig.i18nPrefix}.form.${button.label}`) }}
          </el-button>
        </el-tooltip>
      </el-form-item>
    </template>

    <el-form-item v-if="alterShow[1]" label-width="null">
      <el-alert
        :title="alertList[1].title"
        type="primary"
        show-icon
        @close="() => alterShow[1] = false"
      />
    </el-form-item>

  </el-form>
</template>

<style scoped>
</style>