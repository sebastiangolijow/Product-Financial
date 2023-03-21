<template>
  <b-container fluid class="px-3 px-md-5 py-5 background-color">
    <b-row>
      <b-col class="title"><h1>Financial dashboard</h1></b-col>
    </b-row>
    <hr class="detail" />
    <b-row>
      <b-col cols="6" sm="4" md="3">
        <div class="float-left">
          <new-form-input
            :field="search_field"
            label="Search"
            placeholder="Search"
            v-model="search_value"
            @input="searchUpdateDebounced"
          />
        </div>
        <div class="btn-group btn-group-toggle ml-2 search-field-selector" data-toggle="buttons">
          <label
            class="btn btn-lg"
            :class="search_field == 'investor_name' ? 'btn-primary' : 'btn-outline-primary'"
          >
            <input
              type="radio"
              autocomplete="off"
              checked
              v-model="search_field"
              value="investor_name"
              @click="filterBills(search_value, 'investor_name')"
            />
            <i class="far fa-user valign-text-top"></i>
          </label>
          <label
            class="btn btn-lg"
            :class="search_field == 'fundraising_name' ? 'btn-primary' : 'btn-outline-primary'"
          >
            <input
              type="radio"
              name="options"
              autocomplete="off"
              v-model="search_field"
              value="fundraising_name"
              @click="filterBills(search_value, 'fundraising_name')"
            />
            <i class="far fa-chart-line valign-text-top"></i>
          </label>
        </div>
      </b-col>
      <b-col cols="6" sm="4" md="3">
        <new-form-select
          @input="filterBills"
          :options="selects.bill_type_choices"
          field="type"
          nullable
          null_text="All types"
          label="Bill type filter"
        >
        </new-form-select>
      </b-col>
      <b-col cols="6" sm="4" md="3">
        <new-form-select
          @input="filterBills"
          :options="selects.bill_year_choices"
          field="year"
          nullable
          null_text="All years"
          label="Bill year filter"
        >
        </new-form-select>
      </b-col>
      <b-col cols="6" sm="4" md="3">
        <new-form-select
          @input="filterBills"
          :options="selects.bill_status_choices"
          field="payment_status"
          nullable
          null_text="All status"
          label="Bill status filter"
        >
        </new-form-select>
      </b-col>
    </b-row>
    <b-row v-show="isFinanceTableLoading" align-h="center">
      <loading :active="isFinanceTableLoading"></loading>
    </b-row>
    <b-row class="mt-4" v-show="!isFinanceTableLoading">
      <FinancesTable @loading="setFinanceTableLoading"> </FinancesTable>
    </b-row>
    <BillsEnglishVersion
      :show="getShowBillUkModal"
      :bill="getDataBillUkModal"
      @hidden="closeBillUkModal"
    />
    <FrenchBillPrefillModal
      :show="getShowBillFRModal"
      :bill="getDataBillFRModal"
      @hidden="closeBillFRModal"
    />
    <SendCashCallModal
      :show="getShowSendEmailModal"
      :bill="getDataSendEmailModal"
      @hidden="closeSendEmailModal"
    />
    <CashCallEmailPrefill
      :show="getShowCashCallModal"
      spv_country="FR"
      :bill="getDataCashCallModal"
      @hidden="closeCashCallModal"
    />
    <CashCallMembershipEmailPrefill
      :show="getShowCashCallMembershipModal"
      :bill="getDataCashCallMembershipModal"
      @hidden="closeCashCallMembershipModal"
    />
    <MultipleCashCallEmailPrefill
      :show="getShowMultipleCashCallModal"
      :bills="getDataMultipleCashCallModal"
      @hidden="closeMultipleCashCallModal"
    />
  </b-container>
</template>

<script>
import debounce from 'lodash/debounce';

import { mapGetters, mapMutations, mapActions } from 'vuex';
import FinancesTable from '@/components/Pages/Finances/sections/FinancesTable';

import BillsEnglishVersion from '@/components/Pages/Finances/modals/BillsEnglishVersion';
import FrenchBillPrefillModal from '@/components/Pages/Finances/modals/FrenchBillPrefillModal.vue';
import SendCashCallModal from '@/components/Pages/Finances/modals/SendCashCallModal/SendCashCallModal';
import CashCallEmailPrefill from '@/components/Pages/Finances/modals/CashCallEmailPrefillModal';
import CashCallMembershipEmailPrefill from '@/components/Pages/Finances/modals/CashCallMembershipEmailPrefillModal';
import MultipleCashCallEmailPrefill from '@/components/Pages/Finances/modals/MultipleCashCallEmailPrefillModal';

