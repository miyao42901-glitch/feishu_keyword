import { useI18n } from 'vue-i18n';
import { FieldType, NumberFormatter, DateFormatter } from '@lark-base-open/js-sdk';
import pluginAPI from '@/utils/request';
import { getMaxCreateTimeByUser } from '@/utils/tableHelper';

export const dyPlatformConfig = (t) => ({
  i18nPrefix: 'dyForm',
  userIdentifierField: 'sec_uid',
  workIdentifierField: 'aweme_id',
  workTimeField: 'create_time',
  workUniqueKey: 'aweme_id',
  showUpdateUser: true,
  
  searchFields: [
    { model: 'searchValue', label: 'userId', placeholder: 'userIdPlaceholder' },
    { model: 'searchValue2', label: 'shareLink', placeholder: 'shareLinkPlaceholder' }
  ],
  
  interactionButtons: [
    { label: 'updateVideoInteraction', params: {} }
  ],

  userFields: () => ({
    nickname: { label: t('dyForm.userFields.nickname'), fieldType: FieldType.Text, isPrimary: true },
    sec_uid: { label: t('dyForm.userFields.sec_uid'), fieldType: FieldType.Text },
    max_follower_count: { label: t('dyForm.userFields.max_follower_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    mplatform_followers_count: { label: t('dyForm.userFields.mplatform_followers_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    following_count: { label: t('dyForm.userFields.following_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    signature: { label: t('dyForm.userFields.signature'), fieldType: FieldType.Text },
    total_favorited: { label: t('dyForm.userFields.total_favorited'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    last_get_time: { label: t('dyForm.userFields.last_get_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    get_interaction_flag: {
      label: t('dyForm.userFields.get_interaction_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('dyForm.options.interaction.unknow'),
        fail: t('dyForm.options.interaction.fail'),
        success: t('dyForm.options.interaction.success'),
      },
    },
    interaction_fail_reason: { label: t('dyForm.userFields.interaction_fail_reason'), fieldType: FieldType.Text },
    get_work_flag: {
      label: t('dyForm.userFields.get_work_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('dyForm.options.video.unknow'),
        fail: t('dyForm.options.video.fail'),
        success: t('dyForm.options.video.success'),
      },
    },
    vedio_fail_reason: { label: t('dyForm.userFields.vedio_fail_reason'), fieldType: FieldType.Text },
  }),

  workFields: (linkTableId = '') => ({
    caption: { label: t('dyForm.videoFields.caption'), fieldType: FieldType.Text, isPrimary: true },
    user_link: {
      label: t('dyForm.videoFields.dy_link'),
      fieldType: FieldType.SingleLink,
      property: {
        tableId: linkTableId,
        multiple: false,
      }
    },
    aweme_id: { label: t('dyForm.videoFields.aweme_id'), fieldType: FieldType.Text },
    vedio_url: { label: t('dyForm.videoFields.vedio_url'), fieldType: FieldType.Url },
    create_time: { label: t('dyForm.videoFields.create_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    digg_count: { label: t('dyForm.videoFields.digg_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    comment_count: { label: t('dyForm.videoFields.comment_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    share_count: { label: t('dyForm.videoFields.share_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    collect_count: { label: t('dyForm.videoFields.collect_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    last_get_time: { label: t('dyForm.videoFields.last_get_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    get_interaction_flag: {
      label: t('dyForm.videoFields.get_interaction_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('dyForm.options.interaction.unknow'),
        fail: t('dyForm.options.interaction.fail'),
        success: t('dyForm.options.interaction.success'),
      },
    },
    interaction_fail_reason: { label: t('dyForm.videoFields.interaction_fail_reason'), fieldType: FieldType.Text },
  }),

  extractSecUid: (input) => {
    if (input == null) return '';
    const trimmed = String(input).trim();
    if (!trimmed) return '';
    const m = trimmed.match(/\/user\/([^?#\s/]+)/);
    return m ? m[1] : trimmed;
  },

  isValidSecUid: (secUid) => {
    return typeof secUid === 'string' && (secUid.length === 55 || secUid.length === 76);
  },

  buildAddUserRequest: (searchValue, searchValue2, key) => {
    const secUid = dyPlatformConfig(t).extractSecUid(searchValue);
    return {
      url: '/fbmain/monitor/v3/douyin_user_data',
      body: {
        sec_user_id: secUid,
        share_text: searchValue2,
      },
      params: { key }
    };
  },

  transformAddUserResponse: (data, searchValue, searchValue2, get_time) => {
    const secUid = dyPlatformConfig(t).extractSecUid(searchValue);
    if (secUid && secUid !== searchValue) {
      searchValue = secUid;
    }
    return {
      ...data.data.user,
      get_interaction_flag: 'success',
      last_get_time: get_time,
      get_work_flag: 'unknow',
    };
  },

  buildUpdateUserRequest: (identifier, key) => {
    const secUid = dyPlatformConfig(t).extractSecUid(identifier);
    return {
      url: '/fbmain/monitor/v3/douyin_user_data',
      body: { sec_user_id: secUid },
      params: { key }
    };
  },

  transformUpdateUserResponse: (data, get_time) => ({
    ...data.data.user,
    last_get_time: get_time,
    get_interaction_flag: 'success',
    interaction_fail_reason: '',
  }),

  async fetchWorks(identifier, user_cut_time, searchDays, key, t, i18nPrefix) {
    const secUid = dyPlatformConfig(t).extractSecUid(identifier);
    if (!dyPlatformConfig(t).isValidSecUid(secUid)) {
      return {
        dataList: [],
        totalCost: 0,
        statusData: {
          get_work_flag: 'fail',
          vedio_fail_reason: t(`${i18nPrefix}.messages.invalidSecUid`)
        }
      };
    }

    let totalCost = 0;
    const dataList = [];
    let max_cursor = "";
    let new_cut_time = user_cut_time;

    while (true) {
      const get_time = Date.now();
      const res = await pluginAPI.post('/plugin_forward', {
        url: '/fbmain/monitor/v3/douyin_user_post',
        body: { sec_user_id: secUid, max_cursor },
        params: { key }
      });

      if (!(res && res.data && res.data.code === 0)) {
        return {
          dataList,
          totalCost,
          statusData: {
            get_work_flag: 'fail',
            vedio_fail_reason: res.data.msg || t(`${i18nPrefix}.messages.unknownError`)
          }
        };
      }

      max_cursor = String(res.data.data.max_cursor);
      totalCost += res.data.price;

      const preFilteringData = res.data.data.aweme_list.filter(item => item.is_top != 1 || item.create_time * 1000 > user_cut_time);
      const filteredData = preFilteringData
        .filter(item => item.create_time * 1000 > user_cut_time)
        .map(item => ({
          digg_count: item.statistics.digg_count,
          comment_count: item.statistics.comment_count,
          share_count: item.statistics.share_count,
          collect_count: item.statistics.collect_count,
          caption: item.caption,
          aweme_id: item.aweme_id,
          vedio_url: 'https://www.douyin.com/video/' + item.aweme_id,
          create_time: item.create_time * 1000,
          last_get_time: get_time,
          get_interaction_flag: 'success',
        }));

      new_cut_time = Math.max(...filteredData.map(item => item.create_time), new_cut_time);
      dataList.push(...filteredData);

      if (filteredData.length === 0 || filteredData.length < preFilteringData.length) break;
    }

    return {
      dataList,
      totalCost,
      statusData: { get_work_flag: 'success', vedio_fail_reason: '' }
    };
  },

  buildWorkInteractRequest: (identifier, key) => ({
    url: '/fbmain/monitor/v3/douyin_aweme_detail',
    body: { aweme_id: identifier },
    params: { key }
  }),

  transformWorkInteractResponse: (data, get_time) => ({
    digg_count: data.data.aweme_detail.statistics.digg_count,
    comment_count: data.data.aweme_detail.statistics.comment_count,
    share_count: data.data.aweme_detail.statistics.share_count,
    collect_count: data.data.aweme_detail.statistics.collect_count,
    last_get_time: get_time,
    get_interaction_flag: 'success',
    interaction_fail_reason: '',
  })
});

export const ghPlatformConfig = (t) => ({
  i18nPrefix: 'ghForm',
  userIdentifierField: 'biz',
  workIdentifierField: 'url',
  workTimeField: 'post_time',
  workUniqueKey: 'url',
  showUpdateUser: false,
  
  searchFields: [
    { model: 'searchValue', label: 'ghName', placeholder: 'ghNamePlaceholder' }
  ],
  
  interactionButtons: [
    { label: 'updateArticleInteraction', params: {} }
  ],

  userFields: () => ({
    name: { label: t('ghForm.userFields.name'), fieldType: FieldType.Text, isPrimary: true },
    biz: { label: t('ghForm.userFields.biz'), fieldType: FieldType.Text },
    desc: { label: t('ghForm.userFields.desc'), fieldType: FieldType.Text },
    get_work_flag: {
      label: t('ghForm.userFields.get_work_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('ghForm.options.article.unknow'),
        fail: t('ghForm.options.article.fail'),
        success: t('ghForm.options.article.success'),
      },
    },
    fail_reason: { label: t('ghForm.userFields.fail_reason'), fieldType: FieldType.Text },
  }),

  workFields: (linkTableId = '') => ({
    title: { label: t('ghForm.articleFields.title'), fieldType: FieldType.Text, isPrimary: true },
    user_link: {
      label: t('ghForm.articleFields.gh_link'),
      fieldType: FieldType.SingleLink,
      property: {
        tableId: linkTableId,
        multiple: false,
      }
    },
    url: { label: t('ghForm.articleFields.url'), fieldType: FieldType.Url },
    post_time: { label: t('ghForm.articleFields.post_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    digest: { label: t('ghForm.articleFields.digest'), fieldType: FieldType.Text },
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
    read: { label: t('ghForm.articleFields.read'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    zan: { label: t('ghForm.articleFields.zan'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    looking: { label: t('ghForm.articleFields.looking'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    share_num: { label: t('ghForm.articleFields.share_num'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    collect_num: { label: t('ghForm.articleFields.collect_num'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    comment_count: { label: t('ghForm.articleFields.comment_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    last_get_time: { label: t('ghForm.articleFields.last_get_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    get_interaction_flag: {
      label: t('ghForm.articleFields.get_interaction_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('ghForm.options.interaction.unknow'),
        fail: t('ghForm.options.interaction.fail'),
        success: t('ghForm.options.interaction.success'),
      },
    },
    fail_reason: { label: t('ghForm.articleFields.fail_reason'), fieldType: FieldType.Text },
  }),

  buildAddUserRequest: (searchValue, searchValue2, key) => ({
    url: '/fbmain/monitor/v3/avatar_type',
    body: { name: searchValue, key }
  }),

  transformAddUserResponse: (data, searchValue, searchValue2, get_time) => ({
    ...data.data,
    get_work_flag: 'unknow'
  }),

  async fetchWorks(identifier, user_cut_time, searchDays, key, t, i18nPrefix) {
    let totalCost = 0;
    const dataList = [];

    if (searchDays === 1) {
      const res = await pluginAPI.post('/plugin_forward', {
        url: '/fbmain/monitor/v3/post_condition',
        body: { biz: identifier, key }
      });

      if (!(res && res.data && res.data.code === 0)) {
        return {
          dataList,
          totalCost: res.data?.cost_money || 0,
          statusData: {
            get_work_flag: 'fail',
            fail_reason: res.data.msg || t(`${i18nPrefix}.messages.unknownError`)
          }
        };
      }

      totalCost += res.data.cost_money;
      const filteredData = res.data.data
        .filter(item => item.post_time * 1000 > user_cut_time)
        .map(item => ({
          ...item,
          post_time: item.post_time * 1000,
          get_interaction_flag: 'unknow'
        }));
      dataList.push(...filteredData);
    } else {
      let i = 0;
      while (true) {
        i++;
        const res = await pluginAPI.post('/plugin_forward', {
          url: '/fbmain/monitor/v3/post_history',
          body: { biz: identifier, key, page: i }
        });

        if (!(res && res.data && res.data.code === 0)) {
          return {
            dataList,
            totalCost,
            statusData: {
              get_work_flag: 'fail',
              fail_reason: res.data.msg || t(`${i18nPrefix}.messages.unknownError`)
            }
          };
        }

        totalCost += res.data.cost_money;
        const filteredData = res.data.data
          .filter(item => item.post_time * 1000 > user_cut_time)
          .map(item => ({
            ...item,
            post_time: item.post_time * 1000,
            get_interaction_flag: 'unknow'
          }));
        dataList.push(...filteredData);

        if (filteredData.length === 0 || filteredData.length < res.data.data.length || res.data.now_page >= res.data.total_page) break;
      }
    }

    return {
      dataList,
      totalCost,
      statusData: { get_work_flag: 'success', fail_reason: '' }
    };
  },

  buildWorkInteractRequest: (identifier, key) => ({
    url: '/fbmain/monitor/v3/read_zan_pro',
    body: { url: identifier, key }
  }),

  transformWorkInteractResponse: (data, get_time) => ({
    ...data.data,
    last_get_time: get_time,
    get_interaction_flag: 'success',
    fail_reason: '',
  })
});

export const ksPlatformConfig = (t) => ({
  i18nPrefix: 'ksForm',
  userIdentifierField: 'user_id',
  workIdentifierField: 'eid',
  workTimeField: 'timestamp',
  workUniqueKey: 'photo_id',
  showUpdateUser: true,
  
  searchFields: [
    { model: 'searchValue', label: 'shareLink', placeholder: 'shareLinkPlaceholder' }
  ],
  
  interactionButtons: [
    { label: 'updateWorkInteraction', params: {} }
  ],

  userFields: () => ({
    user_name: { label: t('ksForm.userFields.user_name'), fieldType: FieldType.Text, isPrimary: true },
    user_id: { label: t('ksForm.userFields.user_id'), fieldType: FieldType.Text },
    eid: { label: t('ksForm.userFields.eid'), fieldType: FieldType.Text },
    kwaiId: { label: t('ksForm.userFields.kwaiId'), fieldType: FieldType.Text },
    user_text: { label: t('ksForm.userFields.user_text'), fieldType: FieldType.Text },
    fan: { label: t('ksForm.userFields.fan'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    follow: { label: t('ksForm.userFields.follow'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    photo: { label: t('ksForm.userFields.photo'), fieldType: FieldType.Text },
    cityName: { label: t('ksForm.userFields.cityName'), fieldType: FieldType.Text },
    shareLink: { label: t('ksForm.userFields.shareLink'), fieldType: FieldType.Url },
    last_get_time: { label: t('ksForm.workFields.last_get_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    get_interaction_flag: {
      label: t('ksForm.userFields.get_interaction_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('ksForm.options.interaction.unknow'),
        fail: t('ksForm.options.interaction.fail'),
        success: t('ksForm.options.interaction.success'),
      },
    },
    interaction_fail_reason: { label: t('ksForm.userFields.interaction_fail_reason'), fieldType: FieldType.Text },
    get_work_flag: {
      label: t('ksForm.userFields.get_work_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('ksForm.options.work.unknow'),
        fail: t('ksForm.options.work.fail'),
        success: t('ksForm.options.work.success'),
      },
    },
    work_fail_reason: { label: t('ksForm.userFields.work_fail_reason'), fieldType: FieldType.Text },
  }),

  workFields: (linkTableId = '') => ({
    caption: { label: t('ksForm.workFields.caption'), fieldType: FieldType.Text, isPrimary: true },
    user_link: {
      label: t('ksForm.workFields.user_link'),
      fieldType: FieldType.SingleLink,
      property: {
        tableId: linkTableId,
        multiple: false,
      }
    },
    photo_id: { label: t('ksForm.workFields.photo_id'), fieldType: FieldType.Text },
    eid: { label: t('ksForm.workFields.eid'), fieldType: FieldType.Text },
    timestamp: { label: t('ksForm.workFields.timestamp'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    like_count: { label: t('ksForm.workFields.like_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    view_count: { label: t('ksForm.workFields.view_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    forward_count: { label: t('ksForm.workFields.forward_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    comment_count: { label: t('ksForm.workFields.comment_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    last_get_time: { label: t('ksForm.workFields.last_get_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    get_interaction_flag: {
      label: t('ksForm.workFields.get_interaction_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('ksForm.options.interaction.unknow'),
        fail: t('ksForm.options.interaction.fail'),
        success: t('ksForm.options.interaction.success'),
      },
    },
    interaction_fail_reason: { label: t('ksForm.workFields.interaction_fail_reason'), fieldType: FieldType.Text },
  }),

  buildAddUserRequest: (searchValue, searchValue2, key) => ({
    url: '/fbmain/monitor/v3/ks_user_data_v2',
    body: { share_text: searchValue, key }
  }),

  transformAddUserResponse: (data, searchValue, searchValue2, get_time) => ({
    ...data.data.ownerCount,
    ...data.data.profile,
    cityName: data.data.cityName,
    shareLink: searchValue,
    get_work_flag: 'unknow',
    get_interaction_flag: 'success',
    last_get_time: get_time,
  }),

  buildUpdateUserRequest: (identifier, key) => ({
    url: '/fbmain/monitor/v3/ks_user_data_v2',
    body: { share_text: identifier, key }
  }),

  transformUpdateUserResponse: (data, get_time, searchValue) => ({
    ...data.data.ownerCount,
    ...data.data.profile,
    cityName: data.data.cityName,
    shareLink: searchValue,
    last_get_time: get_time,
    get_interaction_flag: 'success',
    interaction_fail_reason: '',
  }),

  async fetchWorks(identifier, user_cut_time, searchDays, key, t, i18nPrefix) {
    let totalCost = 0;
    const dataList = [];
    let last_buffer = "";

    while (true) {
      const get_time = Date.now();
      const res = await pluginAPI.post('/plugin_forward', {
        url: '/fbmain/monitor/v3/ks_user_post_v1',
        body: { uid: identifier, pcursor: last_buffer, key }
      });

      if (!(res && res.data && res.data.code === 0)) {
        return {
          dataList,
          totalCost,
          statusData: {
            get_work_flag: 'fail',
            fail_reason: res.data.msg || t(`${i18nPrefix}.messages.unknownError`)
          }
        };
      }

      last_buffer = res.data.data.pcursor;
      totalCost += res.data.price;

      const preProcessingData = res.data.data.feeds || [];
      const filteredData = preProcessingData
        .filter(item => item.timestamp > user_cut_time)
        .map(item => {
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
            last_get_time: get_time,
            get_interaction_flag: 'success',
          };
        });

      dataList.push(...filteredData);

      if (filteredData.length === 0 || filteredData.length < preProcessingData.length) break;
    }

    return {
      dataList,
      totalCost,
      statusData: { get_work_flag: 'success', fail_reason: '' }
    };
  },

  buildWorkInteractRequest: (identifier, key) => ({
    url: '/fbmain/monitor/v3/ks_video_detail',
    body: { share_text: "https://www.kuaishou.com/short-video/" + identifier, key }
  }),

  transformWorkInteractResponse: (data, get_time) => ({
    caption: data.data[0].caption,
    like_count: data.data[0].likeCount,
    view_count: data.data[0].viewCount,
    forward_count: data.data[0].forwardCount,
    comment_count: data.data[0].commentCount,
    last_get_time: get_time,
    get_interaction_flag: 'success',
    fail_reason: '',
  })
});

export const v2PlatformConfig = (t) => ({
  i18nPrefix: 'v2Form',
  userIdentifierField: 'username',
  workIdentifierField: 'object_id',
  workTimeField: 'publish_time',
  workUniqueKey: 'object_id',
  showUpdateUser: false,
  
  searchFields: [
    { model: 'searchValue', label: 'v2Name', placeholder: 'v2NamePlaceholder' }
  ],
  
  interactionButtons: [
    { label: 'updateWorkInteraction', params: { type: 9 } },
    { label: 'updateWorkInteractionWithDownload', params: { type: 3 } }
  ],

  userFields: () => ({
    nickname: { label: t('v2Form.userFields.nickname'), fieldType: FieldType.Text, isPrimary: true },
    username: { label: t('v2Form.userFields.username'), fieldType: FieldType.Text },
    signature: { label: t('v2Form.userFields.signature'), fieldType: FieldType.Text },
    get_work_flag: {
      label: t('v2Form.userFields.get_work_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('v2Form.options.work.unknow'),
        fail: t('v2Form.options.work.fail'),
        success: t('v2Form.options.work.success'),
      },
    },
    fail_reason: { label: t('v2Form.userFields.fail_reason'), fieldType: FieldType.Text },
  }),

  workFields: (linkTableId = '') => ({
    title: { label: t('v2Form.workFields.title'), fieldType: FieldType.Text, isPrimary: true },
    user_link: {
      label: t('v2Form.workFields.user_link'),
      fieldType: FieldType.SingleLink,
      property: {
        tableId: linkTableId,
        multiple: false,
      }
    },
    object_id: { label: t('v2Form.workFields.object_id'), fieldType: FieldType.Text },
    export_id: { label: t('v2Form.workFields.export_id'), fieldType: FieldType.Text },
    publish_time: { label: t('v2Form.workFields.publish_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    video_play_len: { label: t('v2Form.workFields.video_play_len'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    like_count: { label: t('v2Form.workFields.like_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    fav_count: { label: t('v2Form.workFields.fav_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    forward_count: { label: t('v2Form.workFields.forward_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    comment_count: { label: t('v2Form.workFields.comment_count'), fieldType: FieldType.Number, property: { formatter: NumberFormatter.INTEGER } },
    download_url: { label: t('v2Form.workFields.download_url'), fieldType: FieldType.Url },
    last_get_time: { label: t('v2Form.workFields.last_get_time'), fieldType: FieldType.DateTime, property: { dateFormat: DateFormatter.DATE_TIME } },
    get_interaction_flag: {
      label: t('v2Form.workFields.get_interaction_flag'),
      fieldType: FieldType.SingleSelect,
      options: {
        unknow: t('v2Form.options.interaction.unknow'),
        fail: t('v2Form.options.interaction.fail'),
        success: t('v2Form.options.interaction.success'),
      },
    },
    fail_reason: { label: t('v2Form.workFields.fail_reason'), fieldType: FieldType.Text },
  }),

  getTimeFromStr: (dateStr) => {
    if (!dateStr) return 0;
    const date = new Date(dateStr);
    return date.getTime();
  },

  buildAddUserRequest: (searchValue, searchValue2, key) => ({
    url: '/fbmain/monitor/v3/wxvideo',
    body: { keywords: searchValue, type: 6, key }
  }),

  transformAddUserResponse: (data, searchValue, searchValue2, get_time) => ({
    ...data.v2_info_list.contact,
    get_work_flag: 'unknow'
  }),

  async fetchWorks(identifier, user_cut_time, searchDays, key, t, i18nPrefix) {
    let totalCost = 0;
    const dataList = [];
    let last_buffer = "";

    while (true) {
      const get_time = Date.now();
      const res = await pluginAPI.post('/plugin_forward', {
        url: '/fbmain/monitor/v3/wxvideo',
        body: { v2_name: identifier, type: 1, last_buffer, key }
      });

      if (!(res && res.data && res.data.code === 0)) {
        return {
          dataList,
          totalCost,
          statusData: {
            get_work_flag: 'fail',
            fail_reason: res.data.msg || t(`${i18nPrefix}.messages.unknownError`)
          }
        };
      }

      last_buffer = res.data.last_buffer;
      totalCost += res.data.cost;

      const preFilteringData = res.data.object.filter(item => !item.sticky_time || v2PlatformConfig(t).getTimeFromStr(item.publish_time) > user_cut_time);
      const filteredData = preFilteringData
        .filter(item => v2PlatformConfig(t).getTimeFromStr(item.publish_time) > user_cut_time)
        .map(item => ({
          object_id: item.object_id,
          export_id: item.export_id,
          title: item.title,
          publish_time: v2PlatformConfig(t).getTimeFromStr(item.publish_time),
          fav_count: item.fav_count,
          like_count: item.like_count,
          forward_count: item.forward_count,
          comment_count: item.comment_count,
          video_play_len: item.video_play_len,
          last_get_time: get_time,
          get_interaction_flag: 'success',
        }));

      dataList.push(...filteredData);

      if (filteredData.length === 0 || filteredData.length < preFilteringData.length || res.data.continue_flag === 0) break;
    }

    return {
      dataList,
      totalCost,
      statusData: { get_work_flag: 'success', fail_reason: '' }
    };
  },

  buildWorkInteractRequest: (identifier, key, extraParams) => ({
    url: '/fbmain/monitor/v3/wxvideo',
    body: { object_id: identifier, key, type: extraParams.type || 9 }
  }),

  transformWorkInteractResponse: (data, get_time, extraParams) => {
    if (extraParams.type === 3) {
      return {
        fav_count: data.fav_count,
        like_count: data.like_count,
        forward_count: data.forward_count,
        comment_count: data.comment_count,
        download_url: data.download_url,
        last_get_time: get_time,
        get_interaction_flag: 'success',
        fail_reason: '',
      };
    }
    return {
      fav_count: data.count_info.fav_count,
      like_count: data.count_info.like_count,
      forward_count: data.count_info.forward_count,
      comment_count: data.count_info.comment_count,
      last_get_time: get_time,
      get_interaction_flag: 'success',
      fail_reason: '',
    };
  }
});