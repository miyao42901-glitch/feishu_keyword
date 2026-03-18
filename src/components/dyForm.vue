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
      function dyUserFields() {
        return {
          nickname: { label: '用户名', fieldType: FieldType.Text, isPrimary: true},
          sec_user_id: { label: '用户id', fieldType: FieldType.Text, },
          max_follower_count: { label: '最大粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          mplatform_followers_count: { label: '当前粉丝数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          following_count: { label: '关注数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          signature: { label: '简介', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          total_favorited: { label: '获赞总数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          last_update_time: { label: '最后获取视频时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
        }
      }

      function dyVedioFields(linkTableId = '') {
        return {
          preview_title: { label: '视频标题', fieldType: FieldType.Text, isPrimary: true},
          dy_link: {
            label: '视频作者',
            fieldType: FieldType.SingleLink,
            property:{
              tableId: linkTableId, 
              multiple: false,
            }
          },
          aweme_id: { label: '视频id', fieldType: FieldType.Text, },
          create_time: { label: '视频发布时间', fieldType: FieldType.DateTime, property: {dateFormat: DateFormatter.DATE_TIME }},
          digg_count: { label: '点赞数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          comment_count: { label: '评论数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          share_count: { label: '分享数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
          collect_count: { label: '收藏数', fieldType: FieldType.Number, property: {formatter: NumberFormatter.INTEGER}, },
        }
      }

      const dyData = ref({
        sec_user_id: null,
        userTableId: null,
        vedioTableId: null,
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
            '抖音账号数据表模板' + timestamp
          );
          if (res1.success) {
            const res2 = await writeToTable(
              null,
              [],
              dyVedioFields(res1.data.tableId),
              '抖音视频数据表模板' + timestamp
            );
          }
        }catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      const addDyUser = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const res = await pluginAPI.post(`/fbmain/monitor/v3/douyin_user_data?key=${props.formData.key}`, {
            sec_user_id: dyData.value.sec_user_id,
          })

          if (res.data.code === 0) {
            const result = await writeToTable(
              dyData.value.userTableId,
              [{...res.data.data.user, sec_user_id: dyData.value.sec_user_id}],
              dyUserFields(),
            );
          }
        } catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getRecentVedios = async(maxDay = 1) => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          const searchDays = typeof maxDay === 'number' && !isNaN(maxDay) ? Math.min(30, Math.max(1, Math.floor(maxDay))) : 1
          const date = new Date()
          date.setHours(0, 0, 0, 0)
          date.setDate(date.getDate() - (searchDays - 1))
          const min_time = date.getTime()
          
          // const recordIdList = await bitable.ui.selectRecordIdList(ghData.value.selectedGhTableId)
          // const accountTable = await bitable.base.getTable(ghData.value.selectedGhTableId)

          // const fieldList = await accountTable.getFieldList()
          // const fieldMap = {};
          // for (const field of fieldList) {
          //   const fieldName = await field.getName();
          //   fieldMap[fieldName] = field;
          // }
          // const ac_fields = ghAccountFields()

          // const totalData = {}
          // const totalLastTime = {}
          // for (const ac_recordId of recordIdList){
          //   const accountRecord = await accountTable.getRecordById(ac_recordId);
          //   const ac_biz = accountRecord.fields[fieldMap[ac_fields.biz.label].id][0]
          //   const ac_last_time = Math.max(accountRecord.fields[fieldMap[ac_fields.last_update_time.label].id] || min_time, min_time)

          //   // console.log(ac_name, ac_biz, ac_last_time)
          //   let max_post_time = Math.max(ac_last_time, Date.now())
          //   if (searchDays === 1){
          //     const res = await pluginAPI.post('/fbmain/monitor/v3/post_condition', {
          //       biz: ac_biz.text,
          //       key: props.formData.key,
          //     })

          //     const dataList = res.data.data
          //     .filter(item => item.post_time * 1000 > ac_last_time)
          //     .map(item => ({
          //       ...item,
          //       post_time: item.post_time * 1000, // 转换为毫秒级时间戳
          //       gh_link: [ac_recordId],
          //     }))

          //     max_post_time = Math.max(...dataList.map(item => item.post_time), max_post_time)
          //     // console.log(max_post_time)

          //     // 将数据添加到对象中，使用 url 作为 key
          //     dataList.forEach(item => {
          //       if (item.url) {
          //         totalData[item.url] = item;
          //       }
          //     });
              
          //     // 将数据添加到对象中，使用 ac_recordId 作为 key
          //     totalLastTime[ac_recordId] = {
          //       recordId: ac_recordId, 
          //       data: {
          //         last_update_time: max_post_time,
          //       }
          //     };
          //   }
          //   else{
          //     let i = 0
          //     while(true){
          //       i += 1
          //       const res = await pluginAPI.post('/fbmain/monitor/v3/post_history', {
          //         biz: ac_biz.text,
          //         key: props.formData.key,
          //         page: i
          //       })

          //       const dataList = res.data.data
          //       .filter(item => item.post_time * 1000 > ac_last_time)
          //       .map(item => ({
          //         ...item,
          //         post_time: item.post_time * 1000, // 转换为毫秒级时间戳
          //         gh_link: [ac_recordId],
          //       }))

          //       max_post_time = Math.max(...dataList.map(item => item.post_time), max_post_time)
          //     // console.log(max_post_time)

          //     // 将数据添加到对象中，使用 url 作为 key
          //       dataList.forEach(item => {
          //         if (item.url) {
          //           totalData[item.url] = item;
          //         }
          //       });
                
          //       // 将数据添加到对象中，使用 ac_recordId 作为 key
          //       totalLastTime[ac_recordId] = {
          //         recordId: ac_recordId, 
          //         data: {
          //           last_update_time: max_post_time,
          //         }
          //       };

          //       if (dataList.length === 0 || res.data.total_page === res.data.now_page){
          //         break
          //       }
          //     }
          //   }
          // }

          
          // await writeToTable(
          //   ghData.value.selectedArticleTableId,
          //   Object.values(totalData),
          //   ghArticleFields(ghData.value.selectedGhTableId),
          // );
          
          // await updateTable(
          //   ghData.value.selectedGhTableId,
          //   Object.values(totalLastTime),
          //   ghAccountFields()
          // )

        } catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      const getVedioInteract = async() => {
        if (props.isLocked) return;
        emit('update:isLocked', true);

        try{
          // const articleTable = await bitable.base.getTable(ghData.value.selectedArticleTableId)
          // const recordIdList = await bitable.ui.selectRecordIdList(ghData.value.selectedArticleTableId)

          // const fieldList = await articleTable.getFieldList()
          // const fieldMap = {};
          // for (const field of fieldList) {
          //   const fieldName = await field.getName();
          //   fieldMap[fieldName] = field;
          // }

          // const ar_fields = ghArticleFields()
          // const totalInteract = []
          // for (const ar_recordId of recordIdList){
          //   const articleRecord = await articleTable.getRecordById(ar_recordId);
          //   const ar_url = articleRecord.fields[fieldMap[ar_fields.url.label].id][0]
          //   const get_time = Date.now()
          //   const res = await pluginAPI.post('/fbmain/monitor/v3/read_zan_pro', {
          //     url: ar_url.text,
          //     key: props.formData.key,
          //   })
            
          //   // 构建 updateTable 所需的格式
          //   const updateItem = { recordId: ar_recordId, data: {} };

          //   updateItem.data = {
          //     ...res.data.data,
          //     last_get_time: get_time,
          //   }
            
          //   totalInteract.push(updateItem);
          // }
          
          // await updateTable(
          //   ghData.value.selectedArticleTableId,
          //   totalInteract,
          //   ghArticleFields()
          // )
        } catch (error) {
          console.error('操作失败:', error);
        } finally {
          emit('update:isLocked', false);
        }
      }

      return {
        dyData,
        addTableTemplate,
        addDyUser,
        getRecentVedios,
        getVedioInteract,
      };
    },
  };
</script>

<template>
  <el-form class="ghForm" label-position="left" label-width="120px">
    <el-form-item 
      label="抖音号数据表"
    >
      <TableSelect v-model="dyData.userTableId" />
    </el-form-item>

    <el-form-item 
      label="视频数据表"
    >
      <TableSelect v-model="dyData.vedioTableId" />
    </el-form-item>

    <el-form-item
      label="抖音用户id"
    >
      <el-input 
        v-model="dyData.sec_user_id"
        placeholder="请输入抖音用户id"  
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
        :disabled="isLocked || !formData.key || !dyData.sec_user_id || !dyData.userTableId"
        @click="addDyUser"
        plain
        style="flex: 1;"
      >
        添加抖音账号
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !dyData.userTableId || !dyData.vedioTableId"
        @click="getRecentVedios"
        plain
        style="flex: 1;"
      >
        获取今日发布视频(开发中)
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !dyData.userTableId || !dyData.vedioTableId"
        @click="getRecentVedios(7)"
        plain
        style="flex: 1;"
      >
        获取近期最多7天视频(开发中)
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !dyData.userTableId || !dyData.vedioTableId"
        @click="getRecentVedios(30)"
        plain
        style="flex: 1;"
      >
        获取近期最多30天视频(开发中)
      </el-button>
    </el-form-item>

    <el-form-item label-width="null">
      <el-button 
        type="primary" 
        size="large" 
        :disabled="isLocked || !formData.key || !dyData.vedioTableId"
        @click="getVedioInteract"
        plain
        style="flex: 1;"
      >
        更新视频互动信息(开发中)
      </el-button>
    </el-form-item>

    <p>{{ dyData }}</p>
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