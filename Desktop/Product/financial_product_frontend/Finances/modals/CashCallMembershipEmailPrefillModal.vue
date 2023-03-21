<template>
  <validation-observer v-slot="{ invalid }">
    <div>
      <b-modal
        v-model="showModal"
        size="lg"
        content-class="shadow-lg"
        cancel-variant="outline-secondary"
        @hidden="hide"
      >
        <template #modal-header>
          <b-container fluid>
            <b-row>
              <b-col cols="12">
                <h5 class="mt-2">Prepare cash call email</h5>
              </b-col>
            </b-row>
            <hr />
          </b-container>
        </template>
        <b-container fluid v-if="!isEmpty(bill)">
          <b-row class="mb-4">
            <b-col cols="12">
              <div
                class="border overflow-auto"
                style="height: 250px; resize: vertical"
                v-html="email_template.htmlContent"
              ></div>
            </b-col>
          </b-row>
          <b-row>
            <b-col cols="6">
              <new-form-input
                label="Investor name"
                v-model="cashcall.investor_name"
                :initialValue="cashcall.investor_name"
                rules="required"
              ></new-form-input>
            </b-col>
          </b-row>
          <b-row>
            <b-col cols="6">
              <label class="mb-0"><b>Fees type</b></label>
              <div class="data-box">{{ cashcall.fees_type }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Membership fee type</b></label>
              <div class="data-box">
                {{ bill.investor ? investorMembershipType : 'No investor linked' }}
              </div>
            </b-col>
          </b-row>
          <hr />
          <b-row class="mb-3">
            <b-col cols="12">
              <h3 class="mb-3">
                Total fees:
                <span class="float-right">€{{ formatNumber(totalFees) }}</span>
              </h3>
              <h3>
                Total transferred:
                <span class="float-right">€{{ formatNumber(totalTransfered) }}</span>
              </h3>
            </b-col>
          </b-row>
          <hr />
          <b-row>
            <b-col cols="12">
              <new-form-input
                label="Add team members in copy to the email"
                v-model="cashcall.cc_emails"
                :initialValue="cashcall.cc_emails"
                rules="multiple_emails"
              ></new-form-input>
            </b-col>
          </b-row>
        </b-container>
        <template #modal-footer="{ cancel }">
          <b-container fluid>
            <b-row>
              <b-col>
                <btn
                  :disabled="invalid"
                  size="fluid"
                  :color="!invalid ? 'red-gradient' : 'grey'"
                  @click="saveSingleEntity()"
                  >Prepare cash call</btn
                >
              </b-col>
              <b-col>
                <btn size="fluid" color="dark-grey" @click="cancel">Cancel</btn>
              </b-col>
            </b-row>
          </b-container>
        </template>
      </b-modal>
    </div>
  </validation-observer>
</template>

<script>
import { ValidationObserver } from 'vee-validate';
import { mapActions, mapMutations } from 'vuex';

export default {
  name: 'CashCallMembershipEmailPrefill',
  components: {
    'validation-observer': ValidationObserver,
  },
  props: {
    show: {
      type: Boolean,
      required: true,
      default: false,
    },
    bill: {
      type: Object,
      default: () => {},
    },
  },
  watch: {
    show(new_val) {
      this.showModal = new_val;
    },
    bill(newVal) {
      if (!this.isEmpty(newVal)) {
        this.manageBillData();
        this.getEmailTemplate();
      }
    },
  },
  computed: {
    investorMembershipType() {
      let type = null;
      const { investor } = this.bill;
      if (investor.advanced_investment_fee && investor.community_fee) {
        type = 'Full membership';
      } else if (investor.advanced_investment_fee && !investor.community_fee) {
        type = 'Advance on investment';
      } else if (!investor.advanced_investment_fee && investor.community_fee) {
        type = 'Community access';
      } else {
        type = 'Exempted';
      }
      return type;
    },
    totalFees() {
      return Number(this.cashcall.committed_amount);
    },
    totalTransfered() {
      return this.totalFees;
    },
  },
  data() {
    return {
      showModal: false,
      cashcall: {
        id: null,
        investor: null,
        investor_name: null,
        committed_amount: null,
        fees_type: null,
        cc_emails: null,
        sendinblue_template_id: null,
      },
      email_template: {
        htmlContent: null,
      },
      templatesIds: {
        EN: {
          membership_fees: 103,
        },
        FR: {
          membership_fees: 126,
        },
      },
      membershipAmounts: {
        'Full membership': 2000,
        'Advance on investment': 1200,
        'Community access': 800,
        Exempted: 0,
      },
    };
  },
  methods: {
    ...mapActions(['checkCashcallAndSave', 'getInvestorLanguagePreference']),
    ...mapMutations(['updateBillinTable']),
    async getEmailTemplate() {
      if (!this.isEmpty(this.bill.investor)) {
        const languagePreference = await this.getInvestorLanguagePreference(this.bill.investor.id);

        const templateId = this.templatesIds[languagePreference].membership_fees;
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
            this.sendinblue_template_id = templateId;
            this.email_template = json;
          }),
        );
      }
    },
    assignSingleBill() {
      // To adapt total fees and amounts when there is already a cashcall
      if (this.bill.cashcall) {
        this.cashcall = {
          ...this.bill.cashcall,
          cc_emails: this.json_to_emails(this.bill.cc_emails),
          investor: this.bill.investor.id,
        };
        this.cashcall.fees_type = this.bill.type;
      } else {
        this.cashcall.investor_name = this.bill.investor ? this.bill.investor.name : null;
        this.cashcall.fees_type = this.bill.type;
      }
      this.setMembershipFeesAmount();
    },
    setMembershipFeesAmount() {
      if (this.bill.investor) {
        this.cashcall.committed_amount = this.membershipAmounts[this.investorMembershipType];
      }
    },
    hide() {
      (this.cashcall = {
        id: null,
        investor: null,
        investor_name: null,
        committed_amount: null,
        fees_type: null,
        cc_emails: null,
        sendinblue_template_id: null,
      }),
      (this.email_template = {
        htmlContent: null,
      }),
      (this.showModal = false);
      this.$emit('hidden');
    },
    emails_to_json(value) {
      if (value) {
        const splited_values = value.replace(/\s+/g, '').split(',');
        return JSON.stringify(splited_values);
      }
      return '';
    },
    json_to_emails(value) {
      try {
        value = value ? JSON.parse(value).join(',') : null;
      } catch (e) {
        value = value || null;
      }
      return value;
    },
    saveSingleEntity() {
      this.checkCashcallAndSave({
        cashcall: {
          ...this.cashcall,
          cc_emails: this.emails_to_json(this.cc_emails),
          committed_amount: this.bill.amount_due,
          fees_amount: this.bill.fees_amount_due,
          investor: !this.isEmpty(this.bill.investor) ? this.bill.investor.id : null,
          bill: this.bill.id,
        },
        bill_id: this.bill.id,
      }).then(
        (response) => {
          this.$store.dispatch('triggerAlert', {
            show: true,
            type: 'success',
            message: 'The email was correctly prepared.',
          });
          this.loading = false;

          const updatedBill = {
            id: this.bill.id,
            cashcall: response.data,
          };
          this.updateBillinTable(updatedBill);
          this.hide();
        },
        (error) => {
          this.$store.dispatch('triggerAlert', {
            show: true,
            type: 'danger',
            message: 'Error! The email could not be prepared.',
          });
        },
      );
    },
    manageBillData() {
      this.assignSingleBill();
    },
  },
  mounted() {
    if (!this.isEmpty(this.bill)) {
      this.manageBillData();
      this.getEmailTemplate();
    }
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';
.modal-header {
  padding-bottom: 0px !important;
}

.bills-header {
  font: $main-font-bold;
}

.data-box {
  height: 35px;
  margin: 12px 0 0 10px;
  font-size: 13px;
}
</style>
