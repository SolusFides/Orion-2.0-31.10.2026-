import { configureStore } from '@reduxjs/toolkit';

import navigationReducer from './navigationSlice';
import scenarioReducer from './scenarioSlice';

export const store = configureStore({
  reducer: {
    navigation: navigationReducer,
    scenarios: scenarioReducer
  }
});