
import { createSlice } from '@reduxjs/toolkit';

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    authMode: 'login'
  },
  reducers: {
    setAuthMode: (state, action) => {
      state.authMode = action.payload;
    }
  }
});

export const { setAuthMode } = authSlice.actions;

export default authSlice.reducer;
