<template>
  <div>
    <table class="custom-table">
      <thead>
        <tr class="group-header-bills">
          <td>Investor name</td>
          <td>Fundraising name</td>
          <td>Amount</td>
          <td>Fees</td>
          <td>Fees type</td>
          <td>Payment status</td>
          <td>Payment sent date</td>
          <td>Payment paid date</td>
          <td>Bill number</td>
          <td>Bill number (deprecated)</td>
          <td>Actions</td>
          <td>Send</td>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in singleBills" :key="row.id">
        <!-- <tr v-for="row in financeTableData" :key="row.id"> -->
          <td class="name-tab">
            <div :id="'checkbox-' + row.id">
              <input
                :disabled="!isSelectable(row)"
                class="check"
                type="checkbox"
                @change="setInvestorOfSelection($event, row)"
                :value="row.id"
                v-model="checkedBills"
              />
              <b-tooltip
                v-if="!isSelectable(row)"
                :target="'checkbox-' + row.id"
                variant="light"
                triggers="hover"
              >
                {{ getWhyIsDisabled(row) }}
              </b-tooltip>
            </div>
            <span class="name" :class="{ 'text-muted': isEmpty(row.investor) }">
              {{ !isEmpty(row.investor) ? row.investor.name : 'No investor linked' }}
            </span>
            <!-- <span class="name">
              {{row.investor_name ? row.investor_name : 'No investor linked'}}
            </span> -->
          </td>
          <td>
            {{
              !isEmpty(row.investment) && !isEmpty(row.investment.fundraising)
                ? row.investment.fundraising.name
                : isEmpty(row.investment)
                ? 'No investment linked'
                : 'No fundraising linked to investment'
            }}
            <!-- {{
              !isEmpty(row.fundraising_name)
                ? row.fundraising_name
                : 'No fundraising linked to investment'
            }} -->
          </td>
          <td>
            <span
              v-if="
                !isEmpty(row.payin)
                && (row.type === 'rhapsody_fees' || row.type === 'membership_fees')
              "
            >
              {{ getCurrencySign(row) + formatNumber(row.payin['amount'] - row.payin['fees']) }}
            </span>
            <span v-else-if="!isEmpty(row.investment)">
              {{ getCurrencySign(row) + formatNumber(row.amount_due) }}
            </span>
            <!-- <span v-if="row.amount">
              {{row.amount}}
            </span> -->
            <span v-else class="text-muted">
              No investment linked
            </span>
          </td>
          <td>
            <span v-if="!isEmpty(row.investment)">
              {{ getCurrencySign(row) + formatNumber(calculateFeesAmount(row)) }}
            </span>
            <span v-else-if="!isEmpty(row.payin) && row.type == 'membership_fees'">
              {{ getCurrencySign(row) + formatNumber(row.payin['fees']) }}
            </span>
            <!-- <span v-if="row.fees">
              {{parseFloat(row.fees).toFixed(2)}}
            </span> -->
            <span v-else class="text-muted">
              No investment linked
            </span>
          </td>
          <td>{{ humanize(row.type) }}</td>
          <!-- <td>{{ humanize(row.fees_type) }}</td> -->
          <td>
            {{ !isEmpty(row.payin) ? statusToHuman[row.payin['status']] : null }}
            <!-- {{ !isEmpty(row.payment_status) ? statusToHuman[row.payment_status] : null }} -->
          </td>
          <td>
            {{ !isEmpty(row.last_sent) ? moment(row.last_sent).format('DD/MM/YYYY') : null }}
            <!-- {{ !isEmpty(row.payment_sent_date) ?
            moment(row.payment_sent_date).format('DD/MM/YYYY') : null }} -->
          </td>
          <td>
            {{
              !isEmpty(row.payin) && row.payin['execution_date']
                ? moment(row.payin['execution_date']).format('DD/MM/YYYY')
                : null
            }}
            <!-- {{
              !isEmpty(row.payment_paid_date)
                ? moment(row.payment_paid_date).format('DD/MM/YYYY')
                : null
            }} -->
          </td>
          <td>
            {{ row.invoice_number }}
            <!-- {{ row.bill_number }} -->
          </td>
          <td>
            {{ row.invoice_number_deprecated }}
            <!-- {{ row.deprecated_bill_number }} -->
          </td>
          <!-- Actions -->
          <td>
            <div class="d-flex align-items-center">
              <div :id="'bill-button-' + row.id" class="mr-3 d-flex align-items-center">
                <div
                  v-if="
                    (row.updated_by || row.cashcall || row.last_sent) &&
                      row.type !== 'membership_fees' && isNotACreditNote(row)
                  "
                >
                  <img
                    class="
                                            checked-icon-image
                                            cursor-pointer
                                        "
                    :src="require('@/assets/images/finances_table/document_checked.png')"
                    alt="document checked"
                    @click="showBillsModal(row)"
                  />
                </div>
                <i
                  v-else
                  class="fas fa-file-invoice-dollar"
                  :class="
                    row.type === 'membership_fees' || !isNotACreditNote(row)
                    ? 'text-muted' : 'text-primary cursor-pointer'
                  "
                  @click="showBillsModalExtraConditions(row)"
                >
                </i>
                <b-tooltip
                  v-if="row.type === 'membership_fees' && isNotACreditNote(row) "
                  :target="'bill-button-' + row.id"
                  variant="light"
                  triggers="hover"
                >
                  This modal is not available for membership fees bills
                </b-tooltip>
              </div>
              <div class="text-primary mr-3" @click="showEmailModal(row)">
                <div v-if="row.cashcall && isNotACreditNote(row)">
                  <img
                    class="
                                            checked-icon-image
                                            cursor-pointer
                                        "
                    :src="require('@/assets/images/finances_table/envelope_checked.png')"
                    alt="envelope checked"
                  />
                </div>
                <div v-else>
                  <i class="fas fa-envelope" :class="getEnvelopeIconClass(row)" />
                </div>
              </div>
            </div>
          </td>
          <!-- Send -->
          <td>
            <div class="d-flex align-items-center" @click="showSendModal(row)">
              <div v-if="!row.last_sent || !isNotACreditNote(row)">
                <i class="fas fa-share" :class="getSendIconClass(row)"></i>
              </div>
              <div class="d-flex" v-else>
                <img
                  class="checked-icon-image cursor-pointer"
                  :src="require('@/assets/images/finances_table/arrow_checked.png')"
                  alt="arrow checked"
                />
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import {
  mapGetters, mapMutations,
} from 'vuex';
// import {
//   mapGetters, mapMutations, mapActions, mapState,
// } from 'vuex';

