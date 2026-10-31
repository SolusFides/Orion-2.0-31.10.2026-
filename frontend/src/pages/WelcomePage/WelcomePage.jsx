
import { useDispatch } from 'react-redux';

import { setPage } from '../../store/navigationSlice';
import { setAuthMode } from '../../store/authSlice';

function WelcomePage() {
  const dispatch = useDispatch();

  const handleLogin = () => {
    dispatch(setAuthMode('login'));
    dispatch(setPage('login'));
  };

  const handleRegister = () => {
    dispatch(setAuthMode('register'));
    dispatch(setPage('login'));
  };

  return (
    <main>
      <h1>У вас есть умный дом?</h1>

      <p>
        Подключим ваши устройства Ujin или поможем собрать дом с нуля.
        Сценарии заработают сразу — даже до покупки устройств.
      </p>

      <div>
        <button onClick={handleLogin}>
          Да, у меня есть умный дом
        </button>

        <button onClick={handleRegister}>
          Нет, хочу собрать с нуля
        </button>
      </div>
    </main>
  );
}

export default WelcomePage;
