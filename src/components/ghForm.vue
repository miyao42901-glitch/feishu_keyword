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
      }
    },
    emits: ['update:isLocked'],
    setup(props, { emit }) {
      const { t } = useI18n();
      function ghAccountFields() {
        return {
          name: { label: t('ghForm.userFields.name'), fieldType: FieldType.Text, isPrimary: true},
          biz: { label: t('ghForm.userFields.biz'), fieldType: FieldType.Text, },
          desc: { label: t('ghForm.userFields.desc'), fieldType: FieldType.Text, },
          get_article_flag: {
            label: t('ghForm.userFields.get_article_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('ghForm.options.article.unknow'),
              fail: t('ghForm.options.article.fail'),
              success: t('ghForm.options.article.success'),
            },
          },
          fail_reason: { label: t('ghForm.userFields.fail_reason'), fieldType: FieldType.Text, },
        }
      }

      function ghArticleFields(linkTableId = '') {
        return {
          title: { label: t('ghForm.articleFields.title'), fieldType: FieldType.Text, isPrimary: true },
          gh_link: {
            label: t('ghForm.articleFields.gh_link'),
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          url: { label: t('ghForm.articleFields.url'), fieldType: FieldType.Url, },
          post_time: { label: t('ghForm.articleFields.post_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME },},
          digest: { label: t('ghForm.articleFields.digest'), fieldType: FieldType.Text, },
          original: {
            label: t('ghForm.articleFields.original'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              0: t('ghForm.options.original.0'),
              1: t('ghForm.options.original.1'),
              2: t('ghForm.options.original.2')
            },
          },
          item_show_type: {
            label: t('ghForm.articleFields.item_show_type'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              0: t('ghForm.options.item_show_type.0'),
              5: t('ghForm.options.item_show_type.5'),
              7: t('ghForm.options.item_show_type.7'),
              8: t('ghForm.options.item_show_type.8'),
              10: t('ghForm.options.item_show_type.10'),
              11: t('ghForm.options.item_show_type.11')
            },
          },
          read: {label: t('ghForm.articleFields.read'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          zan: {label: t('ghForm.articleFields.zan'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          looking: {label: t('ghForm.articleFields.looking'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_num: {label: t('ghForm.articleFields.share_num'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_num: {label: t('ghForm.articleFields.collect_num'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: {label: t('ghForm.articleFields.comment_count'), fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          last_get_time: { label: t('ghForm.articleFields.last_get_time'), fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          get_interaction_flag: {
            label: t('ghForm.articleFields.get_interaction_flag'), 
            fieldType: FieldType.SingleSelect, 
            options: {
              unknow: t('ghForm.options.interaction.unknow'),
              fail: t('ghForm.options.interaction.fail'),
              success: t('ghForm.options.interaction.success'),
            },
          },
          fail_reason: { label: t('ghForm.articleFields.fail_reason'), fieldType: FieldType.Text, },
        }
      }

      const alertList = computed(() => ({
        0: { title: t('ghForm.alerts.template') },
        1: { title: t('ghForm.alerts.duplicate') },
      }))
      
      const alterShow = ref({
        0: true,
        1: true,
      })

      const dateRange = ref([1,3,7,15,30])

      const ghData = ref({
        ghSearchValue: null,
        selectedGhTableId: null,
        selectedArticleTableId: null,
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
            ghAccountFields(),
            timestamp + '公众号账号'
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              ghArticleFields(res1.data.tableId),
              timestamp + '公众号文章'
            );
            if (res2.success) {
              ghData.value.selectedGhTableId = res1.data.tableId
              ghData.value.selectedArticleTableId = res2.data.tableId
            }
          }
        }catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ghForm.messages.operationFailed', { error: error.message || t('ghForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const addGhAccount = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const res = await pluginAPI.post('/fbmain/monitor/v3/avatar_type', {
            name: ghData.value.ghSearchValue,
            key: props.formData.key,
          })

          if (res && res.data && res.data.code === 0) {
            const result = await writeToTable(
              ghData.value.selectedGhTableId,
              [{...res.data.data, get_article_flag: 'unknow'}],
              ghAccountFields(),
            );
            props.formData.message = t('ghForm.messages.addGhAccountSuccess');
            props.formData.messageType = 'success';
          }
          else{
            props.formData.message = t('ghForm.messages.operationFailed', { error: res.data.msg || t('ghForm.messages.unknownError') });
            props.formData.messageType = 'error';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ghForm.messages.operationFailed', { error: error.message || t('ghForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getRecentArticles = async(maxDay = 1, timeCut = true) => {
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
          
          const recordIdList = await bitable.ui.selectRecordIdList(ghData.value.selectedGhTableId)
          const accountTable = await bitable.base.getTable(ghData.value.selectedGhTableId)

          const fieldList = await accountTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }
          const ac_fields = ghAccountFields()
          
          const totalData = {}
          const totalLastTime = {}
          for (const ac_recordId of recordIdList){
            const accountRecord = await accountTable.getRecordById(ac_recordId);
            const ac_biz = accountRecord.fields[fieldMap[ac_fields.biz.label].id][0]
            let ac_cut_time = min_time
            if (timeCut){
              ac_cut_time = await getMaxCreateTimeByUser(
                ghData.value.selectedArticleTableId,
                ac_recordId,
                ghArticleFields(),
                'gh_link',
                'post_time',
                min_time
              );
            }

            // console.log(ac_name, ac_biz, ac_cut_time)
            // let new_cut_time = Math.max(ac_cut_time, Date.now())
            let new_cut_time = ac_cut_time
            if (searchDays === 1){
              const res = await pluginAPI.post('/fbmain/monitor/v3/post_condition', {
                biz: ac_biz.text,
                key: props.formData.key,
              })
              
              if (!(res && res.data && res.data.code === 0)) {
                  totalLastTime[ac_recordId] = {
                  recordId: ac_recordId, 
                  data: {
                    get_article_flag: 'fail',
                    fail_reason: res.data.msg || t('ghForm.messages.unknownError'),
                  }
                };
                  continue
                }

              totalCost += res.data.cost_money
              lastRemainMoney = res.data.remain_money

              const dataList = res.data.data
              .filter(item => item.post_time * 1000 > ac_cut_time)
              .map(item => ({
                ...item,
                post_time: item.post_time * 1000, // 转换为毫秒级时间戳
                gh_link: [ac_recordId],
              }))

              new_cut_time = Math.max(...dataList.map(item => item.post_time), new_cut_time)
              // console.log(new_cut_time)

              // 将数据添加到对象中，使用双层结构 ac_recordId -> url -> item
              dataList.forEach(item => {
                if (item.url) {
                  if (!totalData[ac_recordId]) {
                    totalData[ac_recordId] = {};
                  }
                  totalData[ac_recordId][item.url] = {...item, get_interaction_flag: 'unknow'};
                }
              });
              
              // 将数据添加到对象中，使用 ac_recordId 作为 key
              totalLastTime[ac_recordId] = {
                recordId: ac_recordId, 
                data: {
                  get_article_flag: 'success',
                  fail_reason: '',
                }
              };
            }
            else{
              let i = 0
              while(true){
                i += 1
                const res = await pluginAPI.post('/fbmain/monitor/v3/post_history', {
                  biz: ac_biz.text,
                  key: props.formData.key,
                  page: i
                })

                if (!(res && res.data && res.data.code === 0)) {
                  totalLastTime[ac_recordId] = {
                    recordId: ac_recordId, 
                    data: {
                      get_article_flag: 'fail',
                      fail_reason: res.data.msg || t('ghForm.messages.unknownError'),
                    }
                  };
                  break
                }
                
                totalCost += res.data.cost_money
                lastRemainMoney = res.data.remain_money
                
                const dataList = res.data.data
                .filter(item => item.post_time * 1000 > ac_cut_time)
                .map(item => ({
                  ...item,
                  post_time: item.post_time * 1000, // 转换为毫秒级时间戳
                  gh_link: [ac_recordId],
                  get_interaction_flag: 'unknow'
                }))

                new_cut_time = Math.max(...dataList.map(item => item.post_time), new_cut_time)
              // console.log(new_cut_time)

              // 将数据添加到对象中，使用双层结构 ac_recordId -> url -> item
                
                dataList.forEach(item => {
                  if (item.url) {
                    if (!totalData[ac_recordId]) {
                      totalData[ac_recordId] = {};
                    }
                    totalData[ac_recordId][item.url] = item;
                  }
                });
                
                // 将数据添加到对象中，使用 ac_recordId 作为 key
                totalLastTime[ac_recordId] = {
                  recordId: ac_recordId, 
                  data: {
                    get_article_flag: 'success',
                    fail_reason: '',
                  }
                };

                if (dataList.length === 0 || dataList.length < res.data.data.length || res.data.now_page >= res.data.total_page){
                  break
                }
              }
            }
          }

          // 将嵌套的 totalData 结构展平为数组，只包含 totalLastTime 中为 success 的记录 recordId
          const flatData = Object.entries(totalData)
            // .filter(([recordId]) => totalLastTime[recordId].data.get_article_flag === 'success')
            .flatMap(([_, recordData]) => Object.values(recordData));

          await writeToTable(
            ghData.value.selectedArticleTableId,
            flatData,
            ghArticleFields(ghData.value.selectedGhTableId),
          );
          
          await updateTable(
            ghData.value.selectedGhTableId,
            Object.values(totalLastTime),
            ghAccountFields()
          )
          
          if(recordIdList.length > 0){
            const successCount = Object.values(totalLastTime).filter(item => item.data.get_article_flag === 'success').length;
            props.formData.message = t('ghForm.messages.getArticlesSuccess', { total: recordIdList.length, success: successCount, new: flatData.length, price: totalCost.toFixed(2) });
            props.formData.messageType = 'success';
          }
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ghForm.messages.operationFailed', { error: error.message || t('ghForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getArticleInteract = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          let successCount = 0
          let totalCost = 0
          let lastRemainMoney = 0

          const articleTable = await bitable.base.getTable(ghData.value.selectedArticleTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(ghData.value.selectedArticleTableId)

          const fieldList = await articleTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const ar_fields = ghArticleFields()
          const totalInteract = []
          for (const ar_recordId of recordIdList){
            const articleRecord = await articleTable.getRecordById(ar_recordId);
            const ar_url = articleRecord.fields[fieldMap[ar_fields.url.label].id][0]
            const get_time = Date.now()
            const res = await pluginAPI.post('/fbmain/monitor/v3/read_zan_pro', {
              url: ar_url.text,
              key: props.formData.key,
            })
            
            // 构建 updateTable 所需的格式
            const updateItem = { recordId: ar_recordId, data: {} };

            
            if (res && res.data && res.data.code === 0) {
              successCount++
              totalCost += res.data.cost_money
              lastRemainMoney = res.data.remain_money
              updateItem.data = {
                ...res.data.data,
                last_get_time: get_time,
                get_interaction_flag: 'success',
                fail_reason: '',
              }
            }
            else{
              updateItem.data = {
                get_interaction_flag: 'fail',
                fail_reason: res.data.msg || t('ghForm.messages.unknownError'),
              }
            }

            totalInteract.push(updateItem);
          }
          
          await updateTable(
            ghData.value.selectedArticleTableId,
            totalInteract,
            ghArticleFields()
          )
          
          if(recordIdList.length > 0){
            props.formData.message = t('ghForm.messages.updateArticleSuccess', { total: recordIdList.length, success: successCount, price: totalCost.toFixed(2) });
            props.formData.messageType = 'success';
          }
          
        } catch (error) {
          console.error('操作失败:', error);
          props.formData.message = t('ghForm.messages.operationFailed', { error: error.message || t('ghForm.messages.unknownError') });
          props.formData.messageType = 'error';
        } finally {
          emit('update:isLocked', false);
        }
      }

      return {
        alertList,
        alterShow,
        ghData,
        dateRange,
        addTableTemplate,
        addGhAccount,
        getRecentArticles,
        getArticleInteract,
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
        :content="t('ghForm.tooltips.generateTemplate')" 
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
          {{ t('ghForm.form.generateTemplate') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('ghForm.form.ghTable')"
    >
      <TableSelect v-model="ghData.selectedGhTableId" />
    </el-form-item>

    <el-form-item
      :label="t('ghForm.form.ghName')"
    >
      <el-input 
        v-model="ghData.ghSearchValue"
        :placeholder="t('ghForm.form.ghNamePlaceholder')"
      />
    </el-form-item>
    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !ghData.ghSearchValue || 
        !ghData.selectedGhTableId ? t('ghForm.tooltips.addGhAccount') : t('ghForm.form.addGhAccount') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !ghData.ghSearchValue || !ghData.selectedGhTableId"
          @click="addGhAccount"
          plain
          style="flex: 1;"
        >
          {{ t('ghForm.form.addGhAccount') }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item 
      :label="t('ghForm.form.articleTable')"
    >
      <TableSelect v-model="ghData.selectedArticleTableId" />
    </el-form-item>
    
    <el-form-item :label="t('ghForm.form.dateLimit')">
      <el-select v-model="ghData.searchDate" :placeholder="t('ghForm.form.dateLimitPlaceholder')">
        <el-option v-for="item in dateRange" :key="item" :label="item > 1 ? item + t('ghForm.form.days') : t('ghForm.form.today')" :value="item" />
      </el-select>
    </el-form-item>

    <el-form-item label-width="null">
      <el-radio-group v-model="ghData.useTimeCut">
        <el-radio :label="false">{{ t('ghForm.form.allInDate') }}</el-radio>
        <el-radio :label="true">{{ t('ghForm.form.newInDate') }}</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || !ghData.selectedGhTableId || 
        !ghData.selectedArticleTableId ? t('ghForm.tooltips.getArticles') : t('ghForm.form.getArticles') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !ghData.selectedGhTableId || !ghData.selectedArticleTableId"
          @click="getRecentArticles(ghData.searchDate, ghData.useTimeCut)"
          plain
          style="flex: 1;"
        >
          {{ t('ghForm.form.getArticles', { days: ghData.searchDate > 1 ? ghData.searchDate + t('ghForm.form.days') : t('ghForm.form.today') }) }}
        </el-button>
      </el-tooltip>
    </el-form-item>

    <el-form-item label-width="null">
      <el-tooltip 
        :content="isLocked || !formData.key || 
        !ghData.selectedArticleTableId ? t('ghForm.tooltips.updateArticleInteraction') : t('ghForm.form.updateArticleInteraction') " 
        effect="dark"
        placement="top"
      >
        <el-button 
          type="primary" 
          :disabled="isLocked || !formData.key || !ghData.selectedArticleTableId"
          @click="getArticleInteract"
          plain
          style="flex: 1;"
        >
          {{ t('ghForm.form.updateArticleInteraction') }}
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

    <!-- <p>{{ ghData }}</p> -->
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