<template>
  <validation-observer v-slot="{ invalid }">
    <div>
      <b-modal
        id="modal"
        size="lg"
        v-model="showModal"
        content-class="shadow-lg"
        cancel-variant="outline-secondary"
        @hidden="hide"
      >
        <template #modal-header>
          <b-container fluid>
            <b-row>
              <b-col cols="12">
                <h5 class="mt-2"><b>Create bill</b></h5>
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
          <b-row class="mb-2">
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
              <label class="mb-0"><b>MangoPay User</b></label>
              <entity-label v-if="mangoPayUserValidated" class="my-2" color="green" size="auto">
                validated</entity-label
              >
              <entity-label v-else class="my-2" color="red" size="auto">
                not validated</entity-label
              >
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>MangoPay wallet in €</b></label>
              <div v-if="walletInEuros">
                <i class="fas fa-check checked-icon my-2 mr-2"></i>
                yes
              </div>
              <div v-else>
                <i class="fas fa-times unchecked-icon my-2 mr-2"></i>
                no
              </div>
            </b-col>
          </b-row>
          <hr class="mt-2" />
          <b-row class="mt-2">
            <b-col cols="6">
              <label class="mb-0"><b>Investor name</b></label>
              <div class="data-box">{{ data.investor_name }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Investor email</b></label>
              <div class="data-box">{{ investor_email }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Investment year</b></label>
              <div class="data-box">{{ investment_year }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Investment month</b></label>
              <div class="data-box">{{ investment_month }}</div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0">
                <b>Fundraising entity year</b>
              </label>
              <div class="data-box">
                {{ fundraising_entity_year }}
              </div>
            </b-col>
            <b-col cols="6">
              <label class="mb-0">
                <b>Fundraising entity name</b>
              </label>
              <div class="data-box">
                {{ data.entity_name }}
              </div>
            </b-col>
            <b-col cols="6">
              <new-form-date
                :editable="true"
                label="SA signed date"
                v-model="data.signed_date"
                :initialValue="data.signed_date"
                placeholder="yyyy-mm-dd"
                :rules="{ date_format: 'yyyy-MM-dd' }"
              ></new-form-date>
            </b-col>
            <b-col cols="6">
              <new-form-input
                label="Investment amount"
                v-model="data.committed_amount"
                :initialValue="data.committed_amount"
                type="number"
                rules="required"
              />
            </b-col>
            <b-col cols="6">
              <label class="mb-0"><b>Investment fees type</b></label>
              <div class="data-box">{{ data.fees_type }}</div>
            </b-col>
            <b-col cols="6">
              <new-form-input
                label="Fees(%)"
                v-model="data.fees_percentage"
                :initialValue="data.fees_percentage"
                type="number"
                rules="required"
              />
            </b-col>
          </b-row>
          <hr />
          <b-row class="mb-3">
            <b-col cols="12">
              <h3 class="mb-3">
                Amount due:
                <span class="float-right">{{ currencySign + formatNumber(totalFees) }}</span>
              </h3>
            </b-col>
          </b-row>
        </b-container>
        <template #modal-footer="{ cancel }">
          <b-container fluid>
            <b-row>
              <b-col><btn size="fluid" color="dark-grey" @click="cancel">Cancel</btn></b-col>
              <b-col
                ><btn
                  size="fluid"
                  :color="!invalid ? 'red-gradient' : 'grey'"
                  @click="invalid ? null : saveEntity()"
                  >Create bill</btn
                ></b-col
              >
            </b-row>
          </b-container>
        </template>
      </b-modal>
    </div>
  </validation-observer>
</template>

<script>
import { ValidationObserver } from 'vee-validate';
import {
  mapGetters, mapActions, mapMutations,
} from 'vuex';
// import {
//   mapGetters, mapActions, mapMutations, mapState,
// } from 'vuex';
import moment from 'moment';
import bills from '@/components/lib/mixins/bills.js';

export default {
  name: 'FrenchBillPrefillModal',
  mixins: [bills],
  components: {
    'validation-observer': ValidationObserver,
  },
  props: {
    bill: {
      type: Object,
      default: null,
    },
    show: {
      type: Boolean,
      default: false,
    },
  },
  watch: {
    show(new_val) {
      this.showModal = new_val;
      if (new_val) {
        this.updateData();
      }
    },
  },
  computed: {
    // ...mapState({
    //   billData: (state) => state.modalsFinance.dataBillFRModal,
    // }),
    // ...mapGetters(['getInvestor', 'getInvestorOwnerContact', 'currencies', 'getDataBillFRModal',
    // ]),
    ...mapGetters(['getInvestor', 'getInvestorOwnerContact', 'currencies']),
    totalFees() {
      return this.data.committed_amount * (Number(this.data.fees_percentage) / 100);
    },
    investment_creation_date_time() {
      return this.bill.investment ? this.bill.investment.creation_datetime : null;
    },
    investment_year() {
      return this.investment_creation_date_time
        ? moment(this.investment_creation_date_time).format('YYYY')
        : 'No year found';
    },
    investor_email() {
      return this.getInvestorOwnerContact.length > 1
        ? 'More than one owner investor'
        : this.getInvestorOwnerContact.length > 0
          ? this.getInvestorOwnerContact[0].user.email
          : 'No email found';
    },
    investment_month() {
      return this.investment_creation_date_time
        ? moment(this.investment_creation_date_time).format('MM')
        : 'No month found';
    },
    fundraising_creation_date_time() {
      return this.bill.investment && this.bill.investment.fundraising
        ? this.bill.investment.fundraising.creation_datetime
        : null;
    },
    fundraising_entity_year() {
      return this.fundraising_creation_date_time
        ? moment(this.fundraising_creation_date_time).format('YYYY')
        : 'No year found';
    },
    currencySign() {
      const hasFundraisingInfo = this.bill.investment && this.bill.investment.fundraising;
      if (hasFundraisingInfo) {
        const currencyId = this.bill.investment.fundraising.currency;
        const currencyName = this.currencies.find((select) => select.id == currencyId).name;
        return currencyName === 'USD' ? '$' : '€';
      }
      return '€';
    },
  },
  data() {
    return {
      showModal: false,
      billFile: null,
      data: {
        investor_id: null,
        investor_name: null,
        entity_name: null,
        committed_amount: null,
        fees_type: null,
        fees_percentage: null,
        signed_date: null,
      },
      investment_id: null,
      investor_kyc: {},
      walletInEuros: true,
      mangoPayUser: false,
      mangoPayUserValidated: false,
    };
  },
  methods: {
    ...mapActions([
      'getInvestorData',
      'updateSingleBill',
      'getInvestorKYC',
      'getInvestorLanguagePreference',
    ]),
    ...mapMutations(['updateBillinTable']),
    async getInvestorInfo() {
      if (this.data.investor_id) {
        await this.getInvestorKYC(this.bill.investor.id).then(
        // if (this.bill.investor_id) {
        //   await this.getInvestorKYC(this.bill.investor_id).then(
          (response) => {
            this.investor_kyc = response.data.kyc;
            this.mangoPayUserValidated = this.investor_kyc.status;
            this.mangoPayUser = this.investor_kyc.mangopay_relation !== null;
            this.loading = false;
          },
          () => {
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
        const { investment } = this.bill;
        this.data.committed_amount = investment.committed_amount;
        this.data.fees_type = investment.fees_type;
        this.data.fees_percentage = investment.fees_percentage;
        this.data.signed_date = moment(investment.subscription_agreement_signed_date).format(
          'YYYY-MM-DD',
        );
        this.investment_id = investment.id;
        if (investment.fundraising) {
          const { fundraising } = investment;
          this.data.entity_name = fundraising.name;
        }
      }
      this.data.investor_id = this.bill.investor ? this.bill.investor.id : null;
      this.data.investor_name = this.bill.investor ? this.bill.investor.name : null;
    },
    updateData() {
      this.updateBillData();
      this.getInvestorInfo();
      this.getInvestorData(this.bill.investor.id);
    },
    saveEntity() {
      const billData = {
        id: this.bill.id,
        committed_amount: this.data.committed_amount,
        fees_percentage: this.data.fees_percentage,
        sa_signed_date: moment(this.data.signed_date).format(),
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
    hide() {
      this.billFile = null;
      this.data = {
        investor_id: null,
        investor_name: null,
        entity_name: null,
        committed_amount: null,
        fees_type: null,
        fees_percentage: null,
        signed_date: null,
      };
      this.investment_id = null;
      this.investor_kyc = {};
      this.walletInEuros = true;
      this.mangoPayUser = false;
      this.mangoPayUserValidated = false;
      this.showModal = false;
      this.$emit('hidden');
    },
  },
  mounted() {
    if (!this.isEmpty(this.bill)) {
      // this.data.investor_id = this.bill.investor_id;
      this.updateData();
    }
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.modal-header {
  padding-bottom: 0px !important;
}
.data-box {
  height: 35px;
}
</style>
