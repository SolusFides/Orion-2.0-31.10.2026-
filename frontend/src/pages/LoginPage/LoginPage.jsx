import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';

import { setPage } from '../../store/navigationSlice';
import { loginUser } from '../../store/authSlice';

function LoginPage() {
  const dispatch = useDispatch();

  const authMode = useSelector(
    (state) => state.auth.authMode
  );

  const status = useSelector((state) => state.auth.status);
  const error = useSelector((state) => state.auth.error);

  const isLogin = authMode === 'login';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!isLogin) {
      dispatch(setPage('room-selection'));
      return;
    }

    try {
      await dispatch(loginUser({ username, password })).unwrap();
    } catch {
      console.error('Ошибка авторизации');
    }

    dispatch(setPage('home'));
  };

  return (
    <main>
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Логин</label>
          <input
            id="username"
            type="text"
            name="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Введите логин"
          />
        </div>

        <div>
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            name="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Введите пароль"
          />
        </div>

        <button type="submit" disabled={status === 'loading'}>
          {status === 'loading' ? 'Выполняется вход...' : isLogin ? 'Войти' : 'Зарегистрироваться'}
        </button>

        {error && <p>{JSON.stringify(error)}</p>}
      </form>
    </main>
  );
}

export default LoginPage;
