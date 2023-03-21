<template>
  <div class="w-100">
    <b-row class="d-flex justify-content-end mb-4 mr-2">
      <btn
        v-if="selected_tab == 'bills'"
        class="bill-selection-btn mr-3"
        size="fluid"
        :color="isBillSelectionReady ? 'red-gradient' : 'grey'"
        @click="showMultipleEmailModal(true)"
      >
        Bill selection
      </btn>
      <btn
        size="fluid"
        color="purple-gradient"
        class="bill-selection-btn"
        :loading="isFinanceExportButtonLoading"
        @click="exportExcelBills(financesTableFilters)"
      >
        <i class="fas fa-download" aria-hidden="true"></i>
        Export into excel
      </btn>
    </b-row>
    <div class="table-container content">
      <div class="tabs-div" id="tabs">
        <div
          v-on:click="selected_tab = 'bills'"
          class="custom-tabs separator"
          :class="{ 'tab-focused': selected_tab == 'bills' }"
        >
          <span class="icon-bill"><i class="far fa-file-invoice-dollar icon"></i></span>
          <span class="text-tab-bills">BILLS & CASH CALLS</span>
        </div>
        <div
          v-on:click="selected_tab = 'multiple-bills'"
          class="custom-tabs"
          :class="{ 'tab-focused': selected_tab == 'multiple-bills' }"
        >
          <span class="icon-list"><i class="fas fa-list icon"></i></span>
          <span class="text-tab-multiple">MULTIPLE BILLS CASH CALLS</span>
        </div>
      </div>
      <div v-if="selected_tab == 'bills'" style="overflow-x:auto">
        <BillsAndCashCallsTable />
      </div>
      <div v-else-if="selected_tab == 'multiple-bills'" style="overflow-x:auto">
        <MultipleBillsCashCallsTable />
      </div>
    </div>
    <div>
      <b-row class="d-flex justify-content-end mr-2">
        <label for="results">Total bills:</label>
        <span>
          {{ this.billsPagination.count }}
        </span>
      </b-row>
      <b-row class="d-flex justify-content-between">
        <b-col cols="1">
          <btn
            size="fluid"
            v-bind:disabled="!billsPagination.previous"
            :color="billsPagination.previous ? 'red-gradient' : 'grey'"
            @click="updatePreviousBillsTableData()"
          >
            previous
          </btn>
        </b-col>
        <b-col cols="1" class="ml-2">
          <btn
            size="fluid"
            v-bind:disabled="!billsPagination.next"
            :color="billsPagination.next ? 'red-gradient' : 'grey'"
            @click="updateNextBillsTableData()"
          >
            next
          </btn>
        </b-col>
      </b-row>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions, mapMutations } from 'vuex';
import BillsAndCashCallsTable from '@/components/Pages/Finances/sections/BillsAndCashCallsTable';
import MultipleBillsCashCallsTable from '@/components/Pages/Finances/sections/MultipleBillsCashCallsTable';

export default {
  name: 'FinancesTable',
  components: {
    BillsAndCashCallsTable,
    MultipleBillsCashCallsTable,
  },
  data() {
    return {
      bills: {},
      selected_tab: 'bills',
    };
  },
  computed: {
    ...mapGetters([
      'billsPagination',
      'getDataMultipleCashCallModal',
      'financesTableFilters',
      'isFinanceExportButtonLoading',
    ]),
    isBillSelectionReady() {
      return this.getDataMultipleCashCallModal.length > 1;
    },
  },
  methods: {
    ...mapActions(['exportExcelBills', 'updateNextBillsTableData', 'updatePreviousBillsTableData']),
    ...mapMutations(['setBills', 'setBillsPagination', 'setShowMultipleCashCallModal']),
    showMultipleEmailModal(bool) {
      const show = bool && this.isBillSelectionReady;
      this.setShowMultipleCashCallModal(show);
    },
  },
};
</script>

<style lang="scss" scoped>
@import 'src/assets/css/global.scss';

.table-container {
  overflow-x: auto;
  box-shadow: 0 4px 15px 0 rgba(221, 221, 221, 0.8);
  border-radius: 10px;
  width: 100%;
  .tabs-div {
    width: 100%;
    display: flex;
    justify-content: space-around;
    font: $main-font-semibold;
    cursor: pointer;
    .tab-focused {
      color: $red-color;
      border-bottom: solid 3px $red-color;
      background-color: rgba(241, 174, 171, 0.05);
    }
  }
  .separator {
    border-right: 1px solid $grey-color;
  }
  .custom-tabs {
    width: 100%;
    background-color: $white-color;
    padding: 13px;
    display: flex;
    justify-content: center;
    border-bottom: 1px solid $grey-color;
    font-size: $medium-font-size;
    font-weight: 700;
    color: $warm-grey-color;
    transition: background 0.2s ease, color 0.2s ease;
    &:hover {
      color: $red-color;
      background-color: rgba(241, 174, 171, 0.05);
    }
    .icon-list {
      padding: 0 10px 0 0 !important;
    }
    .icon-bill {
      padding: 0 10px 0 0;
    }
  }
}
.bill-selection-btn {
  width: 150px !important;
}
button.button.button-fluid.button-red-gradient {
  width: 70px;
}
button.button.button-fluid.button-grey {
  width: 70px;
}
</style>
