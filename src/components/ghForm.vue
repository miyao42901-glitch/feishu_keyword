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
  } from 'element-plus';
  import pluginAPI from '@/utils/request'
  import { writeToTable, getCellValue } from '@/utils/tableHelper'
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
      function ghAccountFields() {
        return {
          name: { label: '公众号名称', fieldType: FieldType.Text, isPrimary: true},
          biz: { label: '公众号标识(base64)', fieldType: FieldType.Text, },
          desc: { label: '公众号描述', fieldType: FieldType.Text, },
          last_update_time: { label: '最后获取发文时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
        }
      }

      function ghArticleFields(linkTableId = '') {
        return {
          title: { label: '文章标题', fieldType: FieldType.Text, isPrimary: true },
          gh_link: {
            label: '公众号',
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          url: { label: '文章链接', fieldType: FieldType.Url, },
          post_time: { label: '发文时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME },},
          digest: { label: '文章摘要', fieldType: FieldType.Text, },
          original: {
            label: '原创类型', 
            fieldType: FieldType.SingleSelect, 
            options: {
              0: '未声明原创',
              1: '原创',
              2: '转载'
            },
          },
          item_show_type: {
            label: '内容类型', 
            fieldType: FieldType.SingleSelect, 
            options: {
              0: '图文',
              5: '纯视频',
              7: '纯音乐',
              8: '纯图片',
              10: '纯文字',
              11: '其他'
            },
          },
          read: {label: '阅读', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          zan: {label: '点赞', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          looking: {label: '在看', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_num: {label: '转发数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_num: {label: '收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: {label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
        }
      }

      const ghData = ref({
        ghSearchValue: null,
        selectedGhTableId: null,
        selectedArticleTableId: null,
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
            '公众号数据表模板' + timestamp
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              ghArticleFields(res1.data.tableId),
              '文章数据表模板' + timestamp
            );
          }
        }catch (error) {
          console.error('操作失败:', error);
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

          if (res.data.data) {
            const result = await writeToTable(
              ghData.value.selectedGhTableId,
              [res.data.data],
              ghAccountFields(),
            );
          }
        } catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getTodayArticles = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const recordIdList = await bitable.ui.selectRecordIdList(ghData.value.selectedGhTableId)
          const accountTable = await bitable.base.getTable(ghData.value.selectedGhTableId)

          const fieldList = await accountTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }
          const ac_fields = ghAccountFields()
          for (const recordId of recordIdList){
            const accountRecord = await accountTable.getRecordById(recordId);
            const ac_biz = accountRecord.fields[fieldMap[ac_fields.biz.label].id][0]
            const ac_last_time = (accountRecord.fields[fieldMap[ac_fields.last_update_time.label].id] || 0)

            // console.log(ac_name, ac_biz, ac_last_time)
            const res = await pluginAPI.post('/fbmain/monitor/v3/post_condition', {
              biz: ac_biz.text,
              key: props.formData.key,
            })

            const dataList = res.data.data
            .filter(item => item.post_time * 1000 > ac_last_time)
            .map(item => ({
              ...item,
              gh_link: [recordId],
            }))

            const max_post_time = Math.max(...dataList.map(item => item.post_time * 1000), ac_last_time, Date.now())
            // console.log(max_post_time)

            await writeToTable(
              ghData.value.selectedArticleTableId,
              dataList,
              ghArticleFields(ghData.value.selectedGhTableId),
            );

            accountTable.setRecord(recordId, 
              { 
                fields: {
                  [fieldMap[ac_fields.last_update_time.label].id]: max_post_time,
                }
              }
            )
          }
        } catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getArticleInteract = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const articleTable = await bitable.base.getTable(ghData.value.selectedArticleTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(ghData.value.selectedArticleTableId)

          const fieldList = await articleTable.getFieldList()
          const fieldMap = {};
          for (const field of fieldList) {
            const fieldName = await field.getName();
            fieldMap[fieldName] = field;
          }

          const ar_fields = ghArticleFields()
          for (const recordId of recordIdList){
            const articleRecord = await articleTable.getRecordById(recordId);
            const ar_url = articleRecord.fields[fieldMap[ar_fields.url.label].id][0]
            const res = await pluginAPI.post('/fbmain/monitor/v3/read_zan_pro', {
              url: ar_url.text,
              key: props.formData.key,
            })
            articleTable.setRecord(recordId, 
              { 
                fields: {
                  [fieldMap[ar_fields.read.label].id]: res.data.data.read,
                  [fieldMap[ar_fields.zan.label].id]: res.data.data.zan,
                  [fieldMap[ar_fields.looking.label].id]: res.data.data.looking,
                  [fieldMap[ar_fields.share_num.label].id]: res.data.data.share_num,
                  [fieldMap[ar_fields.collect_num.label].id]: res.data.data.collect_num,
                  [fieldMap[ar_fields.comment_count.label].id]: res.data.data.comment_count,
                }
              }
            )
          }
        } catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      return {
        ghData,
        addTableTemplate,
        addGhAccount,
        getTodayArticles,
        getArticleInteract,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="120px">
    <el-form-item 
      label="公众号数据表"
    >
      <TableSelect v-model="ghData.selectedGhTableId" />
    </el-form-item>

    <el-form-item 
      label="文章数据表"
    >
      <TableSelect v-model="ghData.selectedArticleTableId" />
    </el-form-item>

    <el-form-item
      label="公众号名称/id"
    >
      <el-input 
        v-model="ghData.ghSearchValue"
        placeholder="请输入公众号名称或id"
      />
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !ghData.ghSearchValue || !ghData.selectedGhTableId"
        @click="addGhAccount"
        plain
        style="flex: 1;"
      >
        添加公众号
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
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
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !ghData.selectedGhTableId || !ghData.selectedArticleTableId"
        @click="getTodayArticles"
        plain
        style="flex: 1;"
      >
        获取当日发文
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !ghData.selectedArticleTableId"
        @click="getArticleInteract"
        plain
        style="flex: 1;"
      >
        更新文章互动信息
      </el-button>
    </el-form-item>

    <p>{{ ghData }}</p>
    <p>{{ formData.key }}</p>
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