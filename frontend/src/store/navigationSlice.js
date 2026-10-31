import { createSlice } from '@reduxjs/toolkit';

const navigationSlice = createSlice({
  name: 'navigation',
  initialState: {
    currentPage: 'home',
    selectedRoomId: null,
    selectedDeviceId: null,
    selectedScenarioId: null
  },
  reducers: {
    setPage: (state, action) => {
      state.currentPage = action.payload;
    },
    setRoom: (state, action) => {
      state.selectedRoomId = action.payload;
    },
    setDevice: (state, action) => {
      state.selectedDeviceId = action.payload;
    },
    setScenario: (state, action) => {
      state.selectedScenarioId = action.payload;
    }
  }
});

export const {
  setPage,
  setRoom,
  setDevice,
  setScenario
} = navigationSlice.actions;

export default navigationSlice.reducer;