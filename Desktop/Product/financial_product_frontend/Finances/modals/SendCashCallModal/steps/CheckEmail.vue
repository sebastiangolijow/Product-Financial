<template>
  <section>
    <div
      v-if="template_id"
      class="border overflow-auto"
      style="height: 500px; resize: vertical;"
      v-html="email_template.htmlContent"
    ></div>
    <div v-else>No email template available</div>
    <br />
  </section>
</template>

<script>
export default {
  name: 'CheckEmail',
  props: {
    bill: {
      type: Object,
      required: true,
      default: null,
    },
  },
  data() {
    return {
      isEditOn: false,
      email_template: {
        htmlContent: null,
      },
      template_id: null,
    };
  },
  methods: {
    getEmailTemplate(templateId) {
      const options = {
        method: 'GET',
        headers: new Headers({
          'Content-Type': 'application/json',
          'api-key':
            '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',
        }),
        mode: 'cors',
        cache: 'default',
      };
      fetch(`https://api.sendinblue.com/v3/smtp/templates/${templateId}`, options).then(
        (response) => response.json().then((json) => {
          this.email_template = json;
        }),
      );
    },
  },
  mounted() {
    if (this.bill?.sendinblue_template_id) {
      this.template_id = this.bill.sendinblue_template_id;
      this.getEmailTemplate(this.bill.sendinblue_template_id);
    }
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.img-container {
  width: 90%;
  margin: 10px 5%;
  max-height: 60vh;
  overflow-y: scroll;
  .detail-img {
    width: 100%;
    height: auto;
  }
}
</style>