export default {
  name: 'BillsAndCashCallsTable',
  computed: {
    // ...mapState({
    //   financeTableData: (state) => state.bills.financeTableData,
    // }),
    ...mapGetters(['singleBills', 'currencies']),
  },
  watch: {
    checkedBills(billsIds) {
      const billsObjs = billsIds
        .map((billId) => this.singleBills.filter((bill) => bill.id == billId))
        .flat();
      this.setDataMultipleCashCallModal(billsObjs);
    },
  },
  data() {
    return {
      modalToShow: {
        email: null,
        bill_UK: false,
        bill_FR: false,
        send: null,
      },
      statusToHuman: {
        CREATED: 'Pending',
        SUCCEEDED: 'Paid',
        FAILED: 'Expired',
      },
      groupingBillsOfInvestor: null,
      checkedBills: [],
      modalDataUKbills: {},
      modalDataFRbills: {},
    };
  },
  methods: {
    ...mapMutations([
      'setShowBillUkModal',
      'setShowBillFRModal',
      'setShowSendEmailModal',
      'setShowCashCallModal',
      'setShowCashCallMembershipModal',
      'setDataBillUkModal',
      'setDataBillFRModal',
      'setDataSendEmailModal',
      'setDataCashCallModal',
      'setDataCashCallMembershipModal',
      'setDataMultipleCashCallModal',
    ]),
    // ...mapActions([
    //   'getFinanceTableData',
    // ]),
    getWhyIsDisabled(row) {
      if (!row.investment) {
        return 'No investment linked';
      }
      if (row.investment && row.investment.fundraising == null) {
        return 'No fundraising linked to investment';
      }
      if (row.investment && row.investment.fundraising.spv_country_code != 'UK') {
        return 'Only UK bills can be grouped';
      }
      if (row.investor == null) {
        return 'No investor entity linked';
      }
      if (row.investor.id != this.groupingBillsOfInvestor) {
        return 'Different investor selected';
      }
      if (row.last_sent !== null) {
        return 'The cashcall for this investment has been sent already';
      }
      return 'Cannot be grouped';
    },
    isSelectable(row) {
      const isUkSpv = row.investment
        && row.investment.fundraising
        && row.investment.fundraising.spv_country_code === 'UK';

      const billHasInvestor = row.investor != null;
      const alreadyGrouping = this.groupingBillsOfInvestor != null;

      let isFromTheSameInvestor = true;
      if (alreadyGrouping && billHasInvestor) {
        isFromTheSameInvestor = this.groupingBillsOfInvestor == row.investor.id;
      }

      const hasSentCashcall = row.last_sent !== null;

      return isUkSpv && billHasInvestor && isFromTheSameInvestor && !hasSentCashcall;
    },
    setInvestorOfSelection(event, bill) {
      if (event.target.checked && !this.groupingBillsOfInvestor) {
        this.groupingBillsOfInvestor = bill.investor.id;
      } else if (this.checkedBills.length == 0) {
        this.groupingBillsOfInvestor = null;
      }
    },
    showEmailModal(row) {
      const canSeeModal = row.updated_by || row.cashcall || row.type === 'membership_fees';
      if (canSeeModal) {
        if (row.type === 'membership_fees') {
          this.setDataCashCallMembershipModal(row);
          this.setShowCashCallMembershipModal(true);
        } else {
          this.setDataCashCallModal(row);
          this.setShowCashCallModal(true);
        }
      }
    },
    isNotACreditNote(row) {
      return row.amount_due > 0;
    },
    showBillsModalExtraConditions(row) {
      if (row.type !== 'membership_fees' && this.isNotACreditNote(row)) {
        return this.showBillsModal(row);
      }
      return null;
    },
    showBillsModal(row) {
      const isUkSpv = row.investment && row.investment.fundraising
        ? row.investment.fundraising.spv_country_code === 'UK'
        : false;
      if (isUkSpv) {
        this.setDataBillUkModal(row);
        this.setShowBillUkModal(true);
      } else {
        this.setDataBillFRModal(row);
        this.setShowBillFRModal(true);
      }
    },
    showSendModal(row) {
      if (row.cashcall) {
        this.setDataSendEmailModal(row);
        this.setShowSendEmailModal(true);
      }
    },
    calculateFeesAmount(bill) {
      let feesAmount = 0;
      if (bill.cashcall && bill.cashcall.total_fees_amount) {
        feesAmount = bill.cashcall.total_fees_amount;
      } else if (bill.investment) {
        feesAmount = bill.fees_amount_due ? bill.fees_amount_due : 0;
      }
      return feesAmount;
    },
    getCurrencySign(bill) {
      const hasFundraisingInfo = bill.investment && bill.investment.fundraising;
      if (hasFundraisingInfo) {
        const currencyId = bill.investment.fundraising.currency;
        const currencyName = this.currencies.find((select) => select.id == currencyId).name;
        return currencyName === 'USD' ? '$' : '€';
      }
      return '€';
    },
    getEnvelopeIconClass(bill) {
      const hasUpdatedBy = !this.isEmpty(bill.updated_by);
      const isMembershipBill = bill.type === 'membership_fees';
      return (hasUpdatedBy || isMembershipBill) && this.isNotACreditNote(bill) ? 'text-primary cursor-pointer' : 'text-muted';
    },
    getSendIconClass(bill) {
      const hasUpdatedBy = !this.isEmpty(bill.updated_by);
      const isMembershipBill = bill.type === 'membership_fees';
      const hasCashcallAndIsNotACreditNote = this.getEnvelopeIconClass(bill) && !this.isEmpty(bill.cashcall) && this.isNotACreditNote(bill);
      return ((hasUpdatedBy || isMembershipBill) && hasCashcallAndIsNotACreditNote) ? 'text-primary cursor-pointer' : 'text-muted';
    },
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.custom-table {
  width: 100%;
  thead {
    background-color: $white-color;
    font-weight: 600;
    text-align: center;
    font-size: 13px;
    .group-header-bills td {
      padding: 17px 15px;
    }
  }
  tbody {
    font-size: 13px;
    padding: 20px 20px;
    tr {
      background-color: $white-color;
      &:nth-child(odd) {
        background-color: rgba($red-color, 0.08);
      }
      .name-tab {
        display: flex !important;
        align-items: center;
        .name {
          margin-left: 10px;
          width: 100%;
        }
      }
      td {
        font: $main-font-semibold;
        padding: 20px 20px;
        text-align: center;
        .checked-icon-image {
          width: auto;
          height: 18px;
          margin-bottom: 4px;
        }
      }
    }
    th {
      padding: 26px 20px;
    }
  }
}
.cursor-pointer {
  cursor: pointer;
}
</style>
