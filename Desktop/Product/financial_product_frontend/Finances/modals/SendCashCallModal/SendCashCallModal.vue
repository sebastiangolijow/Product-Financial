<template>
  <b-modal
    class-content="modal-white"
    v-model="showModal"
    size="lg"
    hide-footer
    @hidden="hide"
    content-class="shadow border-0"
    body-class="p-0"
  >
    <template #modal-title>
      <h3 class="font-weight-bold">Send cash call</h3>
    </template>
    <hr class="px-5 small-hr" />
    <div class="p-5">
      <check-bill v-show="selectedTab == 'check bill'" :billFile="billFile" :multiple="multiple">
      </check-bill>
      <check-email v-show="selectedTab == 'check email'" :bill="bill" spv_country="FR">
      </check-email>
      <send-cash-call
        v-show="selectedTab == 'send cash call'"
        :investor-email="investor_email"
        :copy-emails="cc_emails"
        :cashcall_id="bill.cashcall ? bill.cashcall.id : null"
        :bill_id="bill.id"
        @hide="hide"
      >
      </send-cash-call>
    </div>
    <tabs-menu :tabs="tabs" @switch-tab="switchTab"> </tabs-menu>
  </b-modal>
</template>

<script>
import { mapActions, mapGetters, mapMutations } from 'vuex';
import TabsMenu from '@/components/utils/TabsMenu';
import CheckBill from '@/components/Pages/Finances/modals/SendCashCallModal/steps/CheckBill';
import CheckEmail from '@/components/Pages/Finances/modals/SendCashCallModal/steps/CheckEmail';
import SendCashCall from '@/components/Pages/Finances/modals/SendCashCallModal/steps/SendCashCall';
import bills from '@/components/lib/mixins/bills.js';

export default {
  name: 'SendCashCallModal',
  mixins: [bills],
  components: {
    'tabs-menu': TabsMenu,
    'check-bill': CheckBill,
    'check-email': CheckEmail,
    'send-cash-call': SendCashCall,
  },
  props: {
    show: {
      type: Boolean,
      required: true,
      default: false,
    },
    bill: {
      type: Object,
      default: null,
    },
  },
  watch: {
    show(newVal) {
      this.showModal = newVal;
    },
    bill(newVal) {
      if (!this.isEmpty(newVal)) {
        this.updateData();
      }
    },
    getInvestor() {
      this.setBillFile();
    },
  },
  computed: {
    ...mapGetters(['getDataSendEmailModal', 'getInvestorOwnerContact', 'getInvestor']),
    investor_email() {
      return this.getInvestorOwnerContact.length > 1
        ? 'More than one owner investor'
        : this.getInvestorOwnerContact.length > 0
          ? this.getInvestorOwnerContact[0].user.email
          : 'No email found';
    },
    cc_emails() {
      return this.bill?.cc_emails || 'no emails found';
    },
    multiple() {
      return !!this.bill.related_bills;
    },
  },
  data() {
    return {
      billFile: null,
      showModal: false,
      selectedTab: 'check bill',
      tabs: [
        {
          var: 'check bill',
          icon: 'fal fa-file-invoice-dollar',
        },
        {
          var: 'check email',
          icon: 'fal fa-envelope',
        },
        {
          var: 'send cash call',
          icon: 'fal fa-check-circle',
        },
      ],
    };
  },
  methods: {
    ...mapMutations(['setInvestorInfo']),
    ...mapActions(['getInvestorData', 'getInvestorLanguagePreference']),
    switchTab(tab) {
      this.selectedTab = tab;
    },
    hide() {
      this.selectedTab = 'check bill';
      this.showModal = false;
      this.$emit('hidden');
    },
    updateData() {
      if (this.bill.investor) {
        this.getInvestorData(this.bill.investor.id);
      } else {
        this.setInvestorInfo(null);
      }
    },
    setBillFile() {
      if (this.bill && this.bill.file) {
        this.billFile = this.bill.file;
      } else if (!this.isEmpty(this.bill)) {
        this.getInvestorLanguagePreference(this.bill.investor.id).then((response) => {
          const billFileTemplate = this.billFileTemplates[response][this.getInvestor.kyc.type][
            this.bill.type
          ];
          this.billFile = billFileTemplate
            || 'https://img.oneragtime.com/uploads/2021/02/EN_upfront_fees_invoice_natural.pdf';
        });
      }
    },
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.small-hr {
  margin-top: -10px;
  width: 86%;
}
</style>
