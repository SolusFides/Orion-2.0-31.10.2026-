import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async ({ username, password }, { rejectWithValue }) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username,
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return rejectWithValue(data.detail || 'Ошибка авторизации');
      }

      return data;
    } catch {
      return rejectWithValue('Не удалось связаться с сервером');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',

  initialState: {
    authMode: 'login',
    accessToken: null,
    tokenType: null,
    expiresIn: null,
    isAuthenticated: false,
    status: 'idle',
    error: null,
  },

  reducers: {
    setAuthMode: (state, action) => {
      state.authMode = action.payload;
    },
  },

  extraReducers: (builder) => {
    builder
      .addCase(loginUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.accessToken = action.payload.access_token;
        state.tokenType = action.payload.token_type;
        state.expiresIn = action.payload.expires_in;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
        state.isAuthenticated = false;
      });
  },
});

export const { setAuthMode } = authSlice.actions;

export default authSlice.reducer;