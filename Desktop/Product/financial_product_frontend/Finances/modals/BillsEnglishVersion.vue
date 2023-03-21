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
                <h5 class="mt-2"><b>Create Bill</b></h5>
              </b-col>
            </b-row>
            <hr />
          </b-container>
        </template>
        <b-container fluid>
          <b-row class="mb-4">
            <b-col cols="12">
              <object
                class="w-100"
                style="height: 300px; resize: vertical"
                :data="billFile"
                type="application/pdf"
                width="300"
                height="200"
              >
                alt : <a :href="billFile">bill.pdf</a>
              </object>
            </b-col>
          </b-row>
          <b-row class="mb-4">
            <b-col cols="6">
              <label class="mb-0"><b>MangoPay User</b></label>
              <div v-if="mangoPayUser">
                <i class="fas fa-check checked-icon my-2 mr-2"></i>
                yes
              </div>
              <div v-else>
                <i class="fas fa-times unchecked-icon my-2 mr-2"></i>
                no
              </div>
            </b-col>
            <b-col cols="6">
              <div>
                <span class="headers">MangoPay User</span>
                <entity-label v-if="mangoPayUserValidated" class="my-2" color="green" size="auto">
                  validated</entity-label
                >
                <entity-label v-else class="my-2" color="red" size="auto">
                  not validated</entity-label
                >
              </div>
            </b-col>
          </b-row>
          <b-row class="mb-4">
            <b-col cols="12">
              <div>
                <span class="headers">MangoPay Wallet in €</span>
                <div v-if="walletInEuros">
                  <i class="fas fa-check checked-icon my-2 mr-2"></i>
                  Yes
                </div>
                <div v-else>
                  <i class="fas fa-times unchecked-icon my-2 mr-2"></i>
                  No
                </div>
              </div>
            </b-col>
          </b-row>
          <hr />
          <b-row>
            <b-col cols="6 mb-5 mt-3">
              <div>
                <span class="headers">Amount</span>
                <new-form-input
                  field="committed_amount"
                  type="number"
                  :initialValue="data.committed_amount"
                  v-model="data.committed_amount"
                  rules="required"
                ></new-form-input>
              </div>
            </b-col>
            <b-col cols="6 mb-5 mt-3">
              <div>
                <span class="headers">Set-up fees (%)</span>
                <new-form-input
                  field="fees_percentage"
                  type="number"
                  :initialValue="data.fees_percentage"
                  v-model="data.fees_percentage"
                  rules="required"
                ></new-form-input>
              </div>
            </b-col>
          </b-row>
          <b-row class="ml-1 mb-0">
            <div>
              <span class="headers">SA signed date</span>
              <new-form-date
                :editable="true"
                placeholder="yyyy-mm-dd"
                v-model="data.subscription_agreement_signed_date"
                :initialValue="data.subscription_agreement_signed_date"
                :rules="{ date_format: 'yyyy-MM-dd' }"
              ></new-form-date>
            </div>
          </b-row>
          <hr />
          <b-row class="my-4 sub-headers">
            <b-col><span>Set-up fees:</span></b-col>
            <b-col class="d-flex flex-row-reverse amount">
              <money-format
                v-if="calculated_fees.total_fees !== 'N/A'"
                :value="parseFloat(calculated_fees.total_fees)"
                :locale="$store.state.locale"
                :currency-code="currencyCode"
              ></money-format>
              <span v-else>{{ calculated_fees.total_fees }}</span>
            </b-col>
          </b-row>
          <b-row class="sub-headers">
            <b-col>
              <span>Acceleration fees with VAT (20%)</span>
            </b-col>
            <b-col class="d-flex flex-row-reverse amount">
              <money-format
                v-if="calculated_fees.total_fees_with_vat !== 'N/A'"
                :value="parseFloat(calculated_fees.total_fees_with_vat)"
                :locale="$store.state.locale"
                :currency-code="currencyCode"
              ></money-format>
              <span v-else>{{ calculated_fees.total_fees_with_vat }}</span>
            </b-col>
          </b-row>
          <b-row class="ml-1">
            <collapse class="p-0 mb-1 collapse-formula" :collapse="collapse" collapse-id="1">
              {{ calculated_fees.fees_with_vat_formula }}
            </collapse>
            <collapse-trigger class="collapse-title" :triggered="collapse" @click="toggleCollapse">
              <span class="formula">Formula</span>
            </collapse-trigger>
          </b-row>
          <b-row class="mb-3 sub-headers mt-1">
            <b-col>
              <span>Total PayIn amount:</span>
            </b-col>
            <b-col class="d-flex flex-row-reverse amount">
              <money-format
                v-if="calculated_fees.transferred_amount !== 'N/A'"
                :value="parseFloat(calculated_fees.transferred_amount)"
                :locale="$store.state.locale"
                :currency-code="currencyCode"
              ></money-format>
              <span v-else>{{ calculated_fees.transferred_amount }}</span>
            </b-col>
          </b-row>
        </b-container>
        <template #modal-footer="{ cancel }">
          <b-container fluid>
            <b-row>
              <b-col>
                <btn size="fluid" color="dark-grey" @click="cancel">
                  Cancel
                </btn>
              </b-col>
              <b-col>
                <btn
                  size="fluid"
                  :color="!invalid ? 'red-gradient' : 'grey'"
                  @click="invalid ? null : saveEntity()"
                >
                  Create bill
                </btn>
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
import MoneyFormat from 'vue-money-format';
import {
  mapGetters, mapActions, mapMutations,
} from 'vuex';
import moment from 'moment';
import PayIn from '@/components/lib/modals/PayIn';
import bills from '@/components/lib/mixins/bills.js';

