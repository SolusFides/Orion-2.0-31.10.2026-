import { useDispatch, useSelector } from 'react-redux';
import { setPage } from '../../store/navigationSlice';

function DevicePage() {
  const dispatch = useDispatch();

  const selectedDeviceId = useSelector(
    (state) => state.navigation.selectedDeviceId
  );

  const devices = {
    1: {
      name: 'Умная лампа',
      type: 'Освещение',
      online: true,
      state: 'Включена',
      parameters: [
        { name: 'Яркость', value: '80%' },
        { name: 'Цветовая температура', value: '4000 K' },
        { name: 'Мощность', value: '12 W' },
      ],
    },
    2: {
      name: 'Кондиционер',
      type: 'Климат',
      online: true,
      state: 'Выключен',
      parameters: [
        { name: 'Температура', value: '22 °C' },
        { name: 'Режим', value: 'Охлаждение' },
        { name: 'Скорость вентилятора', value: 'Авто' },
      ],
    },
  };

  const device = devices[selectedDeviceId];

  if (!device) {
    return (
      <section className="device-page">
        <button onClick={() => dispatch(setPage('room-devices'))}>
          ← Назад
        </button>
        <h1>Устройство не найдено</h1>
      </section>
    );
  }

  return (
    <section>
      <button onClick={() => dispatch(setPage('room-devices'))}>
        ← Назад
      </button>

      <h1>{device.name}</h1>

      <p>Тип: {device.type}</p>
      <p>Подключение: {device.online ? 'В сети' : 'Не в сети'}</p>
      <p>Состояние: {device.state}</p>

      <div>
        <h2>Параметры</h2>

        {device.parameters.map((parameter) => (
          <p key={parameter.name}>
            {parameter.name}: {parameter.value}
          </p>
        ))}
      </div>

      <div>
        <h2>Управление</h2>
        <button onClick={() => console.log('Включение устройства')}>
          Включить
        </button>
        <button onClick={() => console.log('Выключение устройства')}>
          Выключить
        </button>
      </div>

      <div>
        <h2>Сохранённые настройки</h2>
        <button onClick={() => console.log('Сохранение настроек')}>
          Сохранить текущие настройки
        </button>
        <button onClick={() => console.log('Загрузка настроек')}>
          Загрузить настройки
        </button>
      </div>

      <button onClick={() => console.log('Проверка устройства')}>
        Проверить устройство
      </button>
    </section>
  );
}

export default DevicePage;