<script>
  import { ref } from 'vue';
  import { bitable, FieldType, NumberFormatter, DateFormatter } from '@lark-base-open/js-sdk';
  import { ElSelect, ElOption, ElInput, ElIcon } from 'element-plus';
  import { QuestionFilled } from '@element-plus/icons-vue';
  import pluginAPI from '@/utils/request'
  import { writeToTable, updateTable, getFirstRecordByField } from '@/utils/tableHelper'
  import TableSelect from '@/components/TableSelect.vue'
  import platformTip from '@/tipDialogs/platformTip.vue'
  import '@/assets/form-styles.css'

  export default {
    components: { ElSelect, ElOption, ElInput, ElIcon, QuestionFilled, TableSelect, platformTip },
    props: {
      formData: { type: Object, required: true },
      isLocked: { type: Boolean, default: false }
    },
    emits: ['update:isLocked'],
    setup(props, { emit }) {
      function userFields() {
        return {
          username: { label: '视频号id', fieldType: FieldType.Text, isPrimary: true },
          nickname: { label: '视频号名称', fieldType: FieldType.Text },
          signature: { label: '简介', fieldType: FieldType.Text },
          get_work_flag: {
            label: '获取视频状态', fieldType: FieldType.SingleSelect,
            options: { unknow: '未获取过', fail: '获取失败', partial_success: '部分成功', success: '获取成功' },
          },
          work_fail_reason: { label: '获取视频失败原因', fieldType: FieldType.Text },
        }
      }
      function workFields() {
        return {
          object_id: { label: '视频id', fieldType: FieldType.Text, isPrimary: true },
          title: { label: '视频标题', fieldType: FieldType.Text },
          username: { label: '视频号id', fieldType: FieldType.Text },
          nickname: { label: '视频号名称', fieldType: FieldType.Text },
          export_id: { label: '导出id', fieldType: FieldType.Text },
          publish_time: { label: '发布时间', fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
          video_play_len: { label: '播放时长', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          like_count: { label: '点赞数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          fav_count: { label: '收藏数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          forward_count: { label: '转发数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          comment_count: { label: '评论数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          like_count_diff: { label: '新增点赞数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          fav_count_diff: { label: '新增收藏数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          forward_count_diff: { label: '新增转发数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          comment_count_diff: { label: '新增评论数', fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
          download_url: { label: '下载链接', fieldType: FieldType.Url },
          current_get_time: { label: '当前获取时间', fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
          last_get_time: { label: '上次获取时间', fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
        }
      }
      const ranges = ref({
        '当天': { value: 1, type: 'date' }, '3天内': { value: 3, type: 'date' },
        '7天内': { value: 7, type: 'date' }, '15天内': { value: 15, type: 'date' },
        '30天内': { value: 30, type: 'date' }, '1页': { value: 1, type: 'page' },
        '2页': { value: 2, type: 'page' }, '5页': { value: 5, type: 'page' },
        '10页': { value: 10, type: 'page' }, '20页': { value: 20, type: 'page' },
        '50页': { value: 50, type: 'page' },
      })
      const paneData = ref({
        keywords: null, username: null, userTableId: null, workTableId: null,
        searchRange: '1页', getDataType: 0, getWorksType: 1,
      })
      const tipVisible = ref(false)
      const openTip = () => { tipVisible.value = true }
      const getTimeFromStr = (dateStr) => { if (!dateStr) return 0; return new Date(dateStr).getTime() }
      const upsertUser = async () => {
        if (props.isLocked) return
        emit('update:isLocked', true)
        try {
          if (!paneData.value.userTableId) {
            const today = new Date()
            const tableRes = await writeToTable(null, [], userFields(), '视频号账号' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_'))
            if (tableRes.success) paneData.value.userTableId = tableRes.data.tableId
          }
          const res = await pluginAPI.post('/plugin_forward', {
            url: '/fbmain/monitor/v3/wxvideo',
            body: { keywords: paneData.value.keywords, type: 6, key: props.formData.key },
          })
          const tmpUserFields = userFields()
          if (res && res.data && res.data.code === 0) {
            if (!res.data.v2_info_list) {
              props.formData.message = '操作失败：没找到有关视频号'
              props.formData.messageType = 'error'
            } else {
              const username = res.data.v2_info_list.contact.username
              const [record] = await getFirstRecordByField(paneData.value.userTableId, tmpUserFields.username.label, username)
              if (record) {
                await updateTable(paneData.value.userTableId, [{ recordId: record.recordId, data: { username, nickname: res.data.v2_info_list.contact.nickname, signature: res.data.v2_info_list.contact.signature } }], tmpUserFields)
              } else {
                await writeToTable(paneData.value.userTableId, [{ username, nickname: res.data.v2_info_list.contact.nickname, signature: res.data.v2_info_list.contact.signature, get_work_flag: 'unknow' }], tmpUserFields)
              }
              props.formData.message = '新增视频号账号完成，消耗：' + res.data.cost
              props.formData.messageType = 'success'
            }
          } else {
            props.formData.message = '操作失败:' + (res.data.msg || '未知错误')
            props.formData.messageType = 'error'
          }
        } catch (error) {
          console.error('操作失败:', error)
          props.formData.message = '操作失败:' + (error.message || '未知错误')
          props.formData.messageType = 'error'
        } finally { emit('update:isLocked', false) }
      }
      const upsertWork = async (items, get_time, userInfo) => {
        const tmpWorkFields = workFields()
        const insertData = [], updateData = []
        for (const item of items) {
          const object_id = item.object_id
          const [record, fieldMap] = await getFirstRecordByField(paneData.value.workTableId, tmpWorkFields.object_id.label, object_id)
          if (record) {
            const last_get_time = record.fields[fieldMap[tmpWorkFields.current_get_time.label]?.id] || null
            const last_like_count = record.fields[fieldMap[tmpWorkFields.like_count.label]?.id] || 0
            const last_fav_count = record.fields[fieldMap[tmpWorkFields.fav_count.label]?.id] || 0
            const last_forward_count = record.fields[fieldMap[tmpWorkFields.forward_count.label]?.id] || 0
            const last_comment_count = record.fields[fieldMap[tmpWorkFields.comment_count.label]?.id] || 0
            updateData.push({ recordId: record.recordId, data: { object_id, export_id: item.export_id, title: item.title, username: userInfo.username, nickname: userInfo.nickname, publish_time: getTimeFromStr(item.publish_time), fav_count: item.fav_count, like_count: item.like_count, forward_count: item.forward_count, comment_count: item.comment_count, video_play_len: item.video_play_len, like_count_diff: item.like_count - last_like_count, fav_count_diff: item.fav_count - last_fav_count, forward_count_diff: item.forward_count - last_forward_count, comment_count_diff: item.comment_count - last_comment_count, current_get_time: get_time, last_get_time } })
          } else {
            insertData.push({ object_id, export_id: item.export_id, title: item.title, username: userInfo.username, nickname: userInfo.nickname, publish_time: getTimeFromStr(item.publish_time), fav_count: item.fav_count, like_count: item.like_count, forward_count: item.forward_count, comment_count: item.comment_count, video_play_len: item.video_play_len, current_get_time: get_time })
          }
        }
        const insertRes = await writeToTable(paneData.value.workTableId, insertData, tmpWorkFields)
        const updateRes = await updateTable(paneData.value.workTableId, updateData, tmpWorkFields)
        let resultCount = 0
        if (insertRes && insertRes.success) resultCount += insertRes.data.recordIds.length
        if (updateRes && updateRes.success) resultCount += updateRes.data.recordIds.length
        return resultCount
      }
      const getRecentWorks = async (rangeKey, getWorksType = 0) => {
        if (props.isLocked) return
        emit('update:isLocked', true)
        try {
          if (!paneData.value.workTableId) {
            const today = new Date()
            const tableRes = await writeToTable(null, [], workFields(), '视频号视频' + today.toLocaleString('sv-SE').replace(' ', '_').replace(/:/g, '_'))
            if (tableRes.success) paneData.value.workTableId = tableRes.data.tableId
          }
          let workSuccessCount = 0, singleUserSuccess = 1, totalCost = 0
          const range = ranges.value[rangeKey]
          let min_time = 0
          if (range.type === 'date') {
            const date = new Date(); date.setHours(0, 0, 0, 0)
            date.setDate(date.getDate() - (range.value - 1)); min_time = date.getTime()
          }
          const tmpUserFields = userFields(), totalLastTime = {}
          let userInfoList = []
          if (getWorksType === 0) {
            const userTable = await bitable.base.getTable(paneData.value.userTableId)
            const fieldList = await userTable.getFieldList()
            const fieldMap = {}
            for (const field of fieldList) { fieldMap[await field.getName()] = field }
            const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.userTableId)
            const username_set = {}
            for (const userRecordId of recordIdList) {
              const userRecord = await userTable.getRecordById(userRecordId)
              const username = userRecord.fields[fieldMap[tmpUserFields.username.label].id][0].text
              if (username_set[username]) continue
              username_set[username] = true
              userInfoList.push({ recordId: userRecordId, username })
            }
          } else { userInfoList = [{ username: paneData.value.username }] }
          for (const userInfo of userInfoList) {
            let last_buffer = '', i = 0
            while (true) {
              i += 1
              const get_time = Date.now()
              const res = await pluginAPI.post('/plugin_forward', { url: '/fbmain/monitor/v3/wxvideo', body: { v2_name: userInfo.username, type: 1, last_buffer, key: props.formData.key } })
              if (!(res && res.data && res.data.code === 0)) {
                if (getWorksType === 0 && userInfo.recordId) { totalLastTime[userInfo.recordId] = { recordId: userInfo.recordId, data: { get_work_flag: i > 1 ? 'partial_success' : 'fail', work_fail_reason: res.data.msg || '未知错误' } } }
                else { singleUserSuccess = 0 }
                break
              }
              last_buffer = res.data.last_buffer; totalCost += res.data.cost
              let preFilteringData = res.data.object
              if (range.type === 'date') { preFilteringData = res.data.object.filter(item => !(item.sticky_time) || getTimeFromStr(item.publish_time) > min_time) }
              let workAccordCount = 0
              const items = []
              for (const item of preFilteringData) { if (range.type !== 'date' || getTimeFromStr(item.publish_time) > min_time) { workAccordCount += 1; items.push(item) } }
              if (items.length > 0) { workSuccessCount += await upsertWork(items, get_time, { username: res.data.contact.username, nickname: res.data.contact.nickname }) }
              if (getWorksType === 0 && userInfo.recordId) { totalLastTime[userInfo.recordId] = { recordId: userInfo.recordId, data: { get_work_flag: 'success', work_fail_reason: '' } } }
              if (range.type === 'date') { if (workAccordCount === 0 || workAccordCount < preFilteringData.length) break }
              else if (range.type === 'page') { if (i >= range.value) break }
              else { if (preFilteringData.length === 0) break }
            }
          }
          await updateTable(paneData.value.userTableId, Object.values(totalLastTime), tmpUserFields)
          if (userInfoList.length > 0) {
            let userSuccessCount = singleUserSuccess
            if (getWorksType === 0) { userSuccessCount = Object.values(totalLastTime).filter(item => item.data.get_work_flag === 'success').length }
            props.formData.message = '获取视频完成，尝试获取' + userInfoList.length + '个账号，成功操作' + userSuccessCount + '个账号，共写入' + workSuccessCount + '条视频信息，共消耗' + totalCost.toFixed(3)
            props.formData.messageType = 'success'
          }
        } catch (error) {
          console.error('操作失败:', error)
          props.formData.message = '操作失败:' + (error.message || '未知错误')
          props.formData.messageType = 'error'
        } finally { emit('update:isLocked', false) }
      }
      const updateWorks = async (type = 9) => {
        if (props.isLocked) return
        emit('update:isLocked', true)
        try {
          let successCount = 0, totalCost = 0
          const workTable = await bitable.base.getTable(paneData.value.workTableId)
          const recordIdList = await bitable.ui.selectRecordIdList(paneData.value.workTableId)
          const fieldList = await workTable.getFieldList()
          const fieldMap = {}
          for (const field of fieldList) { fieldMap[await field.getName()] = field }
          const tmpWorkFields = workFields()
          for (const workRecordId of recordIdList) {
            const workRecord = await workTable.getRecordById(workRecordId)
            const object_id = workRecord.fields[fieldMap[tmpWorkFields.object_id.label].id][0].text
            const get_time = Date.now()
            const res = await pluginAPI.post('/plugin_forward', { url: '/fbmain/monitor/v3/wxvideo', body: { object_id, key: props.formData.key, type } })
            if (res && res.data && res.data.code === 0) {
              totalCost += res.data.cost
              const last_get_time = workRecord.fields[fieldMap[tmpWorkFields.current_get_time.label]?.id] || null
              const last_like_count = workRecord.fields[fieldMap[tmpWorkFields.like_count.label]?.id] || 0
              const last_fav_count = workRecord.fields[fieldMap[tmpWorkFields.fav_count.label]?.id] || 0
              const last_forward_count = workRecord.fields[fieldMap[tmpWorkFields.forward_count.label]?.id] || 0
              const last_comment_count = workRecord.fields[fieldMap[tmpWorkFields.comment_count.label]?.id] || 0
              let data = {}
              if (type === 9) { data = { fav_count: res.data.count_info.fav_count, like_count: res.data.count_info.like_count, forward_count: res.data.count_info.forward_count, comment_count: res.data.count_info.comment_count, fav_count_diff: res.data.count_info.fav_count - last_fav_count, like_count_diff: res.data.count_info.like_count - last_like_count, forward_count_diff: res.data.count_info.forward_count - last_forward_count, comment_count_diff: res.data.count_info.comment_count - last_comment_count, current_get_time: get_time, last_get_time } }
              else { data = { fav_count: res.data.fav_count, like_count: res.data.like_count, forward_count: res.data.forward_count, comment_count: res.data.comment_count, fav_count_diff: res.data.fav_count - last_fav_count, like_count_diff: res.data.like_count - last_like_count, forward_count_diff: res.data.forward_count - last_forward_count, comment_count_diff: res.data.comment_count - last_comment_count, download_url: res.data.download_url, current_get_time: get_time, last_get_time } }
              const result = await updateTable(paneData.value.workTableId, [{ recordId: workRecordId, data }], tmpWorkFields)
              if (result.success) successCount++
            }
          }
          if (recordIdList.length > 0) {
            props.formData.message = '更新视频号视频完成, 共尝试更新' + recordIdList.length + '条, 成功' + successCount + '条, 消耗' + totalCost.toFixed(3)
            props.formData.messageType = 'success'
          }
        } catch (error) {
          console.error('操作失败:', error)
          props.formData.message = '操作失败:' + (error.message || '未知错误')
          props.formData.messageType = 'error'
        } finally { emit('update:isLocked', false) }
      }
      return { paneData, ranges, tipVisible, openTip, upsertUser, getRecentWorks, updateWorks }
    },
  }
</script>

<template>
  <div class="collect-panel">
    <div class="section-title">采集内容</div>
    <div class="collect-sub-panel">
      <div class="section-block">
        <div class="toggle-wrapper">
          <el-tooltip content="将采集账号的ID、粉丝数、简介、点赞数等基础信息" placement="top">
            <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 0 }" @click="paneData.getDataType = 0">采集博主数据</el-button>
          </el-tooltip>
          <el-tooltip content="将采集作品的点赞、评论、查看、转发、发布时间等数据" placement="top">
            <el-button type="info" class="toggle-btn" :class="{ active: paneData.getDataType === 1 }" @click="paneData.getDataType = 1">采集作品数据</el-button>
          </el-tooltip>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">获取方式</div>
        <div class="toggle-wrapper">
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getWorksType === 1 }" @click="paneData.getWorksType = 1">根据视频号id获取</el-button>
          <el-button type="info" class="toggle-btn" :class="{ active: paneData.getWorksType === 0 }" @click="paneData.getWorksType = 0">根据账号表获取</el-button>
        </div>
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0 && paneData.getWorksType === 0">
        <div class="field-label">选择账号表</div>
        <TableSelect v-model="paneData.userTableId" placeholder="请选择账号表" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">视频号视频表</div>
        <TableSelect v-model="paneData.workTableId" placeholder="未选自动创建" />
      </div>

      <div class="section-block" v-show="paneData.getDataType === 0">
        <div class="field-label">采集到表格</div>
        <TableSelect v-model="paneData.userTableId" placeholder="默认新建表格" />
      </div>

      <div class="section-block" v-show="paneData.getDataType !== 0">
        <div class="field-label">作品数据范围</div>
        <el-select v-model="paneData.searchRange" class="custom-select" placeholder="请选择数据范围">
          <el-option v-for="item in Object.keys(ranges)" :key="item" :label="item" :value="item" />
        </el-select>
      </div>
    </div>

    <div v-show="paneData.getDataType === 0 || paneData.getWorksType === 1">
      <div class="section-title">
        采集账号
        <!-- <el-icon class="icon-hint" @click="openTip"><QuestionFilled /></el-icon> -->
      </div>

      <div class="collect-sub-panel">
        <div class="section-block" v-show="paneData.getDataType === 0">
          <div class="field-label">视频号名称</div>
          <el-input v-model="paneData.keywords" placeholder="请输入视频号名称" class="custom-input" />
        </div>
        <div class="section-block" v-show="paneData.getDataType !== 0 && paneData.getWorksType === 1">
          <div class="field-label">视频号id</div>
          <el-input v-model="paneData.username" placeholder="请输入视频号id" class="custom-input" />
        </div>
      </div>
    </div>

    <div class="collect-btn-container">
      <div class="collect-btn-item" v-if="paneData.getDataType === 0">
        <el-button class="collect-btn" :disabled="isLocked || !formData.key || !paneData.keywords" @click="upsertUser">
          采集数据
        </el-button>
      </div>
      <div class="collect-btn-item" v-if="paneData.getDataType === 1">
        <el-button
          class="collect-btn"
          :disabled="isLocked || !formData.key || (paneData.getWorksType === 0 && !paneData.userTableId) || (paneData.getWorksType === 1 && !paneData.username)"
          @click="getRecentWorks(paneData.searchRange, paneData.getWorksType)"
        >
          采集数据
        </el-button>
      </div>
      <div class="collect-btn-item" v-if="paneData.getDataType === 1 && paneData.workTableId">
        <el-button class="update-btn" :disabled="isLocked || !formData.key" @click="updateWorks(9)">
          批量更新视频号视频数据
        </el-button>
      </div>
      <div class="collect-btn-item" v-if="paneData.getDataType === 1 && paneData.workTableId">
        <el-button class="update-btn" :disabled="isLocked || !formData.key" @click="updateWorks(3)">
          批量更新视频号视频数据(包含下载链接)
        </el-button>
      </div>
    </div>
  </div>

  <platformTip
    v-model:visible="tipVisible"
    platform-name="视频号"
    account-field-name="视频号ID"
  />
</template>

<style scoped>
</style>