export default {
  name: 'BillsEnglishVersion',
  mixins: [bills],
  components: {
    'validation-observer': ValidationObserver,
    'money-format': MoneyFormat,
    PayIn,
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
    show(new_val) {
      this.showModal = new_val;
    },
    bill(oldObj, newObj) {
      const newobjHasData = !!newObj;
      if (newobjHasData) {
        this.updateBillData();
      }
      this.getInvestorInfo();
    },
  },
  data() {
    return {
      showModal: false,
      collapse: false,
      billFile: null,
      data: {
        investor_id: null,
        template_id: null,
        company_name: null,
        committed_amount: null,
        fees_percentage: null,
        fundraising: {
          currency: null,
        },
        subscription_agreement_signed_date: null,
      },
      investment_id: null,
      investor_kyc: {
        representative_address: {
          country_name: {
            name: '',
          },
        },
      },
      walletInEuros: true,
      mangoPayUser: false,
      mangoPayUserValidated: false,
    };
  },
  computed: {
    ...mapGetters(['currencies']),
    totalFees() {
      return this.data.committed_amount * this.data.fees_percentage;
    },
    totalTransfered() {
      return Number(this.data.committed_amount) + Number(this.totalFees);
    },
    lastDayOfTheYear() {
      const last_day_of_current_year = `${new Date().getFullYear()}-12-31`;
      return last_day_of_current_year;
    },
    calculated_fees() {
      const days360 = require('days360');
      const { committed_amount } = this.data;
      const fees_percentage = this.data.fees_percentage / 100;
      const sa_signed_date = new Date(this.data.subscription_agreement_signed_date);
      const last_day_date = new Date(this.lastDayOfTheYear);
      const else_percentage = this.investor_kyc.representative_address.country_name.name == 'France' ? 1.2 : 1;

      const subscriptionagreementIsEmpty = this.data.subscription_agreement_signed_date !== null
        && this.data.subscription_agreement_signed_date !== undefined;
      if (subscriptionagreementIsEmpty) {
        let total_fees = committed_amount * fees_percentage;
        let total_fees_with_vat = committed_amount
          * (((0.02 * days360(sa_signed_date, last_day_date)) / 360) * else_percentage);
        let transferred_amount = committed_amount
          * (1
            + fees_percentage
            + ((0.02 * days360(sa_signed_date, last_day_date)) / 360) * else_percentage);
        const formula = `${committed_amount} * ( 0.02 * ${days360(
          sa_signed_date,
          last_day_date,
        )} / 360 * ${else_percentage} )`;

        // Rounds up to 2 decimals maximum

        total_fees = this.formatAmount(total_fees);
        total_fees_with_vat = this.formatAmount(total_fees_with_vat);
        transferred_amount = this.formatAmount(transferred_amount);

        const obj = {
          total_fees,
          total_fees_with_vat,
          transferred_amount,
          fees_with_vat_formula: formula,
        };
        return obj;
      }
      const formula = `${committed_amount} * ( 0.02 * pro_rata_temporis * ${else_percentage} )`;
      const obj = {
        total_fees: 'N/A',
        total_fees_with_vat: 'N/A',
        transferred_amount: 'N/A',
        fees_with_vat_formula: formula,
      };
      return obj;
    },
    currencyCode() {
      const hasFundraisingInfo = this.bill.investment && this.bill.investment.fundraising;
      if (hasFundraisingInfo) {
        const currencyId = this.bill.investment.fundraising.currency;
        const currencyName = this.currencies.find((select) => select.id == currencyId).name;
        return currencyName;
      }
      return 'EUR';
    },
  },
  methods: {
    ...mapActions(['updateSingleBill', 'getInvestorKYC', 'getInvestorLanguagePreference']),
    ...mapMutations(['updateBillinTable']),
    formatAmount(num) {
      let amount = num;
      amount = amount.toString();
      if (amount.lastIndexOf('.') > 0) {
        amount = amount.slice(0, amount.lastIndexOf('.') + 4);
      }
      amount = parseFloat(amount);
      amount = Math.ceil(amount * 100) / 100;
      return amount;
    },
    async getInvestorInfo() {
      const investorInfoPresent = !!this.bill.investor;
      if (investorInfoPresent) {
        this.loading = true;
        await this.getInvestorKYC(this.bill.investor.id).then(
          (response) => {
            this.investor_kyc = response.data.kyc;
            if (this.isEmpty(this.investor_kyc.representative_address.country_name)) {
              this.investor_kyc.representative_address.country_name = {};
              this.investor_kyc.representative_address.country_name.name = '';
            }
            this.mangoPayUserValidated = this.investor_kyc.status;
            this.mangoPayUser = this.investor_kyc.mangopay_relation !== null;
            this.loading = false;
          },
          (response) => {
            this.loading = false;
            this.$store.dispatch('triggerAlert', {
              show: true,
              type: 'danger',
              message: 'Error! The data could not be loaded.',
            });
          },
        );
        await this.getInvestorLanguagePreference(this.bill.investor.id).then((response) => {
          const billFileTemplate = this.billFileTemplates[response][this.investor_kyc.type][
            this.bill.type
          ];
          this.billFile = billFileTemplate
            || 'https://img.oneragtime.com/uploads/2021/02/EN_upfront_fees_invoice_natural.pdf';
        });
      }
    },
    updateBillData() {
      if (this.bill.investment) {
        this.data.committed_amount = this.bill.investment.committed_amount;
        this.data.fees_percentage = this.bill.investment.fees_percentage;
        this.data.subscription_agreement_signed_date = moment(
          this.bill.investment.subscription_agreement_signed_date,
        ).format('YYYY-MM-DD');
        this.investment_id = this.bill.investment.id;
        if (this.bill.investment.fundraising) {
          this.data.fundraising.currency = this.bill.investment.fundraising.currency;
        }
      }
      this.data.investor_id = this.bill.investor ? this.bill.investor.id : null;
      this.data.investor_name = this.bill.investor ? this.bill.investor.name : null;
    },
    toggleCollapse() {
      this.collapse = !this.collapse;
    },
    hide() {
      (this.billFile = null),
      (this.data = {
        investor_id: null,
        template_id: null,
        company_name: null,
        committed_amount: null,
        fees_percentage: null,
        fundraising: {
          currency: null,
        },
        subscription_agreement_signed_date: null,
      }),
      (this.investment_id = null),
      (this.investor_kyc = {
        representative_address: {
          country_name: {
            name: '',
          },
        },
      }),
      (this.walletInEuros = true),
      (this.mangoPayUser = false),
      (this.mangoPayUserValidated = false),
      (this.showModal = false);
      this.$emit('hidden');
    },
    saveEntity() {
      const billData = {
        id: this.bill.id,
        committed_amount: this.data.committed_amount,
        fees_percentage: this.data.fees_percentage,
        sa_signed_date: moment(this.data.subscription_agreement_signed_date).format(),
      };

      this.updateSingleBill(billData).then((response) => {
        const updatedInvestement = {
          id: this.investment_id,
          committed_amount: response.data.committed_amount,
          fees_percentage: response.data.fees_percentage,
          subscription_agreement_signed_date: response.data.sa_signed_date,
          fees_type: this.bill.investment.fees_type,
          fundraising: this.bill.investment.fundraising,
          creation_datetime: this.bill.investment.creation_datetime,
        };

        const updatedBill = {
          id: this.bill.id,
          updated_by: response.data.updated_by,
          updated_at: response.data.updated_at,
          investment: updatedInvestement,
        };

        this.updateBillinTable(updatedBill);
        this.hide();
      });
    },
  },
  mounted() {
    if (!this.isEmpty(this.bill)) {
      this.updateBillData();
    }
    this.getInvestorInfo();
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.modal-header {
  padding-bottom: 0px !important;
}
.headers {
  margin: 9px 0;
  color: $black-color;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.38;
  letter-spacing: -0.3px;
}
.sub-headers {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.38px;
  color: $black-color;
  margin-top: 26px;
  .amount {
    font-size: 24px;
    font-weight: 900;
    letter-spacing: -0.45px;
  }
}
.formula {
  font-size: 12px;
  font-weight: bold;
  color: $red-color;
}
.collapse-formula {
  color: $black-color;
}

.collapse-title {
  color: $red-color;
  font-weight: 600;
}
</style>
<style lang="scss">
.div-date {
  margin-bottom: 0 !important;
}
.collapse-triggered {
  margin-top: 30px;
}
</style>
