<template>
  <table class="custom-table">
    <thead>
      <tr class="group-header-multiple">
        <td>Investor name</td>
        <td>Cash call number</td>
        <td>Total amount</td>
        <td>Payment status</td>
        <td>Payment sent date</td>
        <td>Payment paid date</td>
        <td>Cash call email</td>
        <td>Send</td>
      </tr>
    </thead>
    <tbody>
      <div v-for="(row, index) in multipleBills" :key="row.id" class="display-contents">
        <tr>
          <td>
            <div
              href="#"
              v-b-toggle="'collapse-' + index"
              variant="secondary"
              class="d-flex table-container"
            >
              <div aria-hidden="true" class="bills-name">
                <span>{{
                  !isEmpty(row.cashcall) ? row.cashcall.investor_name : 'No Investor Name'
                }}</span>
                <div class="bills-icons">
                  <div class="mr-3">
                    <i class="fas fa-chevron-down"></i>
                  </div>
                  <!-- <div class="mr-3"><i class="fas fa-chevron-up"></i></div> -->
                </div>
              </div>
            </div>
          </td>
          <td>{{ row.cashcall.id }}</td>
          <!-- To check: this field corresponds to Cash call number column -->
          <td>{{ '€' + formatNumber(row.total_amount) }}</td>
          <td>
            {{ !isEmpty(row.payin) ? statusToHuman[row.payin['status']] : null }}
          </td>
          <td>{{ formatDate(row.last_sent) }}</td>
          <td>
            {{ !isEmpty(row.payin) ? formatDate(row.payin['execution_date']) : null }}
          </td>
          <td>
            <span>
              <!-- Actions -->
              <i
                class="fas fa-envelope icon-link icon-delete"
                aria-hidden="true"
                @click="showEmailModal(row.related_bills)"
              ></i>
            </span>
          </td>
          <td>
            <span @click="showSendModal(row)">
              <!-- Send -->
              <i
                class="fas fa-share icon-link share icon-delete"
                aria-hidden="true"
                @click="showSendModal(row)"
              ></i>
            </span>
          </td>
        </tr>
        <b-collapse class="display-contents" :id="'collapse-' + index" role="tabpanel" tag="tr">
          <tr class="bills-sub-header">
            <td class="">Fundraising</td>
            <td>Amount</td>
            <td>Fees</td>
            <td>Fees Type</td>
            <td>Bill</td>
            <td colspan="3"></td>
          </tr>
          <tr v-for="bill in row.related_bills" :key="bill.id" class="bills-sub-body">
            <td>
              {{
                !isEmpty(bill.investment) && !isEmpty(bill.investment.fundraising)
                  ? bill.investment.fundraising.name
                  : 'Membership fees'
              }}
            </td>
            <td>
              <span v-if="!isEmpty(bill.investment)">
                {{ getCurrencySign(bill) + formatNumber(bill.investment['committed_amount']) }}
              </span>
            </td>
            <td>
              <span v-if="!isEmpty(bill.investment)">
                {{ getCurrencySign(bill) + formatNumber(calculateFeesAmount(bill)) }}
              </span>
            </td>
            <td>{{ humanize(bill.type) }}</td>
            <td>
              <span
                ><i class="fas fa-file-invoice-dollar icon-delete" @click="showBillsModal(bill)"></i
              ></span>
            </td>
            <td colspan="3"></td>
          </tr>
        </b-collapse>
      </div>
    </tbody>
  </table>
</template>

<script>
import { mapGetters, mapMutations } from 'vuex';

export default {
  name: 'MultipleBillsCashCallsTable',
  computed: {
    ...mapGetters(['multipleBills', 'currencies']),
  },
  data() {
    return {
      modalToShow: {
        email: null,
        send: null,
      },
      statusToHuman: {
        CREATED: 'Pending',
        SUCCEEDED: 'Paid',
        FAILED: 'Expired',
      },
    };
  },
  methods: {
    ...mapMutations([
      'updateBillsSelectedIds',
      'setShowBillUkModal',
      'setShowBillFRModal',
      'setShowSendEmailModal',
      'setShowMultipleCashCallModal',
      'setDataBillUkModal',
      'setDataBillFRModal',
      'setDataSendEmailModal',
      'setDataMultipleCashCallModal',
    ]),
    showEmailModal(row) {
      this.setDataMultipleCashCallModal(row);
      this.setShowMultipleCashCallModal(true);
    },
    showBillsModal(bill) {
      const isUkSpv = bill.investment && bill.investment.fundraising
        ? bill.investment.fundraising.spv_country_code === 'UK'
        : false;

      if (isUkSpv) {
        this.setDataBillUkModal(bill);
        this.setShowBillUkModal(true);
      } else {
        this.setDataBillFRModal(bill);
        this.setShowBillFRModal(true);
      }
    },
    showSendModal(row) {
      this.setDataSendEmailModal(row);
      this.setShowSendEmailModal(true);
    },
    calculateFeesAmount(bill) {
      return Number(bill.investment.committed_amount) * (Number(bill.fees_percentage) / 100);
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
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';
.display-contents {
  display: contents;
}
.custom-table {
  width: 100%;
  thead {
    background-color: $white-color;
    font-weight: 600;
    text-align: center;
    font-size: 13px;
    .group-header-multiple td {
      padding: 26px 15px;
    }
  }
  tbody {
    font-size: 13px;
    padding: 20px 20px;
    .display-contents:nth-child(odd) {
      tr {
        background-color: rgba($red-lighter-color, 0.08);
      }
    }
    tr {
      background-color: $white-color;
      td {
        font: $main-font-semibold;
        padding: 26px 20px;
        text-align: center;
      }
    }
    th {
      padding: 26px 20px;
    }
    .bills-name {
      display: flex;
      flex-direction: row !important;
      .bills-icons {
        margin: 3px 0 0 9px;
        font-size: 10px;
      }
    }
    .bills-sub-header {
      background-color: rgba($red-lighter-color, 0.2) !important;
      td {
        padding: 26px 20px;
        font-size: 12px;
        font-weight: 900;
      }
    }
    .bills-sub-body {
      background-color: rgba($red-lighter-color, 0.2) !important;
      td {
        padding: 26px 20px;
        font-size: 12px;
      }
    }
  }
}
</style>
<style lang="scss">
.table-container {
  .not-collapsed {
    outline: none;
  }
  .collapsed {
    outline: none;
  }
}
</style>
