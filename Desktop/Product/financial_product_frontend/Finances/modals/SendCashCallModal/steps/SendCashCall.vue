<template>
  <section>
    <div class="my-5 mx-auto w-50 text-center">
      <p>
        Make sure you have checked all the files before sending the cash call to:
      </p>
      <br />
      <p class="my-0">
        <b>Primary receiver: {{ investorEmail }}</b>
      </p>
      <p class="my-0">In copy: {{ inCopy }}</p>
    </div>
    <hr />
    <div class="d-flex btn-container my-5 px-5">
      <btn
        :loading="sendingCashcall"
        :disabled="sendingCashcall"
        class="mx-auto"
        color="red-gradient"
        @click="finishCashcall(cashcall_id)"
      >
        Send cash call
      </btn>
      <btn class="mx-auto" color="white" @click="hideModal"> Cancel </btn>
    </div>
  </section>
</template>

<script>
import { mapActions, mapMutations } from 'vuex';

export default {
  name: 'SendCashCall',
  props: {
    'investor-email': {
      type: String,
    },
    'copy-emails': {
      type: String,
    },
    bbc: {
      type: String,
    },
    cashcall_id: {
      type: Number,
    },
    bill_id: {
      type: Number,
    },
  },
  data() {
    return {
      sendingCashcall: false,
    };
  },
  computed: {
    inCopy() {
      if (this.copyEmails) {
        return this.copyEmails
          .replaceAll('"', '')
          .replaceAll('[', '')
          .replaceAll(']', '')
          .replaceAll(',', ', ');
      }
      return 'No emails in copy';
    },
  },
  methods: {
    ...mapActions(['sendCashCall', 'getSingleBill']),
    ...mapMutations(['updateBillinTable']),
    hideModal() {
      this.$emit('hide');
    },
    finishCashcall(id) {
      if (id != null) {
        this.sendingCashcall = true;
        this.sendCashCall(id).then(
          () => {
            this.updateTable();
          },
          () => {
            this.sendingCashcall = false;
          },
        );
      } else {
        this.$store.dispatch('triggerAlert', {
          show: true,
          type: 'danger',
          message: 'Error! The Bill does not have an assigned CashCall',
        });
      }
    },
    updateTable() {
      this.getSingleBill({ id: this.bill_id }).then((response) => {
        this.updateBillinTable(response.data);
        this.sendingCashcall = false;
        this.hideModal();
      });
    },
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.btn-container {
  width: 90%;
  margin: auto;
  button {
    width: 40%;
    font-size: 16px;
  }
}
hr {
  width: 95%;
}
</style>
