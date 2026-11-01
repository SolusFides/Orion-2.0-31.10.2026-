
import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';

import { setPage } from '../../store/navigationSlice';

function LoginPage() {
  const dispatch = useDispatch();

  const authMode = useSelector(
    (state) => state.auth.authMode
  );

  const isLogin = authMode === 'login';

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = () => {
    localStorage.setItem('username', username);
    localStorage.setItem('password', password);

    if (isLogin) {
      dispatch(setPage('home'));
    } else {
      dispatch(setPage('room-selection'));
    }
  };

  return (
    <main>
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>

      <form>
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

        <button type="button" onClick={handleSubmit}>
          {isLogin ? 'Войти' : 'Зарегистрироваться'}
        </button>
      </form>
    </main>
  );
}

export default LoginPage;
