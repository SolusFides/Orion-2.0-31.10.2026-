
import { createSlice } from '@reduxjs/toolkit';

const navigationSlice = createSlice({
  name: 'navigation',
  initialState: {
    currentPage: 'welcome',
    selectedRoomId: null,
    selectedDeviceId: null
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
    }
  }
});

export const {
  setPage,
  setRoom,
  setDevice
} = navigationSlice.actions;

export default navigationSlice.reducer;