export default {
  name: 'Finances',
  components: {
    FinancesTable,
    BillsEnglishVersion,
    FrenchBillPrefillModal,
    SendCashCallModal,
    CashCallEmailPrefill,
    CashCallMembershipEmailPrefill,
    MultipleCashCallEmailPrefill,
  },
  computed: {
    ...mapGetters([
      'getShowBillUkModal',
      'getShowBillFRModal',
      'getShowSendEmailModal',
      'getShowCashCallModal',
      'getShowCashCallMembershipModal',
      'getShowMultipleCashCallModal',
      'getDataBillUkModal',
      'getDataBillFRModal',
      'getDataSendEmailModal',
      'getDataCashCallModal',
      'getDataCashCallMembershipModal',
      'getDataMultipleCashCallModal',
      'isFinanceTableLoading',
      'financesTableFilters',
    ]),
  },
  data() {
    return {
      selects: {
        bill_type_choices: [],
        bill_status_choices: [],
        bill_year_choices: [],
      },
      search_field: 'investor_name',
      search_value: null,
    };
  },
  methods: {
    ...mapMutations([
      'setShowBillUkModal',
      'setShowBillFRModal',
      'setShowSendEmailModal',
      'setShowCashCallModal',
      'setShowCashCallMembershipModal',
      'setShowMultipleCashCallModal',
      'setDataBillUkModal',
      'setDataBillFRModal',
      'setDataSendEmailModal',
      'setDataCashCallModal',
      'setDataCashCallMembershipModal',
      'setDataMultipleCashCallModal',
      'setFinanceTableLoading',
      'updateFinanceTableFilters',
    ]),
    ...mapActions(['getAllBills', 'getCurrencies']),
    // ...mapActions(['getAllBills', 'getCurrencies', 'getFinanceTableData']),
    getBills() {
      this.getAllBills(this.financesTableFilters);
      // this.getFinanceTableData(this.financesTableFilters);
    },
    searchUpdateDebounced: debounce(function (value, field) {
      this.filterBills(value, field);
    }, 500),
    filterBills(value, field) {
      const filterObj = {};
      filterObj[field] = value;
      if (field == 'investor_name') {
        filterObj.fundraising_name = null;
      }
      if (field == 'fundraising_name') {
        filterObj.investor_name = null;
      }
      this.updateFinanceTableFilters(filterObj);
      this.getBills();
    },
    getChoices() {
      this.apiGet('choices/?choice=bill_type_choices').then(
        (response) => {
          this.selects.bill_type_choices = response.data;
        },
        () => {},
      );
      this.selects.bill_status_choices = [
        { text: 'Pending', value: 'CREATED' },
        { text: 'Paid', value: 'SUCCEEDED' },
        { text: 'Expired', value: 'FAILED' },
      ];
      for (let year = 2013; year < 2024; year++) {
        this.selects.bill_year_choices.push({ text: year, value: year });
      }
    },
    closeBillUkModal() {
      this.setShowBillUkModal(false);
      this.setDataBillUkModal({});
    },
    closeBillFRModal() {
      this.setShowBillFRModal(false);
      this.setDataBillFRModal({});
    },
    closeSendEmailModal() {
      this.setShowSendEmailModal(false);
      this.setDataSendEmailModal({});
    },
    closeCashCallModal() {
      this.setShowCashCallModal(false);
      this.setDataCashCallModal({});
    },
    closeCashCallMembershipModal() {
      this.setShowCashCallMembershipModal(false);
      this.setDataCashCallMembershipModal({});
    },
    closeMultipleCashCallModal() {
      this.setShowMultipleCashCallModal(false);
      this.setDataMultipleCashCallModal([]);
    },
  },
  mounted() {
    document.title = 'OneRagtime - Core';
    if (!this.$store.getters.isOrtFinance) {
      this.$router.push({ name: 'Dashboard' });
    } else {
      this.$store.dispatch('focusSection', 'Finances');
      this.getChoices();
      this.getBills();
      // this.getFinanceTableData();
      this.getCurrencies();
    }
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';
.title {
  display: flex;
  justify-content: center;
}
.detail {
  width: 63px;
  height: 8px;
  border-radius: 4.5px;
  background-image: linear-gradient(to right, #f1aeab 0%, #8471b0 160%);
  background-color: rgba(241, 174, 171, 0.05);
}
.background-color {
  background-color: rgba(241, 174, 171, 0.05);
}
.search-field-selector {
  margin-top: 25px;
}
.valign-text-top {
  vertical-align: text-top;
}
</style>
