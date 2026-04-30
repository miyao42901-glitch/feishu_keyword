<script>
import { useI18n } from 'vue-i18n';
import BaseForm from './BaseForm.vue';
import { ghPlatformConfig } from '@/configs/platformConfigs';

export default {
  components: {
    BaseForm
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
    const platformConfig = ghPlatformConfig(t);

    return {
      platformConfig,
      formData: props.formData,
      isLocked: props.isLocked,
      emit
    };
  }
};
</script>

<template>
  <BaseForm
    :form-data="formData"
    :is-locked="isLocked"
    :platform-config="platformConfig"
    @update:is-locked="emit('update:isLocked', $event)"
  />
</template>