
import { useSelector, useDispatch } from 'react-redux';

import { setPage } from '../../store/navigationSlice';

function LoginPage() {
  const dispatch = useDispatch();

  const authMode = useSelector(
    (state) => state.auth.authMode
  );

  const isLogin = authMode === 'login';

  const handleLogin = () => {
    dispatch(setPage('home'));
  };

  const handleRegister = () => {
    dispatch(setPage('room-selection'));
  };

  return (
    <main>
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>

      <form>
        <div>
          <label htmlFor="email">Электронная почта</label>
          <input
            id="email"
            type="email"
            name="email"
            placeholder="Введите электронную почту"
          />
        </div>

        <div>
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            name="password"
            placeholder="Введите пароль"
          />
        </div>

        {isLogin ? (
          <button type="button" onClick={handleLogin}>
            Войти
          </button>
        ) : (
          <button type="button" onClick={handleRegister}>
            Зарегистрироваться
          </button>
        )}
      </form>
    </main>
  );
}

export default LoginPage;
