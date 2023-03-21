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
          <!-- This has dummy data, to adapt -->
          <b-row>
            <b-col cols="6">
              <new-form-input
                label="Investor name"
                v-model="cashcall.investor_name"
                :initialValue="cashcall.investor_name"
                rules="required"
              ></new-form-input>
            </b-col>
            <b-col cols="6" v-if="spv_country == 'FR'">
                <label class="mb-0"><b>Company Name</b></label>
              <div class="data-box">{{ cashcall.company_name }}</div>
            </b-col>
          </b-row>
          <b-row v-if="spv_country == 'FR'">
            <b-col cols="6">
              <label class="mb-0"><b>Fees type</b></label>
              <div class="data-box">{{ cashcall.fees_type }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Fees Percentage</b></label>
              <div class="data-box">{{ cashcall.fees_percentage }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Commited amount</b></label>
              <div class="data-box">{{ cashcall.committed_amount }}</div>
            </b-col>
          </b-row>
          <hr />
          <b-row class="mb-3">
            <b-col cols="12">
              <h3 class="mb-3">
                Total fees:
                <span class="float-right">{{ currencySign + formatNumber(totalFees) }}</span>
              </h3>
              <h3>
                Total transferred:
                <span class="float-right">{{ currencySign + formatNumber(totalTransfered) }}</span>
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
import { mapGetters, mapActions, mapMutations } from 'vuex';
import moment from 'moment';
import axios from 'axios';

export default {
  name: 'CashCallEmailPrefill',
  components: {
    'validation-observer': ValidationObserver,
  },
  props: {
    show: {
      type: Boolean,
      required: true,
      default: false,
    },
    spv_country: {
      type: String,
      required: true,
      default: null,
    },
    bill: {
      type: Object,
      default: () => {},
    },
  },
  watch: {
    show(newVal) {
      this.showModal = newVal;
    },
    bill(newVal) {
      if (!this.isEmpty(newVal)) {
        this.assignSingleBill();
        this.getEmailTemplate();
      }
    },
  },
  computed: {
    ...mapGetters(['currencies']),
    isBillManagementFees() {
      return this.bill.type === 'management_fees';
    },
    isInvestmentCurrentYear() {
      const investmentYear = moment(this.bill.investment.creation_datetime).format('YYYY');
      return investmentYear.toString() === new Date().getFullYear().toString();
    },
    isManagementFeesAndIsNotCurrentYear() {
      return this.isBillManagementFees && !this.isInvestmentCurrentYear;
    },
    totalFees() {
      return this.totalAmountOfFees;
    },
    totalTransfered() {
      const committedAmount = Number(this.cashcall.committed_amount);
      const amountToSum = this.isManagementFeesAndIsNotCurrentYear ? 0 : committedAmount;
      return this.totalFees + amountToSum;
    },
    currencySign() {
      const hasFundraisingInfo = this.bill.investment && this.bill.investment.fundraising;
      if (hasFundraisingInfo) {
        const currencyId = this.bill.investment.fundraising.currency;
        const currencyName = this.currencies.find(
          (select) => select.id.toString() === currencyId.toString(),
        ).name;
        return currencyName === 'USD' ? '$' : '€';
      }
      return '€';
    },
  },
  data() {
    return {
      showModal: false,
      cashcall: {
        id: null,
        investor: null,
        investor_name: null,
        company_name: null,
        committed_amount: null,
        fees_type: null,
        fees_percentage: null,
        cc_emails: null,
        sendinblue_template_id: null,
      },
      totalAmountOfFees: null,
      email_template: {
        htmlContent: null,
      },
      templatesIds: {
        EN: {
          management_fees: 364,
          rhapsody_fees: 219,
          membership_fees: 103,
          upfront_fees: 216,
        },
        FR: {
          management_fees: 364,
          rhapsody_fees: 239,
          membership_fees: 126,
          upfront_fees: 240,
        },
      },
    };
  },
  methods: {
    ...mapActions(['createCashcall', 'getInvestorLanguagePreference', 'updateInvestment', 'getSingleBill']),
    ...mapMutations(['updateBillinTable', 'setBill']),
    async getEmailTemplate() {
      if (!this.isEmpty(this.bill.investor)) {
        const languagePreference = await this.getInvestorLanguagePreference(this.bill.investor.id);
        const templateId = this.templatesIds[languagePreference][this.bill.type];
        const url = `https://api.sendinblue.com/v3/smtp/templates/${templateId}`;
        const config = {
          method: 'get',
          headers: {
            'Content-Type': 'application/json',
            'api-key':
              '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',
          },
          mode: 'cors',
          cache: 'default',
          url,
        };

        axios(config).then(
          (response) => response.json().then(
            (json) => {
              this.bill.sendinblue_template_id = templateId;
              this.email_template = json;
            },
          ),
        ).catch(
          (err) => {
            console.log(err);
          },
        );
      }
    },
    assignSingleBill() {
      if (this.bill.cashcall) {
        this.cashcall = {
          ...this.bill.cashcall,
          cc_emails: this.json_to_emails(this.bill.cc_emails),
          investor: this.bill.investor.id,
          investor_name: this.bill.investor_name,
        };
        this.cashcall.fees_type = this.bill.type;
      } else {
        this.investor_name = this.bill.investor ? this.bill.investor.name : null;
        this.cashcall.fees_type = this.bill.type;
      }
      if (this.bill.investment) {
        this.cashcall.committed_amount = this.bill.investment.committed_amount;
      }
      if (this.bill.investment && !this.isManagementFeesAndIsNotCurrentYear) {
        this.cashcall.fees_percentage = this.bill.investment.fees_percentage;
      }
      if (this.bill.investment && this.bill.investment.fundraising) {
        this.cashcall.company_name = this.bill.investment.fundraising.name;
      }
      this.setTotalAmounts();
    },
    setTotalAmounts() {
      const amount = this.cashcall.committed_amount;
      const feesPercentage = this.cashcall.fees_percentage;
      const params = `amount=${amount}&fees_percentage=${feesPercentage}`;
      this.apiGetV3(`/bills/${this.bill.id}/cash_call_calculate_amounts?${params}`).then(
        (response) => {
          this.totalAmountOfFees = response.data.fees_amount;
        },
      );
    },
    hide() {
      this.cashcall = {
        id: null,
        investor: null,
        investor_name: null,
        company_name: null,
        committed_amount: null,
        fees_type: null,
        fees_percentage: null,
        cc_emails: null,
        sendinblue_template_id: null,
      };
      this.totalAmountOfFees = null;
      this.email_template = {
        htmlContent: null,
      };
      this.showModal = false;
      this.$emit('hidden');
    },
    emails_to_json(value) {
      if (value) {
        const splitedValues = value.replace(/\s+/g, '').split(',');
        return JSON.stringify(splitedValues);
      }
      return '';
    },
    json_to_emails(value) {
      let parsedValue = value;
      try {
        parsedValue = value ? JSON.parse(value).join(',') : null;
      } catch (e) {
        parsedValue = value;
      }
      return parsedValue;
    },
    async saveSingleEntity() {
      const response = await this.createCashcall({
        cashcall: {
          ...this.cashcall,
          cc_emails: this.emails_to_json(this.cashcall.cc_emails),
          committed_amount: this.bill.amount_due,
          fees_amount: this.bill.fees_amount_due,
          investor: !this.isEmpty(this.bill.investor) ? this.bill.investor.id : null,
          bill: this.bill.id,
        },
        bill_id: this.bill.id,
      });
    },
    saveInvestment() {
      if (!this.isManagementFeesAndIsNotCurrentYear) {
        const investmentData = {
          investment_id: this.bill.investment.id,
          committed_amount: this.cashcall.committed_amount,
          fees_percentage: this.cashcall.fees_percentage,
        };
        this.updateInvestment(investmentData);
      }
    },
  },
  mounted() {
    if (!this.isEmpty(this.bill)) {
      this.assignSingleBill();
      this.getEmailTemplate();
    }
  },
};
</script>
