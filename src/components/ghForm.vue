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
  import { writeToTable, updateTable, getCellValue } from '@/utils/tableHelper'
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
          last_get_time: { label: '互动信息更新时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
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

          if (res.data.code === 0) {
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

      const getRecentArticles = async(maxDay = 1) => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
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
            const ac_last_time = Math.max(accountRecord.fields[fieldMap[ac_fields.last_update_time.label].id] || min_time, min_time)

            // console.log(ac_name, ac_biz, ac_last_time)
            let max_post_time = Math.max(ac_last_time, Date.now())
            if (searchDays === 1){
              const res = await pluginAPI.post('/fbmain/monitor/v3/post_condition', {
                biz: ac_biz.text,
                key: props.formData.key,
              })
              
              if (res.data.code !== 0) continue

              const dataList = res.data.data
              .filter(item => item.post_time * 1000 > ac_last_time)
              .map(item => ({
                ...item,
                post_time: item.post_time * 1000, // 转换为毫秒级时间戳
                gh_link: [ac_recordId],
              }))

              max_post_time = Math.max(...dataList.map(item => item.post_time), max_post_time)
              // console.log(max_post_time)

              // 将数据添加到对象中，使用 url 作为 key
              dataList.forEach(item => {
                if (item.url) {
                  totalData[item.url] = item;
                }
              });
              
              // 将数据添加到对象中，使用 ac_recordId 作为 key
              totalLastTime[ac_recordId] = {
                recordId: ac_recordId, 
                data: {
                  last_update_time: max_post_time,
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

                if (res.data.code !== 0) break

                const dataList = res.data.data
                .filter(item => item.post_time * 1000 > ac_last_time)
                .map(item => ({
                  ...item,
                  post_time: item.post_time * 1000, // 转换为毫秒级时间戳
                  gh_link: [ac_recordId],
                }))

                max_post_time = Math.max(...dataList.map(item => item.post_time), max_post_time)
              // console.log(max_post_time)

              // 将数据添加到对象中，使用 url 作为 key
                dataList.forEach(item => {
                  if (item.url) {
                    totalData[item.url] = item;
                  }
                });
                
                // 将数据添加到对象中，使用 ac_recordId 作为 key
                totalLastTime[ac_recordId] = {
                  recordId: ac_recordId, 
                  data: {
                    last_update_time: max_post_time,
                  }
                };

                if (dataList.length === 0 || res.data.total_page === res.data.now_page){
                  break
                }
              }
            }
          }

          
          await writeToTable(
            ghData.value.selectedArticleTableId,
            Object.values(totalData),
            ghArticleFields(ghData.value.selectedGhTableId),
          );
          
          await updateTable(
            ghData.value.selectedGhTableId,
            Object.values(totalLastTime),
            ghAccountFields()
          )

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

            updateItem.data = {
              ...res.data.data,
              last_get_time: get_time,
            }

            totalInteract.push(updateItem);
          }
          
          await updateTable(
            ghData.value.selectedArticleTableId,
            totalInteract,
            ghArticleFields()
          )
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
        getRecentArticles,
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
        :disabled="isLocked || !formData.key || !ghData.selectedGhTableId || !ghData.selectedArticleTableId"
        @click="getRecentArticles"
        plain
        style="flex: 1;"
      >
        获取今日发文
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !ghData.selectedGhTableId || !ghData.selectedArticleTableId"
        @click="getRecentArticles(7)"
        plain
        style="flex: 1;"
      >
        获取近期最多7天发文
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !ghData.selectedGhTableId || !ghData.selectedArticleTableId"
        @click="getRecentArticles(30)"
        plain
        style="flex: 1;"
      >
        获取近期最多30天发文
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