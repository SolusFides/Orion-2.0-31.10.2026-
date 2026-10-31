
import { useSelector, useDispatch } from 'react-redux';

import { setPage } from '../../store/navigationSlice';

function LoginPage() {
  const dispatch = useDispatch();

  const authMode = useSelector(
    (state) => state.auth.authMode
  );

  const isLogin = authMode === 'login';

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!isLogin) {
      dispatch(setPage('room-selection'));
    }
  };

  return (
    <main>
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>

      <form onSubmit={handleSubmit}>
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

        <button type="submit">
          {isLogin ? 'Войти' : 'Зарегистрироваться'}
        </button>
      </form>
    </main>
  );
}

export default LoginPage;
