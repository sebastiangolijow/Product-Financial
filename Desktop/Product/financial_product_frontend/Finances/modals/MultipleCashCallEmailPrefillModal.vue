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
        <b-container fluid v-if="!isEmpty(bills)">
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
          <hr />
          <b-row>
            <b-col>
              <b-row>
                <b-col class="bills-header">Fundraising name</b-col>
                <b-col class="bills-header">Investment amount</b-col>
                <b-col class="bills-header">Fees (%)</b-col>
                <b-col class="bills-header">Investment fees</b-col>
                <b-col class="bills-header">Investment date</b-col>
              </b-row>
              <b-row v-for="bill in multipleBillForTable" :key="bill.id">
                <b-col>
                  {{ bill.investment.fundraising ? bill.investment.fundraising.name : null }}
                </b-col>
                <b-col> €{{ bill.investment ? bill.investment.committed_amount : null }} </b-col>
                <b-col>
                  {{ bill.fees.percentage }}
                </b-col>
                <b-col> €{{ bill.fees.amount }} </b-col>
                <b-col>
                  {{
                    bill.investment
                      ? moment(bill.investment.creation_datetime).format('DD/MM/YYYY')
                      : null
                  }}
                </b-col>
              </b-row>
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
                  @click="saveMultipleEntities()"
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
import moment from 'moment';

export default {
  name: 'MultipleCashCallEmailPrefill',
  components: {
    'validation-observer': ValidationObserver,
  },
  props: {
    show: {
      type: Boolean,
      required: true,
      default: false,
    },
    bills: {
      type: Array,
      default: () => [],
    },
  },
  watch: {
    show(new_val) {
      this.showModal = new_val;
    },
    bills(newVal) {
      if (!this.isEmpty(newVal)) {
        this.manageBillData();
        this.getEmailTemplate();
      }
    },
  },
  computed: {
    totalFees() {
      let total = 0;
      if (!this.isEmpty(this.multipleBillForTable)) {
        total = this.multipleBillForTable.reduce((acc, val) => {
          const { amount } = val.fees;
          const sum = acc + amount;
          return sum;
        }, 0);
      }
      return total;
    },
    totalTransfered() {
      let totalCommited = 0;
      if (!this.isEmpty(this.multipleBillForTable)) {
        totalCommited = this.multipleBillForTable.reduce((acc, val) => {
          let amount = 0;
          if (val.investment && this.isInvestmentCurrentYear(val.investment)) {
            amount = Number(val.investment.committed_amount);
          }
          const sum = acc + amount;
          return sum;
        }, 0);
      }
      return this.totalFees + totalCommited;
    },
  },
  data() {
    return {
      showModal: false,
      cashcall: {
        id: null,
        payin: null,
        investor: null,
        investor_name: null,
        company_name: null,
        committed_amount: null,
        fees_type: null,
        fees_percentage: null,
        cc_emails: null,
        total_fees_amount: null,
        sendinblue_template_id: null,
        total_committed_amount: null,
      },
      multipleBillForTable: null,
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
    ...mapActions([
      'checkCashcallAndSave',
      'updateBillFromCashCall',
      'getAllBills',
      'getInvestorLanguagePreference',
    ]),
    ...mapMutations(['updateBillsSelectedIds', 'updateBillinTable']),
    async getEmailTemplate() {
      if (!this.isEmpty(this.bills)) {
        const languagePreference = await this.getInvestorLanguagePreference(
          this.bills[0].investor.id,
        );
        const templateId = this.templatesIds[languagePreference][this.bills[0].type];
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
      }
    },
    async assignMultipleBills() {
      if (this.bills[0].cashcall) {
        this.cashcall = {
          ...this.bills[0].cashcall,
          cc_emails: this.json_to_emails(this.bills[0].cc_emails),
          investor: !this.isEmpty(this.bills[0].investor) ? this.bills[0].investor.id : null,
        };
      } else {
        this.cashcall.investor = !this.isEmpty(this.bills[0].investor)
          ? this.bills[0].investor.id
          : null;
      }
      this.cashcall.investor_name = !this.isEmpty(this.bills[0].investor)
        ? this.bills[0].investor.name
        : null;
      Promise.all(
        this.bills.map((bill) => Promise.resolve(this.setInvestmentData(bill))),
      ).then((values) => {
        this.multipleBillForTable = values;
      });
    },
    async setInvestmentData(bill) {
      const amount = bill.investment.committed_amount;
      const { fees_percentage } = bill.investment;
      const params = `amount=${amount}&fees_percentage=${fees_percentage}`;
      const investment = await this.apiGetV3(
        `/bills/${bill.id}/cash_call_calculate_amounts?${params}`,
      ).then((response) => ({
        fundraising: bill.investment.fundraising,
        investment: bill.investment,
        fees: {
          amount: response.data.fees_amount,
          percentage: response.data.percentage,
        },
      }));
      return investment;
    },
    isInvestmentCurrentYear(investment) {
      const investmentYear = moment(investment.creation_datetime).format('YYYY');
      return investmentYear == new Date().getFullYear();
    },
    hide() {
      (this.cashcall = {
        id: null,
        payin: null,
        investor: null,
        investor_name: null,
        company_name: null,
        committed_amount: null,
        fees_type: null,
        fees_percentage: null,
        cc_emails: null,
        total_fees_amount: null,
        sendinblue_template_id: null,
        total_committed_amount: null,
      }),
      (this.multipleBillForTable = null),
      (this.email_template = {
        htmlContent: null,
      }),
      (this.showModal = false);
      this.$emit('hidden');
    },
    json_to_emails(value) {
      try {
        value = value ? JSON.parse(value).join(',') : null;
      } catch (e) {
        value = value || null;
      }
      return value;
    },
    saveMultipleEntities() {
      this.checkCashcallAndSave({
        cashcall: this.cashcall,
        bill_id: this.bills[0].id,
        investor: this.bills[0].investor.id,
      }).then(
        (response) => {
          for (let i = 0; i < this.bills.length; i++) {
            const bill = this.bills[i];
            const body = {
              bill_id: bill.id,
              cashcall_id: response.data.id,
            };
            this.updateBillFromCashCall(body);

            const updatedBill = {
              id: bill.id,
              cashcall: response.data,
            };

            this.updateBillinTable(updatedBill);
          }
          this.$store.dispatch('triggerAlert', {
            show: true,
            type: 'success',
            message: 'The email was correctly prepared.',
          });
          this.loading = false;

          this.updateBillsSelectedIds([]);
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
      this.assignMultipleBills();
    },
  },
  mounted() {
    if (!this.isEmpty(this.bills)) {
      this.manageBillData();
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
