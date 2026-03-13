<script>
  import { ref } from 'vue';
  import { FieldType } from '@lark-base-open/js-sdk';
  import {
    ElFormItem,
    ElSelect,
    ElOption,
    ElInput,
    ElButton,
  } from 'element-plus';
  import pluginAPI from '@/utils/request'
  import { writeToTable } from '@/utils/tableHelper'

  export default {
    components: {
      ElFormItem,
      ElSelect,
      ElOption,
      ElInput,
      ElButton,
    },
    props: {
      disabled: {
        type: Boolean,
        default: false
      },
      formData: {
        type: Object,
        required: true
      }
    },
    setup(props) {
      const ghSearchField = {
        name: {value: 'name', label: '公众号名称或微信id'},
        url: {value: 'url', label: '文章链接'},
        biz: {value: 'biz', label: '公众号标识(base64)'},
      }

      const ghTableFields = {
        appmsgid: {value: 'appmsgid', label: '文章ID', fieldType: FieldType.Text},
        url: {value: 'url', label: '文章链接', fieldType: FieldType.Url},
        post_time: {value: 'post_time', label: '发文时间', fieldType: FieldType.DateTime},
        title: {value: 'title', label: '文章标题', fieldType: FieldType.Text},
        digest: {value: 'digest', label: '文章摘要', fieldType: FieldType.Text},
      }
      

      const ghData = ref({
        selectedSearchField: ghSearchField.name.value,
        searchFieldValue: null,
      })

      const testClick = async() => {
        try {
          // 这里应该是获取公众号数据的API调用
          // 暂时使用模拟数据
          const mockData = [
            {
              "position": 1,
              "url": "https://mp.weixin.qq.com/s/C0ECOjDPSgJoRHhKMLgMkg",
              "post_time": 1773273540,
              "post_time_str": "2026-03-12 07:59:00",
              "cover_url": "https://mmbiz.qpic.cn/mmbiz_jpg/qR1zR3jHiclfxuv34Q9r6jdicPfy55FzrKKQ9eoL5ZATFmo3SU0Sc7lz4zecCFcJe2aiaMIMau5MEsiaGKVl1Am3xw/0?wx_fmt=jpeg",
              "original": 0,
              "item_show_type": 0,
              "digest": "",
              "title": "局地有中雪、中雨！河北大范围雨雪大风天气今起上线｜冀青早八点",
              "pre_post_time": 1773270037,
              "appmsgid": 2652634941,
              "msg_status": 2,
              "msg_fail_reason": "",
              "send_to_fans_num": -1,
              "update_time": 0,
              "is_deleted": "0",
              "types": 9,
              "pic_cdn_url_235_1": "https://mmbiz.qpic.cn/mmbiz_jpg/qR1zR3jHiclfxuv34Q9r6jdicPfy55FzrK2OicEickiau74jFoqwdwUiaic1oPlHnZ9ic3dcGrf1hwaCcvLxDFDoZkrE8w/0?wx_fmt=jpeg",
              "pic_cdn_url_16_9": "",
              "pic_cdn_url_1_1": "https://mmbiz.qpic.cn/mmbiz_jpg/qR1zR3jHiclfxuv34Q9r6jdicPfy55FzrKKQ9eoL5ZATFmo3SU0Sc7lz4zecCFcJe2aiaMIMau5MEsiaGKVl1Am3xw/0?wx_fmt=jpeg"
            }
          ];
          
          // 调用写入表格方法
          const result = await writeToTable(
            props.formData.selectedTableId,
            mockData,
            ghTableFields,
            props.formData.newTable,
            '公众号数据'
          );
          
          if (result.success) {
            console.log('数据写入成功:', result.data);
            // 可以添加成功提示
          } else {
            console.error('数据写入失败:', result.error);
            // 可以添加失败提示
          }
        } catch (error) {
          console.error('操作失败:', error);
        }
      }

      return {
        ghData,
        ghSearchField,
        testClick,
        ghTableFields,
      };
    },
  };
</script>

<template>
  <div class="ghForm">
    <el-form-item 
      label="查询方式"
      label-position="left"
    >
      <el-select
        v-model="ghData.selectedSearchField"
        placeholder="请选择查询方式"
      >
        <el-option
          v-for="item in ghSearchField"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        >
        </el-option>
      </el-select>
    </el-form-item>

    <el-form-item>
      <el-input 
        v-model="ghData.searchFieldValue"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 8 }"
        resize="none"
        placeholder="请输入查询方式值"
      />
    </el-form-item>

    <el-form-item>
      <el-button 
        type="primary" 
        size="large" 
        :disabled="disabled || !ghData.searchFieldValue"
        @click="testClick"
        plain
        style="flex: 1;"
      >
        获取当日发文
      </el-button>
      <el-button 
        type="primary" 
        size="large" 
        :disabled="disabled || !ghData.searchFieldValue"
        @click="testClick"
        plain
        style="flex: 1;"
      >
        获取历史发文
      </el-button>
    </el-form-item>
  </div>
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