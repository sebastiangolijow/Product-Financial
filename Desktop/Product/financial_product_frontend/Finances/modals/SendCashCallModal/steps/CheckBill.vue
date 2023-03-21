<template>
  <section>
    <div class="img-container">
      <object
        v-if="billFile"
        class="w-100"
        style="height: 300px; resize: vertical"
        :data="billFile"
        type="application/pdf"
        width="300"
        height="200"
      >
        alt : <a :href="billFile">bill.pdf</a>
      </object>
      <div v-else-if="multiple">
        This email has multiple bills related. You can check each individual bill related to this
        email by going back to the general table
      </div>
      <div v-else>No bill available</div>
    </div>
    <hr />
  </section>
</template>

<script>
export default {
  name: 'CheckBill',
  props: {
    billFile: {
      required: true,
      default: null,
    },
    multiple: {
      type: Boolean,
      default: false,
    },
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
