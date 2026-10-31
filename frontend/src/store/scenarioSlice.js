import { createSlice } from '@reduxjs/toolkit';

const scenarioSlice = createSlice({
  name: 'scenarios',
  initialState: {
    selectedScenario: null,
    scenarios: []
  },
  reducers: {
    setSelectedScenario: (state, action) => {
      state.selectedScenario = action.payload;
    },
    clearSelectedScenario: (state) => {
      state.selectedScenario = null;
    },
    setScenarios: (state, action) => {
      state.scenarios = action.payload;
    }
  }
});

export const {
  setSelectedScenario,
  clearSelectedScenario,
  setScenarios
} = scenarioSlice.actions;

export default scenarioSlice.reducer;