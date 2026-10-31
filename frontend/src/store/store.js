
import { configureStore } from '@reduxjs/toolkit';

import navigationReducer from './navigationSlice';
import scenarioReducer from './scenarioSlice';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: {
    navigation: navigationReducer,
    scenarios: scenarioReducer,
    auth: authReducer
  }
});
